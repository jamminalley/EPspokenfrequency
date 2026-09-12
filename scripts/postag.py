"""The `pos_guess` heuristic.

README: "rule-based POS heuristic (closed-class lookup + suffix rules).
Values: det, prep, conj, pron, adv, intj, num, noun, adj, verb, mwe, unk.
Verify downstream."

The rule tables live in scripts/data/postag_rules.yaml, fitted from the
original out/ by scripts/fit_postag.py.  Order matters and mirrors what the
original's outputs imply: MWE, then the closed-class lookup, then -mente,
then infinitive endings, then open-class suffixes, then unk.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_RULES_PATH = Path(__file__).parent / "data" / "postag_rules.yaml"


class PosTagger:
    def __init__(self, rules: dict[str, Any]) -> None:
        self.closed: dict[str, str] = rules["closed_class"]
        self.verb_endings: tuple[str, ...] = tuple(rules["verb_endings"])
        self.verb_min_length: int = rules.get("verb_min_length", 4)
        self.adverb_suffix: str = rules["adverb_suffix"]
        # Longest suffix first so the most specific rule wins.
        self.open_suffixes: list[tuple[str, str]] = sorted(
            rules["open_suffixes"].items(), key=lambda kv: (-len(kv[0]), kv[0])
        )
        self.fallback: str = rules["fallback"]

    @classmethod
    def load(cls, path: str | Path | None = None) -> "PosTagger":
        path = Path(path) if path else DEFAULT_RULES_PATH
        if not path.is_file():
            raise FileNotFoundError(
                f"{path} not found -- run `python -m scripts.fit_postag` first"
            )
        with path.open(encoding="utf-8") as fh:
            return cls(yaml.safe_load(fh))

    def tag(self, lemma: str, is_mwe: bool = False) -> str:
        if is_mwe:
            return "mwe"
        hit = self.closed.get(lemma)
        if hit:
            return hit
        if lemma.endswith(self.adverb_suffix):
            return "adv"
        if len(lemma) >= self.verb_min_length and lemma.endswith(self.verb_endings):
            return "verb"
        for suffix, tag in self.open_suffixes:
            if len(lemma) > len(suffix) and lemma.endswith(suffix):
                return tag
        return self.fallback
