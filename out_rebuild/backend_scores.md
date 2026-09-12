# Lemmatizer backend comparison

Scored against `eval/lemma_gold.tsv` with sampled sentence context
(5 sentences per type, 395 of 400 gold surfaces covered).

> **Provisional.** 0 of 400 gold rows carry a human verdict, so the gold
> falls back to `claude_lemma`, a first-pass guess. The *direction* of this
> result is robust — spaCy's errors are independently verifiable non-words —
> but the magnitude is not. Fill in `jim_lemma` / `jim_verdict` to firm it up.

| backend | overall | ranks 1–1000 | 1001–10000 | 10001+ | errors |
|---|---:|---:|---:|---:|---:|
| `spacy` pt_core_news_lg 3.8.0 | 83.8% | 82.3% | 83.3% | 85.8% | 65 |
| `simplemma` 2.0.0 | 90.8% | 90.0% | 91.3% | 90.8% | 37 |
| `stanza` pt | 92.2% | **96.2%** | 92.7% | 87.5% | 31 |
| `vote` (all three) | **93.2%** | 93.1% | **94.0%** | **92.5%** | 27 |

The backends fail in genuinely different places: only **6** gold rows defeat
all three. Stanza rescues 30 simplemma errors; simplemma rescues 24 Stanza
errors. That independence is why the majority beats every member.

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

## But the vote loses on this project's own problem cases

Aggregate accuracy is not the whole story. On the specific errors the
original README documented, the vote is **worse than Stanza alone**:

| surface | simplemma | spaCy | stanza | vote | correct |
|---|---|---|---|---|---|
| `chegas` | `chega` ✗ | `chega` ✗ | `chegar` ✓ | `chega` ✗ | `chegar` |
| `voce` | `voce` ✗ | `voce` ✗ | `você` ✓ | `voce` ✗ | `você` |
| `nao` | `não` ✓ | `nao` ✗ | `nao` ✗ | `nao` ✗ | `não` |

`chegas` → `chega` is the exact error the original README calls out. Stanza
fixes it; the vote reintroduces it. The mechanism is simple: spaCy, the
weakest backend at 83.8%, carries equal weight, so whenever it echoes
simplemma's mistake it outvotes the strongest backend 2–1.

## Recommendation

Three options, in order of preference:

1. **Stanza alone.** Best single backend (92.2%, and 96.2% on the first
   1000 ranks where accuracy matters most), and it fixes the documented
   `chegas` error. Costs ~1s per 20 sentences — fine at type level.
2. **Weighted or Stanza-anchored vote** — require Stanza to be outvoted by
   *both* others rather than either. Keeps the aggregate gain without
   letting the weakest member reintroduce known errors.
3. **Plain 3-way vote.** Best aggregate (93.2%) but demonstrably
   reintroduces errors this project already knows about.

Dropping spaCy entirely is also defensible: it is last by 7 points, emits
non-words, and its one real contribution (noun over-lemmatization) is
already covered by Stanza.

All of these numbers rest on an unreviewed gold set. The `chegas` / `voce`
/ `nao` rows above do not — those are checkable by inspection.
