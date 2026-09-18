"""Lemmatization conventions from eval/conventions.md.

These are headword policies, not facts about Portuguese, so each is driven
by config.yaml (`conventions:`) and every change it makes is logged for the
stage 2 report.  They run on the surface -> lemma map after the backend and
before lemma closure, so closure (which uses the map as its own oracle)
respects them rather than undoing them.

  1. contractions   ao, aos, desta, naquilo ... are their own headwords
  2. gender         feminine nouns fold into the masculine, except a
                    feminine with its own meaning (ferida "wound")
  3. diminutives    coisinha, patinho stay separate from coisa, pato
  4. comparatives   maior, melhor, pior, menor are their own lemmas
  5. spelling       pre-1990 spellings merge under the post-1990 one
                    (acção -> ação, exactamente -> exatamente)

Conventions 1, 3 and 4 protect a form from being folded; 2 and 5 fold.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping

from scripts.tokenizer import strip_diacritics

_DIMINUTIVE = re.compile(r"^(?P<base>.+?)(?P<suffix>z?inh)(?P<vowel>[oa])s?$")

# Silent consonants removed by the 1990 Orthographic Agreement.  Tried as a
# full rewrite first, then one cluster at a time, so a word with one silent
# and one pronounced cluster still finds its reformed spelling.
_REFORM_RULES = (("cç", "ç"), ("pç", "ç"), ("ct", "t"), ("pt", "t"))


@dataclass
class ConventionLog:
    """(surface, old_lemma, new_lemma) per convention."""

    changes: dict[str, list[tuple[str, str, str]]] = field(default_factory=dict)

    def add(self, convention: str, surface: str, old: str, new: str) -> None:
        self.changes.setdefault(convention, []).append((surface, old, new))

    def summary(self, counts: Mapping[str, int]) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        for name, rows in sorted(self.changes.items()):
            out[name] = {
                "surfaces": len(rows),
                "tokens": sum(counts.get(s, 0) for s, _, _ in rows),
            }
        return out


def _singular(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def reform_candidates(word: str) -> list[str]:
    """Post-1990 spellings to try for a pre-1990 word, in fixed order."""
    full = word
    for old, new in _REFORM_RULES:
        full = full.replace(old, new)
    cands = [full] if full != word else []
    for old, new in _REFORM_RULES:
        start = 0
        while (i := word.find(old, start)) >= 0:
            cand = word[:i] + new + word[i + len(old):]
            if cand not in cands and cand != word:
                cands.append(cand)
            start = i + 1
    return cands


def reformed_spelling(
    lemma: str,
    in_dictionary: Callable[[str], bool],
    relemmatize: Callable[[str], str],
) -> str | None:
    """Convention 5.  Only rewrites a lemma the dictionary does not know
    into one it does, so `facto` and `contacto` -- which keep their
    consonant in post-1990 European spelling and are in the dictionary --
    are never touched.  A reformed plural (`acções` -> `ações`) is passed
    back through the lemmatizer to reach its singular."""
    if in_dictionary(lemma):
        return None
    for cand in reform_candidates(lemma):
        if in_dictionary(cand):
            again = relemmatize(cand)
            return again if in_dictionary(again) else cand
    return None


def masculine_candidates(lemma: str) -> list[str]:
    if lemma.endswith("esa"):
        return [lemma[:-3] + "ês"]
    if lemma.endswith("ora"):
        return [lemma[:-1]]
    if lemma.endswith("a") and not lemma.endswith("ã"):
        return [lemma[:-1] + "o"]
    return []


def apply(
    lemma_map: Mapping[str, str],
    cfg: dict[str, Any],
    in_dictionary: Callable[[str], bool],
    relemmatize: Callable[[str], str],
) -> tuple[dict[str, str], ConventionLog]:
    """Apply every enabled convention to a surface -> lemma map."""
    conv = cfg["conventions"]
    log = ConventionLog()
    out = dict(lemma_map)

    contractions = set(conv["contractions"]["forms"]) if conv["contractions"]["enabled"] else set()
    comparatives: dict[str, str] = {}
    if conv["comparatives"]["enabled"]:
        for lemma, forms in conv["comparatives"]["forms"].items():
            for form in forms:
                comparatives[form] = lemma
    fold_pairs, keep_pairs = gender_pairs(cfg) if conv["gender"]["enabled"] else ({}, {})
    gender_exceptions = set(conv["gender"].get("exceptions", ())) if conv["gender"]["enabled"] else set()

    for surface in sorted(out):
        lemma = out[surface]

        # 4. comparatives and superlatives are their own lemmas
        if surface in comparatives:
            if lemma != comparatives[surface]:
                log.add("4_comparatives", surface, lemma, comparatives[surface])
            out[surface] = comparatives[surface]
            continue

        # 1. contractions are their own entries
        if surface in contractions:
            if lemma != surface:
                log.add("1_contractions", surface, lemma, surface)
            out[surface] = surface
            continue

        # 3. diminutives stay separate -- revert only when the backend
        # actually stripped the diminutive (coisinha -> coisa), so words
        # that merely end in -inho (caminho, vizinho, tinha) are untouched.
        if conv["diminutives"]["enabled"]:
            m = _DIMINUTIVE.match(surface)
            if m:
                base = strip_diacritics(m.group("base"))
                plain = strip_diacritics(lemma)
                # The lemma must be the base word itself (coisa, pato, café),
                # and the base long enough to be one: `tinha` -> `ter` has
                # base `t`, and is a verb form, not a diminutive.
                if len(base) >= 3 and plain in {base, base + "o", base + "a", base + "e"}:
                    target = _singular(surface)
                    log.add("3_diminutives", surface, lemma, target)
                    out[surface] = target
                    continue

        # 5. spelling-reform variants merge under the post-1990 spelling
        if conv["spelling_reform"]["enabled"]:
            new = reformed_spelling(lemma, in_dictionary, relemmatize)
            if new and new != lemma:
                log.add("5_spelling_reform", surface, lemma, new)
                lemma = new
                out[surface] = new

        # 2. Gendered nouns fold into the masculine -- but only for pairs
        # listed as `fold` in the reviewed pairs file. No automatic signal
        # separates menina/menino (fold) from música/músico (keep): simplemma
        # folds every -a form, and stanza keeps every feminine noun.
        sg = _singular(surface)
        # Configured exceptions are named in eval/conventions.md itself, so
        # they are protected unconditionally -- including from a verb
        # reading (stanza: ferida -> ferir, the participle).
        if sg in gender_exceptions:
            if lemma != sg:
                log.add("2_gender_exception", surface, lemma, sg)
            out[surface] = sg
            continue
        if lemma in fold_pairs:
            log.add("2_gender", surface, lemma, fold_pairs[lemma])
            out[surface] = fold_pairs[lemma]
            continue
        # A `keep` pair (or a configured exception such as ferida) stays
        # separate. Only a gender fold made by the backend is reverted, so a
        # legitimate participle lemma (vestida -> vestir) is left alone.
        if sg in keep_pairs and lemma == keep_pairs[sg]:
            log.add("2_gender_exception", surface, lemma, sg)
            out[surface] = sg

    return out, log


def gender_pairs(cfg: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    """Read the reviewed feminine/masculine pairs.

    The file carries a first-pass `claude_decision` and a `jim_decision`
    column; a non-empty jim_decision wins, as in the lemma gold set.
    Returns ({feminine: masculine} to fold, {feminine: masculine} to keep).
    """
    import csv
    from pathlib import Path

    gcfg = cfg["conventions"]["gender"]
    fold: dict[str, str] = {}
    keep: dict[str, str] = {}
    path = Path(gcfg["pairs_file"])
    if path.is_file():
        with path.open(encoding="utf-8", newline="") as fh:
            for rec in csv.DictReader(fh, delimiter="\t"):
                decision = (rec.get("jim_decision") or "").strip() or rec["claude_decision"].strip()
                target = fold if decision == "fold" else keep
                target[rec["feminine"].strip()] = rec["masculine"].strip()
    for fem in gcfg.get("exceptions", ()):
        fold.pop(fem, None)
        for masc in masculine_candidates(fem):
            keep[fem] = masc
    return fold, keep


def protected_forms(cfg: dict[str, Any]) -> set[str]:
    """Headwords a convention deliberately keeps separate.  The quality
    report must not flag them as duplicates of their neighbours."""
    conv = cfg["conventions"]
    keep: set[str] = set()
    if conv["contractions"]["enabled"]:
        keep |= set(conv["contractions"]["forms"])
    if conv["comparatives"]["enabled"]:
        for lemma, forms in conv["comparatives"]["forms"].items():
            keep.add(lemma)
            keep |= set(forms)
    return keep
