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

