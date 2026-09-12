"""Pass 1: tokenize the corpus and count unigram surface forms.

README pipeline step 1.

A single reader process streams the gzip and hands ordered chunks to a
worker pool; each worker tokenizes its chunk and returns a local Counter,
which the parent merges.  Chunks are consumed in corpus order (``imap``,
not ``imap_unordered``) so that merge order -- and therefore the output --
is identical on every run.
"""

from __future__ import annotations

import multiprocessing as mp
import sys
import time
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterator

from scripts import corpus
from scripts.tokenizer import Tokenizer

# Per-worker state, set by the pool initializer.
_TOKENIZER: Tokenizer | None = None


def _init_worker(tok_cfg: dict[str, Any]) -> None:
    global _TOKENIZER
    _TOKENIZER = Tokenizer(tok_cfg)


def _count_chunk(lines: list[str]) -> tuple[Counter, int, int]:
    """Tokenize a chunk.  Returns (counts, n_lines, n_tokens)."""
    assert _TOKENIZER is not None, "worker not initialized"
    counts: Counter = Counter()
    n_tokens = 0
    tokenize = _TOKENIZER.tokenize
    for line in lines:
        toks = tokenize(line)
        n_tokens += len(toks)
        counts.update(toks)
    return counts, len(lines), n_tokens


@dataclass
class UnigramResult:
    counts: Counter
    n_lines: int
    n_tokens: int
    elapsed_s: float

    @property
    def n_types(self) -> int:
        return len(self.counts)

    def fingerprint(self) -> dict[str, int]:
        return {"lines": self.n_lines, "tokens": self.n_tokens, "types": self.n_types}


def unigram_pass(cfg: dict[str, Any], progress: bool = True) -> UnigramResult:
    """Run the counting pass over the whole corpus (or the configured sample)."""
    workers = cfg["run"]["workers"]
    started = time.monotonic()
    counts: Counter = Counter()
    n_lines = n_tokens = 0

    ctx = mp.get_context("spawn")
    with ctx.Pool(
        processes=workers,
        initializer=_init_worker,
        initargs=(cfg["tokenizer"],),
    ) as pool:
        stream = corpus.chunks(cfg)
        for i, (chunk_counts, chunk_lines, chunk_tokens) in enumerate(
            pool.imap(_count_chunk, stream, chunksize=1), start=1
        ):
            counts.update(chunk_counts)
            n_lines += chunk_lines
            n_tokens += chunk_tokens
            if progress and i % 20 == 0:
                rate = n_lines / max(time.monotonic() - started, 1e-9)
                print(
                    f"  pass1 chunk {i:5d}  lines {n_lines:,}  tokens {n_tokens:,}  "
                    f"types {len(counts):,}  ({rate:,.0f} lines/s)",
                    file=sys.stderr,
                    flush=True,
                )

    return UnigramResult(counts, n_lines, n_tokens, time.monotonic() - started)


def compare_fingerprint(result: UnigramResult, cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Compare this run's totals against the original build's published
    numbers.  Returns one row per metric for the comparison report.

    On a sample run the absolute totals cannot match, so the useful signal
    is tokens-per-line, which is scale-free.
    """
    expected = cfg["corpus"]["expected"]
    got = result.fingerprint()
    rows = []
    for metric in ("lines", "tokens", "types"):
        exp, act = expected[metric], got[metric]
        rows.append(
            {
                "metric": metric,
                "expected": exp,
                "actual": act,
                "delta": act - exp,
                "pct": (act - exp) / exp * 100 if exp else float("nan"),
            }
        )
    exp_tpl = expected["tokens"] / expected["lines"]
    act_tpl = result.n_tokens / max(result.n_lines, 1)
    rows.append(
        {
            "metric": "tokens_per_line",
            "expected": round(exp_tpl, 4),
            "actual": round(act_tpl, 4),
            "delta": round(act_tpl - exp_tpl, 4),
            "pct": (act_tpl - exp_tpl) / exp_tpl * 100,
        }
    )
    return rows


def format_fingerprint(rows: list[dict[str, Any]]) -> str:
    out = [
        "| metric | original | this run | delta | delta % |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        exp = f"{r['expected']:,}" if isinstance(r["expected"], int) else f"{r['expected']}"
        act = f"{r['actual']:,}" if isinstance(r["actual"], int) else f"{r['actual']}"
        dlt = f"{r['delta']:+,}" if isinstance(r["delta"], int) else f"{r['delta']:+}"
        out.append(f"| `{r['metric']}` | {exp} | {act} | {dlt} | {r['pct']:+.3f}% |")
    return "\n".join(out)


# -- caching ---------------------------------------------------------------
#
# Pass 1 takes ~3 minutes on the full corpus.  Later stages only need its
# output, so it is cached to a gzipped TSV.  The cache is keyed by a digest
# of the settings that affect counting, so changing a tokenizer rule or the
# sample size invalidates it automatically rather than silently reusing
# stale counts.


def cache_key(cfg: dict[str, Any]) -> str:
    import hashlib
    import json

    material = {
        "tokenizer": cfg["tokenizer"],
        "sample_lines": cfg["run"].get("sample_lines"),
        "corpus": cfg["corpus"]["path"],
    }
    blob = json.dumps(material, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def cache_path(cfg: dict[str, Any]) -> "Path":
    from pathlib import Path

    return Path(cfg["paths"]["cache_dir"]) / f"unigrams_{cache_key(cfg)}.tsv.gz"


def save(result: UnigramResult, cfg: dict[str, Any]) -> "Path":
    """Write counts to the cache.  Sorted by count desc then lexicographically
    so the file is byte-identical for identical input."""
    import gzip

    path = cache_path(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", newline="\n") as fh:
        fh.write(f"# lines\t{result.n_lines}\n")
        fh.write(f"# tokens\t{result.n_tokens}\n")
        fh.write(f"# elapsed_s\t{result.elapsed_s:.3f}\n")
        for surface, count in sorted(result.counts.items(), key=lambda kv: (-kv[1], kv[0])):
            fh.write(f"{surface}\t{count}\n")
    tmp.replace(path)
    return path


def load(cfg: dict[str, Any]) -> UnigramResult | None:
    """Return cached counts for this config, or None if absent."""
    import gzip

    path = cache_path(cfg)
    if not path.is_file():
        return None
    counts: Counter = Counter()
    n_lines = n_tokens = 0
    elapsed = 0.0
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("# "):
                key, _, value = line[2:].rstrip("\n").partition("\t")
                if key == "lines":
                    n_lines = int(value)
                elif key == "tokens":
                    n_tokens = int(value)
                elif key == "elapsed_s":
                    elapsed = float(value)
                continue
            surface, _, count = line.rstrip("\n").partition("\t")
            counts[surface] = int(count)
    return UnigramResult(counts, n_lines, n_tokens, elapsed)


def unigram_pass_cached(cfg: dict[str, Any], progress: bool = True) -> UnigramResult:
    cached = load(cfg)
    if cached is not None:
        if progress:
            print(f"  pass1: reusing cache {cache_path(cfg)}", file=sys.stderr)
        return cached
    result = unigram_pass(cfg, progress=progress)
    save(result, cfg)
    return result


if __name__ == "__main__":  # calibration entry point
    import argparse
    import json

    from scripts import config as config_mod

    ap = argparse.ArgumentParser(description="Run the unigram pass and print the fingerprint.")
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--sample", type=int, default=None, help="read only the first N lines")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--top", type=int, default=0, help="print the N most common types")
    args = ap.parse_args()

    cfg = config_mod.load(args.config)
    overrides: dict[str, Any] = {}
    if args.sample is not None:
        overrides["run.sample_lines"] = args.sample
    if args.workers is not None:
        overrides["run.workers"] = args.workers
    if overrides:
        cfg = config_mod.with_overrides(cfg, overrides)

    res = unigram_pass_cached(cfg)
    print(f"\nelapsed {res.elapsed_s:.1f}s", file=sys.stderr)
    print(json.dumps(res.fingerprint(), indent=2))
    print(format_fingerprint(compare_fingerprint(res, cfg)))
    if args.top:
        for w, c in res.counts.most_common(args.top):
            print(f"{c:12,}  {w}")
