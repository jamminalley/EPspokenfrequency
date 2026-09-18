"""Published part of speech, from Stanza's tags.

Stanza tags every sampled sentence of every frequent word in one pass
(scripts/occurrence.py). A lemma's POS comes from those tags:

  * a word whose lemma is not split contributes the tags of the sentences
    where Stanza's lemma is the majority lemma or the word itself -- `casa`
    tagged VERB is `casar`, and must not make the noun `casa` a verb, but
    `a` read as the article *o* and as the preposition *a* is still `a`;
  * a word split across lemmas (participles, fomos) already carries a
    (lemma, POS) pair per sentence, and those pairs are used directly.

Each word's corpus count is divided across POS in proportion to its tags,
exactly as a split word's count is divided across lemmas, and the shares
are summed per lemma. The majority POS is published. A secondary POS
becomes an entry of its own when it holds at least `pos.split_min_share`
of the lemma's count and at least `pos.split_min_votes` tagged sentences;
otherwise its share joins the majority. A lemma with no tagged evidence
(contractions, whose tokens Stanza expands, and the low-frequency tail)
falls back to the rule heuristic.

Stanza's tag and lemma for one sentence do not always agree -- `consigo`
comes back as lemma *conseguir* tagged ADV (it read the pronoun), `conta`
as *contar* tagged NOUN, `mais` as NOUN in 19 of 50 sentences. A tag is
only counted when it is consistent with its lemma:
  * a VERB/AUX tag needs a verb lemma;
  * any other tag on a verb lemma counts only for the infinitive itself
    (a nominalised infinitive: *o poder*, *o jantar*);
  * a function word (the closed-class table) cannot be a noun or a verb.
A verb lemma is infinitive-shaped and not tagged mainly as a noun or
adjective in its own sentences, so `lugar` and `mulher` are not verbs.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Mapping, Sequence

from scripts.occurrence import apportion


def map_upos(upos: str, cfg: dict[str, Any], lemma: str | None = None) -> str:
    """UD tag -> the list's POS. A conjunction tag on a word from
    pos.always_prep counts as prep (UD tags "para fazer" as SCONJ)."""
    mapped = cfg["pos"]["upos_map"].get(upos, "unk")
    if mapped == "conj" and lemma is not None and lemma in cfg["pos"].get("always_prep", ()):
        return "prep"
    return mapped


def majority(votes: Counter) -> str | None:
    if not votes:
        return None
    top = max(votes.values())
    return sorted(k for k, v in votes.items() if v == top)[0]


_VERB_TAGS = ("VERB", "AUX")
_NOMINAL_TAGS = ("NOUN", "PROPN", "ADJ")


def verb_lemmas(tags: Mapping[str, Sequence[tuple[str, str, str]]]):
    """Predicate: is this lemma a verb? Infinitive-shaped, and not tagged
    mainly as a noun or adjective where it occurs as a surface itself."""
    nominal: set[str] = set()
    for surface, occs in tags.items():
        upos = majority(Counter(u for _, u, _ in occs))
        if upos in _NOMINAL_TAGS:
            nominal.add(surface)

    def is_verb(lemma: str) -> bool:
        return lemma.endswith(("ar", "er", "ir", "ôr")) and lemma not in nominal
    return is_verb


def consistent(surface: str, lemma: str, upos: str, is_verb, closed) -> bool:
    if upos in _VERB_TAGS:
        return is_verb(lemma) and lemma not in closed
    if is_verb(lemma):
        return surface == lemma
    if lemma in closed and upos in ("NOUN", "PROPN"):
        return False
    return True


def aggregate(
    surface_counts: Mapping[str, int],
    tags: Mapping[str, Sequence[tuple[str, str, str]]],
    joint: Mapping[str, Counter],
    headword_of_surface: Callable[[str], str],
    headword_of_lemma: Callable[[str], str],
    cfg: dict[str, Any],
    closed: frozenset[str] = frozenset(),
    stats: dict[str, int] | None = None,
) -> tuple[dict[str, Counter], dict[str, Counter]]:
    """Count-weighted POS shares and raw tag votes, per final lemma.

    ``joint`` maps a split surface to Counter{(lemma, upos): votes}.
    ``headword_of_surface`` gives the published headword of an unsplit
    surface, and ``headword_of_lemma`` the headword a split surface's
    per-sentence lemma ends up under (both through conventions, closure
    and accent folding).
    """
    weighted: dict[str, Counter] = {}
    raw: dict[str, Counter] = {}
    is_verb = verb_lemmas(tags)

    def add(lemma: str, pos_votes: Counter, count: int) -> None:
        w = weighted.setdefault(lemma, Counter())
        r = raw.setdefault(lemma, Counter())
        for pos, share in apportion(count, pos_votes).items():
            w[pos] += share
        r.update(pos_votes)

    for surface in sorted(surface_counts):
        count = surface_counts[surface]
        if surface in joint:
            cells: dict[str, Counter] = {}
            for (lemma, upos), n in joint[surface].items():
                cells.setdefault(lemma, Counter())[map_upos(upos, cfg, lemma)] += n
            by_lemma = Counter({lemma: sum(c.values()) for lemma, c in cells.items()})
            for lemma, share in apportion(count, by_lemma).items():
                add(headword_of_lemma(lemma), cells[lemma], share)
            continue
        occs = tags.get(surface) or ()
        if not occs:
            continue
        agreed = majority(Counter(lemma for lemma, _, _ in occs))
        votes: Counter = Counter()
        for lemma, upos, _ in occs:
            # A sentence counts if Stanza's lemma is the majority lemma or
            # the word itself: `a` is lemmatized *o* as an article and *a*
            # as a preposition, and both readings belong to the entry `a`.
            if lemma != agreed and lemma != surface:
                continue
            if consistent(surface, lemma, upos, is_verb, closed):
                votes[map_upos(upos, cfg, lemma)] += 1
            elif stats is not None:
                stats["inconsistent"] = stats.get("inconsistent", 0) + 1
        if stats is not None:
            stats["counted"] = stats.get("counted", 0) + sum(votes.values())
        if votes:
            add(headword_of_surface(surface), votes, count)
    return weighted, raw


def assign(
    lemma: str,
    count: int,
    weighted: Mapping[str, Counter],
    raw: Mapping[str, Counter],
    cfg: dict[str, Any],
    fallback: Callable[[str], str],
) -> list[tuple[str, int]]:
    """[(pos, count)] for one lemma: one row, or one per well-supported POS.

    Shares below the split thresholds join the majority POS. The lemma's
    final count is divided in proportion to the kept POS shares.
    """
    shares = weighted.get(lemma)
    if not shares or sum(shares.values()) == 0:
        return [(fallback(lemma), count)]
    total = sum(shares.values())
    votes = raw.get(lemma, Counter())
    main = majority(shares)
    kept = Counter({main: 0})
    for pos, w in shares.items():
        target = pos
        if pos != main and (w / total < cfg["pos"]["split_min_share"]
                            or votes.get(pos, 0) < cfg["pos"]["split_min_votes"]):
            target = main
        kept[target] += w
    parts = apportion(count, kept)
    return sorted(parts.items(), key=lambda kv: (-kv[1], kv[0]))
