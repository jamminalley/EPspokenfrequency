"""Band labels, Anki tag strings, and entry ranking."""

from __future__ import annotations

import pytest

from scripts.emit import Entry, band_label, build_tags, rank_entries


class TestBandLabel:
    @pytest.mark.parametrize(
        "rank,size,expected",
        [
            (1, 500, "0001-0500"), (500, 500, "0001-0500"),
            (501, 500, "0501-1000"), (1000, 500, "0501-1000"),
            (5001, 500, "5001-5500"), (10000, 500, "9501-10000"),
            (1, 1000, "0001-1000"), (1000, 1000, "0001-1000"),
            (1001, 1000, "1001-2000"), (5001, 1000, "5001-6000"),
        ],
    )
    def test_labels(self, rank, size, expected):
        assert band_label(rank, size) == expected

    def test_boundary_is_inclusive(self):
        """Rank 500 belongs to the first band, 501 to the second."""
        assert band_label(500, 500) != band_label(501, 500)


class TestTags:
    def test_matches_original_rank_1(self, cfg):
        """Byte-identical to out/ep_spoken_anki_minimal.tsv, or an existing
        Anki import breaks."""
        assert build_tags(1, "det", cfg) == (
            "freq::0001-0500 freq500::0001-0500 freq1000::0001-1000 pos::det "
            "source::opensubtitles_ep_v2018 variety::EP register::spoken"
        )

    def test_matches_original_rank_5001(self, cfg):
        assert build_tags(5001, "adj", cfg) == (
            "freq::5001-5500 freq500::5001-5500 freq1000::5001-6000 pos::adj "
            "source::opensubtitles_ep_v2018 variety::EP register::spoken"
        )

    def test_tag_order_is_fixed(self, cfg):
        parts = build_tags(1, "verb", cfg).split()
        assert [p.split("::")[0] for p in parts] == [
            "freq", "freq500", "freq1000", "pos", "source", "variety", "register",
        ]

    def test_pos_is_carried_through(self, cfg):
        assert "pos::mwe" in build_tags(62, "mwe", cfg)


class _Tagger:
    def tag(self, lemma, is_mwe=False):
        return "mwe" if is_mwe else "noun"


class TestRanking:
    def test_orders_by_count_then_alphabetically(self):
        entries = rank_entries(
            {"casa": 100, "bola": 100, "arvore": 300}, [], 1_000_000, _Tagger(), 10
        )
        assert [e.lemma for e in entries] == ["arvore", "bola", "casa"]

    def test_ties_are_deterministic(self):
        """Equal counts must not depend on dict insertion order."""
        a = rank_entries({"b": 5, "a": 5}, [], 1_000, _Tagger(), 10)
        b = rank_entries({"a": 5, "b": 5}, [], 1_000, _Tagger(), 10)
        assert [e.lemma for e in a] == [e.lemma for e in b] == ["a", "b"]

    def test_per_million_matches_the_original_formula(self):
        """round(raw / total * 1e6, 3) reproduces all 10,000 original rows."""
        e = rank_entries({"o": 58_080_476}, [], 623_920_347, _Tagger(), 1)[0]
        assert e.freq_per_million == 93089.569

    def test_mwes_are_interleaved_by_count(self):
        entries = rank_entries(
            {"casa": 100}, [{"mwe": "não é", "raw_freq": 500}], 1_000_000, _Tagger(), 10
        )
        assert [(e.lemma, e.is_mwe) for e in entries] == [("não é", True), ("casa", False)]

    def test_limit_is_respected(self):
        assert len(rank_entries({f"w{i}": i for i in range(50)}, [], 1_000, _Tagger(), 10)) == 10
