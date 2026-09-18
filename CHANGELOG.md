# Changelog

## 2026-09 — rebuilt pipeline, human-checked

The first release whose pipeline is in this repository. `python -m
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
- **`ser` and `ir` separated.** April assigned `foi`, `fomos`, `foram`
  wholesale to `ir`. They are now split by context: `ir` falls from 11.2M
  tokens to 9.5M, and `ser` rises from 20.6M to 22.9M.
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

File names, columns, the Anki note type, deck names and tags, so an
existing Anki import keeps working. The `pos_guess` column is still a
rule-based heuristic, reconstructed from the April list.

## 2026-04 — original release (`v0-april-2026`)

Frequency list of the top 10,000 lemmas, with Anki decks, produced by a
pipeline whose scripts were later lost. Automatic output, not reviewed.
Kept in [archive/out_april_2026/](archive/out_april_2026/) for comparison.

Known problems, all found while rebuilding: inflected forms and accent
variants counted as separate entries, `ser`/`ir` conflated, enclitic
clusters left unsplit despite the documentation, names (`john`, `charlie`)
and a subtitle watermark in the list, and `cara` excluded as Brazilian by
mistake.
