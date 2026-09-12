"""Pluggable lemmatization backends.

README pipeline step 2: lemmatize the type inventory, correct known errors
via an override table, and validate against the pyspellchecker PT dictionary
(rejected lemmas fall back to the surface form).

The original used simplemma alone.  Here the lemmatizer is a swappable
backend so that simplemma, spaCy, Stanza and a majority vote among them can
be scored against the hand-checked gold set in eval/ and compared on equal
terms.

Context.  simplemma is type-level: it sees a bare word.  spaCy and Stanza
are context-sensitive and lemmatize far better given a real sentence, but
running them over 624M tokens is infeasible.  The compromise is sampled
context: pass 2 reservoir-samples a few sentences per surface type, the
backend lemmatizes the word inside those sentences, and the majority lemma
wins.  That also gives a principled way to split forms that are genuinely
ambiguous between lemmas -- `foi`/`fomos` are preterite of both `ser` and
`ir` -- by voting over real usage instead of guessing from a lookup table.
"""

from __future__ import annotations

import functools
from collections import Counter
from typing import Any, Iterable, Mapping, Protocol, Sequence, runtime_checkable

Contexts = Mapping[str, Sequence[str]]


# -- dictionary -----------------------------------------------------------


@functools.lru_cache(maxsize=4)
def pt_dictionary(lang: str = "pt") -> frozenset[str]:
    """The pyspellchecker PT word list, used to validate proposed lemmas.

    Also used by the Stage 2 diacritic-folding fix, where the check is what
    stops real minimal pairs (e/é, da/dá, esta/está) being merged.
    """
    from spellchecker import SpellChecker

    return frozenset(SpellChecker(language=lang).word_frequency.dictionary.keys())


def in_dictionary(word: str, lang: str = "pt") -> bool:
    return word.lower() in pt_dictionary(lang)


# -- backends -------------------------------------------------------------


@runtime_checkable
class LemmaBackend(Protocol):
    name: str

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        """Map each surface type to a lemma.  Must be deterministic."""
        ...


class SimplemmaBackend:
    """Lookup-based, type-level.  Ignores context by construction."""

    name = "simplemma"

    def __init__(self, lang: str = "pt", greedy: bool = False) -> None:
        self.lang = lang
        self.greedy = greedy

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        import simplemma

        out: dict[str, str] = {}
        for surface in types:
            try:
                out[surface] = simplemma.lemmatize(
                    surface, lang=self.lang, greedy=self.greedy
                ).lower()
            except Exception:
                out[surface] = surface
        return out


class SpacyBackend:
    """spaCy pipeline.  Uses sampled sentence context when available.

    With context, each sampled sentence is parsed and the lemma of the token
    matching the surface form is taken; the majority lemma wins, ties broken
    lexicographically so the result is deterministic.  Without context the
    word is parsed alone, which is markedly weaker -- that difference is the
    whole reason sampled context exists.
    """

    name = "spacy"

    def __init__(self, model: str = "pt_core_news_lg", batch_size: int = 256) -> None:
        self.model = model
        self.batch_size = batch_size
        self._nlp = None

    def _load(self):
        if self._nlp is None:
            import spacy

            # The lemmatizer needs the tagger/morphologizer, not the parser
            # or NER; disabling those is a large speedup at no cost here.
            self._nlp = spacy.load(self.model, exclude=["parser", "ner"])
        return self._nlp

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        nlp = self._load()
        out: dict[str, str] = {}

        with_ctx = [t for t in types if contexts and contexts.get(t)]
        without_ctx = [t for t in types if not (contexts and contexts.get(t))]

        # Bare-word path.
        for surface, doc in zip(
            without_ctx, nlp.pipe(without_ctx, batch_size=self.batch_size)
        ):
            out[surface] = (doc[0].lemma_ or surface).lower() if len(doc) else surface

        # Sampled-context path: one flat stream of sentences keeps nlp.pipe
        # batching effective.
        flat: list[str] = []
        owner: list[str] = []
        for surface in with_ctx:
            for sent in contexts[surface]:  # type: ignore[index]
                flat.append(sent)
                owner.append(surface)

        votes: dict[str, Counter] = {t: Counter() for t in with_ctx}
        for surface, doc in zip(owner, nlp.pipe(flat, batch_size=self.batch_size)):
            for token in doc:
                if token.text.lower() == surface:
                    votes[surface][(token.lemma_ or surface).lower()] += 1

        for surface in with_ctx:
            out[surface] = _majority(votes[surface], fallback=surface)
        return out


class StanzaBackend:
    """Stanza pipeline.  Not installed by default; import is deferred."""

    name = "stanza"

    def __init__(self, lang: str = "pt") -> None:
        self.lang = lang
        self._nlp = None

    def _load(self):
        if self._nlp is None:
            import stanza

            self._nlp = stanza.Pipeline(
                lang=self.lang, processors="tokenize,pos,lemma", verbose=False
            )
        return self._nlp

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        nlp = self._load()
        out: dict[str, str] = {}
        for surface in types:
            sents = list(contexts.get(surface, ())) if contexts else []
            votes: Counter = Counter()
            for text in sents or [surface]:
                doc = nlp(text)
                for sent in doc.sentences:
                    for word in sent.words:
                        if word.text.lower() == surface:
                            votes[(word.lemma or surface).lower()] += 1
            out[surface] = _majority(votes, fallback=surface)
        return out


# Stanza worker state, set by the pool initializer.
_STANZA_NLP = None
_STANZA_CTX: dict[str, list[str]] = {}


def _init_stanza_worker(lang: str, contexts: dict[str, list[str]]) -> None:
    global _STANZA_NLP, _STANZA_CTX
    import os

    # One torch thread per worker: the parallelism is across processes, and
    # letting each worker spawn its own thread pool oversubscribes the CPU.
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    import torch

    torch.set_num_threads(1)
    import stanza

    _STANZA_NLP = stanza.Pipeline(
        lang=lang, processors="tokenize,pos,lemma", verbose=False,
        tokenize_no_ssplit=True,
    )
    _STANZA_CTX = contexts


def _stanza_chunk(types: list[str]) -> dict[str, str]:
    """Lemmatize a slice of types, batching every sentence into one call.

    Feeding sentences to the pipeline one at a time wastes most of Stanza's
    throughput -- measured 242 ms/type that way even across 4 processes.
    Batching the whole slice through ``bulk_process`` amortizes the neural
    forward passes over many sentences at once.
    """
    assert _STANZA_NLP is not None
    from stanza import Document

    texts: list[str] = []
    owners: list[str] = []
    for surface in types:
        for text in _STANZA_CTX.get(surface) or [surface]:
            texts.append(text)
            owners.append(surface)

    votes: dict[str, Counter] = {t: Counter() for t in types}
    if texts:
        docs = _STANZA_NLP.bulk_process([Document([], text=t) for t in texts])
        for surface, doc in zip(owners, docs):
            for sent in doc.sentences:
                for word in sent.words:
                    if word.text.lower() == surface:
                        votes[surface][(word.lemma or surface).lower()] += 1

    return {t: _majority(votes[t], fallback=t) for t in types}


class ParallelStanzaBackend:
    """Stanza across a process pool.

    Stanza is ~1000x slower per type than simplemma, so a full-inventory run
    is impractical single-threaded (measured: 309 ms/type, ~6 h for 70k
    types).  Each worker loads its own pipeline and handles a contiguous
    slice of the type list; slices are recombined in order, so the result
    does not depend on scheduling.
    """

    name = "stanza"

    def __init__(self, lang: str = "pt", workers: int = 4, chunk: int = 200) -> None:
        self.lang = lang
        self.workers = workers
        self.chunk = chunk

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        import multiprocessing as mp
        import sys
        import time

        types = list(types)
        if not types:
            return {}
        ctx = {t: list(contexts.get(t, ())) for t in types} if contexts else {}
        slices = [types[i : i + self.chunk] for i in range(0, len(types), self.chunk)]

        out: dict[str, str] = {}
        started = time.monotonic()
        mpctx = mp.get_context("spawn")
        with mpctx.Pool(
            processes=self.workers,
            initializer=_init_stanza_worker,
            initargs=(self.lang, ctx),
        ) as pool:
            for i, part in enumerate(pool.imap(_stanza_chunk, slices, chunksize=1), 1):
                out.update(part)
                if i % 10 == 0 or i == len(slices):
                    done = len(out)
                    rate = done / max(time.monotonic() - started, 1e-9)
                    eta = (len(types) - done) / rate if rate else float("nan")
                    print(
                        f"    stanza {done:,}/{len(types):,} types "
                        f"({rate:.1f}/s, eta {eta / 60:.0f}m)",
                        file=sys.stderr, flush=True,
                    )
        return out


class TieredBackend:
    """Expensive backend for frequent types, cheap backend for the tail.

    Only types frequent enough to reach the published bands justify the
    expensive lemmatizer.  ``min_count`` is derived from the count at the
    last published rank divided by a safety factor, so a surface well below
    the cutoff can still be lemmatized accurately if several surfaces
    aggregate onto one lemma.
    """

    def __init__(
        self,
        primary: "LemmaBackend",
        fallback: "LemmaBackend",
        counts: Mapping[str, int],
        min_count: int,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.counts = counts
        self.min_count = min_count
        self.name = f"tiered({primary.name}>={min_count},{fallback.name})"

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        import sys

        hot = [t for t in types if self.counts.get(t, 0) >= self.min_count]
        tail = [t for t in types if self.counts.get(t, 0) < self.min_count]
        print(
            f"  tiered: {len(hot):,} types -> {self.primary.name}, "
            f"{len(tail):,} -> {self.fallback.name}",
            file=sys.stderr, flush=True,
        )
        out = self.fallback.lemmatize_types(tail, contexts) if tail else {}
        if hot:
            out.update(self.primary.lemmatize_types(hot, contexts))
        return out


class VoteBackend:
    """Majority vote across member backends.

    Ties are broken by the configured priority order rather than by whichever
    backend happens to be listed first in a dict, so the result does not
    depend on iteration order.
    """

    name = "vote"

    def __init__(self, members: Sequence[LemmaBackend], tiebreak: Sequence[str]) -> None:
        if not members:
            raise ValueError("vote backend needs at least one member")
        self.members = list(members)
        self.tiebreak = list(tiebreak)
        if len(self.members) == 2:
            # With two members every disagreement is a 1-1 tie, so the
            # tiebreak backend always wins and the vote is just that backend
            # wearing a hat. Three or more is needed for a real majority.
            import warnings

            warnings.warn(
                "VoteBackend with 2 members is equivalent to the first "
                f"tiebreak backend ({self.tiebreak[0] if self.tiebreak else '?'}); "
                "add a third member for a meaningful majority.",
                stacklevel=2,
            )

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        per_backend = {
            m.name: m.lemmatize_types(types, contexts) for m in self.members
        }
        out: dict[str, str] = {}
        for surface in types:
            votes: Counter = Counter()
            for name, mapping in per_backend.items():
                votes[mapping.get(surface, surface)] += 1
            top = max(votes.values())
            winners = sorted(w for w, c in votes.items() if c == top)
            if len(winners) == 1:
                out[surface] = winners[0]
                continue
            # Tie: defer to the highest-priority backend that proposed one
            # of the tied candidates.
            chosen = None
            for name in self.tiebreak:
                candidate = per_backend.get(name, {}).get(surface)
                if candidate in winners:
                    chosen = candidate
                    break
            out[surface] = chosen if chosen is not None else winners[0]
        return out


class GatedBackend:
    """Primary backend with a dictionary-validated fallback.

    Stanza is the most accurate backend on European Portuguese but it
    occasionally emits forms that are not words at all (`agradeço` ->
    `agradeçar`, `Comprei` -> `comprir`).  Those are detectable without a
    gold set: they are absent from the PT dictionary.  When that happens the
    fallback backend's answer is used instead.

    This is the same validation the original pipeline applied to simplemma,
    turned into a backend-selection rule rather than a surface-form reset.
    """

    def __init__(
        self,
        primary: "LemmaBackend",
        fallback: "LemmaBackend",
        lang: str = "pt",
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self.lang = lang
        self.name = f"{primary.name}+gate"

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        primary = self.primary.lemmatize_types(types, contexts)
        # Only ask the fallback about the forms the gate actually rejects.
        vocab = pt_dictionary(self.lang)
        rejected = [
            t
            for t in types
            if primary.get(t, t) != t and primary.get(t, t).lower() not in vocab
        ]
        secondary = (
            self.fallback.lemmatize_types(rejected, contexts) if rejected else {}
        )
        out = dict(primary)
        for surface in rejected:
            out[surface] = secondary.get(surface, surface)
        return out

    def gate_stats(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, Any]:
        """How often the gate fires -- for the report."""
        primary = self.primary.lemmatize_types(types, contexts)
        vocab = pt_dictionary(self.lang)
        rejected = [
            t for t in types
            if primary.get(t, t) != t and primary.get(t, t).lower() not in vocab
        ]
        return {"n_types": len(types), "n_rejected": len(rejected),
                "examples": [(t, primary[t]) for t in sorted(rejected)[:15]]}


def _majority(votes: Counter, fallback: str) -> str:
    """Most-voted item; ties broken lexicographically for determinism."""
    if not votes:
        return fallback
    top = max(votes.values())
    return sorted(w for w, c in votes.items() if c == top)[0]


# -- factory --------------------------------------------------------------


def get_backend(name: str, cfg: dict[str, Any]) -> LemmaBackend:
    lem = cfg["lemmatizer"]
    if name == "simplemma":
        return SimplemmaBackend()
    if name == "spacy":
        return SpacyBackend(model=lem["spacy_model"])
    if name == "stanza":
        workers = lem.get("stanza_workers", 1)
        if workers > 1:
            return ParallelStanzaBackend(
                lang=lem["stanza_lang"], workers=workers,
                chunk=lem.get("stanza_chunk", 200),
            )
        return StanzaBackend(lang=lem["stanza_lang"])
    if name == "vote":
        members = [get_backend(n, cfg) for n in lem["vote"]["members"]]
        return VoteBackend(members, lem["vote"]["tiebreak"])
    if name in ("gated", "stanza+gate"):
        gate = lem["gate"]
        return GatedBackend(
            get_backend(gate["primary"], cfg),
            get_backend(gate["fallback"], cfg),
            lem.get("spellchecker_lang", "pt"),
        )
    raise ValueError(f"unknown lemmatizer backend: {name!r}")


# -- override table and validation ----------------------------------------


def load_overrides(path: str | None) -> dict[str, str]:
    """Load the hand-curated surface -> lemma override table.

    The original's ~200-entry table was lost.  scripts/overrides.py rebuilds
    a candidate table empirically; entries confirmed by review live here.
    Missing file is not an error -- it simply means no overrides.
    """
    from pathlib import Path

    if not path:
        return {}
    p = Path(path)
    if not p.is_file():
        return {}
    out: dict[str, str] = {}
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            surface, _, lemma = line.partition("\t")
            if surface and lemma:
                out[surface.strip()] = lemma.strip()
    return out


def close_lemma_map(
    lemma_map: Mapping[str, str],
    backend: "LemmaBackend" | None = None,
    contexts: Contexts | None = None,
    max_iterations: int = 5,
) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """Make the lemma inventory closed under its own lemmatizer.

    A lemmatizer can be inconsistent across the surfaces of one paradigm:
    `achas` -> `achar` but `acha` -> `acha`, leaving both `acha` and `achar`
    as separate entries for the same verb.  This is the defect the project
    set out to fix -- inflected forms surfacing as their own entries.

    Each distinct lemma is fed back through the lemmatizer; when the result
    is a *different* lemma that is also in the inventory, the first is
    redirected onto the second.  Redirects are followed to a fixed point.
    A cycle (A -> B -> A) is resolved to its lexicographically smallest
    member so the outcome does not depend on iteration order.

    The map is its own oracle wherever possible: nearly every lemma is also
    a surface form that has already been lemmatized, so its answer is looked
    up rather than recomputed.  That keeps closure consistent with the
    backend that built the map -- a mismatch here leaves exactly the
    duplicates closure is supposed to remove -- and avoids re-running an
    expensive backend over the inventory.

    Returns the rewritten map and the list of (from, into) redirects.
    """
    mapping = dict(lemma_map)
    all_redirects: list[tuple[str, str]] = []

    for _ in range(max_iterations):
        inventory = set(mapping.values())
        probe = sorted(inventory)

        relemma = {l: mapping[l] for l in probe if l in mapping}
        missing = [l for l in probe if l not in mapping]
        if missing and backend is not None:
            relemma.update(backend.lemmatize_types(missing, contexts))

        redirect = {
            lemma: relemma[lemma]
            for lemma in probe
            if relemma.get(lemma, lemma) != lemma and relemma[lemma] in inventory
        }
        if not redirect:
            break

        # Follow chains to a fixed point; break cycles deterministically.
        resolved: dict[str, str] = {}
        for start in sorted(redirect):
            seen = [start]
            current = start
            while current in redirect:
                current = redirect[current]
                if current in seen:
                    current = min(seen + [current])
                    break
                seen.append(current)
            resolved[start] = current

        resolved = {k: v for k, v in resolved.items() if k != v}
        if not resolved:
            break
        all_redirects += sorted(resolved.items())
        mapping = {s: resolved.get(l, l) for s, l in mapping.items()}

    return mapping, all_redirects


def lemma_cache_path(cfg: dict[str, Any], types: Sequence[str]) -> "Path":
    """Cache key covers everything that can change a lemma decision."""
    import hashlib
    import json
    from pathlib import Path

    h = hashlib.sha256()
    for t in types:
        h.update(t.encode("utf-8"))
        h.update(b"\x00")
    material = {
        "lemmatizer": cfg["lemmatizer"],
        "types_digest": h.hexdigest()[:16],
        "n_types": len(types),
    }
    digest = hashlib.sha256(
        json.dumps(material, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]
    return Path(cfg["paths"]["cache_dir"]) / f"lemmas_{digest}.tsv.gz"


def save_lemma_map(mapping: Mapping[str, str], path) -> None:
    import gzip

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        for surface in sorted(mapping):
            fh.write(f"{surface}\t{mapping[surface]}\n")
    tmp.replace(path)


def load_lemma_map(path) -> dict[str, str] | None:
    import gzip

    if not path.is_file():
        return None
    out: dict[str, str] = {}
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            surface, _, lemma = line.rstrip("\n").partition("\t")
            if surface:
                out[surface] = lemma
    return out


def build_lemma_map(
    cfg: dict[str, Any],
    types: Sequence[str],
    contexts: Contexts | None = None,
    backend: LemmaBackend | None = None,
) -> dict[str, str]:
    """Full step 2: backend -> overrides -> dictionary validation.

    A lemma the PT dictionary does not recognise is rejected and the surface
    form is kept, exactly as the original README describes.
    """
    lem = cfg["lemmatizer"]
    backend = backend or get_backend(lem["backend"], cfg)

    # Stanza costs ~1 hour over the full inventory, so the raw backend
    # output is cached before overrides and the dictionary gate are applied.
    # Those are cheap and may change between runs.
    types = list(types)
    cache = lemma_cache_path(cfg, types)
    mapping = load_lemma_map(cache)
    if mapping is None:
        mapping = backend.lemmatize_types(types, contexts)
        save_lemma_map(mapping, cache)
    else:
        import sys

        print(f"  lemmas: reusing cache {cache}", file=sys.stderr)
    mapping = dict(mapping)

    overrides = load_overrides(lem.get("overrides_path"))
    for surface, lemma in overrides.items():
        if surface in mapping:
            mapping[surface] = lemma

    if lem.get("validate_with_spellchecker"):
        lang = lem.get("spellchecker_lang", "pt")
        vocab = pt_dictionary(lang)
        for surface, lemma in mapping.items():
            # An override is a human decision and outranks the dictionary.
            if surface in overrides:
                continue
            if lemma != surface and lemma.lower() not in vocab:
                mapping[surface] = surface
    return mapping
