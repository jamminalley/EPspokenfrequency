# European Portuguese Spoken Frequency List

A frequency list of the **10,000 most common lemmas in European Portuguese
film and TV dialogue**, built from the Portugal-tagged portion of the
OpenSubtitles 2018 corpus — 636 million tokens of subtitle text.

Ready-to-import Anki decks are included.

| | |
|---|---|
| Entries | 10,000 rows (two files of 5,000): 9,390 distinct words, 311 of them listed once per part of speech, plus 295 multi-word expressions |
| Corpus | OPUS OpenSubtitles v2018, `pt` (Portugal-tagged) |
| Corpus size | 118,469,705 lines · 636,214,452 tokens · 838,358 unique surface types |
| Lemmatization accuracy | 98.5% on a 332-word human-reviewed sample |
| Part of speech | From a neural tagger (Stanza), by majority vote over up to 50 sentences per word |
| Licence | CC BY-SA 4.0 — see [LICENSE](LICENSE) |

An earlier version of this list (April 2026) was never published; the
pipeline that produced it was lost. It is kept for comparison only in
[`archive/out_april_2026/`](archive/out_april_2026/) (tag
`v0-april-2026`), and [CHANGELOG.md](CHANGELOG.md) records how this list
differs from it.

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
  121, *morrer* at 153, *arma* at 248 and *polícia* at 267 — higher than
  any corpus of everyday life would put them. The vocabulary of work,
  admin, school and errands correspondingly sits lower.
- **Much of it is translated.** A large share of these subtitles are
  translations of English-language film and TV, so the phrasing can carry
  translation artifacts and English-shaped idiom rather than natively
  produced Portuguese.
- **The `pt` tag is corpus metadata, not verified provenance.** It is a
  strong signal of European Portuguese, but Brazilian material can leak
  through. An explicit BP exclusion list is applied, and it is a blunt
  instrument — it removes obvious markers, not every Brazilianism.
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
| Corpus | ~636M tokens, subtitles only | ~20M tokens, balanced across registers |
| Registers | Film/TV dialogue | Spoken, fiction, newspaper, academic |
| Variety | Portugal-tagged, BP markers excluded post hoc; headwords in post-1990 spelling | Both varieties, with BP/EP marked per entry |
| Glosses & examples | None | English glosses and example sentences throughout |
| Lemmatization | Automatic: a neural tagger (Stanza) reading each word in up to 50 real sentences, checked against a dictionary. 98.5% correct on a 332-word hand-checked sample | Curated |
| POS tags | Automatic, from the same tagger: majority vote over each word's sample sentences, and a word used as two parts of speech is listed once for each. Not hand-checked | Professionally tagged |
| Contractions (*do*, *ao*, *pela*) | Kept as their own entries | Split into preposition + article |
| Review | Automatic output. Spot-checked against a hand-reviewed sample, with about 830 individual decisions made by hand (gold set, gender pairs, proper-noun drops); not edited entry by entry | Edited and peer-reviewed |
| Cost | Free | A book you buy |

What this list offers that Davies does not is scale on a single register
and a strictly European-Portuguese slant: 30× more tokens, all of it
dialogue, with Brazilian markers filtered out. That makes it a decent
*complement* to Davies for a learner targeting spoken EP. It is not a
replacement, and it has not been edited the way a published dictionary is.

### Known technical caveats

These are specific and worth knowing before you study from the list.

- **Part of speech is tagger output, not hand-checked.** The `pos`
  column is Stanza's tag, by majority vote over each word's sample
  sentences (50 for the 4,347 most frequent word forms, 5 for the rest).
  The tagger is not always consistent with itself: 3% of its tags
  contradicted the lemma it gave in the same sentence (a VERB tag on the
  noun *pergunta*) and were discarded. A word the tagger regularly uses two
  ways gets one row per part of speech, with its count divided between
  them: `a` (article and preposition), `que` (conjunction and pronoun),
  `este` (determiner and pronoun), `morto` (adjective and noun). The tags
  follow Universal Dependencies conventions, with one exception made for
  learners: a preposition is never counted as a conjunction (UD tags *para*
  in *para fazer* as one). 148 entries the tagger never saw intact, mostly
  contractions such as `do` and `pela`, keep a rule-based guess.
- **`ser` and `ir` are separated by a rule, not by the tagger.** `foi`,
  `fui`, `fomos`, `foram` and `fora` belong to *ser* ("was") or *ir*
  ("went") depending on the sentence, and the tagger assigns them to *ser*
  almost every time (*fui ao Paquistão* included). So the tagger only
  decides whether an occurrence is a verb at all — the adverb *fora*,
  "outside", is not — and a rule reading the neighbouring words picks the
  verb: *ir* before *a*, *ao*, *para*, *embora* or an infinitive, or after
  *lá*; *ser* before a participle, an adjective, a noun phrase or nothing.
  Against 100 random corpus lines checked by hand, it is right on 95.9% of
  the verb uses it decides and abstains on 9%; an abstention takes the
  form's own *ser*/*ir* ratio. The split is estimated from 1,000 random
  lines per form, so each form's share is good to about ±3 percentage
  points. It misses idioms (*ele não foi nessa*) and elliptical questions (*sempre
  foram?*). *Ser* counts 21.3M tokens and *ir* 9.0M.
- **Lemmatization is not perfect.** 98.5% on the hand-checked sample means
  something like 150 of the 10,000 entries may carry a lemma error. The
  known pattern: Stanza sometimes reads a verb form as a noun (`procura`,
  `mentes`, `sacas` kept as nouns) or picks the wrong verb (`vejam` as
  *vir*, not *ver*).
- **Split counts are estimates.** Participles (`educados`: the verb
  *educar* or the adjective *educado*) and words used as two parts of
  speech have their counts divided according to how the tagger reads a
  sample of sentences: 50 for word forms with 10,000+ occurrences, which
  gives 2% steps, and 5 for the rest (20% steps).
- **Six known duplicates remain.** Missing-accent forms are folded into
  their accented twin only when the accented form is at least 10× as
  frequent. Six pairs fall below that and appear twice: `camera`/`câmera`,
  `frigorifico`/`frigorífico`, `amen`/`ámen`, `bla`/`blá`, `mafia`/`máfia`,
  `karate`/`karaté`. They are accepted as known typo pairs rather than
  hidden. Treat the unaccented one as a typo of the other.
- **Folding by frequency can over-merge.** The same 10× rule folds a rare
  unaccented form into a common accented one even when the rare form is a
  real word. Every fold is listed in `reports/QUALITY.md`, with the
  borderline ones (10–20×) in their own section.
- **Proper nouns are removed by capitalization, and some will slip
  through.** A word is treated as a name if it is capitalized away from the
  start of a line almost every time. Dictionary words that the filter
  removed at 5,000+ occurrences were reviewed one by one — `deus`, `sr`,
  `natal` and 26 others were restored — but names below that threshold were
  not reviewed. Everything removed with 100+ occurrences is listed in
  `out/dropped_proper_nouns.txt`.
- **English words are only partly filtered.** English plurals and many
  English names are removed; other English words that turn up in
  Portuguese dialogue (`ok`, `zombie`) are kept, deliberately in the case of
  `ok`.
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
| `pos` | Part of speech from the tagger. One of `det`, `prep`, `conj`, `pron`, `adv`, `intj`, `num`, `noun`, `adj`, `verb`, `mwe`, `unk`. A word used as two parts of speech has one row for each. See caveats. |
| `raw_freq` | Lemma occurrence count across the full corpus. |
| `freq_per_million` | Occurrences per million tokens (of 636,214,452). |

### The Anki decks

| File | Fields |
|---|---|
| `ep_spoken_anki_minimal.tsv` | Rank, Lemma_PT, POS, Is_MWE, Raw_Freq, Freq_per_million, Tags |
| `ep_spoken_anki_enrichable.tsv` | The same, plus empty `Gloss_EN`, `Example_PT`, `Example_EN` for you to fill in |
| `ep_spoken_5001_10000_anki_minimal.tsv` | Ranks 5001–10000, minimal fields |
| `ep_spoken_5001_10000_anki_enrichable.tsv` | Ranks 5001–10000, enrichable fields |

### Quality-control files

| File | What it is |
|---|---|
| `qc_sample.csv` | A spot-check sample across the first band — a quick way to eyeball output quality without opening a 5,000-row file. |
| `dropped_proper_nouns.txt` | Words removed as proper nouns (with 100+ occurrences), plus the BP exclusions, English plurals and fragments removed by the other filters. |

The build reports are in [`reports/`](reports/): `COMPARISON.md` (this
list against the unpublished April 2026 version), `QUALITY.md` (the quality gate and every
accent fold), and `backend_scores.md` (how the lemmatizers compared).

---

## How the list is built

From `pt.txt.gz` to `out/`, in one command (`python -m scripts.build`):

1. **Tokenize and count.** A Portuguese-aware tokenizer strips subtitle
   artifacts and lowercases. Enclitic clusters are split and the verb is
   restored: `fazê-lo` counts as *fazer* + *lo*, and `dar-lhe-ia` as
   *daria* + *lhe*.
2. **Second pass.** Bigram counts for multi-word expressions, sample
   sentences for every frequent word (50 for the 4,347 word forms with
   10,000+ occurrences, 5 for the rest), and capitalization statistics for
   the proper-noun filter.
3. **Tag and lemmatize.** [Stanza](https://stanfordnlp.github.io/stanza/)
   reads the 63,253 word forms frequent enough to reach the list inside
   their sample sentences — about 500,000 sentences — and gives each
   occurrence a lemma and a part of speech. The majority lemma wins, after
   discarding votes where the lemma and the tag contradict each other. When
   Stanza's answer is not a dictionary word (it occasionally invents forms
   like *agradeçar*),
   [simplemma](https://github.com/adbar/simplemma) is used instead; simplemma
   also handles the rare tail. A small table of hand-verified corrections
   covers errors Stanza makes at high frequency (`dói` is *doer*, not
   *dizer*).
4. **Resolve context-dependent forms per occurrence.** Participles are
   split between the verb and the adjective according to how Stanza tags
   them in their sample sentences. `foi`, `fui`, `fomos`, `foram` and
   `fora` are split between *ser* and *ir* by a separate next-word rule,
   because the tagger cannot tell them apart (see caveats).
5. **Apply the lemmatization conventions** in
   [eval/conventions.md](eval/conventions.md):
   1. contractions (`do`, `ao`, `pela`) are their own entries;
   2. adjectives fold to the masculine, but nouns for people keep the
      feminine (`senhora`, `rapariga`), and a feminine with its own meaning
      always stays (`música`, `sexta`) — decided pair by pair in
      [eval/gender_pairs.tsv](eval/gender_pairs.tsv);
   3. diminutives stay separate (`coisinha`);
   4. comparatives and irregular superlatives are their own entries
      (`maior`, `melhor`, `ótimo`);
   5. spelling-reform variants merge under the post-1990 spelling
      (`acção` → `ação`, `óptimo` → `ótimo`), while words that keep their
      consonant in European spelling (`facto`, `contacto`) are left alone.

   Pronouns are their own entries too (`me`, not *eu*).
6. **Fold remaining duplicates.** Each lemma is checked against the
   lemmatizer again, and regular plurals are folded onto their singular
   (guarded: `óculos`, `férias` and `cais` are not plurals of anything). An
   unaccented form folds into its accented twin when the accented form is at
   least 10× as frequent, and wrong or Brazilian accents (`näo`, `prêmio`)
   fold into the European spelling.
7. **Filter.** BP-leaning words are removed from the exclusion list —
   `aeromoça`, `bacana`, `banheiro`, `celular`, `galera`, `geladeira`,
   `legal`, `mano`, `massa`, `né`, `oi`, `trem`, `você`, `vocês`, `xícara`,
   `ônibus`, with their unaccented variants. Proper nouns are removed by
   capitalization, subject to the reviewed decisions in
   [eval/proper_noun_drops_review.tsv](eval/proper_noun_drops_review.tsv).
   English plurals are removed, and so are one- and two-letter fragments
   that are neither words nor interjections.
8. **Assign part of speech.** Each word's count is divided across the
   parts of speech the tagger gave it, the same way participle counts are
   divided across lemmas. A second part of speech becomes its own row only
   if it holds at least 25% of the word's count and at least 3 tagged
   sentences; otherwise it joins the majority.
9. **Rank and emit** the top 10,000 rows by count, with multi-word
   expressions — kept by log-likelihood (Dunning G² ≥ 2500) and a
   collocation share of at least 5% — ranked alongside them. 295 of them
   make the top 10,000: 191 in the first band and 104 in the second.

### How it is checked

- **A human-reviewed gold set.** [eval/lemma_gold.tsv](eval/lemma_gold.tsv)
  is 400 words sampled from the corpus across the frequency range, each
  checked by hand. 332 are scored; 68 were marked as names, foreign words or
  junk. The published lemmas are correct for **98.5%** of them.
- **A quality gate.** Every build looks for entries that are probably the
  same word counted twice — a form that lemmatizes to another entry, an
  accent variant of another entry, a regular plural of another entry — and
  fails if it finds any that are not explicitly accepted. **This release
  passes.** Two kinds of pair are accepted in `config.yaml`, each listed:
  words that are genuinely different (`avô`/`avó`, `pôr`/`por`,
  `cirurgiã`/`cirurgia`), and the six known typo pairs from the caveats,
  which sit below the 10× folding threshold. Any new suspect fails the
  build.
- **A hand-checked *ser*/*ir* sample.**
  [eval/ser_ir_sample.tsv](eval/ser_ir_sample.tsv) is 100 corpus lines
  drawn at random, 20 for each of `foi`, `fui`, `fomos`, `foram` and
  `fora`. The labels were proposed by an AI model acting as a Portuguese
  informant and checked independently by hand. The *ser*/*ir* rule is right
  on **95.9%** of the verb uses it decides (71 of 74), abstains on 9%, and
  none of the 19 lines where *fora* is the adverb reaches it. The build
  uses the rule only while a score of at least 95% exists for its current
  version; the full table is in
  [reports/serir_scores.md](reports/serir_scores.md).
- **Determinism.** The same corpus, configuration and library versions
  produce byte-identical output.

---

## Reproducing this

You need Python 3.13 and several GB of free disk (the corpus, Stanza's
models and PyTorch). The first build takes about an hour on an 8-core
machine; later builds reuse cached passes and take a minute.

```bash
git clone https://github.com/jamminalley/EPspokenfrequency.git
cd EPspokenfrequency
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -c "import stanza; stanza.download('pt')"
```

Download the corpus (1.1 GB) into `data/` as described in
[DATA_SOURCES.md](DATA_SOURCES.md), then:

```bash
./.venv/bin/python -m scripts.build
```

This writes `out/` and `reports/` and exits with status 0. If you change
the configuration and the build exits with status 1, the quality gate has
found a new suspected duplicate: it is listed in `reports/QUALITY.md`, and
every output has still been written.

`requirements.txt` pins the exact versions used for this release. With
them the build reproduces `out/` byte for byte; a different Stanza or
simplemma release can change individual lemmas. To rebuild the April-style
list for comparison, run `python -m scripts.build --stage 1` (output in
`build/stage1/`). [scripts/README.md](scripts/README.md) covers the other
options.

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

- *minimal*: `Rank`, `Lemma_PT`, `POS`, `Is_MWE`, `Raw_Freq`,
  `Freq_per_million`
- *enrichable*: `Rank`, `Lemma_PT`, `POS`, `Gloss_EN`, `Example_PT`,
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
| `pos::det`, `pos::verb`, … | Part of speech |
| `source::opensubtitles_ep_v2018` | Provenance |
| `variety::EP`, `register::spoken` | Variety and register |

Use the Anki browser to select a band, and suspend the rest until you get
to it.

---

## Repository layout

```
out/                   Published frequency lists and Anki decks
reports/               Build reports: comparison, quality gate, backend scores
archive/out_april_2026/  The unpublished April 2026 list, kept for comparison
eval/                  Gold set, conventions, and the hand-reviewed decision files
scripts/               The pipeline (python -m scripts.build)
tests/                 Unit tests (pytest; no corpus needed)
config.yaml            Every threshold, list and switch the pipeline uses
data/                  Corpus download target — gitignored, never committed
DATA_SOURCES.md        Corpus citation and download instructions
CHANGELOG.md           What changed between versions
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
