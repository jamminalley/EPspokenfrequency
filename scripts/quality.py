"""Quality report: suspect duplicate entries.

Runs on every build and lists entries that look like the same word counted
twice:

  relemmatize   an entry that lemmatizes to another entry (chega -> chegar)
  diacritic     an unaccented entry alongside its accented twin (nao/não)
  inflected     an entry that is a regular inflection of another entry

Stage 1 reproduces a pipeline whose documented flaws are exactly these, so
its suspect list is expected to be long and the gate only warns.  Stage 2
must set quality.fail_on_suspects, and config validation enforces that, so
a suspect that is not explicitly whitelisted fails the build.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence

from scripts.tokenizer import strip_diacritics


@dataclass(frozen=True)
class Suspect:
    kind: str
    entry: str
    other: str
    entry_rank: int
    other_rank: int
    detail: str

    @property
    def pair_key(self) -> str:
        """Order-independent key, so a whitelist entry covers both directions."""
        a, b = sorted((self.entry, self.other))
        return f"{a}|{b}"


def _plural_forms(lemma: str) -> set[str]:
    """Regular Portuguese plurals.  Deliberately conservative."""
    out: set[str] = set()
    if lemma.endswith("ão"):
        stem = lemma[:-2]
        out |= {stem + "ões", stem + "ães", stem + "ãos"}
    elif lemma.endswith("ês"):
        # inglês -> ingleses: the circumflex goes in the plural.
        out.add(lemma[:-2] + "eses")
    elif lemma.endswith(("r", "z", "s")):
        out.add(lemma + "es")
    elif lemma.endswith("l"):
        out.add(lemma[:-1] + "is")
    elif lemma.endswith("m"):
        out.add(lemma[:-1] + "ns")
    else:
        out.add(lemma + "s")
    return out


def singular_of(plural: str, inventory: set[str]) -> str | None:
    """Singular in ``inventory`` of which ``plural`` is a regular plural."""
    if not plural.endswith("s") or len(plural) < 3:
        return None
    cands: list[str] = []
    if plural.endswith(("ões", "ães", "ãos")):
        cands.append(plural[:-3] + "ão")
    if plural.endswith("eses"):
        cands.append(plural[:-4] + "ês")
    if plural.endswith("es"):
        cands.append(plural[:-2])
    if plural.endswith("is"):
        cands.append(plural[:-2] + "l")
    if plural.endswith("ns"):
        cands.append(plural[:-2] + "m")
    cands.append(plural[:-1])
    for cand in cands:
        if cand in inventory and plural in _plural_forms(cand):
            return cand
    return None


def singular_candidates(plural: str, inventory: set[str]) -> list[str]:
    """Every singular in ``inventory`` that ``plural`` could be the plural
    of, in rule order.  The caller picks the first that passes its guards:
    taking only the first hit let a junk tail lemma (`bol`, `rel`) shadow
    the real singular (`boi`, `rei`)."""
    if not plural.endswith("s") or len(plural) < 3:
        return []
    cands: list[str] = []
    if plural.endswith(("ões", "ães", "ãos")):
        cands.append(plural[:-3] + "ão")
    if plural.endswith("eses"):
        cands.append(plural[:-4] + "ês")
    if plural.endswith("es"):
        cands.append(plural[:-2])
    if plural.endswith("is"):
        cands.append(plural[:-2] + "l")
    if plural.endswith("ns"):
        cands.append(plural[:-2] + "m")
    cands.append(plural[:-1])
    return [c for c in cands if c in inventory and plural in _plural_forms(c)]


def _gender_forms(lemma: str) -> set[str]:
    out: set[str] = set()
    # -ão is not the masculine -o ending; coração has no *coraçãa.
    if lemma.endswith("o") and not lemma.endswith("ão"):
        out.add(lemma[:-1] + "a")
    if lemma.endswith("or"):
        out.add(lemma + "a")
    if lemma.endswith("ês"):
        out.add(lemma[:-2] + "esa")
    return out


def inflections(lemma: str, include_gender: bool = False) -> set[str]:
    """Regular inflected forms of a lemma, excluding the lemma itself.

    Gender is off by default.  A masculine/feminine pair in Portuguese is
    usually two legitimate entries rather than one word counted twice
    (`menino`/`menina`), and the rule also fires on contractions that are
    simply different words -- `na`/`no` (em+a, em+o), `pela`/`pelo`
    (por+a, por+o) -- and on non-words like `problemo`. Including it made
    the gate unusable: 1,274 suspects, nearly all spurious.

    Plurals are the real duplicate risk, and are kept.
    """
    forms = set(_plural_forms(lemma))
    if include_gender:
        forms |= _gender_forms(lemma)
        for gendered in list(_gender_forms(lemma)):
            forms |= _plural_forms(gendered)
    forms.discard(lemma)
    return forms


def find_suspects(
    entries: Sequence[Any],
    cfg: dict[str, Any],
    relemmatize: Callable[[str], str] | None = None,
    closed_class: frozenset[str] = frozenset(),
) -> list[Suspect]:
    """Scan the ranked entry list for duplicate-looking pairs.

    ``closed_class`` holds function words.  The inflection check skips them:
    `mas` is not the plural of `mo`, nor `mais` of `mal`, but a regular
    inflection generator will happily propose both.  Inflection only makes
    sense for open-class vocabulary.
    """
    qcfg = cfg["quality"]
    rank_of = {e.lemma: e.rank for e in entries if not e.is_mwe}
    lemmas = list(rank_of)
    found: list[Suspect] = []

    if qcfg.get("check_relemmatize") and relemmatize is not None:
        for lemma in lemmas:
            target = relemmatize(lemma)
            if target != lemma and target in rank_of:
                found.append(
                    Suspect("relemmatize", lemma, target, rank_of[lemma],
                            rank_of[target], f"{lemma} lemmatizes to {target}")
                )

    if qcfg.get("check_diacritic_pairs"):
        by_folded: dict[str, list[str]] = {}
        for lemma in lemmas:
            by_folded.setdefault(strip_diacritics(lemma), []).append(lemma)
        for folded, group in by_folded.items():
            if len(group) < 2:
                continue
            # Report against the most frequent member (lowest rank).
            group = sorted(group, key=lambda w: rank_of[w])
            head = group[0]
            for other in group[1:]:
                found.append(
                    Suspect("diacritic", other, head, rank_of[other], rank_of[head],
                            f"both fold to {folded!r}")
                )

    if qcfg.get("check_inflected_forms"):
        include_gender = qcfg.get("inflection_include_gender", False)
        inflected_index: dict[str, str] = {}
        for lemma in lemmas:
            if lemma in closed_class:
                continue
            for form in inflections(lemma, include_gender):
                # First lemma wins; ties resolved by rank for determinism.
                if form not in inflected_index or rank_of[lemma] < rank_of[inflected_index[form]]:
                    inflected_index[form] = lemma
        for lemma in lemmas:
            if lemma in closed_class:
                continue
            base = inflected_index.get(lemma)
            if base and base != lemma:
                found.append(
                    Suspect("inflected", lemma, base, rank_of[lemma], rank_of[base],
                            f"{lemma} is a regular inflection of {base}")
                )

    def _key(pair: str) -> str:
        a, _, b = pair.partition("|")
        return "|".join(sorted((a, b)))

    whitelist = {_key(p) for p in (qcfg.get("whitelist_pairs") or ())}
    whitelist |= {_key(p) for p in (qcfg.get("manual_whitelist_pairs") or ())}
    found = [s for s in found if s.pair_key not in whitelist]
    # Deduplicate (a pair can trip more than one check) and order by rank.
    seen: set[tuple[str, str]] = set()
    unique: list[Suspect] = []
    for s in sorted(found, key=lambda s: (s.entry_rank, s.kind, s.entry)):
        key = (s.kind, s.pair_key)
        if key in seen:
            continue
        seen.add(key)
        unique.append(s)
    return unique


def render_report(suspects: Sequence[Suspect], cfg: dict[str, Any]) -> str:
    stage = cfg["run"]["stage"]
    gate = cfg["quality"]["fail_on_suspects"]
    by_kind: dict[str, int] = {}
    for s in suspects:
        by_kind[s.kind] = by_kind.get(s.kind, 0) + 1

    lines = [
        "# Quality report: suspect duplicate entries",
        "",
        f"Stage {stage}. Gate: {'FAIL on suspects' if gate else 'warn only'}.",
        "",
    ]
    if stage == 1:
        lines += [
            "> Stage 1 reproduces the original pipeline including its known",
            "> flaws, so a long list here is the expected result, not a",
            "> regression. The gate is enforced from stage 2.",
            "",
        ]
    lines += [f"**{len(suspects)} suspects**: " + (
        ", ".join(f"{k} {v}" for k, v in sorted(by_kind.items())) or "none"), ""]
    if not suspects:
        lines.append("No suspect pairs found.")
        return "\n".join(lines) + "\n"

    lines += ["| kind | entry | rank | duplicate of | rank | detail |",
              "|---|---|---:|---|---:|---|"]
    for s in suspects[:200]:
        lines.append(
            f"| {s.kind} | `{s.entry}` | {s.entry_rank} | `{s.other}` | "
            f"{s.other_rank} | {s.detail} |"
        )
    if len(suspects) > 200:
        lines.append(f"\n_{len(suspects) - 200} further suspects omitted; "
                     "see the TSV for the full list._")
    return "\n".join(lines) + "\n"


def render_folds(fold_log, cfg: dict[str, Any]) -> str:
    """Every accent-variant fold the build made, for review.

    Folds whose source is itself a PT dictionary word come first: the
    frequency ratio merged them anyway, and those are the ones that could
    be a real minimal pair rather than a typo.
    """
    ratio = cfg["fixes"].get("diacritic_fold_ratio", 20)
    words = [f for f in fold_log if f[5]]
    lines = [
        "",
        "## Diacritic folds",
        "",
        f"{len(fold_log):,} lemmas were folded into an accent variant at least "
        f"{ratio}x as frequent ({sum(1 for f in fold_log if f[4] == 'unaccented'):,} "
        f"unaccented, {sum(1 for f in fold_log if f[4] == 'accent_variant'):,} wrong "
        "or Brazilian accent). Every fold is listed.",
        "",
        f"### Folds of a dictionary word ({len(words):,}) — review these",
        "",
        "The source is a real PT word, merged on frequency alone. Most are "
        "missing-accent typos of a far commoner word; any that is a genuine "
        "second word should go on a keep-list.",
        "",
        "| from | count | into | count | ratio |",
        "|---|---:|---|---:|---:|",
    ]
    for src, dst, sc, dc, kind, _ in words:
        lines.append(f"| `{src}` | {sc:,} | `{dst}` | {dc:,} | {dc / sc:,.0f}x |")
    upper = cfg["fixes"].get("diacritic_review_below", 20)
    band = [f for f in fold_log if f[4] == "unaccented" and f[3] < upper * f[2]]
    lines += [
        "",
        f"### Folds between {ratio}x and {upper}x ({len(band):,}) — review these",
        "",
        f"Merged since the ratio was lowered from {upper}x to {ratio}x. Each is a "
        "missing-accent form at 10-20x less frequent than its accented twin.",
        "",
        "| from | count | into | count | ratio | from is a PT word |",
        "|---|---:|---|---:|---:|---|",
    ]
    for src, dst, sc, dc, kind, is_word in band:
        lines.append(f"| `{src}` | {sc:,} | `{dst}` | {dc:,} | {dc / sc:,.1f}x | "
                     f"{'yes' if is_word else ''} |")
    rest = [f for f in fold_log if not f[5]]
    lines += ["", f"<details><summary>All other folds ({len(rest):,})</summary>", "",
              "| from | count | into | count | kind |", "|---|---:|---|---:|---|"]
    for src, dst, sc, dc, kind, _ in rest:
        lines.append(f"| `{src}` | {sc:,} | `{dst}` | {dc:,} | {kind} |")
    lines += ["", "</details>", ""]
    return "\n".join(lines)


def write_tsv(suspects: Sequence[Suspect], path) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("kind\tentry\tentry_rank\tother\tother_rank\tdetail\n")
        for s in suspects:
            fh.write(f"{s.kind}\t{s.entry}\t{s.entry_rank}\t{s.other}\t"
                     f"{s.other_rank}\t{s.detail}\n")


class QualityGateFailure(RuntimeError):
    """Raised when the gate is on and unwhitelisted suspects remain."""


def enforce(suspects: Sequence[Suspect], cfg: dict[str, Any]) -> None:
    if cfg["quality"]["fail_on_suspects"] and suspects:
        raise QualityGateFailure(
            f"{len(suspects)} suspect duplicate entries and "
            "quality.fail_on_suspects is set. Fix them, or whitelist the pairs "
            "explicitly in config.quality.whitelist_pairs. "
            f"First: {', '.join(s.pair_key for s in suspects[:5])}"
        )
