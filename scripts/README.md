# scripts/

The pipeline that builds the frequency lists from `data/pt.txt.gz`.

The original scripts were lost. This is a reconstruction from the README's
Pipeline section, rebuilt in two stages:

- **Stage 1 — baseline.** Reproduce the original pipeline as documented,
  flaws included, and report how far the rebuild diverges from `out/`.
  Writes to `out_rebuild/`. Never touches `out/`.
- **Stage 2 — fixes.** Each correction sits behind its own config flag so
  its effect can be measured in isolation.

## Running it

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m spacy download pt_core_news_lg      # optional backend

./.venv/bin/python -m scripts.build --config config.yaml  # full build
./.venv/bin/python -m scripts.build --sample 2000000      # dev run, ~11s
```

`--sample N` reads only the first N lines and writes to
`out_rebuild_sampleN/`, so a dev run can never overwrite a full one.
Any config value can be overridden from the command line:

```bash
./.venv/bin/python -m scripts.build --stage 2 --set fixes.diacritic_folding=true
```

Pass 1 is cached under `.cache/`, keyed by a digest of the settings that
affect counting, so a rerun that only changes a later stage skips it.
Full build: ~3 minutes for pass 1, ~4 for pass 2, both cached afterwards.

Other entry points:

| Command | Does |
|---|---|
| `python -m scripts.counts --sample N --top 20` | Pass 1 only; prints the tokenizer fingerprint |
| `python -m scripts.eval_lemmas --backend simplemma --backend spacy` | Score backends against the gold set |
| `python -m scripts.fit_postag` | Regenerate `data/postag_rules.yaml` from `out/` |

## Layout

| Module | README step | Does |
|---|---|---|
| `build.py` | — | CLI entry point; runs every step, writes the reports |
| `config.py` | — | Loads and validates `config.yaml` |
| `corpus.py` | — | Streams the gzip; never decompresses to disk |
| `tokenizer.py` | 1 | Artifact stripping, lowercasing, enclitic splitting |
| `counts.py` | 1 | Parallel unigram pass + fingerprint + cache |
| `lemmas.py` | 2 | Pluggable backends, override table, dictionary gate |
| `bigrams.py` | 3 | Bigram counts, sampled contexts, casing, Dunning G² |
| `filters.py` | 4 | BP exclusions, proper-noun filter, diacritic folding |
| `postag.py` | 5 | `pos_guess` heuristic |
| `emit.py` | 5 | Ranking, per-million, TSV/CSV/Anki writers |
| `quality.py` | — | Suspect duplicate entries + the build gate |
| `compare.py` | — | `out_rebuild/` vs `out/` → `COMPARISON.md` |
| `eval_lemmas.py` | — | Backend accuracy against `eval/lemma_gold.tsv` |
| `fit_postag.py` | — | Derives the POS rule tables from `out/` |

## Things worth knowing

**The original README's step 1 is wrong.** It claims "enclitic-cluster
splitting", but the original did not split. Splitting overshoots the
published token total by 2.04%; not splitting matches it to 0.0014%. And
`out/` contains clusters that splitting would have destroyed: `vai-te
embora`, `vou-me embora`, `levem-no` (rank 3492), `hei-de`, `há-de`. The
baseline runs with `tokenizer.split_enclitics: false`. The splitter is
implemented and tested, behind `fixes.split_enclitics` for stage 2.

**Two rule sets are fitted to `out/`, not derived independently.**
`pos_guess` (via `fit_postag.py`, 97.5% self-agreement) and the closed-class
lookup are reverse-engineered from the original's own output, so their
agreement figures in `COMPARISON.md` are partly circular. They reproduce the
original's decisions including its mistakes — `aqui`→`pron`, `também`→`conj`,
`ano`→`adj`.

**The proper-noun heuristic could not be recovered** and is a reconstruction,
not a replica. A dictionary test alone cannot be what the original used: 14%
of what it dropped is *in* the PT dictionary (`jack`, `mary`), and 845
lemmas it kept are not — including leaked names (`charlie`, `joe`, `bob`)
and legitimate pre-1990 EP spellings (`óptimo`, `exactamente`, `direcção`).
The rebuild uses capitalization away from line start, which separates
cleanly (`john` 1.00, `maria` 1.00 vs `casa` 0.03, `muito` 0.001).

**simplemma has moved on.** The original needed ~200 hand-curated overrides
against a simplemma of its era; 2.0.0 already lemmatizes `foi`/`fomos` to
`ser`, so the original's headline `ser`/`ir` caveat does not reproduce. The
`chegas`→`chega` error does persist.

**Determinism.** Same corpus and config give byte-identical output. Chunks
are consumed in corpus order; ties break lexicographically; sampled contexts
are chosen by digest of `(seed, type, sentence)` rather than by an RNG, so
selection does not depend on worker count or scheduling.

## Stage 2

```bash
./.venv/bin/python -m scripts.build --all-fixes
```

Writes to `out_rebuild_stage2/` and compares against both `out/` and the
stage 1 baseline in `out_rebuild/`. Full run from cold: ~1 hour, nearly all
of it Stanza over the 63,253 frequent types; every pass is cached, so a
rerun after a config change takes about a minute.

What stage 2 does on top of the baseline:

- **Enclitic splitting**, with the verb restored (`fazê-lo` -> `fazer` +
  `lo`, `dar-lhe-ia` -> `daria` + `lhe`). Tokens 636.2M, types 838k.
- **Lemmatizer**: Stanza with a PT-dictionary gate, simplemma for the tail.
- **Conventions** from `eval/conventions.md`, with gender pairs taken from
  the advisor's `jim_decision` in `eval/gender_pairs.tsv`.
- **Per-occurrence splitting** of participles and fomos-type forms by
  Stanza POS over the sampled contexts: 1,388 surfaces split across lemmas.
- **Lemma closure** with plural folding (guards: plurale tantum and
  invariant nouns in config, no closed-class words, a real singular, and a
  frequency ratio).
- **Diacritic folding**: unaccented forms at >= 20x; wrong and Brazilian
  accents whenever the form is not a PT word. Every fold is in QUALITY.md.
- **Filters**: BP list (with `cara` restored), proper nouns by
  capitalization, English plurals to the foreign-word filter.

Published lemma map: 98.5% on the reviewed gold set.

**The gate fails on 18 suspects**, listed with reasons in QUALITY.md. 44
pairs whose members are both PT dictionary words are whitelisted by the
rule in `make_whitelist.py`.

## Not yet done

- 18 duplicate-entry suspects: 11 missing-accent typos below the 20x
  ratio, 2 feminine nouns the dictionary lacks (`cirurgiã`, `espiã`), and
  5 pairs of junk or distinct short tokens (`hã`/`ha`, `ã`, `nã`, `ra`,
  `sa`).
- The extended proper-noun filter drops capitalized common words:
  `deus`, `sr`, `sra`, `dr`, `natal`, `cristo`, `majestade`.
- `data/lemma_overrides.tsv` (the empirical override table) is empty.
