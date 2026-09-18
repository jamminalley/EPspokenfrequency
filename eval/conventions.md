# Lemmatization conventions

Policy decisions for what counts as one headword in this list. These are
choices, not facts; they are recorded here so the pipeline implements them
consistently (in `config.yaml`) and so readers know how this list differs
from *A Frequency Dictionary of Portuguese* (Davies & Preto-Bay, 2008).

General rule: verbs lemmatize to the infinitive, nouns to the singular,
adjectives to the masculine singular; adverbs, pronouns, interjections and
function words lemmatize to themselves.

## 1. Contractions are their own entries

`ao`, `aos`, `nas`, `desta`, `nesse`, `naquilo`, `do`, `da`, `pelo` … are
kept as headwords, not split into preposition + article/demonstrative.
Learners meet and produce them as single words. This is the main
deliberate departure from Davies, which splits them — it is why `do`,
`da`, `ao` appear "missing" from his list and near the top of this one.

## 2. Adjectives fold to the masculine; noun pairs keep the feminine

Adjectives and participles fold to the masculine singular (`branca` →
`branco`, `culpada` → `culpado`), since the feminine is pure agreement.
Nouns for people and animals keep the feminine as its own headword
(`senhora`, `namorada`, `tia`, `miúda`, `viúva`): a learner has to learn
these words, and hiding `senhora` (237k occurrences) inside `senhor` would
misrepresent what is actually said. This matches Davies, who lists
`senhora`, `filha`, `menina` separately. A feminine with its own distinct
meaning always stays (`música`, `sexta`, `ferida`). Forms that are both
adjective and noun (`inglesa`) are resolved per occurrence by the tagger.
The pair-by-pair decisions are in `eval/gender_pairs.tsv`.

## 3. Diminutives stay separate

`coisinha`, `patinho`, `dinheirinho` are their own headwords, not folded
into `coisa`, `pato`, `dinheiro`. How much spoken Portuguese leans on the
diminutive is itself something a learner needs to see.

## 4. Comparatives and superlatives are their own lemmas

`maior`, `melhor`, `pior`, `menor` are headwords, as in every dictionary
(and as in Davies). They are not folded into `grande`, `bom`, `mau`,
`pequeno`.

## 5. Spelling-reform variants merge under the post-1990 spelling

`acção`/`ação`, `óptimo`/`ótimo`, `direcção`/`direção`, `exactamente`/
`exatamente` are one headword each, spelled per the 1990 Orthographic
Agreement. The corpus mixes both eras, so merging is necessary to avoid
double counting; the README notes it. (This is orthography only — the
BP/EP *vocabulary* filter is a separate step.)

## Related rules that are not conventions but bugs to fix

- Missing-accent forms (`nao`, `numero`, `dificil`) fold into the accented
  form only when the unaccented string is not itself a valid word
  (`esta`/`está`, `e`/`é`, `da`/`dá` must never merge).
- Enclitic stems left by hyphen splitting (`apanhámo` from `apanhámo-lo`)
  are tokenizer artifacts, not lemmas.
- Ambiguous forms whose lemma depends on context (`fomos` → `ir` or `ser`)
  are resolved per-occurrence by a tagger over sampled context, not
  assigned wholesale to one lemma. In `eval/lemma_gold.tsv` such rows list
  both, `ir|ser`, and the scorer accepts either.
