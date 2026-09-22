# Changelog

## Unreleased — part of speech from the tagger, larger samples

**Overlap with the April list** is now 79.0% of band 1 (ρ 0.944) and
63.3% of band 2 (ρ 0.851). Against v0.9 the word lists barely change; what
changes is the POS column and, through POS splitting, which rows fill the
last places of each band.

- **A ready-to-import Anki package**, `out/EP_Spoken_Frequency.apkg`: one
  note type, two decks (1–5000, 5001–10000), a Portuguese → English card
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
  abstaining on 9%; none of the 19 adverbial *fora* lines reaches it.
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
