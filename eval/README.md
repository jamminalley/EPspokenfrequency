# eval/

`lemma_gold.tsv` — hand-checked lemmatization gold set.

How it was sampled: surface forms counted over the first 40,000,000 lines of
`data/pt.txt.gz` (213M tokens, 439k types) with a simple lowercase regex
tokenizer that splits on hyphens. 400 forms drawn with a fixed seed (20260912),
stratified by rank: 130 from ranks 1–1000, 150 from 1001–10000, 120 from
10001–40000. Raw sample in `lemma_gold_sample_source.tsv`.

Columns: `claude_lemma` is a first-pass guess; `category` flags proper nouns,
foreign words, contractions, typos, tokenizer artifacts and convention
decisions; `note` explains the tricky ones. `jim_lemma` / `jim_verdict`
(ok / fix / drop) are the human review — the gold standard is whatever is in
`jim_lemma` when non-empty, else `claude_lemma`, for rows whose verdict is not
`drop`.

## `ser_ir_sample.tsv` — for human labeling

100 corpus lines containing `foi`, `fui`, `fomos`, `foram` or `fora`, 20
per form, drawn uniformly at random from the whole corpus (reservoir
sampling, seed 20260912; regenerate with `python -m scripts.serir`, which
refuses to overwrite once labels are entered). It exists to test a
next-word rule for telling *ser* from *ir*, because the tagger cannot: it
assigns these forms to *ser* almost regardless of context.

Columns: `form`, `sentence`, `rule_guess` (the rule's answer: `ser`, `ir`,
or `?` where it abstains), and `human_label`, blank, for:

- `ser` — "was" (*foi feito*, *fui eu*)
- `ir` — "went" (*fui ao médico*, *fomos buscar ajuda*)
- `other` — not a form of either verb. Most `fora` rows are the adverb
  "outside" (*lá fora*, *fora de questão*), and the rule labels them
  anyway, so these rows show where it misfires.

If a line contains the form more than once, label the first occurrence:
that is the one the rule reads. Subtitle text repeats, so the same line
can be drawn twice. The rule is not applied to the published counts until
this sample has been scored.
