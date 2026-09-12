"""Score lemmatizer backends against the hand-checked gold set.

The gold set at eval/lemma_gold.tsv is authored by hand and is never
generated or modified by this pipeline.  Its convention, from eval/README.md:
the gold answer is `jim_lemma` when non-empty, else `claude_lemma`, for rows
whose `jim_verdict` is not `drop`.

Until the human review is filled in, the gold falls back entirely to
`claude_lemma` -- a first-pass guess.  Scores in that state measure
agreement with a guess, not accuracy, and every report says so.

Run: python -m scripts.eval_lemmas --config config.yaml [--backend simplemma ...]
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class GoldRow:
    surface: str
    gold: str
    rank: int
    count: int
    category: str
    reviewed: bool


def load_gold(cfg: dict[str, Any]) -> tuple[list[GoldRow], dict[str, Any]]:
    path = Path(cfg["paths"]["eval_dir"]) / cfg["paths"]["gold"]["lemma_gold"]
    if not path.is_file():
        raise FileNotFoundError(
            f"gold set not found at {path}. It is authored by hand -- see eval/README.md."
        )
    rows: list[GoldRow] = []
    n_dropped = n_reviewed = 0
    with path.open(encoding="utf-8", newline="") as fh:
        for rec in csv.DictReader(fh, delimiter="\t"):
            verdict = (rec.get("jim_verdict") or "").strip()
            jim = (rec.get("jim_lemma") or "").strip()
            if verdict == "drop":
                n_dropped += 1
                continue
            if jim or verdict:
                n_reviewed += 1
            rows.append(
                GoldRow(
                    surface=rec["surface"].strip(),
                    gold=(jim or rec["claude_lemma"].strip()).lower(),
                    rank=int(rec["rank_40m"]),
                    count=int(rec["count_40m"]),
                    category=(rec.get("category") or "").strip(),
                    reviewed=bool(jim or verdict),
                )
            )
    meta = {
        "path": str(path),
        "n_rows": len(rows),
        "n_dropped": n_dropped,
        "n_reviewed": n_reviewed,
        "fully_reviewed": n_reviewed == len(rows) + n_dropped and len(rows) > 0,
    }
    return rows, meta


def band_of(rank: int) -> str:
    if rank <= 1000:
        return "1-1000"
    if rank <= 10000:
        return "1001-10000"
    return "10001+"


def score(
    rows: Sequence[GoldRow], predictions: Mapping[str, str]
) -> dict[str, Any]:
    hits = 0
    by_band: dict[str, list[int]] = {}
    by_category: dict[str, list[int]] = {}
    errors: list[tuple[str, str, str]] = []
    for row in rows:
        got = (predictions.get(row.surface) or row.surface).lower()
        ok = int(got == row.gold)
        hits += ok
        by_band.setdefault(band_of(row.rank), []).append(ok)
        by_category.setdefault(row.category or "(none)", []).append(ok)
        if not ok:
            errors.append((row.surface, row.gold, got))
    return {
        "n": len(rows),
        "accuracy": hits / len(rows) if rows else float("nan"),
        "by_band": {k: sum(v) / len(v) for k, v in sorted(by_band.items())},
        "by_category": {k: sum(v) / len(v) for k, v in sorted(by_category.items())},
        "errors": errors,
    }


def render(results: Mapping[str, dict[str, Any]], meta: Mapping[str, Any]) -> str:
    lines: list[str] = []
    if not meta["fully_reviewed"]:
        lines += [
            f"> **Provisional.** {meta['n_reviewed']} of "
            f"{meta['n_rows'] + meta['n_dropped']} gold rows carry a human",
            "> verdict. For unreviewed rows the gold falls back to",
            "> `claude_lemma`, a first-pass guess, so these numbers measure",
            "> agreement with that guess rather than accuracy. Fill in",
            "> `jim_lemma` / `jim_verdict` in eval/lemma_gold.tsv to make them",
            "> meaningful.",
            "",
        ]
    lines += [
        f"Gold set: `{meta['path']}` — {meta['n_rows']} scored rows"
        + (f", {meta['n_dropped']} marked `drop` and excluded"
           if meta["n_dropped"] else ""),
        "",
        "| backend | accuracy | ranks 1-1000 | 1001-10000 | 10001+ |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, res in results.items():
        b = res["by_band"]
        lines.append(
            f"| `{name}` | **{res['accuracy']:.1%}** | "
            + " | ".join(f"{b.get(k, float('nan')):.1%}" for k in
                         ("1-1000", "1001-10000", "10001+"))
            + " |"
        )
    lines.append("")

    for name, res in results.items():
        if not res["errors"]:
            continue
        lines += [f"<details><summary>{name}: "
                  f"{len(res['errors'])} disagreements</summary>", "",
                  "| surface | gold | predicted |", "|---|---|---|"]
        for surface, gold, got in res["errors"][:60]:
            lines.append(f"| `{surface}` | `{gold}` | `{got}` |")
        if len(res["errors"]) > 60:
            lines.append(f"\n_{len(res['errors']) - 60} more._")
        lines += ["", "</details>", ""]
    return "\n".join(lines)


def evaluate(
    cfg: dict[str, Any],
    backend_names: Sequence[str],
    contexts: Mapping[str, Sequence[str]] | None = None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    from scripts import lemmas as lemmas_mod

    rows, meta = load_gold(cfg)
    surfaces = [r.surface for r in rows]
    results: dict[str, dict[str, Any]] = {}
    for name in backend_names:
        try:
            backend = lemmas_mod.get_backend(name, cfg)
            preds = backend.lemmatize_types(surfaces, contexts)
        except Exception as exc:  # a missing model must not kill the build
            results[name] = {
                "n": len(rows), "accuracy": float("nan"), "by_band": {},
                "by_category": {}, "errors": [], "unavailable": str(exc),
            }
            continue
        results[name] = score(rows, preds)
    return results, meta


def main() -> None:
    from scripts import config as config_mod

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--backend", action="append", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = config_mod.load(args.config)
    names = args.backend or ["simplemma", "spacy", "vote"]
    results, meta = evaluate(cfg, names)
    report = render(results, meta)
    print(report)
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
