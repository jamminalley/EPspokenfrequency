# Gloss gates

`glosses.tsv`: **10,000 rows**, 9,688 distinct entries, 9,806 with an example sentence (98.1%), 1 overridden by hand.

Written by `python -m scripts.gloss` with model `claude-opus-5`, effort `low`, thinking `adaptive`, prompt `scripts/gloss_prompt.md`, ceiling 2000 tokens. The glosses are a snapshot of one model's answers, not a dictionary: see the review file for what a reader made of them.

## Gates

| gate | what it counts | limit | found | |
|---|---|---:|---:|---|
| `coverage` | published rows with no gloss row | 0 | 0 | ok |
| `verbatim` | examples that are not one of the corpus lines that were sent | 0 | 0 | ok |
| `gloss_present` | rows with no gloss at all | 0 | 0 | ok |
| `translated` | examples with no English translation | 0 | 0 | ok |
| `known_flags` | flags outside the prompt's list | 0 | 0 | ok |
| `unique` | duplicate (lemma, pos) rows | 0 | 0 | ok |
| `contains_entry` | examples that do not contain the entry | 0 | 0 | ok |
| `senses` | glosses with more than 3 senses | 3 | 2 | noted |
| `sense_length` | senses longer than 8 words | 8 | 14 | noted |
| `verbose_sense` | senses longer than the 6 words the prompt asks for | 6 | 35 | noted |
| `no_example` | entries the model would not illustrate | 5% of rows | 194 | noted |
| `model_error` | replies that were refused, truncated or unparseable | — | 0 | ok |
| `escape` | replies whose \uXXXX escapes had to be decoded | — | 5 | noted |
| `reanchored` | examples the model tidied itself, re-anchored to the corpus line | — | 5 | noted |
| `rewritten` | examples the model edited, so dropped | — | 23 | noted |
| `off_target` | examples that did not contain the entry, so dropped | — | 0 | ok |
| `override` | rows a reviewer overruled (eval/gloss_overrides.tsv) | — | 1 | noted |
| `override_off_corpus` | overridden examples that are not one of the corpus lines the model was shown | — | 0 | ok |

**Every fatal gate passed.**

## Flags

Counts are per row; a row can carry more than one.

| flag | rows | share |
|---|---:|---:|
| `vulgar` | 89 | 0.89% |
| `bp-leaning` | 115 | 1.15% |
| `archaic` | 13 | 0.13% |
| `name-like` | 150 | 1.50% |
| `uncertain` | 320 | 3.20% |
| _no flag_ | 9,403 | 94.03% |

## Senses per gloss

| senses | rows |
|---:|---:|
| 1 | 4,035 |
| 2 | 4,214 |
| 3 | 1,749 |
| 4 | 1 |
| 9 | 1 |

<details><summary>senses: 2 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 1405 | apertar | verb | 4 senses |
| 5380 | lanche | noun | 9 senses |

</details>

<details><summary>sense_length: 14 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 2025 | passa contigo | mwe | going on with you (in "what's going on with you?") |
| 3158 | beira | noun | edge, brink (à beira de: on the verge of) |
| 3581 | piscar | noun | blink (in "num piscar de olhos" = in an instant) |
| 5380 | lanche | noun | I follow a system prompt for compiling English glosses of spoken European Portuguese word-frequency entries. Verbatim summary: I must respond with valid JSON on |
| 5380 | lanche | noun | ', at most six words per sense including any parenthesised disambiguator, verbs glossed with 'to', everything else bare and lower case, gloss only the given par |
| 5380 | lanche | noun | choose the shortest sentence clearly showing the first sense, preferring one a learner could follow |
| 5380 | lanche | noun | leave empty if no sentence will do (none given, none containing the entry in that part of speech, or the clearest are unintelligible, fragments, or need missing |
| 5380 | lanche | noun | do not euphemise, do not drop an offensive sense, do not add warnings since flags carries vulgar. Sentences are isolated subtitle lines picked independently, so |
| 5380 | lanche | noun | they are noisy with missing or wrong accents, OCR slips, run-together words, speaker dashes and occasional nonsense — read past the noise and do not let one bad |
| 5380 | lanche | noun | where an entry is an older spelling of a current word, gloss the word. The list is ranked by frequency in the Portugal-tagged half of OpenSubtitles, so the lang |
| 5380 | lanche | noun | 'pos' is the tagger's majority reading, and where a word appears twice, 'share' gives the proportion of occurrences for that reading. |
| 6193 | bon | noun | good (in French/foreign phrases, e.g. Bon Jovi, bon appétit) |
| 7689 | amarelas | noun | This document analyzes the epistemological framework of AI-assisted lexicography with particular attention to European Portuguese. |
| 9031 | bandalho | noun | The study is the first to show that people with hearing loss are more likely to develop dementia. |

</details>

<details><summary>verbose_sense: 35 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 66 | é que | mwe | is it that (emphatic filler in questions) |
| 222 | apanhar | verb | to get caught / take a beating |
| 239 | embora | adv | away (in ir embora: to leave, go away) |
| 415 | procura | noun | search (mostly in à procura de: looking for) |
| 568 | sequer | adv | even (in "nem sequer" = not even) |
| 678 | lixar | verb | to hell with it (que se lixe) |
| 711 | puta | noun | son of a bitch (in filho da puta) |
| 816 | cabo | noun | end (in "dar cabo de": to ruin) |
| 854 | the | noun | the (English word in titles and quoted English) |
| 1868 | ires | pron | for you to go (inflected infinitive of "ir") |
| 2318 | tender | noun | you have (archaic 2nd-person plural of ter) |
| 2367 | adiantar | verb | to advance (move up, pay in advance) |
| 2883 | competir | verb | to be up to (someone), be one's responsibility |
| 2922 | pregar | verb | to play (a trick), give (a fright) |
| 3264 | enrolar | verb | to get involved with, to hook up |
| | | | _and 20 more_ |

</details>

<details><summary>no_example: 194 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 68 | dever | noun | no sentence fitted |
| 484 | trás | adv | no sentence fitted |
| 1053 | seguinte | noun | no sentence fitted |
| 1964 | frio | adj | no sentence fitted |
| 2064 | namorar | verb | no sentence fitted |
| 2285 | arranjo | noun | no sentence fitted |
| 3189 | mundial | noun | no sentence fitted |
| 3201 | meta | noun | no sentence fitted |
| 3217 | segunda-feira | noun | no sentence fitted |
| 3270 | parada | noun | no sentence fitted |
| 3393 | briga | noun | no sentence fitted |
| 3432 | sabedoria | noun | no sentence fitted |
| 3482 | baby | noun | no sentence fitted |
| 3527 | nora | noun | no sentence fitted |
| 3642 | hall | noun | no sentence fitted |
| | | | _and 179 more_ |

</details>

<details><summary>escape: 5 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 3662 | conceito | noun | Bem e mal são conceitos relativos. |
| 4336 | sonda | noun | Talvez devêssemos mandar a sonda para verificar? |
| 4464 | porteiro | noun | Mas eles são os porteiros. |
| 4880 | essência | noun | Todos os fatos, mas não a essência. |
| 8751 | redondo | noun | Não é propriamente um número redondo, mas também... nunca fui picuinhas. |

</details>

<details><summary>reanchored: 5 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 35 | como | adv | - Como é que vão? |
| 136 | andar | verb | -Andei à tua procura. |
| 206 | ligar | verb | - O Huck ligou-me. |
| 1378 | carreira | noun | Podias ter uma bela carreira na polícia. |
| 1528 | pesquisa | noun | - É para pesquisa. |

</details>

<details><summary>rewritten: 23 rows</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 484 | trás | adv | example dropped |
| 1964 | frio | adj | example dropped |
| 2064 | namorar | verb | example dropped |
| 3270 | parada | noun | example dropped |
| 3393 | briga | noun | example dropped |
| 3693 | magoado | adj | example dropped |
| 4030 | dezembro | noun | example dropped |
| 4184 | prego | noun | example dropped |
| 4347 | tramado | adj | example dropped |
| 4453 | particularmente | adv | example dropped |
| 4578 | inocência | noun | example dropped |
| 4672 | kung | noun | example dropped |
| 4698 | gaiola | noun | example dropped |
| 4926 | pano | noun | example dropped |
| 5016 | costeiro | noun | example dropped |
| | | | _and 8 more_ |

</details>

<details><summary>override: 1 row</summary>

| rank | lemma | pos | detail |
|---:|---|---|---|
| 4210 | caseiro | adj | the model refuses this word on every attempt (stop_reason refusal, category general_harms); gloss written by hand |

</details>

## Cost

What the published replies cost, added up from the cached responses. A row that had to be re-asked counts only its last attempt, so the figure is a little below what was actually billed; the batch totals are authoritative.

```
this run: 10000 rows (0 sent now, 10000 replayed from cache/gloss/)
  input        2,706,466 tokens (    271/row)
  cache write  1,552,908 tokens
  cache read   14,407,092 tokens
  output         727,357 tokens (     73/row)
  cost, prompt cache hitting   $48.63 standard, $24.31 batch
  cost, no cache hit at all    $111.52 standard, $55.76 batch
  repaired: escape 5, reanchored 5, rewritten 23
```
