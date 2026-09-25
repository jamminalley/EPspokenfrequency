"""English glosses and example sentences for the published rows (v1.1).

For each of the 10,000 rows in ``out/`` this asks Claude for three things:
a gloss of one to three senses, one example sentence **taken verbatim from
the corpus**, and an English translation of that sentence. The model never
writes the Portuguese: it is given up to twenty real corpus lines
containing the entry and must return one of them unchanged, or nothing.
That is the whole point of the design -- a frequency list of spoken
Portuguese should illustrate itself with sentences people actually said,
and an invented sentence would be unverifiable.

    python -m scripts.gloss --dry-run        # 50 stratified rows -> eval/
    python -m scripts.gloss --submit         # all 10,000 via the Batch API
    python -m scripts.gloss --collect        # batch results -> out/glosses.tsv

The key is read from the environment (``ANTHROPIC_API_KEY``) and nowhere
else; it is never written to disk or into a report. The run aborts with a
message if it is missing.

Everything a response depends on -- model, prompt text, the sentences that
were offered -- is hashed into ``cache/gloss/`` beside the raw response, so
a rerun re-sends only what actually changed and two vintages of gloss can
never be mixed in one file. The cache is gitignored; ``out/glosses.tsv``
is committed.

Where the sentences come from. Pass 2 of the build keeps a digest-selected
sample of corpus lines for each of the 70,000 most frequent surface forms
(``scripts/bigrams.py``), and the lemma map says which forms belong to
which entry. Both are read from ``.cache/``, so this script needs the
corpus only in the sense that a build must already have run; it never
touches ``data/``. For a multi-word entry the phrase is matched over
*tokenized* lines, because a split enclitic (``ver lo``) is a pair of
tokens that never appears as text.

Known approximation: the cached lemma map is the one the backend and the
dictionary gate produced, before the conventions, the closure and the
accent folds merged some lemmas onto others. A handful of entries whose
inflected forms all arrived through such a merge therefore find no
sentences, and are glossed from the headword alone; ``--dry-run`` and
``--submit`` both report how many.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

# Prices per million tokens, Anthropic first-party API, checked 2026-09-24.
# Only used to report what a run cost or would cost.
PRICES = {"claude-opus-5": (5.00, 25.00)}
CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.10
BATCH_MULTIPLIER = 0.50

FLAGS = ("vulgar", "bp-leaning", "archaic", "name-like", "uncertain")

SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "gloss": {"type": "string"},
        "example_pt": {"type": "string"},
        "example_en": {"type": "string"},
        "flags": {"type": "array", "items": {"type": "string", "enum": list(FLAGS)}},
    },
    "required": ["gloss", "example_pt", "example_en", "flags"],
    "additionalProperties": False,
}

COLUMNS = ("rank", "lemma", "pos", "is_mwe", "freq_per_million", "pos_share",
           "gloss", "example_pt", "example_en", "flags")


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


# -- the rows to gloss -------------------------------------------------------


def load_rows(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """The published rows, in rank order, with the POS share of split words."""
    from scripts import config as config_mod

    out_dir = config_mod.out_dir(cfg)
    rows: list[dict[str, Any]] = []
    for spec in cfg["output"]["files"]:
        path = out_dir / f"{spec['stem']}.tsv"
        if not path.is_file():
            raise SystemExit(f"{path} not found: run python -m scripts.build first")
        with path.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                rows.append({"rank": int(r["rank"]), "lemma": r["lemma"],
                             "pos": r["pos"], "is_mwe": r["is_mwe"] == "1",
                             "raw_freq": int(r["raw_freq"]),
                             "freq_per_million": r["freq_per_million"]})
    rows.sort(key=lambda r: r["rank"])

    totals: dict[str, int] = {}
    parts: dict[str, int] = {}
    for r in rows:
        totals[r["lemma"]] = totals.get(r["lemma"], 0) + r["raw_freq"]
        parts[r["lemma"]] = parts.get(r["lemma"], 0) + 1
    for r in rows:
        r["split"] = parts[r["lemma"]] > 1
        r["pos_share"] = r["raw_freq"] / totals[r["lemma"]] if r["split"] else 1.0
    return rows


# -- example sentences -------------------------------------------------------


class _CacheOnlyBackend:
    """Stands in for the lemmatizer so the cached map can be reused without
    loading Stanza. Glossing must never lemmatize anything itself."""

    def lemmatize_types(self, types, contexts=None):  # pragma: no cover
        raise SystemExit(
            "no cached lemma map for this config in .cache/: run "
            "python -m scripts.build first (the glosses reuse its caches)"
        )


class Sentences:
    """Corpus lines that may be offered as an example, per published row."""

    def __init__(self, cfg: dict[str, Any]) -> None:
        from scripts import bigrams as bigrams_mod
        from scripts import build as build_mod
        from scripts import counts as counts_mod
        from scripts import lemmas as lemmas_mod
        from scripts import serir as serir_mod
        from scripts.tokenizer import Tokenizer

        self.cfg = cfg
        self.scfg = cfg["gloss"]["sentences"]
        self._in_dictionary = lemmas_mod.in_dictionary

        build_cfg = build_mod.effective_config(cfg)
        uni = counts_mod.load(build_cfg)
        if uni is None:
            raise SystemExit("no cached unigram counts in .cache/: run "
                             "python -m scripts.build first")
        bg = bigrams_mod.load(build_cfg)
        if bg is None:
            raise SystemExit("no cached pass-2 contexts in .cache/: run "
                             "python -m scripts.build first")
        self.contexts = bg.contexts
        self.tok = Tokenizer(dict(build_cfg["tokenizer"], lowercase=True))

        lemma_map = lemmas_mod.build_lemma_map(
            build_cfg, sorted(uni.counts), bg.contexts, backend=_CacheOnlyBackend()
        )
        joint = frozenset(serir_mod.FORMS) if self.scfg.get("exclude_joint_serir") else frozenset()
        self.by_lemma: dict[str, list[str]] = {}
        for surface, lemma in lemma_map.items():
            if lemma in ("ser", "ir") and surface in joint:
                continue
            self.by_lemma.setdefault(lemma, []).append(surface)
        _log(f"  sentences: {len(self.contexts):,} sampled types, "
             f"{len(self.by_lemma):,} lemmas with surfaces")

    # -- candidates ---------------------------------------------------------

    def _phrase_lines(self, phrase: str) -> list[str]:
        """Lines whose *tokens* contain the phrase, from either constituent's
        sample. Matching on text would miss a split enclitic."""
        parts = phrase.split()
        n = len(parts)
        found: list[str] = []
        for word in dict.fromkeys(parts):
            for line in self.contexts.get(word, ()):
                toks = self.tok.tokenize(line)
                if any(toks[i:i + n] == parts for i in range(len(toks) - n + 1)):
                    found.append(line)
        return found

    def candidates(self, row: dict[str, Any]) -> list[str]:
        if row["is_mwe"]:
            lines = self._phrase_lines(row["lemma"])
        else:
            surfaces = set(self.by_lemma.get(row["lemma"], ())) | {row["lemma"]}
            lines = [l for s in sorted(surfaces) for l in self.contexts.get(s, ())]
        return list(dict.fromkeys(lines))

    # -- filtering ----------------------------------------------------------

    def _all_caps(self, line: str) -> bool:
        letters = [c for c in line if c.isalpha()]
        return bool(letters) and sum(c.isupper() for c in letters) / len(letters) > 0.6

    def _proper_noun_share(self, line: str) -> float:
        words = line.split()
        if not words:
            return 0.0
        n = 0
        for i, w in enumerate(words):
            bare = w.strip("«»\"'()[[]]¿?!.,:;-–—…")
            if i and bare[:1].isupper() and not self._in_dictionary(bare.lower()):
                n += 1
        return n / len(words)

    def _edge_ellipsis(self, line: str) -> bool:
        s = line.strip()
        return s.startswith(("...", "…")) or s.endswith(("...", "…", "-", "–", "—"))

    def _clean(self, line: str, strict: bool) -> bool:
        words = line.split()
        if self.scfg.get("drop_all_caps") and self._all_caps(line):
            return False
        if self._proper_noun_share(line) > self.scfg["max_proper_noun_share"]:
            return False
        if not strict:
            return bool(words)
        if not self.scfg["min_words"] <= len(words) <= self.scfg["max_words"]:
            return False
        if self.scfg.get("drop_ellipsis_edges") and self._edge_ellipsis(line):
            return False
        return True

    def choose(self, row: dict[str, Any]) -> list[str]:
        """Up to ``max_per_row`` lines, shortest first. The strict filters are
        relaxed only when they would leave the entry with nothing."""
        cands = self.candidates(row)
        for strict in (True, False):
            kept = [l for l in cands if self._clean(l, strict)]
            if kept:
                break
        kept.sort(key=lambda l: (len(l.split()), len(l), l))
        return kept[: self.scfg["max_per_row"]]


# -- the request -------------------------------------------------------------


def system_prompt(cfg: dict[str, Any]) -> str:
    """The prompt text, with the file's explanatory header stripped."""
    text = Path(cfg["gloss"]["prompt_path"]).read_text(encoding="utf-8")
    _, _, body = text.partition("\n---\n")
    if not body.strip():
        raise SystemExit(f"{cfg['gloss']['prompt_path']}: no prompt after the '---' header")
    return body.strip() + "\n"


def digest(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:16]


def user_block(row: dict[str, Any], sentences: Sequence[str]) -> str:
    lines = [f"lemma: {row['lemma']}",
             f"pos: {row['pos']}",
             f"rank: {row['rank']} of 10000",
             f"frequency: {row['freq_per_million']} per million words"]
    if row["is_mwe"]:
        lines.append("this entry is a multi-word expression")
    if row["split"]:
        lines.append(f"share: this pos accounts for {row['pos_share']:.0%} of "
                     f"the occurrences of {row['lemma']}; the list holds the "
                     f"other reading as its own row")
    if sentences:
        lines.append("")
        lines.append("corpus sentences (copy one of these verbatim, or none):")
        lines += [f"{i}. {s}" for i, s in enumerate(sentences, 1)]
    else:
        lines.append("")
        lines.append("corpus sentences: none available for this entry; leave "
                     "example_pt and example_en empty.")
    return "\n".join(lines)


def request_params(cfg: dict[str, Any], prompt: str, row: dict[str, Any],
                   sentences: Sequence[str]) -> dict[str, Any]:
    """The Messages request, identical for the dry run and the batch: the dry
    run must exercise the shape the full run will send."""
    g = cfg["gloss"]
    params: dict[str, Any] = {
        "model": g["model"],
        "max_tokens": g["max_tokens"],
        "system": [{"type": "text", "text": prompt,
                    "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user_block(row, sentences)}],
        "output_config": {"effort": g["effort"],
                          "format": {"type": "json_schema", "schema": SCHEMA}},
    }
    if g.get("thinking") == "adaptive":
        params["thinking"] = {"type": "adaptive"}
    elif g.get("thinking") == "disabled":
        params["thinking"] = {"type": "disabled"}
    return params


# -- the response cache ------------------------------------------------------


def _safe(text: str) -> str:
    keep = "".join(c if (c.isalnum() or c in "-_") else "_" for c in text)
    return keep[:48] or "_"


def cache_file(cfg: dict[str, Any], row: dict[str, Any]) -> Path:
    """One file per lemma + POS, named so a human can find it."""
    key = f"{row['lemma']}\x00{row['pos']}"
    return (Path(cfg["gloss"]["cache_dir"])
            / f"{_safe(row['lemma'])}__{_safe(row['pos'])}-{digest(key)[:8]}.json")


def cache_read(cfg: dict[str, Any], row: dict[str, Any], stamp: str) -> dict | None:
    path = cache_file(cfg, row)
    if not path.is_file():
        return None
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if blob.get("stamp") != stamp:
        return None       # model, prompt or sentences changed: ask again
    return blob


def cache_write(cfg: dict[str, Any], row: dict[str, Any], stamp: str,
                sentences: Sequence[str], response: Any, parsed: dict) -> None:
    path = cache_file(cfg, row)
    path.parent.mkdir(parents=True, exist_ok=True)
    blob = {
        "lemma": row["lemma"], "pos": row["pos"], "rank": row["rank"],
        "stamp": stamp, "model": cfg["gloss"]["model"],
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sentences": list(sentences),
        "parsed": parsed,
        "response": response if isinstance(response, dict) else response.to_dict(),
    }
    path.write_text(json.dumps(blob, ensure_ascii=False, indent=2), encoding="utf-8")


def stamp_for(cfg: dict[str, Any], prompt_digest: str, row: dict[str, Any],
              sentences: Sequence[str]) -> str:
    g = cfg["gloss"]
    return digest(g["model"], str(g["max_tokens"]), str(g["effort"]),
                  str(g.get("thinking")), prompt_digest, row["lemma"], row["pos"],
                  *sentences)


# -- talking to the API ------------------------------------------------------


def client():
    """The SDK client. The key comes from the environment and nowhere else."""
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        raise SystemExit(
            "ANTHROPIC_API_KEY is not set in the environment.\n"
            "Export it in this shell before running the glosses; this script\n"
            "reads it from the environment only and never writes it to a file."
        )
    try:
        import anthropic
    except ImportError:  # pragma: no cover
        raise SystemExit("anthropic is not installed: pip install -r requirements.txt")
    return anthropic.Anthropic()


class Usage:
    """Token totals, so a run can report what it cost."""

    def __init__(self, model: str) -> None:
        self.model = model
        self.input = self.output = self.cache_write = self.cache_read = 0
        self.rows = self.live = 0

    def add(self, u: Any, live: bool = True) -> None:
        """Tokens for one row, whether it was just requested or replayed from
        the cache: the cost of the run is what the rows cost to produce."""
        get = u.get if isinstance(u, dict) else (lambda k: getattr(u, k, None))
        self.input += get("input_tokens") or 0
        self.output += get("output_tokens") or 0
        self.cache_write += get("cache_creation_input_tokens") or 0
        self.cache_read += get("cache_read_input_tokens") or 0
        self.rows += 1
        self.live += bool(live)

    def cost(self, batch: bool = False, cached: bool = True) -> float:
        """What these tokens cost. ``cached=False`` prices every cache read as
        a fresh input token: the worst case for a batch, whose requests need
        not land inside one another's five-minute cache window."""
        cin, cout = PRICES.get(self.model, (0.0, 0.0))
        read = self.cache_read * (CACHE_READ_MULTIPLIER if cached else 1.0)
        write = self.cache_write * (CACHE_WRITE_MULTIPLIER if cached else 1.0)
        total = ((self.input + read + write) * cin + self.output * cout) / 1e6
        return total * (BATCH_MULTIPLIER if batch else 1.0)

    def report(self, label: str, rows: int) -> list[str]:
        per = (lambda v: v / rows if rows else 0.0)
        return [
            f"{label}: {rows} rows ({self.live} sent now, "
            f"{self.rows - self.live} replayed from cache/gloss/)",
            f"  input        {self.input:>9,} tokens ({per(self.input):>7.0f}/row)",
            f"  cache write  {self.cache_write:>9,} tokens",
            f"  cache read   {self.cache_read:>9,} tokens",
            f"  output       {self.output:>9,} tokens ({per(self.output):>7.0f}/row)",
            f"  cost, prompt cache hitting   ${self.cost():.2f} standard, "
            f"${self.cost(batch=True):.2f} batch",
            f"  cost, no cache hit at all    ${self.cost(cached=False):.2f} standard, "
            f"${self.cost(batch=True, cached=False):.2f} batch",
        ]


def parse_reply(response: Any) -> dict[str, Any]:
    """The JSON object from a response, or a row flagged for review."""
    stop = getattr(response, "stop_reason", None)
    if stop == "refusal":
        det = getattr(response, "stop_details", None)
        return {"gloss": "", "example_pt": "", "example_en": "",
                "flags": ["uncertain"],
                "error": f"refusal ({getattr(det, 'category', None)})"}
    text = next((b.text for b in response.content if b.type == "text"), "")
    if stop == "max_tokens" and not text.rstrip().endswith("}"):
        return {"gloss": "", "example_pt": "", "example_en": "",
                "flags": ["uncertain"], "error": "truncated at max_tokens"}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {"gloss": "", "example_pt": "", "example_en": "",
                "flags": ["uncertain"], "error": f"unparseable reply: {exc}"}
    data.setdefault("flags", [])
    for k in ("gloss", "example_pt", "example_en"):
        data.setdefault(k, "")
    return data


def verify(parsed: dict[str, Any], sentences: Sequence[str]) -> str:
    """Empty string if the reply is usable, else why not. The example must be
    one of the lines we sent, character for character."""
    if parsed.get("error"):
        return parsed["error"]
    if not parsed["gloss"].strip():
        return "empty gloss"
    ex = parsed["example_pt"]
    if ex and ex not in sentences:
        return "example_pt is not one of the sentences sent"
    if ex and not parsed["example_en"].strip():
        return "example_pt without a translation"
    bad = [f for f in parsed["flags"] if f not in FLAGS]
    if bad:
        return f"unknown flag(s): {', '.join(bad)}"
    return ""


def gloss_rows(cfg: dict[str, Any], rows: Sequence[dict[str, Any]],
               sents: Sentences, progress: bool = True) -> tuple[list[dict], Usage]:
    """One synchronous request per row, cache first. Used by --dry-run; the
    full 10,000 go through --submit instead."""
    prompt = system_prompt(cfg)
    pdig = digest(prompt)
    usage = Usage(cfg["gloss"]["model"])
    cli = None
    results = []
    for i, row in enumerate(rows, 1):
        sentences = sents.choose(row)
        stamp = stamp_for(cfg, pdig, row, sentences)
        blob = cache_read(cfg, row, stamp)
        if blob is None:
            cli = cli or client()
            params = request_params(cfg, prompt, row, sentences)
            response = cli.messages.create(**params)
            parsed = parse_reply(response)
            cache_write(cfg, row, stamp, sentences, response, parsed)
            usage.add(response.usage)
            blob = {"parsed": parsed, "sentences": sentences}
            if progress:
                _log(f"    {i}/{len(rows)}  {row['lemma']} ({row['pos']})")
        else:
            usage.add(blob.get("response", {}).get("usage", {}), live=False)
            if progress:
                _log(f"    {i}/{len(rows)}  {row['lemma']} ({row['pos']})  [cached]")
        results.append({**row, **blob["parsed"],
                        "sentences": blob.get("sentences", sentences),
                        "problem": verify(blob["parsed"], blob.get("sentences", sentences))})
    return results, usage


# -- the full run, through the Batch API ------------------------------------


def submit(cfg: dict[str, Any], rows: Sequence[dict[str, Any]], sents: Sentences) -> str:
    """Send every row that is not already cached as one batch."""
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    prompt = system_prompt(cfg)
    pdig = digest(prompt)
    requests, stamps = [], {}
    for row in rows:
        sentences = sents.choose(row)
        stamp = stamp_for(cfg, pdig, row, sentences)
        if cache_read(cfg, row, stamp) is not None:
            continue
        cid = f"r{row['rank']}-{digest(row['lemma'], row['pos'])[:8]}"
        stamps[cid] = {"row": row, "stamp": stamp, "sentences": sentences}
        requests.append(Request(
            custom_id=cid,
            params=MessageCreateParamsNonStreaming(
                **request_params(cfg, prompt, row, sentences)),
        ))
    if not requests:
        raise SystemExit("every row is already cached: run --collect")
    cli = client()
    batch = cli.messages.batches.create(requests=requests)
    state = Path(cfg["gloss"]["batch"]["state_file"])
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(
        {"batch_id": batch.id, "created": batch.created_at.isoformat(),
         "model": cfg["gloss"]["model"], "prompt_digest": pdig,
         "requests": len(requests),
         "rows": {cid: {"rank": v["row"]["rank"], "lemma": v["row"]["lemma"],
                        "pos": v["row"]["pos"], "stamp": v["stamp"],
                        "sentences": v["sentences"]}
                  for cid, v in stamps.items()}},
        ensure_ascii=False, indent=2), encoding="utf-8")
    _log(f"batch {batch.id}: {len(requests):,} requests submitted; state in {state}")
    return batch.id


def collect(cfg: dict[str, Any], rows: Sequence[dict[str, Any]], sents: Sentences,
            wait: bool = True) -> tuple[list[dict], Usage]:
    """Poll the batch, write every raw response into the cache, then build the
    full result list from the cache."""
    state_path = Path(cfg["gloss"]["batch"]["state_file"])
    if not state_path.is_file():
        raise SystemExit(f"no batch state in {state_path}: run --submit first")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    cli = client()
    usage = Usage(cfg["gloss"]["model"])

    batch = cli.messages.batches.retrieve(state["batch_id"])
    while wait and batch.processing_status != "ended":
        _log(f"  batch {batch.id}: {batch.processing_status}, "
             f"{batch.request_counts.processing:,} still processing")
        time.sleep(cfg["gloss"]["batch"]["poll_seconds"])
        batch = cli.messages.batches.retrieve(state["batch_id"])
    if batch.processing_status != "ended":
        raise SystemExit(f"batch {batch.id} is {batch.processing_status}, not ended")

    by_rank = {r["rank"]: r for r in rows}
    failures = []
    for result in cli.messages.batches.results(batch.id):
        meta = state["rows"].get(result.custom_id)
        if meta is None:
            failures.append((result.custom_id, "unknown custom_id"))
            continue
        row = by_rank.get(meta["rank"])
        if result.result.type != "succeeded":
            failures.append((result.custom_id, result.result.type))
            continue
        message = result.result.message
        parsed = parse_reply(message)
        usage.add(message.usage)
        cache_write(cfg, row, meta["stamp"], meta["sentences"], message, parsed)
    for cid, why in failures:
        _log(f"  batch result {cid}: {why}")

    prompt_digest_ = digest(system_prompt(cfg))
    results, missing = [], 0
    for row in rows:
        sentences = sents.choose(row)
        blob = cache_read(cfg, row, stamp_for(cfg, prompt_digest_, row, sentences))
        if blob is None:
            missing += 1
            continue
        results.append({**row, **blob["parsed"], "sentences": blob["sentences"],
                        "problem": verify(blob["parsed"], blob["sentences"])})
    if missing:
        _log(f"  {missing:,} rows have no response yet: rerun --submit then --collect")
    return results, usage


# -- output ------------------------------------------------------------------


def write_tsv(path: Path, results: Sequence[dict[str, Any]],
              show_sentences: bool = False) -> None:
    cols = list(COLUMNS)
    if show_sentences:
        cols += ["problem", "n_sentences", "sentences_offered"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        # csv defaults, as everywhere else in the pipeline: a sentence that
        # contains a quotation mark is quoted rather than altered.
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(cols)
        for r in results:
            out = [r["rank"], r["lemma"], r["pos"], "1" if r["is_mwe"] else "0",
                   r["freq_per_million"],
                   f"{r['pos_share']:.3f}" if r["split"] else "",
                   r["gloss"], r["example_pt"], r["example_en"],
                   " ".join(r["flags"])]
            if show_sentences:
                out += [r.get("problem", ""), len(r["sentences"]),
                        " | ".join(r["sentences"])]
            w.writerow(["" if v is None else " ".join(str(v).split()) for v in out])


# -- the dry run -------------------------------------------------------------


def kept_feminine_nouns(cfg: dict[str, Any]) -> set[str]:
    """Feminine person nouns the reviewer kept as their own entry (convention 2)."""
    path = Path(cfg["paths"]["eval_dir"]) / "gender_pairs.tsv"
    if not path.is_file():
        return set()
    with path.open(encoding="utf-8", newline="") as fh:
        return {r["feminine"] for r in csv.DictReader(fh, delimiter="\t")
                if (r.get("jim_decision") or "").strip() == "keep"}


def dryrun_sample(cfg: dict[str, Any], rows: Sequence[dict[str, Any]]) -> list[dict]:
    """A stratified 50 rows: deterministic given the seed, and guaranteed to
    include the cases most likely to break -- split POS, multi-word entries,
    and a feminine noun the conventions keep separate from its masculine."""
    d = cfg["gloss"]["dryrun"]
    rng = random.Random(d["seed"])
    strata = [(lo, hi, n) for lo, hi, n in d["strata"]]
    quota = {i: n for i, (_, _, n) in enumerate(strata)}
    chosen: dict[int, dict] = {}

    def stratum_of(row: dict) -> int | None:
        for i, (lo, hi, _) in enumerate(strata):
            if lo <= row["rank"] <= hi:
                return i
        return None

    def take(pool: Sequence[dict], n: int) -> None:
        order = list(pool)
        rng.shuffle(order)
        taken = 0
        for row in order:
            if taken >= n:
                break
            i = stratum_of(row)
            if i is None or quota[i] <= 0 or row["rank"] in chosen:
                continue
            chosen[row["rank"]] = row
            quota[i] -= 1
            taken += 1
        if taken < n:
            _log(f"  warning: only {taken} of {n} rows available for one requirement")

    feminine = kept_feminine_nouns(cfg)
    req = d["require"]
    take([r for r in rows if r["split"]], req["multi_pos"])
    take([r for r in rows if r["is_mwe"]], req["mwe"])
    take([r for r in rows if r["pos"] == "noun" and r["lemma"] in feminine],
         req["kept_feminine_nouns"])
    for i, (lo, hi, _) in enumerate(strata):
        pool = [r for r in rows if lo <= r["rank"] <= hi and r["rank"] not in chosen]
        take(pool, quota[i])
    return [chosen[k] for k in sorted(chosen)]


# -- CLI ---------------------------------------------------------------------


def main() -> None:
    from scripts import config as config_mod

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="config.yaml")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true",
                      help="gloss the stratified sample into eval/")
    mode.add_argument("--submit", action="store_true",
                      help="send every uncached row as one batch")
    mode.add_argument("--collect", action="store_true",
                      help="poll the batch and write out/glosses.tsv")
    mode.add_argument("--estimate", action="store_true",
                      help="count input tokens for the full run; no glossing")
    ap.add_argument("--no-wait", action="store_true",
                    help="--collect: do not poll, take whatever is ready")
    args = ap.parse_args()

    cfg = config_mod.load(args.config)
    g = cfg["gloss"]
    rows = load_rows(cfg)
    _log(f"{len(rows):,} published rows, "
         f"{len({r['lemma'] for r in rows}):,} distinct entries")
    sents = Sentences(cfg)

    if args.estimate:
        prompt = system_prompt(cfg)
        cli = client()
        n_none = 0
        total = 0
        for row in rows:
            s = sents.choose(row)
            n_none += not s
            total += len(s)
        sample = rows[:: max(len(rows) // 40, 1)]
        counted = 0
        for row in sample:
            p = request_params(cfg, prompt, row, sents.choose(row))
            counted += cli.messages.count_tokens(
                model=p["model"], system=p["system"], messages=p["messages"]
            ).input_tokens
        per = counted / len(sample)
        print(f"rows with no example sentence: {n_none}")
        print(f"sentences offered: {total:,} ({total / len(rows):.1f} per row)")
        print(f"input tokens: {per:,.0f} per row on {len(sample)} sampled rows "
              f"=> {per * len(rows):,.0f} for {len(rows):,} rows")
        return

    if args.submit:
        submit(cfg, rows, sents)
        print("submitted; run --collect when the batch has ended")
        return

    if args.collect:
        results, usage = collect(cfg, rows, sents, wait=not args.no_wait)
        out = config_mod.out_dir(cfg) / g["out_file"]
        write_tsv(out, results)
        review = [r for r in results if r["problem"] or not r["example_pt"]
                  or set(r["flags"]) & {"uncertain", "name-like"}]
        write_tsv(Path(cfg["paths"]["eval_dir"]) / g["review_file"], review,
                  show_sentences=True)
        print(f"{out}: {len(results):,} rows")
        print(f"for review: {len(review):,} rows")
        print("\n".join(usage.report("this collect", len(results))))
        return

    # --dry-run
    sample = dryrun_sample(cfg, rows)
    _log(f"dry run: {len(sample)} rows "
         f"({sum(r['split'] for r in sample)} split POS, "
         f"{sum(r['is_mwe'] for r in sample)} MWEs)")
    results, usage = gloss_rows(cfg, sample, sents)
    path = Path(cfg["paths"]["eval_dir"]) / g["dryrun"]["file"]
    write_tsv(path, results, show_sentences=True)
    print(f"{path}: {len(results)} rows")
    problems = [r for r in results if r["problem"]]
    print(f"problems: {len(problems)}")
    for r in problems:
        print(f"  {r['rank']} {r['lemma']} ({r['pos']}): {r['problem']}")
    print("\n".join(usage.report("dry run", len(results))))
    if usage.rows:
        n = len(rows)
        lo = usage.cost(batch=True) / usage.rows * n
        hi = usage.cost(batch=True, cached=False) / usage.rows * n
        print(f"projected for all {n:,} rows through the Batch API: "
              f"${lo:.2f} if the prompt cache holds, ${hi:.2f} if it never does "
              f"(${usage.cost() / usage.rows * n:.2f}-"
              f"${usage.cost(cached=False) / usage.rows * n:.2f} without the batch discount)")


if __name__ == "__main__":
    main()
