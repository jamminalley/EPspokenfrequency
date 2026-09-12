"""Pluggable lemmatization backends.

README pipeline step 2: lemmatize the type inventory, correct known errors
via an override table, and validate against the pyspellchecker PT dictionary
(rejected lemmas fall back to the surface form).

The original used simplemma alone.  Here the lemmatizer is a swappable
backend so that simplemma, spaCy, Stanza and a majority vote among them can
be scored against the hand-checked gold set in eval/ and compared on equal
terms.

Context.  simplemma is type-level: it sees a bare word.  spaCy and Stanza
are context-sensitive and lemmatize far better given a real sentence, but
running them over 624M tokens is infeasible.  The compromise is sampled
context: pass 2 reservoir-samples a few sentences per surface type, the
backend lemmatizes the word inside those sentences, and the majority lemma
wins.  That also gives a principled way to split forms that are genuinely
ambiguous between lemmas -- `foi`/`fomos` are preterite of both `ser` and
`ir` -- by voting over real usage instead of guessing from a lookup table.
"""

from __future__ import annotations

import functools
from collections import Counter
from typing import Any, Iterable, Mapping, Protocol, Sequence, runtime_checkable

Contexts = Mapping[str, Sequence[str]]


# -- dictionary -----------------------------------------------------------


@functools.lru_cache(maxsize=4)
def pt_dictionary(lang: str = "pt") -> frozenset[str]:
    """The pyspellchecker PT word list, used to validate proposed lemmas.

    Also used by the Stage 2 diacritic-folding fix, where the check is what
    stops real minimal pairs (e/é, da/dá, esta/está) being merged.
    """
    from spellchecker import SpellChecker

    return frozenset(SpellChecker(language=lang).word_frequency.dictionary.keys())


def in_dictionary(word: str, lang: str = "pt") -> bool:
    return word.lower() in pt_dictionary(lang)


# -- backends -------------------------------------------------------------


@runtime_checkable
class LemmaBackend(Protocol):
    name: str

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        """Map each surface type to a lemma.  Must be deterministic."""
        ...


class SimplemmaBackend:
    """Lookup-based, type-level.  Ignores context by construction."""

    name = "simplemma"

    def __init__(self, lang: str = "pt", greedy: bool = False) -> None:
        self.lang = lang
        self.greedy = greedy

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        import simplemma

        out: dict[str, str] = {}
        for surface in types:
            try:
                out[surface] = simplemma.lemmatize(
                    surface, lang=self.lang, greedy=self.greedy
                ).lower()
            except Exception:
                out[surface] = surface
        return out


class SpacyBackend:
    """spaCy pipeline.  Uses sampled sentence context when available.

    With context, each sampled sentence is parsed and the lemma of the token
    matching the surface form is taken; the majority lemma wins, ties broken
    lexicographically so the result is deterministic.  Without context the
    word is parsed alone, which is markedly weaker -- that difference is the
    whole reason sampled context exists.
    """

    name = "spacy"

    def __init__(self, model: str = "pt_core_news_lg", batch_size: int = 256) -> None:
        self.model = model
        self.batch_size = batch_size
        self._nlp = None

    def _load(self):
        if self._nlp is None:
            import spacy

            # The lemmatizer needs the tagger/morphologizer, not the parser
            # or NER; disabling those is a large speedup at no cost here.
            self._nlp = spacy.load(self.model, exclude=["parser", "ner"])
        return self._nlp

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        nlp = self._load()
        out: dict[str, str] = {}

        with_ctx = [t for t in types if contexts and contexts.get(t)]
        without_ctx = [t for t in types if not (contexts and contexts.get(t))]

        # Bare-word path.
        for surface, doc in zip(
            without_ctx, nlp.pipe(without_ctx, batch_size=self.batch_size)
        ):
            out[surface] = (doc[0].lemma_ or surface).lower() if len(doc) else surface

        # Sampled-context path: one flat stream of sentences keeps nlp.pipe
        # batching effective.
        flat: list[str] = []
        owner: list[str] = []
        for surface in with_ctx:
            for sent in contexts[surface]:  # type: ignore[index]
                flat.append(sent)
                owner.append(surface)

        votes: dict[str, Counter] = {t: Counter() for t in with_ctx}
        for surface, doc in zip(owner, nlp.pipe(flat, batch_size=self.batch_size)):
            for token in doc:
                if token.text.lower() == surface:
                    votes[surface][(token.lemma_ or surface).lower()] += 1

        for surface in with_ctx:
            out[surface] = _majority(votes[surface], fallback=surface)
        return out


class StanzaBackend:
    """Stanza pipeline.  Not installed by default; import is deferred."""

    name = "stanza"

    def __init__(self, lang: str = "pt") -> None:
        self.lang = lang
        self._nlp = None

    def _load(self):
        if self._nlp is None:
            import stanza

            self._nlp = stanza.Pipeline(
                lang=self.lang, processors="tokenize,pos,lemma", verbose=False
            )
        return self._nlp

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        nlp = self._load()
        out: dict[str, str] = {}
        for surface in types:
            sents = list(contexts.get(surface, ())) if contexts else []
            votes: Counter = Counter()
            for text in sents or [surface]:
                doc = nlp(text)
                for sent in doc.sentences:
                    for word in sent.words:
                        if word.text.lower() == surface:
                            votes[(word.lemma or surface).lower()] += 1
            out[surface] = _majority(votes, fallback=surface)
        return out


class VoteBackend:
    """Majority vote across member backends.

    Ties are broken by the configured priority order rather than by whichever
    backend happens to be listed first in a dict, so the result does not
    depend on iteration order.
    """

    name = "vote"

    def __init__(self, members: Sequence[LemmaBackend], tiebreak: Sequence[str]) -> None:
        if not members:
            raise ValueError("vote backend needs at least one member")
        self.members = list(members)
        self.tiebreak = list(tiebreak)

    def lemmatize_types(
        self, types: Sequence[str], contexts: Contexts | None = None
    ) -> dict[str, str]:
        per_backend = {
            m.name: m.lemmatize_types(types, contexts) for m in self.members
        }
        out: dict[str, str] = {}
        for surface in types:
            votes: Counter = Counter()
            for name, mapping in per_backend.items():
                votes[mapping.get(surface, surface)] += 1
            top = max(votes.values())
            winners = sorted(w for w, c in votes.items() if c == top)
            if len(winners) == 1:
                out[surface] = winners[0]
                continue
            # Tie: defer to the highest-priority backend that proposed one
            # of the tied candidates.
            chosen = None
            for name in self.tiebreak:
                candidate = per_backend.get(name, {}).get(surface)
                if candidate in winners:
                    chosen = candidate
                    break
            out[surface] = chosen if chosen is not None else winners[0]
        return out


def _majority(votes: Counter, fallback: str) -> str:
    """Most-voted item; ties broken lexicographically for determinism."""
    if not votes:
        return fallback
    top = max(votes.values())
    return sorted(w for w, c in votes.items() if c == top)[0]


# -- factory --------------------------------------------------------------


def get_backend(name: str, cfg: dict[str, Any]) -> LemmaBackend:
    lem = cfg["lemmatizer"]
    if name == "simplemma":
        return SimplemmaBackend()
    if name == "spacy":
        return SpacyBackend(model=lem["spacy_model"])
    if name == "stanza":
        return StanzaBackend(lang=lem["stanza_lang"])
    if name == "vote":
        members = [get_backend(n, cfg) for n in lem["vote"]["members"]]
        return VoteBackend(members, lem["vote"]["tiebreak"])
    raise ValueError(f"unknown lemmatizer backend: {name!r}")


# -- override table and validation ----------------------------------------


def load_overrides(path: str | None) -> dict[str, str]:
    """Load the hand-curated surface -> lemma override table.

    The original's ~200-entry table was lost.  scripts/overrides.py rebuilds
    a candidate table empirically; entries confirmed by review live here.
    Missing file is not an error -- it simply means no overrides.
    """
    from pathlib import Path

    if not path:
        return {}
    p = Path(path)
    if not p.is_file():
        return {}
    out: dict[str, str] = {}
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            surface, _, lemma = line.partition("\t")
            if surface and lemma:
                out[surface.strip()] = lemma.strip()
    return out


def build_lemma_map(
    cfg: dict[str, Any],
    types: Sequence[str],
    contexts: Contexts | None = None,
    backend: LemmaBackend | None = None,
) -> dict[str, str]:
    """Full step 2: backend -> overrides -> dictionary validation.

    A lemma the PT dictionary does not recognise is rejected and the surface
    form is kept, exactly as the original README describes.
    """
    lem = cfg["lemmatizer"]
    backend = backend or get_backend(lem["backend"], cfg)
    mapping = backend.lemmatize_types(list(types), contexts)

    overrides = load_overrides(lem.get("overrides_path"))
    for surface, lemma in overrides.items():
        if surface in mapping:
            mapping[surface] = lemma

    if lem.get("validate_with_spellchecker"):
        lang = lem.get("spellchecker_lang", "pt")
        vocab = pt_dictionary(lang)
        for surface, lemma in mapping.items():
            # An override is a human decision and outranks the dictionary.
            if surface in overrides:
                continue
            if lemma != surface and lemma.lower() not in vocab:
                mapping[surface] = surface
    return mapping
