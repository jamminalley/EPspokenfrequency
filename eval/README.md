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
