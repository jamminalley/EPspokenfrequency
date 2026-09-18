"""Write eval/proper_noun_drops_review.tsv.

Lists every word the proper-noun filter dropped that is also a PT
dictionary word and has at least --min-count occurrences: the drops most
likely to be mistakes (deus, sr, natal) rather than names (jack, paris).

The file is for human review, so it is never overwritten blindly: if it
exists, decisions already filled in are carried over by lemma.

Run after a stage 2 build:
    python -m scripts.make_proper_noun_review --min-count 5000
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    from scripts import config as config_mod
    from scripts.lemmas import in_dictionary

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--drops", default="out_rebuild_stage2/dropped_proper_nouns_full.txt")
    ap.add_argument("--out", default="eval/proper_noun_drops_review.tsv")
    ap.add_argument("--min-count", type=int, default=5000)
    args = ap.parse_args()
    config_mod.load(args.config)

    rows = []
    with open(args.drops, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 4:
                continue
            count, lemma, ratio, reason = int(parts[0]), parts[1], parts[2], parts[3]
            if count >= args.min_count and in_dictionary(lemma):
                rows.append((lemma, count, ratio, reason))

    out = Path(args.out)
    previous: dict[str, str] = {}
    if out.is_file():
        with out.open(encoding="utf-8", newline="") as fh:
            for rec in csv.DictReader(fh, delimiter="\t"):
                if rec.get("decision", "").strip():
                    previous[rec["lemma"]] = rec["decision"].strip()

    rows.sort(key=lambda r: (-r[1], r[0]))
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("lemma\tcount\tcap_ratio\treason\tdecision\n")
        for lemma, count, ratio, reason in rows:
            fh.write(f"{lemma}\t{count}\t{ratio}\t{reason}\t{previous.get(lemma, '')}\n")
    print(f"{len(rows)} rows -> {out}"
          + (f" ({len(previous)} existing decisions kept)" if previous else ""))


if __name__ == "__main__":
    main()
