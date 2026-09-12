# Lemmatizer backend comparison

Scored against `eval/lemma_gold.tsv` with sampled sentence context
(5 sentences per type, 395 of 400 gold surfaces covered).

> **Provisional.** 0 of 400 gold rows carry a human verdict, so the gold
> falls back to `claude_lemma`, a first-pass guess. The *direction* of this
> result is robust — spaCy's errors are independently verifiable non-words —
> but the magnitude is not. Fill in `jim_lemma` / `jim_verdict` to firm it up.

| backend | overall | ranks 1–1000 | 1001–10000 | 10001+ |
|---|---:|---:|---:|---:|
| `simplemma` 2.0.0 | **90.8%** | 90.0% | 91.3% | 90.8% |
| `spacy` pt_core_news_lg 3.8.0 | 83.8% | 82.3% | 83.3% | 85.8% |
| `vote` (simplemma + spacy) | 90.8% | 90.0% | 91.3% | 90.8% |

Error overlap: 23 simplemma-only, 51 spaCy-only, 14 shared.

## spaCy loses on verb morphology, and invents non-words

Verified directly, outside the pipeline wrapper:

| surface | spaCy lemma | correct |
|---|---|---|
| `cheguei` | `cheguei` (unchanged) | `chegar` |
| `Abram` | `Abram` (capital kept) | `abrir` |
| `agradeço` | `agradeçar` — not a word | `agradecer` |
| `combinámos` | `combinár` — not a word | `combinar` |
| `tua` | `tuo` — not a word | `teu` |
| `ao` | `a o` — contains a space | `ao` |

`combinámos` is the European spelling specifically (BP writes
`combinamos`), so the failure is worst exactly where this project cares.
The `a o` output would also break the `is_mwe` distinction, since a lemma
with a space is indistinguishable from a multi-word entry.

## simplemma loses by over-lemmatizing nouns into verbs

spaCy is right and simplemma wrong on this class:

| surface | simplemma | correct |
|---|---|---|
| `agulha` | `agulhar` | `agulha` (a needle) |
| `fenda` | `fender` | `fenda` (a crack) |
| `ferida` | `ferido` | `ferida` (a wound) |
| `cara` | `caro` | `cara` (a face) |
| `coisinha` | `coisa` | `coisinha` |

That `cara` row is the same word the original pipeline wrongly excluded as
Brazilian.

## The 2-member vote was meaningless

`vote` scored identically to `simplemma` to four figures — not a
coincidence. With two members every disagreement is a 1–1 tie, so the
tiebreak priority decides every case and the vote reduces to its first
backend. It needs three members. Stanza is being installed as the third.

## Conclusion so far

simplemma is the better single backend by 7 points. The two backends fail
in *different* directions — simplemma over-lemmatizes nouns, spaCy
under-lemmatizes verbs — which is exactly the case where a genuine
three-way majority should beat either alone.
