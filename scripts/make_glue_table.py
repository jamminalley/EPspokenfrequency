"""Generate scripts/data/enclitic_clusters.tsv: glued enclitic clusters.

The corpus writes the same cluster both ways. `fazê-lo` appears 98,209 times
and `fazêlo` appears as well; `conheço-a` 3,806 times and `conheçoa` 4,019.
With the hyphen the splitter handles it and the tokens land on *fazer* and
*lo*; without it the whole thing survives as one type and reaches the
published list as a word (`conheçoa` at rank 5,290, glossed "I know her").

There is no safe way to spot these by rule. Stripping a clitic-shaped tail
and asking whether the stem is a verb form also splits `sera` (a missing
accent on *será*), `rodeo` and `eramos`, because Portuguese verb forms are
short and common word endings are clitic-shaped. What does work is the
corpus itself: repair a glued spelling only where the corpus also writes the
same cluster hyphenated, often enough to mean it.

So this reads the pass-1 inventory counted with `split_enclitics` off -- the
one the stage 1 baseline produces, where hyphenated clusters survive as
types -- and for each one checks the glued spelling against three tests:

  attested    the hyphenated form occurs at least `min_hyphenated` times
  dominant    hyphenated / glued is at least `min_ratio`, so the hyphen is
              the normal spelling and the glued one is the slip. This is
              what keeps `rodeo` (1,347 glued, 15 hyphenated) intact.
  not a word  the glued form is not in the PT dictionary and is not itself a
              recognised inflected verb form, and the stem is in the
              dictionary -- so neither a real word nor a non-verb is broken
              up. `contate` is the Brazilian subjunctive of *contatar* as
              well as a possible `conta-te`, and stays whole.
  not a name  the glued form is not usually capitalized mid-line. This is
              the test that matters most: `mateo` is written 1,113 times
              away from the start of a line and capitalized every single
              time -- it is *Mateo*, not `mate-o` -- and `nola`, `pirate`,
              `rise` and `jello` are the same story. Casing comes from the
              pass-2 evidence of a build with this repair switched off, so
              the table never depends on itself.

The result is a vetted list, and the tokenizer consults it rather than
guessing. Its digest is part of every cache key (`scripts/config.py`), so
regenerating it invalidates the passes that depend on it.

    python -m scripts.make_glue_table            # rewrite the table
    python -m scripts.make_glue_table --show 40  # and print the top rows
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

HEADER = ("glued", "stem", "clitic", "hyphenated_count", "glued_count", "ratio")


def evidence_config(cfg: dict[str, Any]) -> dict[str, Any]:
    """The release tokenizer as if glue repair did not exist.

    Both passes this script reads are cached under a hash of the tokenizer
    settings, and one of those settings is the digest of the table this
    script writes. Reading them under a configuration with the whole feature
    removed breaks that circle: the evidence is fixed, whatever the table
    ends up saying.
    """
    import copy

    out = copy.deepcopy(cfg)
    out["tokenizer"].pop("glue_repair", None)
    out["tokenizer"].pop("repair_glue", None)
    out["tokenizer"]["split_enclitics"] = True
    return out


def is_verb_form(word: str) -> bool:
    """Is this already an inflected verb form in its own right?

    The 2nd singular preterite ends in -ste and the clitic *te* ends the same
    way, so `saiste` (a missing accent on *saíste*) looks exactly like a glued
    `sais-te`. Asking the lemmatizer settles most of them.
    """
    import simplemma

    lemma = simplemma.lemmatize(word, lang="pt")
    return lemma != word and lemma.endswith(("ar", "er", "ir", "ôr"))


def candidates(counts: dict[str, int], cap, cfg: dict[str, Any],
               in_dictionary) -> list[tuple[str, str, str, int, int, float]]:
    """Clusters worth repairing, most frequent hyphenated form first.

    ``counts`` is the inventory that still has hyphens in it; ``cap`` answers
    (capitalized, non-initial) for a surface form.
    """
    from scripts.tokenizer import Tokenizer

    gcfg = cfg["tokenizer"]["glue_repair"]
    # A splitter with the release settings, so the stem written into the
    # table is the stem the build will produce (fazê-lo -> fazer, not fazê).
    tok = Tokenizer(dict(cfg["tokenizer"], split_enclitics=True, lowercase=True,
                         repair_glue=False))
    out, dropped = [], []
    for word, hyph in counts.items():
        if "-" not in word or hyph < gcfg["min_hyphenated"]:
            continue
        parts = tok.split_enclitic(word)
        if len(parts) != 2:
            continue                      # one clitic only: keep it simple
        stem, clitic = parts
        if not stem or clitic not in tok._enclitic_set:
            continue
        if not in_dictionary(stem):
            continue                      # jell-o is not a verb plus a clitic
        glued = word.replace("-", "")
        if glued == word or in_dictionary(glued) or is_verb_form(glued):
            continue
        glued_count = counts.get(glued, 0)
        if glued_count < gcfg["min_glued"]:
            continue
        ratio = hyph / glued_count
        if ratio < gcfg["min_ratio"]:
            continue
        caps, noninitial = cap(glued)
        if (noninitial >= gcfg["min_cap_evidence"]
                and caps / noninitial >= gcfg["max_cap_ratio"]):
            dropped.append((glued, caps, noninitial))
            continue
        out.append((glued, stem, clitic, hyph, glued_count, ratio))
    out.sort(key=lambda r: (-r[3], r[0]))
    if dropped:
        import sys

        print("  dropped as names: " + ", ".join(
            f"{g} ({c}/{n} capitalized)" for g, c, n in sorted(dropped)),
            file=sys.stderr)
    return out


def write(rows, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("# Generated by scripts/make_glue_table.py -- do not hand-edit.\n")
        fh.write("# Glued spellings of hyphenated enclitic clusters, which the\n")
        fh.write("# tokenizer splits as if the hyphen were there. Every row is\n")
        fh.write("# attested both ways in the corpus; see the module docstring.\n")
        fh.write("\t".join(HEADER) + "\n")
        for glued, stem, clitic, hyph, glued_count, ratio in rows:
            fh.write(f"{glued}\t{stem}\t{clitic}\t{hyph}\t{glued_count}\t{ratio:.3f}\n")


def load(path: str | Path) -> dict[str, tuple[str, str]]:
    """glued form -> (stem, clitic). Empty when the table is absent."""
    import csv

    path = Path(path)
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8", newline="") as fh:
        body = [l for l in fh if l.strip() and not l.lstrip().startswith("#")]
    return {r["glued"]: (r["stem"], r["clitic"])
            for r in csv.DictReader(body, delimiter="\t")}


def main() -> None:
    from scripts import config as config_mod
    from scripts import bigrams as bigrams_mod
    from scripts import counts as counts_mod
    from scripts import lemmas as lemmas_mod

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--show", type=int, default=0)
    args = ap.parse_args()
    cfg = config_mod.load(args.config)

    # The inventory that still has hyphens in it. This is the stage 1
    # tokenizer, so a stage 1 build has already paid for this pass.
    nosplit = evidence_config(cfg)
    nosplit["tokenizer"]["split_enclitics"] = False
    uni = counts_mod.unigram_pass_cached(nosplit)

    # Casing, from the same build with the repair switched off.
    ev = evidence_config(cfg)
    split = counts_mod.unigram_pass_cached(ev)
    bg = bigrams_mod.bigram_pass_cached(ev, split.counts)

    def cap(word: str) -> tuple[int, int]:
        return bg.cap_counts.get(word, 0), bg.noninitial_counts.get(word, 0)

    rows = candidates(uni.counts, cap, cfg, lemmas_mod.in_dictionary)
    path = Path(cfg["tokenizer"]["glue_repair"]["table"])
    write(rows, path)
    tokens = sum(r[4] for r in rows)
    print(f"{path}: {len(rows):,} clusters, {tokens:,} glued tokens to repair")
    for row in rows[: args.show]:
        print(f"  {row[0]:<18} -> {row[1]} + {row[2]:<5} "
              f"hyphenated {row[3]:>8,}  glued {row[4]:>7,}  ratio {row[5]:.2f}")


if __name__ == "__main__":
    main()
