"""Plural folding in closure, the English-plural filter, and per-occurrence
resolution of participles and fomos-type forms."""

from __future__ import annotations

from collections import Counter

import pytest

from scripts import lemmas, occurrence
from scripts.filters import is_english_plural
from scripts.quality import singular_of


class TestPluralFolding:
    def test_singular_of_regular_plurals(self):
        inv = {"anjo", "operação", "inglês", "animal", "homem", "rapaz"}
        assert {p: singular_of(p, inv) for p in
                ["anjos", "operações", "ingleses", "animais", "homens", "rapazes"]} == {
            "anjos": "anjo", "operações": "operação", "ingleses": "inglês",
            "animais": "animal", "homens": "homem", "rapazes": "rapaz"}

    def test_no_singular_in_the_list_means_no_fold(self):
        assert singular_of("anjos", {"casa"}) is None

    def _close(self, mapping, tantum=(), closed=(), protected=()):
        def rule(lemma, inventory):
            if lemma in tantum:
                return None
            sg = singular_of(lemma, inventory)
            return None if sg is None or sg in closed else sg
        out, _ = lemmas.close_lemma_map(mapping, None, None, protected=frozenset(protected),
                                        plural_rule=rule)
        return out

    def test_closure_folds_plural_onto_singular(self):
        assert self._close({"anjos": "anjos", "anjo": "anjo"})["anjos"] == "anjo"

    def test_plurale_tantum_is_kept(self):
        out = self._close({"óculos": "óculos", "óculo": "óculo"}, tantum={"óculos"})
        assert out["óculos"] == "óculos"

    def test_closed_class_singular_is_not_a_target(self):
        """bens is not the plural of the adverb bem."""
        out = self._close({"bens": "bens", "bem": "bem"}, closed={"bem"})
        assert out["bens"] == "bens"

    def test_protected_lemma_is_never_redirected(self):
        out = self._close({"educado": "educar", "educar": "educar"}, protected={"educado"})
        assert out["educado"] == "educar"        # the surface still maps as before
        out2, _ = lemmas.close_lemma_map({"x": "educado", "educado": "educar"}, None, None,
                                         protected=frozenset({"educado"}))
        assert out2["x"] == "educado"            # but the lemma is not closed away


class TestEnglishPlurals:
    EN = {"zombie", "zombies", "shirt", "shirts", "casa"}
    PT = {"casas", "anjos"}

    @pytest.mark.parametrize("word,expected", [
        ("zombies", True), ("t-shirts", True), ("casas", False), ("anjos", False), ("mas", False)])
    def test_detection(self, word, expected):
        assert is_english_plural(word, self.PT.__contains__, self.EN.__contains__) is expected


class TestOccurrenceResolution:
    WORDS = {"educar", "educado", "bater", "batida", "ser", "ir"}

    def _resolve(self, tagged, cfg):
        return occurrence.resolve(tagged, {}, cfg, self.WORDS.__contains__, lambda w: w)

    def test_participle_split_by_pos(self, cfg):
        tagged = {"educados": [("educar", "VERB", "VerbForm=Part")] * 3
                  + [("educado", "ADJ", "")] * 2}
        assert self._resolve(tagged, cfg)["educados"] == Counter({"educar": 3, "educado": 2})

    def test_participle_noun_keeps_its_gender(self, cfg):
        tagged = {"batidas": [("bater", "VERB", "")] * 2 + [("batida", "NOUN", "")] * 3}
        assert self._resolve(tagged, cfg)["batidas"] == Counter({"bater": 2, "batida": 3})

    def test_fomos_split_between_ser_and_ir(self, cfg):
        tagged = {"fomos": [("ser", "AUX", "")] * 2 + [("ir", "VERB", "")] * 3}
        assert self._resolve(tagged, cfg)["fomos"] == Counter({"ser": 2, "ir": 3})

    def test_apportion_is_exact(self):
        parts = occurrence.apportion(1001, {"a": 1, "b": 1, "c": 1})
        assert sum(parts.values()) == 1001 and parts == {"a": 334, "b": 334, "c": 333}
