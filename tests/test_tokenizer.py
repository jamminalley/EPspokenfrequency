"""Tokenizer, artifact stripping, and enclitic splitting."""

from __future__ import annotations

import pytest

from scripts.tokenizer import Tokenizer, has_diacritics, strip_diacritics


class TestBasicTokenization:
    def test_plain_sentence(self, tok):
        assert tok.tokenize("Só me está a fazer perder tempo.") == [
            "só", "me", "está", "a", "fazer", "perder", "tempo",
        ]

    def test_lowercases(self, tok):
        assert tok.tokenize("NÃO SEI") == ["não", "sei"]

    def test_punctuation_is_not_a_token(self, tok):
        assert tok.tokenize("Olá! Tudo bem? Sim...") == ["olá", "tudo", "bem", "sim"]

    def test_digits_dropped_by_default(self, tok):
        # keep_digits: false -- bare numbers and alphanumerics are dropped.
        assert tok.tokenize("Tenho 87 anos") == ["tenho", "anos"]

    def test_empty_and_whitespace(self, tok):
        assert tok.tokenize("") == []
        assert tok.tokenize("   \n") == []

    def test_accents_preserved(self, tok):
        assert tok.tokenize("coração à ação") == ["coração", "à", "ação"]


class TestArtifactStripping:
    def test_html_italics(self, tok):
        assert tok.tokenize("<i>Olá isso</i>") == ["olá", "isso"]

    def test_leading_dialogue_dash(self, tok):
        assert tok.tokenize("- Não, minha senhora.") == ["não", "minha", "senhora"]

    def test_bracketed_sound_cues(self, tok):
        assert tok.tokenize("[SOM] música") == ["música"]

    def test_parenthetical_stage_direction(self, tok):
        assert tok.tokenize("(sussurrando) vem cá") == ["vem", "cá"]

    def test_music_notes(self, tok):
        assert tok.tokenize("♪ canção ♪") == ["canção"]

    def test_ass_override_tags(self, tok):
        assert tok.tokenize("{\\an8}olá") == ["olá"]


class TestEncliticSplitting:
    """Splitting is off in the stage 1 baseline; these exercise the splitter
    itself, which stage 2 can enable."""

    @pytest.mark.parametrize(
        "word,expected",
        [
            ("dá-me", ["dá", "me"]),
            ("diz-lhe", ["diz", "lhe"]),
            ("vê-lo", ["vê", "lo"]),
            ("diz-me-o", ["diz", "me", "o"]),
            ("deram-lhes", ["deram", "lhes"]),
        ],
    )
    def test_true_enclitics_split(self, tok_split, word, expected):
        assert tok_split.split_enclitic(word) == expected

    @pytest.mark.parametrize(
        "word",
        ["guarda-chuva", "arco-íris", "bem-te-vi", "porta-a-porta", "não-sei-quê"],
    )
    def test_compounds_left_whole(self, tok_split, word):
        """A hyphenated compound whose tail is not a clitic must survive
        intact -- splitting these would invent spurious types."""
        assert tok_split.split_enclitic(word) == [word]

    @pytest.mark.parametrize(
        "word,expected",
        [("dar-lhe-ia", ["dar", "lhe", "ia"]), ("far-se-ia", ["far", "se", "ia"])],
    )
    def test_mesoclisis(self, tok_split, word, expected):
        """The tense infix sits right of the clitic; both come off."""
        assert tok_split.split_enclitic(word) == expected

    def test_longest_clitic_wins(self, tok_split):
        """`lhes` must not be read as `lhe` + stray `s`."""
        assert tok_split.split_enclitic("deu-lhes") == ["deu", "lhes"]

    def test_no_hyphen_is_identity(self, tok_split):
        assert tok_split.split_enclitic("casa") == ["casa"]

    def test_enabling_splitting_splits_in_tokenize(self, tok_split):
        assert tok_split.tokenize("dá-me isso") == ["dá", "me", "isso"]

    def test_baseline_config_keeps_clusters_whole(self, tok):
        """Stage 1 fidelity guard: the shipped config must not split, or the
        token total stops matching the original build."""
        assert tok.tokenize("dá-me isso") == ["dá-me", "isso"]


class TestDiacritics:
    @pytest.mark.parametrize(
        "word,folded",
        [
            ("não", "nao"), ("difícil", "dificil"), ("coração", "coracao"),
            ("só", "so"), ("já", "ja"), ("ação", "acao"), ("pôr", "por"),
            ("à", "a"), ("está", "esta"), ("dá", "da"),
        ],
    )
    def test_strip(self, word, folded):
        assert strip_diacritics(word) == folded

    def test_plain_word_unchanged(self):
        assert strip_diacritics("casa") == "casa"

    def test_idempotent(self):
        once = strip_diacritics("coração")
        assert strip_diacritics(once) == once

    def test_has_diacritics(self):
        assert has_diacritics("não") is True
        assert has_diacritics("nao") is False

    def test_cedilla_is_folded(self):
        """Fold c-cedilla too: `acao` and `ação` are the same word typed
        with and without diacritics."""
        assert strip_diacritics("ç") == "c"
