# ser / ir rule: score against the hand-checked sample

`eval/ser_ir_sample.tsv`: 100 random corpus lines, 20 per form. Gold labels were
proposed by an LLM acting as a European Portuguese informant and checked
independently by hand, with disputed rows reviewed (see eval/README.md).

The rule runs only on occurrences Stanza tags VERB or AUX; anything else
is `other` and never reaches it. Accuracy is on the verb rows the rule
decided; abstentions fall back, in the counts, to the form's own ser/ir
ratio among decided occurrences.

| form | verb rows | decided | correct | accuracy | abstained | abstention rate | gated out | `other` rows | `other` given a verb |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `foi` | 20 | 17 | 16 | 94.1% | 3 | 15% | 0 | 0 | 0 |
| `fui` | 20 | 19 | 19 | 100.0% | 1 | 5% | 0 | 0 | 0 |
| `fomos` | 20 | 19 | 18 | 94.7% | 1 | 5% | 0 | 0 | 0 |
| `foram` | 20 | 18 | 17 | 94.4% | 2 | 10% | 0 | 0 | 0 |
| `fora` | 1 | 1 | 1 | 100.0% | 0 | 0% | 0 | 19 | 0 |
| **all** | 81 | 74 | 71 | 95.9% | 7 | 9% | 0 | 19 | 0 |

**Accuracy on decided verb rows: 95.9%** (71/74); threshold for applying the rule to the counts: 95%.

## Errors

| form | sentence | gold | rule |
|---|---|---|---|
| `foi` | Uma vez tentei que ele fizesse de freira numa cadeira de rodas, mas ele não foi nessa. | ir | ser |
| `fomos` | Nós jogamos, fomos a uma daquelas capelas de casamento baratas. | ir | ser |
| `foram` | Então, sempre foram? | ir | ser |


## Held-out test set: `eval/ser_ir_sample2.tsv`

100 further corpus lines drawn the same way, 20 per form; 99
carry a label. Labeled by a native-speaker Portuguese teacher after
the rule was finished: these labels were never used to shape it,
so this is the honest estimate of how the rule behaves on new text.

| form | verb rows | decided | correct | accuracy | abstained | abstention rate | gated out | `outro` rows | `outro` given a verb |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `foi` | 20 | 17 | 17 | 100.0% | 3 | 15% | 0 | 0 | 0 |
| `fui` | 19 | 17 | 16 | 94.1% | 2 | 11% | 0 | 0 | 0 |
| `fomos` | 20 | 20 | 19 | 95.0% | 0 | 0% | 0 | 0 | 0 |
| `foram` | 20 | 19 | 16 | 84.2% | 1 | 5% | 0 | 0 | 0 |
| `fora` | 0 | 0 | 0 | – | 0 | – | 0 | 20 | 1 |
| **all** | 79 | 73 | 68 | 93.2% | 6 | 8% | 0 | 20 | 1 |

**Accuracy on decided verb rows: 93.2%** (68/73), abstaining on 6 of 79. The rule is not tuned against this set.

<details><summary>Errors</summary>

| form | sentence | tutor | rule |
|---|---|---|---|
| `foram` | Já foram todos? | ir | ser |
| `foram` | O que me recorda aquela vez em que um inglês, um irlandês, um escocês, um vigário, um rabino e um padre foram todos ao mesmo bar. | ir | ser |
| `fui` | Tu sabes, Eu fui da Ford à cinco meses atrás. | ir | ser |
| `fomos` | - Pai, já fomos. | ir | ser |
| `foram` | Foram á procura dele em tua casa! | ir | ser |

</details>

