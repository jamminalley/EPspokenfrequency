# European Portuguese Spoken Frequency List

A frequency list of the **10,000 most common lemmas in European Portuguese
film and TV dialogue**, built from the Portugal-tagged portion of the
OpenSubtitles 2018 corpus — 623.9 million tokens of subtitle text.

Ready-to-import Anki decks are included.

| | |
|---|---|
| Entries | 10,000 lemmas (two files of 5,000) |
| Multi-word expressions | 290, flagged with `is_mwe` |
| Corpus | OPUS OpenSubtitles v2018, `pt` (Portugal-tagged) |
| Corpus size | 118,469,705 lines · 623,920,347 tokens · 955,446 unique surface types |
| Licence | CC BY-SA 4.0 — see [LICENSE](LICENSE) |

---

## Who this is for

**Learners of European Portuguese** who want to study vocabulary in the
order they are likely to actually hear it. If you have worked through a
beginner course and want a principled answer to "what should I learn
next?", a frequency list built from dialogue is a reasonable guide — and
the Anki decks in `out/` let you start tonight.

It is particularly aimed at learners who keep finding that the Portuguese
in their textbook is Brazilian, or that their word list is drawn from
newspapers rather than conversation.

**Researchers and tool-builders** may find the lists useful as a rough
register baseline, provided you read the Limitations below first and treat
the numbers accordingly.

**It is not a course, a dictionary, or a substitute for either.** There are
no definitions, no translations, and no example sentences — just lemmas,
ranks, and counts. (The "enrichable" Anki files leave empty columns for
you to fill in your own glosses and examples.)

---

## Limitations

**Please read this section before you rely on anything here.** This is a
hobbyist project, and being honest about what it is not is more useful than
overselling what it is.

### This is subtitle text, not a balanced corpus

Every number here comes from one source: subtitles for films and TV shows.
That has real consequences.

- **Subtitles are written approximations of speech, not speech.** They are
  condensed to fit reading speed, cleaned of disfluencies, hesitations,
  repairs, and overlaps, and they lose everything about how something was
  said. Real conversation looks different.
- **The register is dramatic dialogue.** Film and TV over-represent crime,
  conflict, romance, and emergencies. *Matar* ("to kill") lands at rank
  116, *morrer* at 153, *arma* at 225 and *polícia* at 242 — higher than
  any corpus of everyday life would put them. The vocabulary of work,
  admin, school and errands correspondingly sits lower.
- **Much of it is translated.** A large share of these subtitles are
  translations of English-language film and TV, so the phrasing can carry
  translation artifacts and English-shaped idiom rather than natively
  produced Portuguese.
- **The `pt` tag is corpus metadata, not verified provenance.** It is a
  strong signal of European Portuguese, but Brazilian material can leak
  through. An explicit BP exclusion list was applied (see the pipeline
  below), and it is a blunt instrument — it removes obvious markers, not
  every Brazilianism.
- **It is single-genre and one snapshot in time.** No news, no academic
  prose, no fiction, no non-fiction, no actual recorded conversation, and
  nothing newer than the 2018 corpus release.

### How this differs from Davies

The standard published reference is Mark Davies and Ana Maria Raposo
Preto-Bay's *A Frequency Dictionary of Portuguese* (Routledge, 2008). If
you are choosing between them, choose Davies — it is peer-reviewed,
professionally edited, and comes with the things this list lacks.

|  | This list | Davies |
|---|---|---|
| Corpus | ~624M tokens, subtitles only | ~20M tokens, balanced across registers |
| Registers | Film/TV dialogue | Spoken, fiction, newspaper, academic |
| Variety | Portugal-tagged, BP markers excluded post hoc | Both varieties, with BP/EP marked per entry |
| Glosses & examples | None | English glosses and example sentences throughout |
| POS tags | Heuristic guess, unverified | Professionally tagged |
| Lemmatization | Automatic, lookup-based | Curated |
| Review | None — unreviewed automatic output | Edited and peer-reviewed |
| Cost | Free | A book you buy |

What this list offers that Davies does not is scale on a single register
and a strictly European-Portuguese slant: 30× more tokens, all of it
dialogue, with Brazilian markers filtered out. That makes it a decent
*complement* to Davies for a learner targeting spoken EP. It is not a
replacement, and it has not been checked by anyone.

### Known technical caveats

These are specific and worth knowing before you study from the list.

- **`ser`/`ir` conflation.** `foi`, `fui`, `fomos`, `foram` and `fora` are
  lemmatized as `ir`. In a conversational register many of these are in
  fact preterite forms of `ser` (the copula, "was"). This biases `ir`
  upward. Consider downstream POS-disambiguation if precise `ser`/`ir`
  splits matter to you.
- **Accent-stripped duplicates are counted separately.** Subtitle text is
  often typed without diacritics, and the pipeline does not fold these back
  together. So `nao` appears at rank 1004 alongside `não` at rank 4, and
  the same happens for `so`/`só`, `ja`/`já`, `familia`/`família` and
  `dificil`/`difícil`. Treat an unaccented entry as a spelling artifact of
  a word you already have, not as a separate word to learn.
- **One BP marker slipped through on spelling.** The exclusion list held the
  accented `você`, so the unaccented `voce` survived at rank 2182. Ignore
  it; it is not EP usage.
- **Lemmatization misses.** The lemmatizer is lookup-based, so a handful of
  low-frequency verb 2sg forms fall out as distinct lemmas (e.g. `chega`
  from `chegas` instead of rolling into `chegar`). These errors are in the
  low single digits at ranks ≥ 3000 and are generally harmless.
- **`pos_guess` is a heuristic, not a tagger.** It is a closed-class lookup
  plus suffix rules. Feminine/masculine nouns with bare `-a`/`-o` endings
  fall through to `noun`; some of those are really adjectives or verb
  forms. Verify downstream. A real POS tagger would do better — spaCy's
  `pt_core_news_sm` is the obvious upgrade, but was unavailable in the
  build environment.
- **Proper nouns still leak.** The OOV heuristic caught ~500 of them
  (listed in `out/dropped_proper_nouns.txt`), but it is not exhaustive —
  e.g. `cristina` survives at rank 4999. Likewise a few MWE candidates are
  junk rather than expressions (`d c`).
- **MWE counts are an overlay, not a replacement.** An MWE's `raw_freq` is
  the bigram count, and it is *not* subtracted from its constituent words'
  lemma counts. This is the usual frequency-list convention, but it means
  the column does not sum to the corpus.

---

## What's in `out/`

Two rank bands — **1–5000** and **5001–10000** — each published in four
formats. Files without a number in the name are the first band.

### The frequency lists

| File | What it is |
|---|---|
| `ep_spoken_top5000.tsv` / `.csv` | Ranks 1–5000. The main list. |
| `ep_spoken_5001_10000.tsv` / `.csv` | Ranks 5001–10000. |

TSV and CSV hold identical data; pick whichever your tools prefer. Columns:

| Column | Meaning |
|---|---|
| `rank` | 1-based rank by `raw_freq`. |
| `lemma` | Lemma form, or the surface multi-word expression for MWE entries. |
| `is_mwe` | `1` for a multi-word expression, `0` otherwise. |
| `pos_guess` | Rule-based POS heuristic. One of `det`, `prep`, `conj`, `pron`, `adv`, `intj`, `num`, `noun`, `adj`, `verb`, `mwe`, `unk`. Verify downstream. |
| `raw_freq` | Lemma occurrence count across the full corpus. |
| `freq_per_million` | Occurrences per million tokens. |

### The Anki decks

| File | Fields |
|---|---|
| `ep_spoken_anki_minimal.tsv` | Rank, Lemma_PT, POS_guess, Is_MWE, Raw_Freq, Freq_per_million, Tags |
| `ep_spoken_anki_enrichable.tsv` | The same, plus empty `Gloss_EN`, `Example_PT`, `Example_EN` for you to fill in |
| `ep_spoken_5001_10000_anki_minimal.tsv` | Ranks 5001–10000, minimal fields |
| `ep_spoken_5001_10000_anki_enrichable.tsv` | Ranks 5001–10000, enrichable fields |

### Quality-control files

| File | What it is |
|---|---|
| `qc_sample.csv` | A spot-check sample across the rank range — a quick way to eyeball output quality without opening a 5,000-row file. |
| `dropped_proper_nouns.txt` | ~500 lemmas removed by the proper-noun/OOV heuristic, sorted by count. Review it to rescue any false positives. |

---

## Pipeline

How the lists were produced from `pt.txt.gz`:

1. **Tokenize and count** unigram surface forms, using a Portuguese-aware
   regex: subtitle artifacts stripped, lowercase normalization, and
   enclitic clusters split.
2. **Lemmatize** the type inventory with [`simplemma`](https://github.com/adbar/simplemma)
   (lookup-based). Known simplemma PT errors are corrected via a
   hand-curated override table of ~200 surface→lemma mappings, then
   validated against the [`pyspellchecker`](https://github.com/barrust/pyspellchecker)
   PT dictionary — lemmas absent from the dictionary are rejected and fall
   back to the surface form.
3. **Collect bigrams** in a second corpus pass, restricted to surface forms
   with ≥ 100 occurrences. MWE candidates are retained on log-likelihood
   ratio (Dunning G² ≥ 2500) and collocation share ≥ 5%. 290 of the
   surviving MWEs land inside the top 10,000 — 179 in the first band, 111
   in the second.
4. **Filter.** BP-leaning lemmas are excluded — `aeromoça`, `bacana`,
   `banheiro`, `cara`, `celular`, `galera`, `geladeira`, `legal`, `mano`,
   `massa`, `né`, `oi`, `trem`, `você`, `vocês`, `xícara`, `ônibus` —
   and proper-noun leaks are filtered by an OOV heuristic, logged to
   `out/dropped_proper_nouns.txt`.
5. **Rank and emit** the top 10,000 entries by raw lemma count as TSV, CSV
   and Anki TSV.

> **Note on reproducing this.** The scripts that produced `out/` were lost;
> they are being rebuilt. `out/` is the output of the original run and is
> left untouched. See [scripts/README.md](scripts/README.md) for status, and
> [DATA_SOURCES.md](DATA_SOURCES.md) for how to obtain the corpus.

---

## Importing the Anki decks

The `*_anki_*.tsv` files carry Anki's header directives, so Anki
configures the import itself — separator, note type, target deck, field
mapping and tags column are all declared in the file.

1. In Anki, choose **File → Import**.
2. Select one of the `out/*_anki_*.tsv` files.
3. The import screen will pre-fill from the file's headers. Check that:
   - **Field separator** is Tab
   - **Notetype** is `Portuguese (EP) – Spoken Frequency`
   - **Deck** is `Portuguese::European Portuguese - Spoken - First 5000`
     (or `... - 5001 to 10000`)
   - **Allow HTML in fields** is off
4. Click **Import**.

**Create the note type first.** Anki will not invent it for you. Before
importing, go to **Tools → Manage Note Types → Add**, name it
`Portuguese (EP) – Spoken Frequency`, and give it fields matching the file
you plan to import:

- *minimal*: `Rank`, `Lemma_PT`, `POS_guess`, `Is_MWE`, `Raw_Freq`,
  `Freq_per_million`
- *enrichable*: `Rank`, `Lemma_PT`, `POS_guess`, `Gloss_EN`, `Example_PT`,
  `Example_EN`, `Is_MWE`, `Raw_Freq`, `Freq_per_million`

(The `Tags` column is not a field — Anki maps it to note tags
automatically.) Then design your own card templates; front/back layout is
a personal choice and none is shipped here.

### Which file should I import?

Take **`ep_spoken_anki_enrichable.tsv`** if you intend to add your own
translations and example sentences as you study — which is the approach
that actually builds retention. Take the *minimal* file if you only want
the ranked word list and will look things up elsewhere.

Either way, start with the first 5,000 and leave `5001_10000` until you
have worked through it.

### Studying in frequency order

Every note is tagged with its rank band, so you can study in slices rather
than importing 5,000 cards and drowning:

| Tag | Meaning |
|---|---|
| `freq::0001-0500`, `freq::0501-1000`, … | 500-word band |
| `freq500::…` | 500-word band (alias) |
| `freq1000::0001-1000`, … | 1000-word band |
| `pos::det`, `pos::verb`, … | Part-of-speech guess |
| `source::opensubtitles_ep_v2018` | Provenance |
| `variety::EP`, `register::spoken` | Variety and register |

Use the Anki browser to select a band, and suspend the rest until you get
to it.

---

## Repository layout

```
out/                 Published frequency lists and Anki decks
scripts/             Pipeline scripts (being rebuilt)
data/                Corpus download target — gitignored, never committed
DATA_SOURCES.md      Corpus citation and download instructions
requirements.txt     Python dependencies for the pipeline
LICENSE              CC BY-SA 4.0
```

`data/` is excluded from version control because the corpus is a 1.1 GB
file that has no business in git history. Download it yourself following
[DATA_SOURCES.md](DATA_SOURCES.md).

---

## Licence and citation

Released under **CC BY-SA 4.0** ([LICENSE](LICENSE)). Use it, change it,
redistribute it — keep the attribution and share derivatives alike.

If you publish anything based on this, please cite the underlying corpus:

> Lison, P., & Tiedemann, J. (2016). OpenSubtitles2016: Extracting Large
> Parallel Corpora from Movie and TV Subtitles. *LREC 2016*.

Full citations, BibTeX and upstream terms are in
[DATA_SOURCES.md](DATA_SOURCES.md).
