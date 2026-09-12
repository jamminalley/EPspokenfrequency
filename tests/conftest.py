"""Shared fixtures.  No test in this suite touches the corpus."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import config as config_mod  # noqa: E402
from scripts.tokenizer import Tokenizer  # noqa: E402


@pytest.fixture(scope="session")
def cfg() -> dict:
    """The real config.yaml.  Tests assert on behaviour it configures, so
    a config change that breaks tokenization shows up here."""
    return config_mod.load(ROOT / "config.yaml")


@pytest.fixture(scope="session")
def tok(cfg) -> Tokenizer:
    return Tokenizer(cfg["tokenizer"])


@pytest.fixture(scope="session")
def tok_split(cfg) -> Tokenizer:
    """Tokenizer with enclitic splitting forced on.

    The stage 1 baseline runs with splitting OFF, because the original
    pipeline did not split despite its README saying so.  The splitter is
    still shipped for stage 2, so it still needs testing.
    """
    return Tokenizer(dict(cfg["tokenizer"], split_enclitics=True))
