# Changelog

## Unreleased

Work towards 1.1.0. Not tagged or released; the version number is fixed
when the glosses have been reviewed.

### Added

- **English glosses and example sentences**, `out/glosses.tsv`: one to
  three English senses per entry, commonest first, plus one sentence taken
  verbatim from the corpus and its translation, and flags for `vulgar`,
  `bp-leaning`, `archaic`, `name-like` and `uncertain`. Written by Claude
  (`claude-opus-5`), one request per entry, from the entry, its part of
  speech, its frequency and up to twenty real corpus sentences containing
  it. The prompt ships with the repository
  (`scripts/gloss_prompt.md`) and the run is pinned in `config.yaml`.
  **These are a snapshot of one model's answers, not a reference work**, and
  are not reproducible byte for byte the way the lists are.
- **A repair step between the model's reply and the published row**
  (`gloss.repair`). Three things went wrong often enough in the first full
  run to be worth handling rather than failing over, and each is handled in
  a way that keeps the published example a real corpus line: a
  doubly-escaped `\uXXXX` is decoded (5 rows); an example the model tidied
  itself — dropped the dialogue dash — is re-anchored to the corpus line it
  tidied, which changes nothing about the card (6 rows); and an example the
  model *edited* (an accent added, a pronoun supplied, a clause trimmed) is
  dropped, because there is no telling a correction from a corruption, and
  the entry keeps its gloss alone (24 rows). Every one is counted and listed
  in the gate report.
- **Gates on the glosses**, `reports/gloss_gates.md`: coverage, and the
  check that matters — every example sentence must be one of the corpus
  lines the model was shown, character for character, and must contain the
  entry. A run failing any fatal gate is not published. Per-flag counts and
  the cost of the run are in the same report.
- **A review sample**, `eval/gloss_review.tsv`: all of ranks 1–500 plus 200
  spread evenly over the rest, with the sentences each entry was offered, so
  a reader can check what the model was working from.
- **A targeted corpus pass for entries the sampled contexts missed.** Nine
  published entries — eight multi-word expressions and one folded adjective
  — had no sampled sentence containing them, because pass 2 keeps lines for
  the 70,000 most frequent forms and, for a phrase, only lines that happen
  to contain the whole phrase. Those now get one scan of their own, choosing
  lines by the same digest rule, so every one of the 10,000 entries was
  glossed from real sentences rather than from its headword alone.

### Known issues

- **One word has no gloss.** `caseiro` (rank 4209, "homemade") trips a
  safety classifier on every attempt; the row ships with an empty gloss and
  an `uncertain` flag. The gate names it and tolerates up to five such rows.
- **200 entries have no example sentence** (2.0%). Either every sampled line
  showed a different word — `doméstica` the adjective rather than the noun —
  or the lines were unintelligible fragments. Those entries have a gloss and
  no example; the reverse Anki card still works, the sentence fields are
  just empty.
- **The glosses are not reproducible byte for byte.** The lists are; these
  are one model's answers on one day, and the response cache in `cache/gloss/`
  is what makes a rerun repeat them rather than re-derive them.

### Changed

- **Every contraction is now published as `det`** (`fixes.contraction_pos`,
  `pos.contraction_pos`). Stanza expands *do*, *nas*, *pelo* and the rest
  into two words before tagging, so the surface token collected almost no
  usable evidence: 28 contraction entries read `unk`, and those with a stray
  tag read worse — `pelo` as a noun, `deste` as a verb, `ao` as a
  conjunction, `contigo` split across three parts of speech. `do` and `da`
  already read `det` on the tagger's own evidence; the rest of the paradigm
  now agrees with them. It is the right answer for the
  preposition-plus-article contractions and a convenience for the
  preposition-plus-pronoun ones (*dele*, *comigo*, *nisso*), which are not
  determiners in any analysis.

  **70 rows changed part of speech** and `unk` rows fell from 106 to 78.
  Because the three `contigo` rows and four other split entries merge into
  one, three entries move into the list from just below rank 10,000
  (`carnívoro`, `decretar`, `lótus`). Word lists, counts and ranks are
  otherwise unchanged; the gold-set score (98.5%) and the quality gate (0
  suspects) are unaffected.

  **This changes Anki note identity for those 70 notes.** A note's GUID
  comes from its word and part of speech, so re-importing over 1.0.0 adds a
  second note for each contraction whose POS changed and leaves the old one
  behind. Deleting the twenty decks before importing is the clean path for
  anyone who has not yet started reviewing.


## 1.0.0 — 2026-09-24

The first public release: 10,000 words of European Portuguese film and TV
dialogue, ranked, with a ready-to-import Anki package. Lemmas come from a
neural tagger checked against a dictionary and score 98.5% on a
hand-reviewed sample; the part of speech is the tagger's, and `ser` and
`ir` are separated by a rule measured against a native-speaker-labeled
sample.

**Overlap with the April list** is 79.0% of band 1 (ρ 0.944) and 63.3% of
band 2 (ρ 0.851). Against the v0.9 checkpoint the word lists barely change;
what changed there was the POS column and, through POS splitting, which
rows fill the last places of each band.

**Known issues.**

- **No glosses or example sentences.** The `Gloss_EN`, `Example_PT` and
  `Example_EN` fields ship empty, for you to fill in; until a note has a
  gloss it has no English → Portuguese card. Glosses are planned for 1.1.
- **Six accent pairs are accepted as known typos** and appear as two
  entries each: `camera`/`câmera`, `frigorifico`/`frigorífico`,
  `amen`/`ámen`, `bla`/`blá`, `mafia`/`máfia`, `karate`/`karaté`. They sit
  below the 10× folding ratio, and the quality gate accepts them by name.
- **The `ser`/`ir` rule is right on 95.9%** of the verb uses it decides on
  the development sample and **93.2%** (68 of 73) on the held-out sample,
  abstaining on 8–9%. Its errors all call an `ir` use `ser`, so `ir` is
  still slightly undercounted. One adverbial *fora* in twenty reaches the
  rule at all (*lá fora*, mistagged by Stanza), affecting about 1% of
  `fora` tokens; left for a later round rather than tuned away against the
  test set.
- **Re-importing a later `.apkg`** matches notes by word and part of
  speech, and Anki's "Update notes" option then replaces every field,
  glosses and examples a learner has typed in included; choosing "Never"
  keeps them but freezes ranks. Deferred to 1.1, when glosses ship.

- **A ready-to-import Anki package**, `out/EP_Spoken_Frequency.apkg`: one
  note type, twenty decks of 500 words numbered in rank order
  (`01 · 1–500` … `20 · 9501–10000`), a Portuguese → English card
  for every note, and an English → Portuguese card that appears only once
  a gloss is added. Notes are identified by word and part of speech, so a
  later release imported over this one updates notes instead of
  duplicating them. The TSV files remain for building your own note type.
- **Part of speech from Stanza.** The POS column -- renamed from
  `pos_guess` to `pos`, and the Anki field from `POS_guess` to `POS` -- is
  now the tagger's majority vote over each word's sample sentences,
  replacing the rule heuristic reconstructed from the April list.
  Prepositions are never counted as conjunctions (Universal Dependencies
  tags *para fazer* as one); the list is in config.yaml. A word the tagger uses
  as two parts of speech gets one row for each, with its count divided the
  same way participle counts are divided across lemmas: 311 words now have
  more than one row (`a` as article and preposition, `que`, `este`,
  `morto`), so the 10,000 rows hold 9,390 distinct words. 148 entries
  without usable tags, mostly contractions, keep the heuristic.
- **Larger samples for frequent words.** Word forms with 10,000+
  occurrences are now read in 50 sentences instead of 5, so their splits
  move in 2% steps instead of 20%.
- **One tagging pass.** Lemmas, participle splits and POS now come from a
  single Stanza pass over about 500,000 sentences, and a lemma vote is
  discarded when Stanza's lemma and tag contradict each other (`saia`
  given the lemma *saia* but tagged VERB). Gold-set accuracy is unchanged
  at 98.5%. `vá` added to the override table (Stanza read it as *ver*).
- **`ser` and `ir` are now split by a rule.** v0.9 said the tagger split
  them by context; it does not. The larger sample shows it assigns `foi`,
  `fui`, `fomos` and `foram` to *ser* almost regardless of context, all 50
  sampled uses of `fui` and `fomos` included (*fui ao Paquistão*). Stanza
  now only decides whether an occurrence is a verb, which keeps the adverb
  *fora* ("outside") out, and a next-word rule (`scripts/serir.py`) picks
  *ser* or *ir*. Scored against 100 random corpus lines checked by hand
  (`eval/ser_ir_sample.tsv`): 95.9% right on the verb uses it decides,
  abstaining on 9%; none of the 19 adverbial *fora* lines reaches it. On a
  held-out sample of another 100 lines labeled afterwards by a
  native-speaker Portuguese teacher (`eval/ser_ir_sample2.tsv`), 93.2%
  (68/73), abstaining on 8% —
  the honest estimate, since the rule was never tuned against it.
  Abstentions, and non-verb tags on forms that are always verbs (Stanza
  tags 6% of `foi` as a conjunction in clefts like *Foi por isso que*),
  take the form's own *ser*/*ir* ratio. The build applies the rule only
  while a passing score exists for its current version. Per form, *ir* is
  now 26% of `fui`, 29% of `fomos`, 11% of `foram` and 10% of `foi`. *Ser*
  goes from 21.5M tokens to 21.3M and *ir* from 8.9M to 9.0M: `fui` and
  `fomos` move a lot, but `foi`, the biggest form by far, is mostly the
  copula.

## v0.9 — 2026-09, rebuilt pipeline, human-checked (private checkpoint)

The first version whose pipeline is in this repository. `python -m
scripts.build` regenerates `out/` from the corpus, byte for byte, with the
pinned library versions.

**Overlap with April.** 79.5% of the April top-5,000 is still in the top
5,000 (Spearman ρ 0.948 on the shared words); 62.4% of the 5,001–10,000
band (ρ 0.879). Most of the movement is deliberate — the April list counted
the same word several times, and this release does not.

### Why ranks moved

- **One word, one entry.** April's lemmatizer left inflected forms and
  spelling variants as separate entries: `nao` at rank 1004 beside `não`,
  `acha` beside `achar`, `chega` beside `chegar`, `exactamente` and
  `exatamente` counted apart. They are now merged, which raises the
  surviving headword and frees the rank the duplicate occupied.
- **A better lemmatizer.** simplemma alone was replaced by Stanza, reading
  each word in real sentences, with a dictionary check and simplemma as the
  fallback: 98.5% correct on a human-reviewed sample, against 90.4% for
  simplemma alone.
- **`ser` and `ir` separated** — *later found not to work; see
  Unreleased.* April assigned `foi`, `fomos`, `foram` wholesale to `ir`.
  They were split by the tagger: `ir` fell from 11.2M tokens to 9.5M, and
  `ser` rose from 20.6M to 22.9M.
- **Enclitics split.** April counted `dá-me` and `vou-me` as single words
  (its README said otherwise). They are now split into verb + pronoun, so
  `vai-te embora` no longer creates its own entries, and object pronouns
  (`me` rank 15, `te` 23, `lhe` 70) are counted in full.
- **Lemmatization conventions**, written down in
  [eval/conventions.md](eval/conventions.md): contractions are entries,
  nouns for people keep the feminine (`senhora`, `rapariga`), diminutives
  and comparatives stay separate, and headwords use the post-1990
  spelling.
- **`a` is now separate from `o`.** April folded the preposition/article
  `a` into `o`; `o` drops from 58.1M tokens to 29.9M, and `a` rises from
  rank 8281 to rank 3.
- **Proper nouns removed properly.** April kept `john` (rank 449), `mr`,
  `charlie`, `peter` and `joe` as vocabulary. Names are now removed by capitalization, with
  every dictionary word removed at 5,000+ occurrences reviewed by hand —
  `deus`, `sr` and `natal` stay.
- **Corrections to April's exclusions.** `cara` ("face") was excluded as
  Brazilian by mistake and is back (rank 340); the unaccented `voce`
  slipped past the BP filter and is now caught.
- **Junk removed.** The subtitle watermark `pt-subs rips`, the MWE `d c`,
  English plurals (`zombies`) and one- or two-letter fragments are gone.

### Also new

- A 400-word gold set, human-reviewed ([eval/lemma_gold.tsv](eval/lemma_gold.tsv)),
  and a quality gate that fails the build on suspected duplicate entries.
  The release passes it. Six missing-accent pairs below the folding
  threshold are accepted as known typo pairs and listed in the README.
- Reports in [reports/](reports/): comparison with April, the quality gate
  with every accent fold, and the lemmatizer comparison.
- Multi-word expressions: 302 in the top 10,000 (April: 290).
- Token count 636,214,452 (April: 623,920,347), because split enclitic
  pronouns now count as tokens of their own.

### Unchanged

The `pos_guess` column was still a rule-based heuristic, reconstructed
from the April list.

## 2026-04 — first version, unpublished (`v0-april-2026`)

Frequency list of the top 10,000 lemmas, with Anki decks, produced by a
pipeline whose scripts were later lost. Automatic output, not reviewed,
and never published.
Kept in [archive/out_april_2026/](archive/out_april_2026/) for comparison.

Known problems, all found while rebuilding: inflected forms and accent
variants counted as separate entries, `ser`/`ir` conflated, enclitic
clusters left unsplit despite the documentation, names (`john`, `charlie`)
and a subtitle watermark in the list, and `cara` excluded as Brazilian by
mistake.
