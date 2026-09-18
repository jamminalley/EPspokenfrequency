"""The five lemmatization conventions of eval/conventions.md."""

from __future__ import annotations

import pytest

from scripts import config as config_mod
from scripts import conventions

WORDS = {"coisa", "pato", "café", "ter", "exatamente", "ação", "ações", "ótimo", "receção",
         "facto", "contacto", "menino", "miúdo", "música", "músico", "ferida",
         "ferido", "grande", "maior", "bom", "melhor", "ao", "desta"}
LEMMAS = {"ações": "ação"}


def in_dict(w: str) -> bool:
    return w in WORDS


def relemma(w: str) -> str:
    return LEMMAS.get(w, w)


@pytest.fixture
def ccfg(cfg, tmp_path):
    pairs = tmp_path / "gender_pairs.tsv"
    pairs.write_text(
        "feminine\tmasculine\tfem_count\tmasc_count\tclaude_decision\treason\tjim_decision\n"
        "menina\tmenino\t9\t9\tfold\tperson\t\n"
        "música\tmúsico\t9\t9\tkeep\tmusic\t\n"
        "miúda\tmiúdo\t9\t9\tkeep\tfirst pass\tfold\n",
        encoding="utf-8",
    )
    return config_mod.with_overrides(cfg, {"conventions.gender.pairs_file": str(pairs)})


def run(ccfg, mapping):
    out, _ = conventions.apply(mapping, ccfg, in_dict, relemma)
    return out


def test_contractions_are_their_own_entries(ccfg):
    assert run(ccfg, {"aos": "ao", "desta": "de"}) == {"aos": "aos", "desta": "desta"}


class TestGender:
    def test_listed_pair_folds(self, ccfg):
        assert run(ccfg, {"menina": "menina", "meninas": "menina"}) == {
            "menina": "menino", "meninas": "menino"}

    def test_jim_decision_overrides_first_pass(self, ccfg):
        assert run(ccfg, {"miúda": "miúda"}) == {"miúda": "miúdo"}

    def test_keep_pair_reverts_a_backend_fold(self, ccfg):
        """música is music, not the feminine of músico."""
        assert run(ccfg, {"músicas": "músico"}) == {"músicas": "música"}

    def test_configured_exception_is_protected(self, ccfg):
        assert run(ccfg, {"ferida": "ferido"}) == {"ferida": "ferida"}

    def test_configured_exception_beats_a_verb_reading(self, ccfg):
        """stanza reads ferida as the participle of ferir; the convention
        names ferida (a wound) as its own headword."""
        assert run(ccfg, {"ferida": "ferir", "feridas": "ferir"}) == {
            "ferida": "ferida", "feridas": "ferida"}

    def test_unlisted_feminine_is_untouched(self, ccfg):
        """No automatic folding: casa must never become caso."""
        assert run(ccfg, {"casa": "casa"}) == {"casa": "casa"}


class TestDiminutives:
    @pytest.mark.parametrize("surface,backend,expected", [
        ("coisinha", "coisa", "coisinha"),
        ("patinhos", "pato", "patinho"),
        ("cafezinho", "café", "cafezinho"),
    ])
    def test_stripped_diminutive_is_restored(self, ccfg, surface, backend, expected):
        assert run(ccfg, {surface: backend}) == {surface: expected}

    def test_verb_form_ending_in_inha_is_not_a_diminutive(self, ccfg):
        assert run(ccfg, {"tinha": "ter"}) == {"tinha": "ter"}


def test_comparatives_are_their_own_lemmas(ccfg):
    assert run(ccfg, {"maiores": "grande", "melhor": "bom"}) == {
        "maiores": "maior", "melhor": "melhor"}


class TestSpellingReform:
    @pytest.mark.parametrize("old,new", [
        ("exactamente", "exatamente"), ("óptimo", "ótimo"), ("recepção", "receção")])
    def test_pre_1990_spelling_merges(self, ccfg, old, new):
        assert run(ccfg, {old: old}) == {old: new}

    def test_reformed_plural_reaches_its_singular(self, ccfg):
        assert run(ccfg, {"acções": "acções"}) == {"acções": "ação"}

    @pytest.mark.parametrize("word", ["facto", "contacto"])
    def test_consonant_kept_in_european_spelling_is_untouched(self, ccfg, word):
        """facto and contacto keep their consonant post-1990 in Portugal and
        are in the dictionary, so they must not become fato / contato."""
        assert run(ccfg, {word: word}) == {word: word}


def test_protected_forms_cover_contractions_and_comparatives(ccfg):
    keep = conventions.protected_forms(ccfg)
    assert {"aos", "nas", "maiores"} <= keep
