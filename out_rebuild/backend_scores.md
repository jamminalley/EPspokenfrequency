# Lemmatizer backend comparison

Scored against the human-reviewed gold set `eval/lemma_gold.tsv`: 332 scored rows, 68 rows marked `drop` excluded. A gold value with `|` accepts either alternative (`fomos` → `ir|ser`). All backends see the same sampled sentence context (5 per type).

Each backend is scored two ways. **With conventions** passes its output through the convention layer from `eval/conventions.md` — contractions, gender pairs, diminutives, comparatives, spelling reform — which is what the pipeline publishes, and is the column that matters. **Raw** is the backend alone.

| backend | with conventions | raw | ranks 1–1000 | 1001–10000 | 10001+ | errors |
|---|---:|---:|---:|---:|---:|---:|
| `stanza+gate` — **pipeline backend** | **94.9%** | 94.6% | 97.6% | 95.9% | 89.4% | 17 |
| `stanza` | **91.9%** | 91.6% | 97.6% | 91.8% | 83.5% | 27 |
| `vote` (simplemma + stanza + spacy) | **92.2%** | 91.9% | 96.8% | 92.6% | 84.7% | 26 |
| `simplemma` 2.0.0 | **92.2%** | 90.4% | 94.4% | 91.8% | 89.4% | 26 |
| `spacy` pt_core_news_lg — *dropped* | **83.1%** | 81.0% | 88.0% | 80.3% | 80.0% | 56 |

Band columns are with conventions. Ranks are from the 40M-line sample the gold set was drawn from.

## Conclusions

- **stanza+gate is the best backend by about 3 points**, and best or tied-best in every band. The gate — fall back to simplemma when Stanza's lemma is not a dictionary word — fixes exactly the errors Stanza makes by inventing non-words (`agradeço` → *agradeçar*, `comprei` → *comprir*).
- **The conventions help simplemma most** (90.4% → 92.2%), because simplemma folds forms the conventions keep apart: `aos`, `nas`, `nos` (contractions), `coisinha` (diminutive), `música`, `cara`, `ferida` (feminines with their own meaning). Stanza already keeps those apart, so the layer barely changes it.
- **spaCy is last by about 12 points** and has been dropped. It fails on European Portuguese verb morphology — `combinámos` → *combinár*, `cheguei` unlemmatized — and emits lemmas containing spaces (`ao` → `a o`).
- **The vote does not beat stanza+gate.** A majority including the weakest backend lets it outvote the strongest one.

## The 17 remaining stanza+gate errors

| surface | gold | pipeline | kind |
|---|---|---|---|
| `lo` | `o` | `ele` | enclitic pronoun from the gold's hyphen-splitting tokenizer; pipeline does not split |
| `procura` | `procurar` | `procura` | stanza picks the noun *procura* over *procurar* |
| `vejam` | `ver` | `vir` | stanza picks *vir* for a form of *ver* |
| `estados` | `estado` | `estados` | plural not folded |
| `mentes` | `mentir` | `mente` | stanza picks the noun *mente* over *mentir* |
| `numero` | `número` | `numero` | **gold conflicts with the no-merge rule** (see below) |
| `detector` | `detector` | `detetor` | **gold conflicts with convention 5** (see below) |
| `arruinado` | `arruinar` | `arruinado` | participle kept as adjective (gold: verb) |
| `quadrados` | `quadrado` | `quadrados` | plural not folded |
| `educados` | `educado` | `educar` | participle read as verb (gold: adjective) |
| `honrados` | `honrado` | `honrar` | participle read as verb (gold: adjective) |
| `sacas` | `sacar` | `saca` | stanza picks the noun *saca* over *sacar* |
| `mascarada` | `mascarado` | `mascarar` | participle read as verb (gold: adjective) |
| `bodes` | `bode` | `bodes` | plural not folded |
| `cientifica` | `científico` | `cientifico` | missing accent + gender; `cientifico` is not reachable by folding |
| `corrompido` | `corromper` | `corrompido` | participle kept as adjective (gold: verb) |
| `sâo` | `são` | `ser` | wrong diacritic (â for ã); not a missing accent, so folding cannot reach it |

Five of the 17 are participles, and the gold is not uniform about them: `arruinado` and `corrompido` go to the verb, while `educados`, `honrados` and `mascarada` go to the adjective. That is a legitimate context-dependent split, but no type-level rule can match both halves. Worth a convention of its own.

## Two gold rows that contradict eval/conventions.md

These count as pipeline errors above, but the pipeline is following the written convention in both. One side or the other needs to change.

- **`detector`** — the gold keeps `detector`, but convention 5 merges pre-1990 spellings under the post-1990 one, and the post-1990 European spelling is `detetor`. Either the gold row or the convention needs an exception.
- **`numero`** — the gold folds it into `número`, and conventions.md even lists `numero` as an example of a missing-accent form to fold. But the same rule says to fold *only when the unaccented string is not itself a valid word*, and `numero` is one: *eu numero*, "I number". The rule and its example disagree.
