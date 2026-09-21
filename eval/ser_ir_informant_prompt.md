# Instructions for the expert informant: *ser* or *ir*?

You are acting as an expert informant on **European Portuguese** (Portugal), with a linguist's eye for morphology and a native speaker's ear for colloquial dialogue. You will be given a CSV of 100 short excerpts from film and TV subtitles. Each excerpt centres on one occurrence of a form that is shared by the verbs **ser** ("to be") and **ir** ("to go") in the pretérito perfeito and pluperfect: **foi, fui, fomos, foram, fora**.

Your task is to decide, for each row, which verb the form actually is *in that occurrence*.

## Why this matters

These five forms are homographs of two different verbs. A frequency list that counts them all as one verb over- or under-counts the other by hundreds of thousands of occurrences. Automatic taggers get this wrong systematically (they assign nearly everything to *ser*). Your labels are the gold standard against which an automatic rule will be scored, so accuracy matters more than speed, and an honest "unsure" is more useful than a confident guess.

## The CSV

Columns:

| column | meaning |
|---|---|
| `id` | row identifier — copy it unchanged |
| `form` | the word to judge: foi, fui, fomos, foram or fora |
| `corpus_line` | position in the source corpus (ignore) |
| `before_2`, `before_1` | the two subtitle lines spoken *before* the target line, in order |
| `sentence` | the target line, containing the form |
| `after_1`, `after_2` | the two subtitle lines spoken *after* it |
| `label` | **fill in**: `ser`, `ir`, or `other` |
| `confidence` | **fill in**: `high`, `medium`, or `low` |
| `reasoning` | **fill in**: one short phrase giving the decisive clue |

The context lines are consecutive subtitles from the same film. They are usually the same scene, but a scene break can fall anywhere, so weigh context as evidence, not proof. If the target sentence already settles the question, the context need not agree with it.

## Labels

**`ser`** — the form means *was / were* (or *had been* for `fora`). Typical signals: followed by an adjective, noun phrase, or past participle (*foi difícil*, *foi ele*, *fui expulso*, *foram os primeiros*); the passive (*foi morto por*); cleft and emphatic constructions (*foi o que eu disse*, *não fui eu*); the very common interjection-like *O que foi?* / *Foi?* / *Não foi?* ("What was that? / Was it? / Wasn't it?").

**`ir`** — the form means *went* (or *had gone*). Typical signals: a destination or direction (*fui a casa*, *foi ao médico*, *fomos para Lisboa*, *foram lá*, *foi até à porta*); *embora* (*foi-se embora*, *fomos embora*); a following infinitive expressing purpose (*fui buscar*, *fomos ver*, *foram comprar*); *ir* as auxiliary of the near future or of motion (*fomos andando*). Note *foi-se* is nearly always *ir* ("went away"), but *foi-se* can also be *ser* in *foi-se a ver* — decide from context.

**`other`** — the form is **not a verb at all** in this occurrence, or the excerpt cannot be read. The main case is **`fora` as the adverb "outside / out"**: *lá fora*, *cá fora*, *fora de casa*, *fora de questão*, *deitar fora*, *fora-da-lei*, *pôr fora*, *Fora!* ("Out!"). Also use `other` for a fragment so mangled or truncated that no reading is possible, or for a foreign-language line that slipped in.

Do **not** use `other` merely because a sentence is ambiguous between *ser* and *ir*; in that case choose the more likely reading and mark `confidence` as `low`.

## How to decide

1. Read the target sentence first and look for the structural signals above.
2. If it is not settled, read the four context lines. Ask: is the speaker describing a state or identity (*ser*) or a movement (*ir*)?
3. For `fora`, first check whether it is the adverb. If it is a verb, decide between *ser* and *ir* exactly as for *foi*.
4. Treat subtitle conventions as normal language: lines beginning with "- " are dialogue turns; ALL CAPS lines are on-screen text; ellipses mark pauses.
5. Never let the form itself bias you: *fui* is *ser* about as often as *ir* in dialogue, and *foi* leans *ser* but is *ir* a substantial minority of the time.

## Output

Return the **complete CSV**, all 100 rows, same columns and order, with `label`, `confidence` and `reasoning` filled in for every row. Keep the text of the other columns exactly as given (do not correct spelling or punctuation in the excerpts). Use lowercase for the labels. Do not add commentary outside the CSV; if you have a general observation about the sample, put it after the CSV under a heading "Notes".

## Worked examples

| excerpt | label | reasoning |
|---|---|---|
| *Não foi mais ninguém. / Foste tu.* | ser | cleft/identity: "it wasn't anyone else" |
| *Fomos buscar ajuda.* | ir | *ir* + infinitive of purpose |
| *Ele foi para o hospital ontem.* | ir | destination with *para* |
| *Fui despedido na segunda.* | ser | passive: *ser* + participle |
| *Está lá fora à espera.* | other | *fora* = adverb "outside" |
| *Foi-se embora sem dizer nada.* | ir | *ir-se embora* |
| *O que foi?* | ser | fixed expression "what was that / what's wrong" |
| *Foi assim que aconteceu.* | ser | cleft: "that's how it happened" |
