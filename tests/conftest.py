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
def release_cfg() -> dict:
    """The real config.yaml: the release (stage 2) build."""
    return config_mod.load(ROOT / "config.yaml")


@pytest.fixture(scope="session")
def cfg(release_cfg) -> dict:
    """The stage 1 view of config.yaml, derived exactly as `--stage 1`
    derives it. Most unit tests start here and switch on the fix under
    test, so each fix is tested in isolation."""
    from scripts.build import stage1_overrides

    overrides = dict(stage1_overrides(release_cfg), **{"run.stage": 1})
    return config_mod.with_overrides(release_cfg, overrides)


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
