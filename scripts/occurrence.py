"""Per-occurrence lemma resolution for ambiguous surfaces.

Most surfaces have one lemma, and the lemma map gives each type exactly one.
Some do not:

  participles   `educados` is the verb educar in "foram educados" and the
                adjective educado in "são muito educados"
  fomos-type    `fomos` is ser or ir depending on the sentence

eval/conventions.md asks for these to be resolved per occurrence by a
tagger, not assigned wholesale to one lemma.  Pass 2 has already sampled up
to K sentences for every frequent type; Stanza tags the surface in each, and
the surface's corpus count is divided across lemmas in proportion to those
tags.  With K = 5 the split has a granularity of 20%.

Rules per tagged occurrence:
  participle, VERB/AUX  -> the infinitive (Stanza's lemma, dictionary-gated)
  participle, ADJ       -> the masculine singular participle (educado),
                           per convention 2: adjectives fold to masculine
  participle, NOUN      -> the noun itself (batida, ferida), per convention
                           2: nouns keep the feminine
  ambiguous form        -> Stanza's lemma, dictionary-gated
"""

from __future__ import annotations

import re
import sys
import time
from collections import Counter
from typing import Any, Callable, Mapping, Sequence

_PARTICIPLE = re.compile(r"(?:ad|id|íd)(?:o|a|os|as)$")

# -- candidate selection ----------------------------------------------------


def _singular(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def adjective_form(surface: str) -> str:
    """educadas -> educado, morta -> morto."""
    sg = _singular(surface)
    return sg[:-1] + "o" if sg.endswith("a") else sg


def noun_form(surface: str) -> str:
    """batidas -> batida: a noun keeps its gender."""
    return _singular(surface)


def is_participle_candidate(surface: str, cfg: dict[str, Any]) -> bool:
    if "-" in surface or len(surface) < 4:
        return False
    irregular = set(cfg["fixes"].get("irregular_participles", ()))
    return bool(_PARTICIPLE.search(surface)) or _singular(surface) in irregular \
        or adjective_form(surface) in irregular


def candidates(
    counts: Mapping[str, int], cfg: dict[str, Any], min_count: int
) -> list[str]:
    ambiguous = set(cfg["fixes"].get("ambiguous_forms", ()))
    return sorted(
        t for t, c in counts.items()
        if c >= min_count and (t in ambiguous or is_participle_candidate(t, cfg))
    )


# -- tagging (Stanza over sampled contexts) -------------------------------

_NLP = None
_CTX: dict[str, list[str]] = {}


def _init(lang: str, contexts: dict[str, list[str]]) -> None:
    global _NLP, _CTX
    import os

    os.environ.setdefault("OMP_NUM_THREADS", "1")
    import torch

    torch.set_num_threads(1)
    import stanza

    _NLP = stanza.Pipeline(lang=lang, processors="tokenize,mwt,pos,lemma",
                           verbose=False, tokenize_no_ssplit=True)
    _CTX = contexts


def _tag_chunk(types: list[str]) -> dict[str, list[tuple[str, str, str]]]:
    from stanza import Document

    texts, owners = [], []
    for t in types:
        for text in _CTX.get(t) or []:
            texts.append(text)
            owners.append(t)
    out: dict[str, list[tuple[str, str, str]]] = {t: [] for t in types}
    if texts:
        docs = _NLP.bulk_process([Document([], text=x) for x in texts])
        for t, doc in zip(owners, docs):
            for sent in doc.sentences:
                for w in sent.words:
                    if w.text.lower() == t:
                        out[t].append(((w.lemma or t).lower(), w.upos or "", w.feats or ""))
                        break
    return out


def tag(
    types: Sequence[str], contexts: Mapping[str, Sequence[str]], cfg: dict[str, Any]
) -> dict[str, list[tuple[str, str, str]]]:
    """(lemma, upos, feats) for each sampled occurrence of each type."""
    import multiprocessing as mp

    types = list(types)
    if not types:
        return {}
    lem = cfg["lemmatizer"]
    ctx = {t: list(contexts.get(t, ())) for t in types}
    chunk = lem.get("stanza_chunk", 200)
    slices = [types[i:i + chunk] for i in range(0, len(types), chunk)]
    out: dict[str, list[tuple[str, str, str]]] = {}
    started = time.monotonic()
    with mp.get_context("spawn").Pool(
        processes=lem.get("stanza_workers", 4), initializer=_init,
        initargs=(lem["stanza_lang"], ctx),
    ) as pool:
        for i, part in enumerate(pool.imap(_tag_chunk, slices, chunksize=1), 1):
            out.update(part)
            if i % 10 == 0 or i == len(slices):
                rate = len(out) / max(time.monotonic() - started, 1e-9)
                print(f"    occurrence tagging {len(out):,}/{len(types):,} ({rate:.1f}/s)",
                      file=sys.stderr, flush=True)
    return out


def cache_path(cfg: dict[str, Any], types: Sequence[str]):
    import hashlib
    import json
    from pathlib import Path

    h = hashlib.sha256("\x00".join(types).encode("utf-8")).hexdigest()[:16]
    material = {"types": h, "context": cfg["lemmatizer"]["context"],
                "lang": cfg["lemmatizer"]["stanza_lang"], "tok": cfg["tokenizer"]}
    d = hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()[:16]
    return Path(cfg["paths"]["cache_dir"]) / f"occurrences_{d}.json.gz"


def tag_cached(types, contexts, cfg):
    import gzip
    import json

    path = cache_path(cfg, types)
    if path.is_file():
        print(f"  occurrences: reusing cache {path}", file=sys.stderr)
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return {k: [tuple(x) for x in v] for k, v in json.load(fh).items()}
    result = tag(types, contexts, cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, sort_keys=True)
    return result


# -- resolution --------------------------------------------------------------


def resolve(
    tagged: Mapping[str, Sequence[tuple[str, str, str]]],
    lemma_map: Mapping[str, str],
    cfg: dict[str, Any],
    in_dictionary: Callable[[str], bool],
    fallback: Callable[[str], str],
) -> dict[str, Counter]:
    """Votes per lemma for each tagged surface.  Only surfaces with at least
    one usable tagged occurrence are returned; the rest keep their map lemma."""
    ambiguous = set(cfg["fixes"].get("ambiguous_forms", ()))
    out: dict[str, Counter] = {}
    for surface in sorted(tagged):
        occs = tagged[surface]
        if not occs:
            continue
        default = lemma_map.get(surface, surface)
        votes: Counter = Counter()
        participle = surface not in ambiguous
        for lemma, upos, feats in occs:
            gated = lemma if in_dictionary(lemma) else None
            if participle:
                if upos in ("VERB", "AUX"):
                    verb = gated or fallback(surface)
                    votes[verb if in_dictionary(verb) else default] += 1
                elif upos == "ADJ":
                    votes[adjective_form(surface)] += 1
                elif upos == "NOUN":
                    votes[noun_form(surface)] += 1
                else:
                    votes[default] += 1
            else:
                votes[gated or default] += 1
        out[surface] = votes
    return out


def apportion(count: int, votes: Mapping[str, int]) -> dict[str, int]:
    """Split an integer count by votes, exactly and deterministically
    (largest remainder; ties to the lexicographically smaller lemma)."""
    total = sum(votes.values())
    if total == 0:
        return {}
    shares = {k: count * v / total for k, v in votes.items()}
    base = {k: int(v) for k, v in shares.items()}
    left = count - sum(base.values())
    order = sorted(votes, key=lambda k: (-(shares[k] - base[k]), k))
    for k in order[:left]:
        base[k] += 1
    return {k: v for k, v in base.items() if v}
