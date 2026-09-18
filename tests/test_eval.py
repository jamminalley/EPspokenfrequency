"""Gold-set loading and scoring rules."""

from __future__ import annotations

import pytest

from scripts import config as config_mod
from scripts import eval_lemmas

HEADER = "rank_40m\tsurface\tcount_40m\tclaude_lemma\tcategory\tnote\tjim_lemma\tjim_verdict\n"


@pytest.fixture
def gold_cfg(cfg, tmp_path):
    def write(rows: list[str]):
        (tmp_path / "lemma_gold.tsv").write_text(HEADER + "".join(rows), encoding="utf-8")
        return config_mod.with_overrides(cfg, {"paths.eval_dir": str(tmp_path)})
    return write


def test_jim_lemma_overrides_claude_lemma(gold_cfg):
    cfg = gold_cfg(["5\tsei\t9\tsaber\tok\t\t\tok\n",
                    "6\testa\t9\teste\tok\t\teste|estar\tfix\n"])
    rows, meta = eval_lemmas.load_gold(cfg)
    assert {r.surface: r.gold for r in rows} == {"sei": ("saber",), "esta": ("este", "estar")}
    assert meta["fully_reviewed"]


def test_drop_rows_are_excluded(gold_cfg):
    cfg = gold_cfg(["5\tsei\t9\tsaber\tok\t\t\tok\n",
                    "7\tkelty\t9\tkelty\tproper\t\t\tdrop\n"])
    rows, meta = eval_lemmas.load_gold(cfg)
    assert [r.surface for r in rows] == ["sei"]
    assert meta["n_dropped"] == 1


def test_either_alternative_is_accepted(gold_cfg):
    cfg = gold_cfg(["9\tfomos\t9\tir\tambiguous\t\tir|ser\tfix\n"])
    rows, _ = eval_lemmas.load_gold(cfg)
    assert eval_lemmas.score(rows, {"fomos": "ser"})["accuracy"] == 1.0
    assert eval_lemmas.score(rows, {"fomos": "ir"})["accuracy"] == 1.0
    assert eval_lemmas.score(rows, {"fomos": "fomo"})["accuracy"] == 0.0


def test_unreviewed_rows_mark_the_set_provisional(gold_cfg):
    cfg = gold_cfg(["5\tsei\t9\tsaber\tok\t\t\t\n"])
    _, meta = eval_lemmas.load_gold(cfg)
    assert not meta["fully_reviewed"]


def test_parse_alternatives():
    assert eval_lemmas.parse_alternatives("ir|ser") == ("ir", "ser")
    assert eval_lemmas.parse_alternatives("casa") == ("casa",)
