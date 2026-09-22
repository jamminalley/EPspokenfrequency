"""The ser/ir next-word rule (not yet applied to counts)."""

from __future__ import annotations

import pytest

from scripts.serir import rule_guess


@pytest.mark.parametrize("form,sentence,expected", [
    ("fui", "Eu fui ao Paquistão.", "ir"),
    ("fomos", "Fomos buscar ajuda.", "ir"),
    ("fui", "Levantei-me e fui embora.", "ir"),
    ("foi", "Ele foi-se embora.", "ir"),          # attached reflexive
    ("foram", "Eles foram-se.", "ir"),
    ("fomos", "Fomos-nos embora cedo.", "ir"),
    ("fui", "Já lá fui.", "ir"),                  # locative before
    ("foi", "Qual foi a tua defesa?", "ser"),      # article, not destination
    ("fui", "Fui à minha casa buscar isso.", "ir"),  # destination noun
    ("foram", "Foram lá ontem.", "ir"),
    ("foi", "Foi feito ontem.", "ser"),            # participle
    ("foi", "Não foi.", "ser"),                    # nothing follows
    ("foi", "Foi o melhor dia.", "ser"),           # noun phrase
    ("foi", "Foi ele, juro.", "ser"),              # pronoun
    ("fui", "Fui logo depois.", "?"),              # adverb: abstain
    ("foi", "Foi com ele.", "?"),                  # unlisted preposition: abstain
])
def test_rule(release_cfg, form, sentence, expected):
    assert rule_guess(form, sentence, release_cfg)[0] == expected


def test_whole_word_only(release_cfg):
    """`foi` inside another word is not a match."""
    assert rule_guess("fora", "Afora isso, nada.", release_cfg)[0] == "?"


def test_only_verb_tags_reach_the_rule(release_cfg):
    from scripts.serir import decide
    assert decide("fora", "Está lá fora.", "ADV", release_cfg) == "other"
    assert decide("fui", "Fui ao médico.", "VERB", release_cfg) == "ir"


def test_abstentions_use_the_forms_own_ratio(release_cfg):
    from scripts.serir import joint_from_tagged
    tagged = ([("Fui ao médico.", "ser", "VERB")] * 3        # ir
              + [("Fui eu.", "ser", "AUX")] * 1               # ser
              + [("Fui logo.", "ser", "VERB")] * 4)           # ? -> 3:1
    j = joint_from_tagged("fui", tagged, release_cfg)
    ir = sum(v for (l, _), v in j.items() if l == "ir")
    ser = sum(v for (l, _), v in j.items() if l == "ser")
    assert (ir, ser) == (6.0, 2.0)        # 3 + 4*3/4, 1 + 4*1/4


def test_nonverb_tag_on_an_always_verb_form_follows_the_ratio(release_cfg):
    """Stanza tags cleft 'Foi por isso que' as SCONJ; foi is always a verb."""
    from scripts.serir import joint_from_tagged
    tagged = ([("Foi ao médico.", "ser", "VERB")] * 1
              + [("Foi eu.", "ser", "AUX")] * 3
              + [("Foi por isso que saí.", "foi", "SCONJ")] * 4)
    j = joint_from_tagged("foi", tagged, release_cfg)
    assert ("foi", "SCONJ") not in j
    assert sum(v for (l, _), v in j.items() if l == "ser") == 6.0   # 3 + 4*3/4


def test_adverbial_fora_keeps_its_reading(release_cfg):
    from scripts.serir import joint_from_tagged
    j = joint_from_tagged("fora", [("Está lá fora.", "fora", "ADV")] * 2
                          + [("Se eu fora rico.", "ser", "AUX")], release_cfg)
    assert j[("fora", "ADV")] == 2 and j[("ser", "AUX")] == 1
