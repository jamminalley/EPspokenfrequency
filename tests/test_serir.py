"""The ser/ir next-word rule (not yet applied to counts)."""

from __future__ import annotations

import pytest

from scripts.serir import rule_guess


@pytest.mark.parametrize("form,sentence,expected", [
    ("fui", "Eu fui ao Paquistão.", "ir"),
    ("fomos", "Fomos buscar ajuda.", "ir"),
    ("fui", "Levantei-me e fui embora.", "ir"),
    ("foi", "Ele foi-se embora.", "ir"),          # reflexive clitic skipped
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
