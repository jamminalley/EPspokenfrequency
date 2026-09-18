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
            "fixes.accent_variant_folding": True,
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
        counts = {"nao": 10, "não": 900}
        folded, log = filters.fold_diacritics(counts, cfg, fake_dict)
        assert folded == counts and log == []

    def test_folds_unaccented_form_at_20x(self, stage2):
        folded, log = filters.fold_diacritics(
            {"nao": 10, "não": 900, "dificil": 5, "difícil": 500}, stage2, fake_dict
        )
        assert folded == {"não": 910, "difícil": 505}
        assert ("nao", "não", 10, 900, "unaccented", False) in log

    def test_below_ratio_is_left_alone(self, stage2):
        folded, log = filters.fold_diacritics({"nao": 10, "não": 190}, stage2, fake_dict)
        assert folded == {"nao": 10, "não": 190} and log == []

    def test_unaccented_fold_ignores_the_dictionary(self, stage2):
        """The ratio replaces the dictionary check: `numero` is a real word
        (eu numero) but folds into `número` on frequency."""
        folded, log = filters.fold_diacritics(
            {"numero": 10, "número": 500}, stage2, lambda w: True
        )
        assert folded == {"número": 510}
        assert log[0][5] is True   # logged as a dictionary word, for review

    def test_never_folds_a_common_form_into_a_rare_typo(self, stage2):
        """Regression: exactamente (120,806) must not fold into exactámente (1)."""
        counts = {"exactamente": 120_806, "exactámente": 1}
        folded, log = filters.fold_diacritics(counts, stage2, fake_dict)
        assert folded["exactamente"] == 120_807   # the typo folds the other way

    def test_wrong_accent_variant_folds(self, stage2):
        folded, log = filters.fold_diacritics(
            {"não": 1000, "näo": 5, "idéia": 3, "ideia": 400}, stage2, fake_dict
        )
        assert folded == {"não": 1005, "ideia": 403}

    @pytest.mark.parametrize("accented,plain", [("pôr", "por"), ("quê", "que"), ("dê", "de")])
    def test_accented_real_word_never_folds(self, stage2, accented, plain):
        """pôr, quê and dê are words: the dictionary test keeps them."""
        vocab = {accented, plain}
        folded, _ = filters.fold_diacritics(
            {plain: 100_000, accented: 10}, stage2, vocab.__contains__
        )
        assert folded == {plain: 100_000, accented: 10}

    def test_minimal_pair_within_ratio_survives(self, stage2):
        folded, _ = filters.fold_diacritics({"avô": 30, "avó": 70}, stage2, lambda w: True)
        assert folded == {"avô": 30, "avó": 70}


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
