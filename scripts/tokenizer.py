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

_APOSTROPHES = {"’": "'", "ʼ": "'"}


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
        line = self.clean(line)
        out: list[str] = []
        for match in _WORD_RE.finditer(line):
            word = match.group(0)
            if "-" in word and self.split_enclitics:
                parts = self.split_enclitic(word)
            else:
                parts = [word]
            for part in parts:
                part = part.strip("'-")
                if len(part) < self.min_token_len:
                    continue
                if not self.keep_digits and any(ch.isdigit() for ch in part):
                    continue
                out.append(part)
        return out

    # -- enclitic handling ------------------------------------------------

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
        return [stem, *tail] if stem else tail


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
