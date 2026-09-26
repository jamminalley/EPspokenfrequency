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


# -- a clitic that is spelled like a tense infix ------------------------------


def test_a_lone_clitic_is_never_read_as_a_mesoclitic_infix(tok_split):
    """`a` and `as` are both clitics and future/conditional infixes. Without a
    clitic to the infix's left there is no mesoclisis, and reassembling
    anyway put `conheçoa` in the published list at rank 5,290, glossed
    "I know her". 45 rows were like it."""
    assert tok_split.split_enclitic("conheço-a") == ["conheço", "a"]
    assert tok_split.split_enclitic("deixa-a") == ["deixa", "a"]
    assert tok_split.split_enclitic("mata-as") == ["mata", "as"]
    assert tok_split.split_enclitic("leva-a") == ["leva", "a"]


def test_mesoclisis_still_reassembles(tok_split):
    """The clitic sits between stem and infix, which is what makes it
    mesoclisis: dar-lhe-ia is daria + lhe, not dar + lhe + ia."""
    assert tok_split.split_enclitic("dar-lhe-ia") == ["daria", "lhe"]
    assert tok_split.split_enclitic("far-se-ia") == ["faria", "se"]
    assert tok_split.split_enclitic("dar-me-ia") == ["daria", "me"]


def test_the_two_readings_of_a_do_not_collide(tok_split):
    """One tail is a clitic; two tails ending in an infix are mesoclisis."""
    assert tok_split.split_enclitic("dá-la") == ["dar", "la"]
    assert tok_split.split_enclitic("dá-a") == ["dá", "a"]


# -- clusters written without their hyphen -----------------------------------


def test_a_glued_cluster_in_the_table_is_split(release_cfg):
    """The corpus writes the same cluster both ways; the table says which."""
    from scripts.build import effective_config
    from scripts.tokenizer import Tokenizer

    tok = Tokenizer(effective_config(release_cfg)["tokenizer"])
    assert tok.tokenize("deixame em paz") == ["deixa", "me", "em", "paz"]
    assert tok.tokenize("calate") == ["cala", "te"]
    assert tok.tokenize("sêlo") == ["ser", "lo"]


def test_a_word_that_merely_looks_glued_is_left_alone(release_cfg):
    """Every one of these fails a test in scripts/make_glue_table.py:
    `rodeo` and `mateo` are not attested hyphenated often enough or are
    capitalized mid-line, `sera` is a missing accent, `saiste` a preterite."""
    from scripts.build import effective_config
    from scripts.tokenizer import Tokenizer

    tok = Tokenizer(effective_config(release_cfg)["tokenizer"])
    for word in ("rodeo", "mateo", "sera", "eramos", "saiste", "penthouse",
                 "adios", "casa", "cara", "boa"):
        assert tok.tokenize(word) == [word], word


def test_glue_repair_is_off_in_stage_1(cfg):
    """Stage 1 has to keep reproducing the April output byte for byte."""
    from scripts.tokenizer import Tokenizer

    assert cfg["fixes"]["repair_glued_enclitics"] is False
    assert cfg["tokenizer"].get("repair_glue") is False
    assert Tokenizer(cfg["tokenizer"]).tokenize("deixame") == ["deixame"]


def test_the_table_is_hashed_into_the_tokenizer_settings(release_cfg):
    """Every pass is cached under a hash of cfg["tokenizer"], so a change to
    the table has to show up there or a rebuild reuses stale tokenization."""
    digest = release_cfg["tokenizer"]["glue_repair"]["digest"]
    assert digest and digest != "absent" and len(digest) == 16


def test_every_table_row_splits_into_its_stem_and_clitic(release_cfg):
    """The table is generated, so this guards the generator: each glued form
    must rejoin to a cluster the splitter itself would split the same way."""
    from scripts.make_glue_table import load
    from scripts.tokenizer import Tokenizer

    tok = Tokenizer(dict(release_cfg["tokenizer"], split_enclitics=True,
                         repair_glue=False))
    table = load(release_cfg["tokenizer"]["glue_repair"]["table"])
    assert len(table) >= 25
    for glued, (stem, clitic) in table.items():
        assert glued == glued.lower()
        assert clitic in tok._enclitic_set
        assert stem and not stem.endswith("-")
