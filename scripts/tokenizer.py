"""Tokenization, subtitle-artifact stripping, and enclitic splitting.

README pipeline step 1: "Tokenize + count unigram surface forms
(Portuguese-aware regex, subtitle-artifact stripping, lowercase
normalization, enclitic-cluster splitting)."

The original implementation is lost.  This is a reconstruction, calibrated
against the three totals the original README published (118,469,705 lines /
623,920,347 tokens / 955,446 unique surface types) -- see
``scripts/counts.py`` and the fingerprint table in COMPARISON.md.

Everything here is pure and side-effect free so it can be unit-tested
without the corpus.
"""

from __future__ import annotations

import unicodedata
from typing import Any, Iterable, Sequence

import regex as re

# A word is a run of Unicode letters, optionally joined by internal
# apostrophes or hyphens (d'agua, guarda-chuva, da-me).  Hyphen-joined
# runs are split further by ``split_enclitic`` when the tail is a clitic.
_WORD_RE = re.compile(r"\p{L}+(?:[-'’]\p{L}+)*")

# Text between two tokens that ends a sentence: final punctuation, or a
# dialogue dash (a hyphen with a space on either side, or an en/em dash).
_SENTENCE_BREAK = re.compile(r"[.!?…]|(?:^|\s)-|-(?:\s|$)|[–—]")

_APOSTROPHES = {"’": "'", "ʼ": "'"}

# Final-vowel accents that an enclitic l-form adds to the verb before it.
_ACCENT_OFF = {"á": "a", "é": "e", "ê": "e", "í": "i", "ó": "o", "ô": "o"}


class Tokenizer:
    """Configured tokenizer.  Construct once, reuse across lines.

    Constructing from config keeps every rule in config.yaml rather than in
    code, so a build's tokenization is fully described by its config file.
    """

    def __init__(self, tok_cfg: dict[str, Any]) -> None:
        self.lowercase: bool = tok_cfg["lowercase"]
        self.strip_artifacts: bool = tok_cfg["strip_artifacts"]
        self.split_enclitics: bool = tok_cfg["split_enclitics"]
        self.keep_digits: bool = tok_cfg["keep_digits"]
        self.min_token_len: int = tok_cfg["min_token_len"]

        self._artifact_res: list[re.Pattern[str]] = [
            re.compile(p) for p in tok_cfg["artifact_patterns"]
        ]
        # Longest-first so that "lhes" wins over "lhe", "los" over "lo".
        self.enclitics: tuple[str, ...] = tuple(
            sorted(set(tok_cfg["enclitics"]), key=lambda s: (-len(s), s))
        )
        self._enclitic_set = frozenset(self.enclitics)
        self._mesoclitic_set = frozenset(tok_cfg.get("mesoclitic_suffixes", ()))
        self.restore_stems: bool = tok_cfg.get("restore_clitic_stems", False)
        self._is_word = None  # PT dictionary, loaded on first use

        # Clusters the corpus also writes without their hyphen. Splitting
        # those cannot be done by rule -- see scripts/make_glue_table.py --
        # so it is done from a table generated from the corpus itself.
        self.repair_glue: bool = bool(tok_cfg.get("repair_glue", False))
        self._glued: dict[str, tuple[str, str]] = {}
        if self.repair_glue:
            from scripts.make_glue_table import load as _load_glue

            self._glued = _load_glue(tok_cfg["glue_repair"]["table"])

    def _word(self, w: str) -> bool:
        if self._is_word is None:
            from scripts.lemmas import pt_dictionary

            vocab = pt_dictionary("pt")
            self._is_word = vocab.__contains__
        return self._is_word(w)

    def restore_stem(self, stem: str, clitic: str) -> str:
        """Undo the sound change a clitic forces on the verb before it.

        Before lo/la/los/las a verb drops its final -r, -s or -z and an
        infinitive gains an accent (fazer-o -> fazê-lo, apanhar-o ->
        apanhá-lo, diz-o -> di-lo, apanhámos-o -> apanhámo-lo); before nos a
        first-person plural drops its -s (vamos-nos -> vamo-nos).  Splitting
        without undoing this leaves non-words such as `fazê` and `apanhámo`,
        which eval/conventions.md lists as tokenizer artifacts.

        Candidates are tried in a fixed order and the first dictionary word
        wins, so `pô-lo` restores to `pôr`, not to the preposition `por`.
        """
        if not self.restore_stems or not stem:
            return stem
        if clitic in ("lo", "la", "los", "las"):
            base = stem[:-1] + _ACCENT_OFF.get(stem[-1], stem[-1])
            for cand in (stem + "r", base + "r", stem + "s", base + "s",
                         base + "z", stem + "z"):
                if self._word(cand):
                    return cand
            return stem
        if clitic == "nos" and stem.endswith("mo") and self._word(stem + "s"):
            return stem + "s"
        return stem

    # -- line level -------------------------------------------------------

    def clean(self, line: str) -> str:
        """Strip subtitle artifacts and normalize case/apostrophes."""
        if self.strip_artifacts:
            for pat in self._artifact_res:
                line = pat.sub(" ", line)
        for odd, plain in _APOSTROPHES.items():
            if odd in line:
                line = line.replace(odd, plain)
        if self.lowercase:
            line = line.lower()
        return line

    def tokenize(self, line: str) -> list[str]:
        """Turn one corpus line into a list of surface forms."""
        return [tok for tok, _ in self.tokenize_with_starts(line)]

    def tokenize_with_starts(self, line: str) -> list[tuple[str, bool]]:
        """Like tokenize, but flag each token that starts a sentence.

        A token starts a sentence if it is first on the line, or if the text
        since the previous token contains sentence-final punctuation (. ! ?
        …) or a dialogue dash.  A capital there says nothing about whether
        the word is a name, so the proper-noun filter must not count it --
        counting it made interjections such as `iá` (98% capitalized) look
        like names.  Only the first part of a split cluster can start one.
        """
        line = self.clean(line)
        out: list[tuple[str, bool]] = []
        prev_end = 0
        for match in _WORD_RE.finditer(line):
            gap = line[prev_end:match.start()]
            starts = not out or bool(_SENTENCE_BREAK.search(gap))
            prev_end = match.end()
            first = True
            for part in self._parts(match.group(0)):
                out.append((part, starts and first))
                first = False
        return out

    def _parts(self, word: str) -> list[str]:
        """One regex match -> surface forms (split, stripped, filtered)."""
        if "-" in word and self.split_enclitics:
            parts = self.split_enclitic(word)
        else:
            parts = self.split_glued(word) if self._glued else [word]
        out: list[str] = []
        for part in parts:
            part = part.strip("'-")
            if len(part) < self.min_token_len:
                continue
            if not self.keep_digits and any(ch.isdigit() for ch in part):
                continue
            out.append(part)
        return out

    # -- enclitic handling ------------------------------------------------

    def split_glued(self, word: str) -> list[str]:
        """Split a cluster whose hyphen the subtitler left out.

        ``conheçoa`` -> ["conheço", "a"]     (also written conheço-a)
        ``deixame``  -> ["deixa", "me"]
        ``rodeo``    -> ["rodeo"]            (not attested hyphenated)

        Only the clusters in the generated table are touched, and only when
        lowercased, so the split is exactly as verifiable as the table is.
        """
        found = self._glued.get(word if self.lowercase else word.lower())
        if found is None:
            return [word]
        stem, clitic = found
        return [stem, clitic]

    def split_enclitic(self, word: str) -> list[str]:
        """Split a hyphenated cluster into stem + clitic pronouns.

        ``da-me``      -> ["da", "me"]
        ``diz-lhe``    -> ["diz", "lhe"]
        ``dar-lhe-ia`` -> ["dar", "lhe", "ia"]   (mesoclitic future)
        ``guarda-chuva`` -> ["guarda-chuva"]     (not a clitic; left whole)

        Splitting proceeds from the right, so only a genuine trailing clitic
        run is peeled off; a compound noun whose tail is not a clitic is
        returned unchanged.
        """
        parts = word.split("-")
        if len(parts) < 2:
            return [word]

        tail: list[str] = []
        idx = len(parts)
        found_clitic = False
        while idx > 1:
            candidate = parts[idx - 1]
            if candidate in self._enclitic_set:
                found_clitic = True
                tail.append(candidate)
                idx -= 1
            elif not tail and candidate in self._mesoclitic_set:
                # Mesoclisis puts the tense infix at the right edge, after
                # the clitic: dar-lhe-ia.  Peel it first, but only keep the
                # split if a real clitic turns up to its left.
                tail.append(candidate)
                idx -= 1
            else:
                break

        # A compound whose tail merely looks clitic-shaped (nao-sei-que) is
        # left whole; only a genuine clitic licenses the split.
        if not found_clitic:
            return [word]
        stem = "-".join(parts[:idx])
        tail.reverse()
        if not stem:
            return tail
        if self.restore_stems and len(tail) > 1 and tail[-1] in self._mesoclitic_set:
            # Mesoclisis splits the future/conditional around the clitic:
            # dar-lhe-ia is daria + lhe. Reassemble the verb rather than
            # leaving `ia`, which would count as a form of `ir`.
            #
            # `len(tail) > 1` is what makes this mesoclisis rather than a
            # plain cluster. `a` and `as` are both clitics and tense infixes,
            # so without the test `conheço-a` reassembled into `conheçoa` and
            # reached the published list as a word (rank 5,290 in 1.0.0,
            # glossed "I know her"); 45 rows were like it. Mesoclisis always
            # has the clitic between stem and infix, so a tail of one is
            # never an infix.
            #
            # The stem is always the future stem, so an accented one
            # restores to -r
            # (fá-lo-ia -> far + ia = faria, not fazia).
            if stem[-1] in _ACCENT_OFF:
                stem = stem[:-1] + _ACCENT_OFF[stem[-1]] + "r"
            return [stem + tail[-1], *tail[:-1]]
        stem = self.restore_stem(stem, tail[0])
        return [stem, *tail]


def strip_diacritics(word: str) -> str:
    """Fold a word to its unaccented form (nao <- nao, difícil -> dificil).

    Used by the Stage 2 diacritic-folding fix and by the quality report's
    diacritic-pair check.  Uses NFD decomposition and drops combining marks,
    which handles the Portuguese inventory (acute, grave, circumflex, tilde,
    cedilla) without a hand-written table.
    """
    decomposed = unicodedata.normalize("NFD", word)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return unicodedata.normalize("NFC", stripped)


def has_diacritics(word: str) -> bool:
    return strip_diacritics(word) != word


def count_tokens(tokenizer: Tokenizer, lines: Iterable[str]) -> int:
    """Convenience for tests and calibration."""
    return sum(len(tokenizer.tokenize(line)) for line in lines)
