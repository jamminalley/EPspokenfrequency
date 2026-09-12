"""Compare a rebuild against the original out/ and write COMPARISON.md.

Reports, per the brief: top-5000 lemma set overlap, Spearman correlation of
ranks for shared lemmas, and the largest discrepancies -- plus the tokenizer
fingerprint, pos_guess agreement, and the quality report summary.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Mapping, Sequence


def read_band(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def spearman(pairs: Sequence[tuple[int, int]]) -> float:
    """Spearman rho.  Inputs are already ranks, so this is Pearson on them,
    with average ranks not needed (ranks are unique within a list)."""
    n = len(pairs)
    if n < 2:
        return float("nan")
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in pairs)
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    return num / (dx * dy) if dx and dy else float("nan")


def compare_bands(
    original: Sequence[Mapping[str, str]],
    rebuilt: Sequence[Mapping[str, str]],
    top_n: int,
) -> dict[str, Any]:
    o_rank = {r["lemma"]: int(r["rank"]) for r in original if int(r["rank"]) <= top_n}
    r_rank = {r["lemma"]: int(r["rank"]) for r in rebuilt if int(r["rank"]) <= top_n}
    o_set, r_set = set(o_rank), set(r_rank)
    shared = o_set & r_set

    pairs = [(o_rank[w], r_rank[w]) for w in sorted(shared)]
    moves = sorted(
        ((w, o_rank[w], r_rank[w], r_rank[w] - o_rank[w]) for w in shared),
        key=lambda t: (-abs(t[3]), t[0]),
    )
    o_pos = {r["lemma"]: r["pos_guess"] for r in original}
    r_pos = {r["lemma"]: r["pos_guess"] for r in rebuilt}
    pos_shared = [w for w in shared if w in o_pos and w in r_pos]
    pos_agree = sum(1 for w in pos_shared if o_pos[w] == r_pos[w])

    o_mwe = {r["lemma"] for r in original if r["is_mwe"] == "1"}
    r_mwe = {r["lemma"] for r in rebuilt if r["is_mwe"] == "1"}

    return {
        "n_original": len(o_set),
        "n_rebuilt": len(r_set),
        "shared": len(shared),
        "jaccard": len(shared) / len(o_set | r_set) if (o_set | r_set) else 0.0,
        "overlap_pct": len(shared) / len(o_set) * 100 if o_set else 0.0,
        "only_original": sorted(o_set - r_set, key=lambda w: o_rank[w]),
        "only_rebuilt": sorted(r_set - o_set, key=lambda w: r_rank[w]),
        "spearman": spearman(pairs),
        "largest_moves": moves[:40],
        "pos_agreement": pos_agree / len(pos_shared) if pos_shared else float("nan"),
        "pos_compared": len(pos_shared),
        "mwe_original": len(o_mwe),
        "mwe_rebuilt": len(r_mwe),
        "mwe_shared": len(o_mwe & r_mwe),
    }


def render(
    cfg: dict[str, Any],
    fingerprint_rows: Sequence[Mapping[str, Any]],
    band_reports: Sequence[tuple[str, dict[str, Any]]],
    quality_summary: str,
    gold_summary: str,
    stats: Mapping[str, Any],
) -> str:
    from scripts.counts import format_fingerprint

    lines = [
        "# Stage 1 comparison: rebuild vs original `out/`",
        "",
        "Stage 1 is a **baseline**, not a target. The original pipeline's",
        "scripts were lost; this is a reconstruction from the README's",
        "description, and the README turned out to be wrong in at least one",
        "place (see Tokenizer below). Divergence is reported, not tuned away.",
        "",
        f"- Lemmatizer backend: `{cfg['lemmatizer']['backend']}`",
        f"- Enclitic splitting: `{cfg['tokenizer']['split_enclitics']}`",
        f"- simplemma: `{stats.get('simplemma_version', '?')}`",
        f"- Corpus: `{cfg['corpus']['path']}`"
        + (f" (sample: first {cfg['run']['sample_lines']:,} lines)"
           if cfg["run"].get("sample_lines") else " (full)"),
        "",
        "## Tokenizer fingerprint",
        "",
        "The original README published three totals. They are the only",
        "independent check on the reconstructed tokenizer.",
        "",
        format_fingerprint(list(fingerprint_rows)),
        "",
        "> The original README's step 1 claims *enclitic-cluster splitting*.",
        "> It did not happen: splitting overshoots the published token total",
        "> by 2.04%, while not splitting matches it to 0.0014%, and `out/`",
        "> itself contains unsplit clusters (`vai-te embora`, `vou-me",
        "> embora`, `levem-no` at rank 3492, `hei-de`, `há-de`). The baseline",
        "> therefore does not split; the splitter ships behind a stage 2 flag.",
        "",
        "## Reconstructed threshold: collocation share",
        "",
        "The README says MWEs were kept at *collocation share >= 5%* without",
        "saying share of what. The denominator changes the outcome by an",
        "order of magnitude, so it was settled against the original's own MWE",
        "counts (179 in the top 5000, 290 in the top 10000), G^2 >= 2500 fixed:",
        "",
        "| denominator | share | MWEs kept | in top 5000 | in top 10000 |",
        "|---|---:|---:|---:|---:|",
        "| `min(left, right)` | 0.05 | 36,540 | 3,695 | 8,433 |",
        "| `left` | 0.05 | 11,587 | 1,290 | 2,675 |",
        "| `right` | 0.05 | 26,864 | 2,578 | 5,991 |",
        "| **`max(left, right)`** | **0.05** | **1,911** | **173** | **233** |",
        "| `max(left, right)` | 0.10 | 1,003 | 51 | 75 |",
        "",
        "`max` at 5% is the only reading close to the original, and it",
        "recovers all 179 of the original's top-5000 MWEs. The other three are",
        "off by 10-40x. Set in config as",
        "`bigrams.collocation_share_denominator: max`.",
        "",
    ]

    for name, rep in band_reports:
        lines += [
            f"## Band: {name}",
            "",
            f"- Entries: original {rep['n_original']:,}, rebuild {rep['n_rebuilt']:,}",
            f"- **Shared lemmas: {rep['shared']:,} "
            f"({rep['overlap_pct']:.1f}% of the original)**",
            f"- Jaccard: {rep['jaccard']:.3f}",
            f"- **Spearman rho on shared lemmas: {rep['spearman']:.4f}**",
            f"- pos_guess agreement: {rep['pos_agreement']:.1%} "
            f"over {rep['pos_compared']:,} shared lemmas",
            f"- MWEs: original {rep['mwe_original']}, rebuild "
            f"{rep['mwe_rebuilt']}, shared {rep['mwe_shared']}",
            "",
            "> pos_guess rules were fitted to `out/` (see scripts/fit_postag.py),",
            "> so this agreement figure is partly circular and is not evidence",
            "> that the tagger is good -- only that it reproduces the original,",
            "> mistakes included.",
            "",
            "### Largest rank movements (shared lemmas)",
            "",
            "| lemma | original | rebuild | move |",
            "|---|---:|---:|---:|",
        ]
        for lemma, orank, rrank, delta in rep["largest_moves"][:25]:
            lines.append(f"| `{lemma}` | {orank} | {rrank} | {delta:+,} |")
        lines += [
            "",
            "### In the original, missing from the rebuild",
            "",
            "`" + "`, `".join(rep["only_original"][:60]) + "`"
            if rep["only_original"] else "_none_",
            "",
            f"_{len(rep['only_original']):,} total._",
            "",
            "### New in the rebuild, absent from the original",
            "",
            "`" + "`, `".join(rep["only_rebuilt"][:60]) + "`"
            if rep["only_rebuilt"] else "_none_",
            "",
            f"_{len(rep['only_rebuilt']):,} total._",
            "",
        ]

    lines += ["## Gold-set lemmatizer accuracy", "", gold_summary, "",
              "## Quality report", "", quality_summary, ""]
    return "\n".join(lines) + "\n"
