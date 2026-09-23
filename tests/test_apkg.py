"""The Anki package: stable ids, stable GUIDs, reverse cards only with glosses."""

from __future__ import annotations

import sqlite3
import zipfile

import genanki

from scripts import build_apkg


def test_ids_are_never_regenerated(release_cfg):
    """Anki identifies the note type and decks by these numbers. Changing
    them makes a re-import create a second note type and second decks."""
    a = release_cfg["output"]["anki"]["apkg"]
    assert a["model_id"] == 1179315797
    assert [d["id"] for d in a["decks"]] == [
        2068073358, 1644245857, 1345053726, 1181939655, 1443946357, 1360713097,
        2105631544, 1709690318, 1546293187, 2089242372, 1374366428, 1142449800,
        1774535697, 1783859346, 1580005185, 2079134348, 1421632181, 1814710621,
        1954409756, 1890686391]


def test_decks_tile_the_whole_range(release_cfg):
    """Twenty decks of 500, contiguous and in order, named to sort."""
    decks = release_cfg["output"]["anki"]["apkg"]["decks"]
    assert len(decks) == 20
    assert [(d["lo"], d["hi"]) for d in decks] == [(i * 500 + 1, i * 500 + 500)
                                                   for i in range(20)]
    assert [d["name"].split("::")[-1] for d in decks][:2] == ["01 · 1–500", "02 · 501–1000"]
    assert decks[-1]["name"].endswith("20 · 9501–10000")
    assert len({d["id"] for d in decks}) == 20


def test_guid_depends_on_lemma_and_pos_only():
    """Pinned: a re-import updates notes only if GUIDs never change."""
    assert build_apkg.note_guid("o", "det") == "HjlLt~;vi{"
    assert build_apkg.note_guid("a", "det") != build_apkg.note_guid("a", "prep")


def test_reverse_card_only_with_a_gloss(release_cfg):
    m = build_apkg.model(release_cfg)
    bare = genanki.Note(model=m, fields=["1", "o", "det", "", "", "", "0", "1", "1"])
    glossed = genanki.Note(model=m, fields=["1", "o", "det", "the", "", "", "0", "1", "1"])
    assert [c.ord for c in bare.cards] == [0]
    assert [c.ord for c in glossed.cards] == [0, 1]


def test_package_from_band_files(release_cfg, tmp_path):
    header = "rank\tlemma\tis_mwe\tpos\traw_freq\tfreq_per_million\n"
    (tmp_path / "ep_spoken_top5000.tsv").write_text(
        header + "1\to\t0\tdet\t100\t1.0\n2\ta\t0\tdet\t90\t0.9\n3\ta\t0\tprep\t80\t0.8\n",
        encoding="utf-8")
    (tmp_path / "ep_spoken_5001_10000.tsv").write_text(
        header + "5001\tfulano\t0\tnoun\t5\t0.1\n", encoding="utf-8")
    res = build_apkg.build(release_cfg, tmp_path)
    counts = {name.split("::")[-1]: n for name, n in res["notes"].items() if n}
    assert counts == {"01 · 1–500": 3, "11 · 5001–5500": 1}
    with zipfile.ZipFile(res["path"]) as z:
        z.extract("collection.anki2", tmp_path)
    db = sqlite3.connect(tmp_path / "collection.anki2")
    assert db.execute("select count(*) from cards").fetchone()[0] == 4
    tags = db.execute("select tags from notes where flds like '1\x1fo\x1f%'").fetchone()[0]
    assert "freq::0001-0500" in tags and "pos::det" in tags
