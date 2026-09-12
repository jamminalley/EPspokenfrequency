"""BP exclusions, the proper-noun filter, and diacritic folding."""

from __future__ import annotations

import pytest

from scripts import config as config_mod
from scripts import filters


@pytest.fixture
def stage2(cfg):
    return config_mod.with_overrides(
        cfg,
        {
            "run.stage": 2,
            "quality.fail_on_suspects": True,
            "fixes.diacritic_folding": True,
            "fixes.bp_after_folding": True,
            "fixes.extended_proper_nouns": True,
        },
    )


# A small stand-in dictionary: the real one is 417k words and the rules,
# not the word list, are what these tests are about.
REAL_WORDS = {"e", "é", "da", "dá", "esta", "está", "so", "só", "casa", "não",
              "difícil", "para", "cara", "jack"}


def fake_dict(word: str) -> bool:
    return word.lower() in REAL_WORDS


class TestBpExclusions:
    def test_stage1_keeps_cara(self, cfg):
        """The original excluded `cara` in error; stage 1 reproduces that."""
        assert "cara" in filters.bp_exclusion_set(cfg)

    def test_stage2_restores_cara(self, stage2):
        assert "cara" not in filters.bp_exclusion_set(stage2)

    def test_stage2_also_excludes_unaccented_variants(self, stage2):
        """`voce` slipped past the original filter, which listed only `você`."""
        s = filters.bp_exclusion_set(stage2)
        assert "você" in s and "voce" in s
        assert "vocês" in s and "voces" in s

    def test_stage1_misses_unaccented_variants(self, cfg):
        s = filters.bp_exclusion_set(cfg)
        assert "você" in s and "voce" not in s


class TestDiacriticFolding:
    def test_disabled_in_stage1(self, cfg):
        counts = {"nao": 10, "não": 90}
        folded, log = filters.fold_diacritics(counts, cfg, fake_dict)
        assert folded == counts and log == []

    def test_folds_non_word_into_accented_twin(self, stage2):
        folded, log = filters.fold_diacritics(
            {"nao": 10, "não": 90, "dificil": 5, "difícil": 50}, stage2, fake_dict
        )
        assert folded == {"não": 100, "difícil": 55}
        assert ("nao", "não", 10) in log

    @pytest.mark.parametrize("bare,accented", [("e", "é"), ("da", "dá"), ("esta", "está"), ("so", "só")])
    def test_real_minimal_pairs_are_never_merged(self, stage2, bare, accented):
        """The dictionary check exists precisely for these: e/é, da/dá,
        esta/está and so/só are distinct words, not typing variants."""
        folded, log = filters.fold_diacritics({bare: 40, accented: 60}, stage2, fake_dict)
        assert folded == {bare: 40, accented: 60}
        assert log == []

    def test_no_fold_without_an_accented_variant_in_the_corpus(self, stage2):
        folded, _ = filters.fold_diacritics({"xpto": 7}, stage2, fake_dict)
        assert folded == {"xpto": 7}

    def test_most_frequent_accented_variant_wins(self, stage2):
        folded, _ = filters.fold_diacritics(
            {"avo": 5, "avô": 30, "avó": 70}, stage2, fake_dict
        )
        assert folded["avó"] == 75 and folded["avô"] == 30


class TestProperNouns:
    def test_high_capitalization_oov_word_is_dropped(self, cfg):
        drop, reason = filters.is_proper_noun("kelty", 500, 0.98, cfg, fake_dict)
        assert drop and "cap_ratio" in reason

    def test_ordinary_noun_is_kept(self, cfg):
        drop, _ = filters.is_proper_noun("casa", 5000, 0.03, cfg, fake_dict)
        assert not drop

    def test_stage1_keeps_a_name_the_dictionary_knows(self, cfg):
        """Stage 1 requires OOV, so `jack` survives -- as it did originally."""
        drop, _ = filters.is_proper_noun("jack", 1000, 1.0, cfg, fake_dict)
        assert not drop

    def test_stage2_catches_it(self, stage2):
        """Fix (c): capitalization alone is enough, so `cristina` goes."""
        drop, _ = filters.is_proper_noun("jack", 1000, 1.0, stage2, fake_dict)
        assert drop

    def test_apply_logs_everything_it_drops(self, cfg):
        kept, log = filters.apply(
            {"casa": 900, "kelty": 500, "cara": 700}, {"kelty": 0.99}, cfg, fake_dict
        )
        assert set(kept) == {"casa"}
        assert [w for w, *_ in log.proper_nouns] == ["kelty"]
        assert [w for w, _ in log.bp_excluded] == ["cara"]
