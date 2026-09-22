"""Build out/EP_Spoken_Frequency.apkg, the ready-to-import Anki package.

One note type, "Portuguese (EP) – Spoken Frequency", with the enrichable
field set, and one deck per rank band. Two card templates:

  Card 1  PT -> EN  every note
  Card 2  EN -> PT  only when Gloss_EN is filled in: its front is wrapped
                    in {{#Gloss_EN}}...{{/Gloss_EN}}, and Anki does not
                    generate a card whose front renders empty. The lists
                    ship without glosses, so no reverse cards exist yet.

Stability across releases. The note type and deck ids live in config.yaml
and are never regenerated. Each note's GUID is derived from its lemma and
POS, so importing a later release over this one updates the matching notes
(new ranks, counts, tags) instead of adding duplicates, and keeps a
learner's review history.

Run by `python -m scripts.build` after the lists are written, or alone:
    python -m scripts.build_apkg
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

FIELDS = ["Rank", "Lemma_PT", "POS", "Gloss_EN", "Example_PT", "Example_EN",
          "Is_MWE", "Raw_Freq", "Freq_per_million"]

FRONT_PT = """<div class="lemma">{{Lemma_PT}}</div>
<div class="pos">{{POS}}</div>"""

BACK_PT = """{{FrontSide}}
<hr id="answer">
{{#Gloss_EN}}<div class="gloss">{{Gloss_EN}}</div>{{/Gloss_EN}}
{{#Example_PT}}<div class="example pt">{{Example_PT}}</div>{{/Example_PT}}
{{#Example_EN}}<div class="example en">{{Example_EN}}</div>{{/Example_EN}}
<div class="footer">#{{Rank}} · {{Freq_per_million}} per million words</div>"""

# The whole front sits inside the Gloss_EN conditional: with no gloss the
# front is empty and Anki generates no card.
FRONT_EN = """{{#Gloss_EN}}<div class="gloss prompt">{{Gloss_EN}}</div>
<div class="pos">{{POS}}</div>{{/Gloss_EN}}"""

BACK_EN = """{{FrontSide}}
<hr id="answer">
<div class="lemma">{{Lemma_PT}}</div>
{{#Example_PT}}<div class="example pt">{{Example_PT}}</div>{{/Example_PT}}
{{#Example_EN}}<div class="example en">{{Example_EN}}</div>{{/Example_EN}}
<div class="footer">#{{Rank}} · {{Freq_per_million}} per million words</div>"""

CSS = """.card {
  font-family: -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 20px;
  line-height: 1.4;
  text-align: center;
  color: #1f2328;
  background: #ffffff;
  padding: 1.2em 1em;
}
.lemma { font-size: 2.2em; font-weight: 600; }
.pos { font-size: 0.8em; color: #6e7781; margin-top: 0.2em; letter-spacing: 0.03em; }
.gloss { font-size: 1.2em; margin: 0.6em 0; }
.gloss.prompt { font-size: 1.6em; }
.example { font-size: 0.95em; margin: 0.4em auto; max-width: 32em; }
.example.en { color: #57606a; font-style: italic; }
.footer { margin-top: 1.4em; font-size: 0.7em; color: #8c959f; }
hr#answer { border: none; border-top: 1px solid #d0d7de; margin: 0.9em 0; }
.nightMode .card, .night_mode .card { color: #e6edf3; background: #0d1117; }
.nightMode .pos, .night_mode .pos, .nightMode .footer, .night_mode .footer { color: #8b949e; }
.nightMode .example.en, .night_mode .example.en { color: #a8b1bb; }
@media (max-width: 480px) { .card { font-size: 18px; } .lemma { font-size: 2em; } }
"""


def model(cfg: dict[str, Any]):
    import genanki

    acfg = cfg["output"]["anki"]
    return genanki.Model(
        acfg["apkg"]["model_id"],
        acfg["notetype"],
        fields=[{"name": f} for f in FIELDS],
        templates=[
            {"name": "Card 1 (PT → EN)", "qfmt": FRONT_PT, "afmt": BACK_PT},
            {"name": "Card 2 (EN → PT)", "qfmt": FRONT_EN, "afmt": BACK_EN},
        ],
        css=CSS,
        sort_field_index=0,
    )


def note_guid(lemma: str, pos: str) -> str:
    """Stable across releases: the same word in the same POS is the same
    note, whatever its rank or count."""
    import genanki

    return genanki.guid_for("ep-spoken-frequency", lemma, pos)


def build(cfg: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Write the .apkg from the band TSVs in out_dir. Returns note counts."""
    import genanki

    from scripts.emit import build_tags

    acfg = cfg["output"]["anki"]
    pcfg = acfg["apkg"]
    mdl = model(cfg)
    decks = []
    counts: dict[str, int] = {}
    seen: set[str] = set()
    for spec, deck_cfg in zip(cfg["output"]["files"], pcfg["decks"]):
        deck = genanki.Deck(deck_cfg["id"], deck_cfg["name"])
        with (out_dir / f"{spec['stem']}.tsv").open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                guid = note_guid(row["lemma"], row["pos"])
                if guid in seen:
                    raise ValueError(f"duplicate note (lemma, pos): {row['lemma']!r}, {row['pos']!r}")
                seen.add(guid)
                rank = int(row["rank"])
                deck.add_note(genanki.Note(
                    model=mdl,
                    fields=[row["rank"], row["lemma"], row["pos"], "", "", "",
                            row["is_mwe"], row["raw_freq"], row["freq_per_million"]],
                    tags=build_tags(rank, row["pos"], cfg).split(),
                    guid=guid,
                    sort_field=row["rank"],
                ))
        decks.append(deck)
        counts[deck_cfg["name"]] = len(deck.notes)

    path = out_dir / pcfg["file"]
    genanki.Package(decks).write_to_file(str(path), timestamp=pcfg["timestamp"])
    return {"path": str(path), "notes": counts, "bytes": path.stat().st_size}


def main() -> None:
    import argparse

    from scripts import config as config_mod

    ap = argparse.ArgumentParser(description="Build the Anki .apkg from out/.")
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()
    cfg = config_mod.load(args.config)
    res = build(cfg, config_mod.out_dir(cfg))
    print(f"{res['path']}: {res['bytes']:,} bytes")
    for name, n in res["notes"].items():
        print(f"  {name}: {n:,} notes")


if __name__ == "__main__":
    main()
