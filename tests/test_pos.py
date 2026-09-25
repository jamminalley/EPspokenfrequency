"""Published POS from tagger votes."""

from __future__ import annotations

from collections import Counter

import pytest

from scripts import config as config_mod
from scripts import pos


@pytest.fixture
def pcfg(release_cfg):
    return release_cfg


def ident(x):
    return x


def test_upos_mapping(pcfg):
    assert [pos.map_upos(u, pcfg) for u in ["NOUN", "AUX", "ADP", "SCONJ", "X"]] == [
        "noun", "verb", "prep", "conj", "unk"]


def test_only_agreeing_sentences_count(pcfg):
    """casa tagged VERB is casar: it must not make the noun casa a verb."""
    tags = {"casa": [("casa", "NOUN", "")] * 4 + [("casar", "VERB", "")]}
    w, raw = pos.aggregate({"casa": 1000}, tags, {}, ident, ident, pcfg)
    assert raw["casa"] == Counter({"noun": 4}) and w["casa"] == Counter({"noun": 1000})


def test_split_surface_carries_lemma_and_pos_together(pcfg):
    joint = {"educados": Counter({("educar", "VERB"): 3, ("educado", "ADJ"): 2})}
    w, _ = pos.aggregate({"educados": 1000}, {}, joint, ident, ident, pcfg)
    assert w["educar"] == Counter({"verb": 600}) and w["educado"] == Counter({"adj": 400})


def test_count_weighting_across_surfaces(pcfg):
    tags = {"bem": [("bem", "ADV", "")] * 5, "bens": [("bem", "NOUN", "")] * 5}
    headword = {"bens": "bem"}.get
    w, _ = pos.aggregate({"bem": 900, "bens": 100}, tags, {},
                         lambda s: headword(s, s), ident, pcfg)
    assert w["bem"] == Counter({"adv": 900, "noun": 100})


class TestAssign:
    def test_single_pos(self, pcfg):
        assert pos.assign("casa", 1000, {"casa": Counter({"noun": 1000})},
                          {"casa": Counter({"noun": 5})}, pcfg, ident) == [("noun", 1000)]

    def test_well_supported_secondary_pos_splits(self, pcfg):
        w = {"bem": Counter({"adv": 600, "noun": 400})}
        raw = {"bem": Counter({"adv": 30, "noun": 20})}
        assert pos.assign("bem", 1000, w, raw, pcfg, ident) == [("adv", 600), ("noun", 400)]

    def test_small_share_joins_the_majority(self, pcfg):
        w = {"bem": Counter({"adv": 900, "noun": 100})}
        raw = {"bem": Counter({"adv": 45, "noun": 5})}
        assert pos.assign("bem", 1000, w, raw, pcfg, ident) == [("adv", 1000)]

    def test_too_few_sentences_joins_the_majority(self, pcfg):
        """One stray tag in a 5-sentence sample is 20-40%: not enough."""
        w = {"x": Counter({"noun": 600, "adj": 400})}
        raw = {"x": Counter({"noun": 3, "adj": 2})}
        assert pos.assign("x", 1000, w, raw, pcfg, ident) == [("noun", 1000)]

    def test_no_evidence_falls_back_to_the_heuristic(self, pcfg):
        assert pos.assign("do", 500, {}, {}, pcfg, lambda l: "det") == [("det", 500)]


class TestConsistency:
    CLOSED = frozenset({"mais", "que"})

    def run(self, tags, cfg, counts=None):
        counts = counts or {k: 1000 for k in tags}
        w, raw = pos.aggregate(counts, tags, {}, ident, ident, cfg, closed=self.CLOSED)
        return raw

    def test_verb_tag_on_a_noun_lemma_is_dropped(self, pcfg):
        """pergunta tagged VERB with lemma pergunta: the verb is perguntar."""
        raw = self.run({"pergunta": [("pergunta", "VERB", "")] * 3
                        + [("pergunta", "NOUN", "")] * 2}, pcfg)
        assert raw["pergunta"] == Counter({"noun": 2})

    def test_other_tag_on_an_inflected_verb_form_is_dropped(self, pcfg):
        """consigo -> conseguir tagged ADV: that is the pronoun, not the verb."""
        raw = self.run({"consigo": [("conseguir", "ADV", "")] * 3
                        + [("conseguir", "VERB", "")] * 2}, pcfg)
        assert raw["consigo"] == Counter({"verb": 2})

    def test_nominalised_infinitive_counts(self, pcfg):
        raw = self.run({"poder": [("poder", "VERB", "")] * 3
                        + [("poder", "NOUN", "")] * 2}, pcfg)
        assert raw["poder"] == Counter({"verb": 3, "noun": 2})

    def test_function_word_cannot_be_a_noun(self, pcfg):
        raw = self.run({"mais": [("mais", "ADV", "")] * 21 + [("mais", "NOUN", "")] * 19
                        + [("mais", "DET", "")] * 7}, pcfg)
        assert raw["mais"] == Counter({"adv": 21, "det": 7})

    def test_ar_noun_is_not_a_verb(self, pcfg):
        """lugar ends in -ar but is tagged NOUN: lugares NOUN still counts."""
        raw = self.run({"lugar": [("lugar", "NOUN", "")] * 5,
                        "lugares": [("lugar", "NOUN", "")] * 5}, pcfg)
        assert raw["lugares"] == Counter({"noun": 5})


def test_tags_backend_drops_self_contradicting_votes():
    from scripts.lemmas import TagsBackend
    tags = {"saia": [("saia", "VERB", "")] * 32 + [("sair", "VERB", "")] * 15
            + [("saia", "NOUN", "")] * 3}
    is_verb = pos.verb_lemmas(tags)
    b = TagsBackend(tags, lambda s, l, u: pos.consistent(s, l, u, is_verb, frozenset()))
    assert b.lemmatize_types(["saia"])["saia"] == "sair"
    assert TagsBackend(tags).lemmatize_types(["saia"])["saia"] == "saia"


@pytest.mark.parametrize("word", ["para", "de", "até", "a"])
def test_prepositions_are_never_conjunctions(pcfg, word):
    assert pos.map_upos("SCONJ", pcfg, word) == "prep"
    assert pos.map_upos("CCONJ", pcfg, word) == "prep"


def test_other_readings_of_listed_words_are_untouched(pcfg):
    """a is also the article; only conjunction tags are remapped."""
    assert pos.map_upos("DET", pcfg, "a") == "det"
    assert pos.map_upos("SCONJ", pcfg, "que") == "conj"


def test_both_readings_of_a_count(pcfg):
    """Stanza lemmatizes the article `a` as *o* and the preposition as *a*."""
    tags = {"a": [("o", "DET", "")] * 6 + [("a", "ADP", "")] * 4}
    w, raw = pos.aggregate({"a": 1000}, tags, {}, ident, ident, pcfg)
    assert raw["a"] == Counter({"det": 6, "prep": 4})


# -- contractions ------------------------------------------------------------


def test_contractions_all_take_one_pos(release_cfg):
    """fixes.contraction_pos: Stanza expands a contraction before tagging, so
    the surface token's own tags are noise. One POS for the paradigm."""
    from collections import Counter

    from scripts import pos as pos_mod

    forms = pos_mod.contraction_forms(release_cfg)
    assert {"do", "da", "nas", "no", "pelo", "deste", "contigo"} <= forms
    # tagger evidence that would otherwise win, and a fallback that answers unk
    weighted = {"nas": Counter({"noun": 900, "adv": 100})}
    for form in ("do", "nas", "pelo", "contigo"):
        parts = pos_mod.assign(form, 1000, weighted, {}, release_cfg,
                               lambda w: "unk", forms)
        assert parts == [(release_cfg["pos"]["contraction_pos"], 1000)]
    # and a contraction is never split across two rows
    assert len(pos_mod.assign("nas", 1000, weighted, {}, release_cfg,
                              lambda w: "unk", forms)) == 1


def test_consigo_is_not_treated_as_a_contraction(release_cfg):
    """It is almost always the verb in speech; config.yaml leaves it out."""
    from scripts import pos as pos_mod

    assert "consigo" not in pos_mod.contraction_forms(release_cfg)


def test_stage_1_leaves_contraction_pos_alone(cfg):
    """The April baseline has to stay reproducible, so the fix is off there."""
    from scripts import pos as pos_mod

    assert cfg["fixes"]["contraction_pos"] is False
    assert pos_mod.contraction_forms(cfg) == frozenset()
