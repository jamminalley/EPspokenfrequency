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
    assert [d["id"] for d in a["decks"]] == [2038517696, 1869653180]


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
    assert list(res["notes"].values()) == [3, 1]
    with zipfile.ZipFile(res["path"]) as z:
        z.extract("collection.anki2", tmp_path)
    db = sqlite3.connect(tmp_path / "collection.anki2")
    assert db.execute("select count(*) from cards").fetchone()[0] == 4
    tags = db.execute("select tags from notes where flds like '1\x1fo\x1f%'").fetchone()[0]
    assert "freq::0001-0500" in tags and "pos::det" in tags
