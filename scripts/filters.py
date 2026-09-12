"""Step 4: BP exclusions and the proper-noun filter.

README: "BP-leaning lemmas excluded (...).  Proper-noun leaks filtered via
OOV heuristic (see `dropped_proper_nouns.txt`)."

The BP list is reproduced verbatim for the stage 1 baseline, `cara`
included -- it is ordinary EP for "face" and was excluded in error, so its
removal is a stage 2 fix rather than a silent correction here.

The proper-noun heuristic could not be recovered (see config.yaml), so it
is reconstructed around the signal that actually separates names from
words: how often a token appears capitalized away from the start of a line.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from scripts.tokenizer import strip_diacritics


@dataclass
class FilterLog:
    """What each filter removed, and why -- everything dropped is logged."""

    bp_excluded: list[tuple[str, str]] = field(default_factory=list)
    proper_nouns: list[tuple[str, int, float, str]] = field(default_factory=list)

    def dropped_lemmas(self) -> set[str]:
        return {w for w, _ in self.bp_excluded} | {w for w, _, _, _ in self.proper_nouns}


def bp_exclusion_set(cfg: dict[str, Any]) -> set[str]:
    """The BP exclusion list for the configured stage.

    Stage 2 removes the entries listed in fixes.bp_exclusion_removals and,
    when fixes.bp_after_folding is on, also excludes unaccented variants --
    which is how `voce` survived the original filter while `você` did not.
    """
    listed = set(cfg["filters"]["bp_exclusions"])
    if cfg["run"]["stage"] < 2:
        return listed
    listed -= set(cfg["fixes"].get("bp_exclusion_removals", ()))
    if cfg["fixes"].get("bp_after_folding"):
        listed |= {strip_diacritics(w) for w in listed}
    return listed


def is_proper_noun(
    lemma: str,
    count: int,
    cap_ratio: float,
    cfg: dict[str, Any],
    in_dictionary: Callable[[str], bool],
) -> tuple[bool, str]:
    """Decide whether a lemma is a proper-noun leak.  Returns (drop, reason)."""
    pn = cfg["filters"]["proper_nouns"]
    if not pn.get("enabled"):
        return False, ""
    if count < pn.get("min_count", 1):
        return False, ""

    stage2 = cfg["run"]["stage"] >= 2 and cfg["fixes"].get("extended_proper_nouns")
    threshold = (
        pn["stage2_cap_ratio_threshold"] if stage2 else pn["cap_ratio_threshold"]
    )
    known = in_dictionary(lemma)

    if cap_ratio >= threshold:
        # Stage 1 keeps the original's OOV requirement, so a capitalized word
        # the dictionary knows (jack, mary) survives -- as it did originally.
        if stage2 or not known:
            return True, f"cap_ratio={cap_ratio:.2f}" + ("" if known else ", oov")
    return False, ""


def apply(
    lemma_counts: Mapping[str, int],
    cap_ratios: Mapping[str, float],
    cfg: dict[str, Any],
    in_dictionary: Callable[[str], bool],
) -> tuple[dict[str, int], FilterLog]:
    """Run both filters.  Returns the surviving counts and a log."""
    log = FilterLog()
    bp = bp_exclusion_set(cfg)
    kept: dict[str, int] = {}

    for lemma, count in lemma_counts.items():
        if lemma in bp:
            log.bp_excluded.append((lemma, "bp_exclusion"))
            continue
        drop, reason = is_proper_noun(
            lemma, count, cap_ratios.get(lemma, 0.0), cfg, in_dictionary
        )
        if drop:
            log.proper_nouns.append((lemma, count, cap_ratios.get(lemma, 0.0), reason))
            continue
        kept[lemma] = count

    log.proper_nouns.sort(key=lambda t: (-t[1], t[0]))
    log.bp_excluded.sort()
    return kept, log


def fold_diacritics(
    counts: Mapping[str, int],
    cfg: dict[str, Any],
    in_dictionary: Callable[[str], bool],
) -> tuple[dict[str, int], list[tuple[str, str, int]]]:
    """Stage 2 fix (a): fold an unaccented form into its accented twin.

    Three conditions, all required:
      1. the form has no diacritics;
      2. it is NOT itself a valid PT word -- this is what keeps the real
         minimal pairs apart (e/é, da/dá, esta/está, so/só are distinct
         words and must never be merged);
      3. an accented variant actually occurs in the corpus.

    Returns the folded counts and a log of (from, into, count).
    """
    if not cfg["fixes"].get("diacritic_folding"):
        return dict(counts), []

    # Accented forms grouped by their folded key.
    by_folded: dict[str, list[str]] = {}
    for word in counts:
        if strip_diacritics(word) != word:
            by_folded.setdefault(strip_diacritics(word), []).append(word)

    folded: dict[str, int] = {}
    log: list[tuple[str, str, int]] = []
    for word, count in counts.items():
        if strip_diacritics(word) == word and not in_dictionary(word):
            candidates = by_folded.get(word)
            if candidates:
                # Most frequent accented variant wins; ties lexicographic.
                target = sorted(candidates, key=lambda w: (-counts[w], w))[0]
                folded[target] = folded.get(target, 0) + count
                log.append((word, target, count))
                continue
        folded[word] = folded.get(word, 0) + count

    log.sort(key=lambda t: (-t[2], t[0]))
    return folded, log
