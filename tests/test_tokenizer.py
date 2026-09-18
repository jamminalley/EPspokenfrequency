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
            ("vê-lo", ["ver", "lo"]),
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
        [("dar-lhe-ia", ["daria", "lhe"]), ("far-se-ia", ["faria", "se"]),
         ("fá-lo-ia", ["faria", "lo"]), ("dir-lhe-ei", ["direi", "lhe"])],
    )
    def test_mesoclisis(self, tok_split, word, expected):
        """The verb is rejoined around the clitic, so the tense infix never
        becomes a token of its own (`ia` would count as a form of `ir`)."""
        assert tok_split.split_enclitic(word) == expected

    @pytest.mark.parametrize(
        "word,expected",
        [
            ("fazê-lo", ["fazer", "lo"]),        # infinitive -r restored
            ("apanhá-lo", ["apanhar", "lo"]),
            ("pô-lo", ["pôr", "lo"]),            # not the preposition `por`
            ("apanhámo-lo", ["apanhámos", "lo"]),  # 1pl -s restored
            ("di-lo", ["diz", "lo"]),            # -z restored
            ("qui-lo", ["quis", "lo"]),          # -s restored
            ("vamo-nos", ["vamos", "nos"]),      # 1pl -s before nos
            ("dão-no", ["dão", "no"]),           # nasal allomorph: no change
        ],
    )
    def test_clitic_stem_restoration(self, tok_split, word, expected):
        """eval/conventions.md: stems like `apanhámo` are tokenizer
        artifacts. The verb is restored before it is counted."""
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


class TestSentenceStarts:
    @pytest.fixture
    def cased(self, cfg):
        return Tokenizer(dict(cfg["tokenizer"], lowercase=False))

    def starts(self, tok, line):
        return [w for w, b in tok.tokenize_with_starts(line) if b]

    def test_line_start(self, cased):
        assert self.starts(cased, "O João foi.") == ["O"]

    @pytest.mark.parametrize("line,expected", [
        ("Sim. Iá, está bem.", ["Sim", "Iá"]),
        ("Olá! Como estás? Bem… Obrigado.", ["Olá", "Como", "Bem", "Obrigado"]),
        ("Vem cá - Não quero.", ["Vem", "Não"]),
        ("Vem cá—Não.", ["Vem", "Não"]),
    ])
    def test_after_final_punctuation_or_dialogue_dash(self, cased, line, expected):
        assert self.starts(cased, line) == expected

    def test_name_mid_sentence_is_not_a_start(self, cased):
        """The evidence the filter needs: Maria capitalized mid-sentence."""
        assert "Maria" not in self.starts(cased, "Eu e a Maria fomos.")

    def test_word_internal_hyphen_is_not_a_dash(self, cased):
        assert self.starts(cased, "Um guarda-chuva Azul.") == ["Um"]

    def test_tokens_match_tokenize(self, tok):
        line = "Sim. Dá-me isso - agora!"
        assert [w for w, _ in tok.tokenize_with_starts(line)] == tok.tokenize(line)
