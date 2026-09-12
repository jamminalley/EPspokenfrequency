"""Derive the pos_guess rule tables from the original out/ files.

The original's POS heuristic -- a closed-class lookup plus suffix rules --
was lost with the scripts.  Its behaviour is, however, fully observable in
out/: the closed classes are small and enumerable, and the open-class
suffix rules can be recovered by majority vote over the 10,000 labelled
entries.

This is deliberately fitted to out/ and is therefore NOT independent
evidence about pos_guess quality.  The agreement figure it produces
measures how well the reconstruction reproduces the original's decisions,
including the original's mistakes (`aqui` -> pron, `também` -> conj,
`bom` -> intj).  COMPARISON.md says so wherever the number appears.

Run:  python -m scripts.fit_postag --config config.yaml
Writes: scripts/data/postag_rules.yaml
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

CLOSED_TAGS = ("det", "prep", "conj", "pron", "num", "intj")
# `-or` is NOT a verb ending here: the original tags senhor/amor/favor/
# maior as `unk`, and no verb-tagged lemma in out/ ends in -or.
VERB_ENDINGS = ("ar", "er", "ir", "ôr")
# Verbs too short for the suffix rule to reach safely (ar, bar, mar, par
# are nouns; ser, ir, ter are verbs) were evidently a lookup.
VERB_MIN_LENGTH = 4
OPEN_TAGS = ("noun", "adj", "unk")


def read_original(cfg: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    base = Path(cfg["paths"]["original_dir"])
    for spec in cfg["output"]["files"]:
        path = base / f"{spec['stem']}.tsv"
        with path.open(encoding="utf-8", newline="") as fh:
            rows.extend(csv.DictReader(fh, delimiter="\t"))
    return rows


def fit(rows: list[dict[str, str]], min_support: int) -> dict[str, Any]:
    closed: dict[str, str] = {}
    for row in rows:
        tag, lemma = row["pos_guess"], row["lemma"]
        if row["is_mwe"] == "1":
            continue
        if tag in CLOSED_TAGS:
            closed[lemma] = tag
        elif tag == "adv" and not lemma.endswith("mente"):
            # -mente is a rule; the rest were a hand-written list.
            closed[lemma] = "adv"
        elif tag == "verb" and len(lemma) < VERB_MIN_LENGTH:
            # ser/ir/ter/ver/vir/dar/ler/rir: shorter than the suffix rule
            # can safely fire, so they must have been listed.
            closed[lemma] = "verb"

    # Open-class suffix table, longest suffix first, majority tag per suffix.
    by_suffix: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        lemma, tag = row["lemma"], row["pos_guess"]
        if row["is_mwe"] == "1" or lemma in closed or tag not in OPEN_TAGS:
            continue
        if tag in ("noun", "adj") and lemma.endswith(VERB_ENDINGS):
            continue  # would be caught by the verb rule first
        for size in (4, 3, 2):
            if len(lemma) > size:
                by_suffix[lemma[-size:]][tag] += 1

    suffixes: dict[str, str] = {}
    for suffix, votes in by_suffix.items():
        total = sum(votes.values())
        tag, count = votes.most_common(1)[0]
        # Only keep a suffix that is both well attested and decisive;
        # anything marginal is left to fall through to `unk`, which is what
        # the original did with 1,792 entries.
        if total >= min_support and count / total >= 0.65 and tag != "unk":
            suffixes[suffix] = tag

    return {
        "closed_class": dict(sorted(closed.items())),
        "verb_endings": list(VERB_ENDINGS),
        "verb_min_length": VERB_MIN_LENGTH,
        "adverb_suffix": "mente",
        "open_suffixes": dict(sorted(suffixes.items(), key=lambda kv: (-len(kv[0]), kv[0]))),
        "fallback": "unk",
        "_provenance": (
            "Fitted to out/ by scripts/fit_postag.py. Reproduces the original's "
            "decisions including its errors; not independent POS evidence."
        ),
    }


def main() -> None:
    from scripts import config as config_mod

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--min-support", type=int, default=8)
    ap.add_argument("--out", default="scripts/data/postag_rules.yaml")
    args = ap.parse_args()

    cfg = config_mod.load(args.config)
    rows = read_original(cfg)
    rules = fit(rows, args.min_support)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(rules, fh, allow_unicode=True, sort_keys=False, width=100)

    from scripts.postag import PosTagger

    tagger = PosTagger(rules)
    agree = sum(
        1
        for r in rows
        if tagger.tag(r["lemma"], is_mwe=r["is_mwe"] == "1") == r["pos_guess"]
    )
    print(f"closed-class entries : {len(rules['closed_class']):,}")
    print(f"open suffix rules    : {len(rules['open_suffixes']):,}")
    print(f"self-agreement       : {agree:,}/{len(rows):,} = {agree / len(rows):.2%}")
    print(f"written              : {out}")

    disagree = [
        (r["lemma"], r["pos_guess"], tagger.tag(r["lemma"], r["is_mwe"] == "1"))
        for r in rows
        if tagger.tag(r["lemma"], r["is_mwe"] == "1") != r["pos_guess"]
    ]
    print("\nsample disagreements (lemma, original, fitted):")
    for lemma, orig, got in disagree[:15]:
        print(f"  {lemma:18} {orig:5} -> {got}")


if __name__ == "__main__":
    main()
