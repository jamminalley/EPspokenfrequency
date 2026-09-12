# scripts/

**This directory is empty on purpose — the pipeline scripts are being
rebuilt.**

The scripts that produced everything in `out/` were lost. The outputs
themselves are intact and are left exactly as the original run emitted
them; nothing in `out/` has been regenerated or edited since.

What survives is the description of what those scripts did: see the
[Pipeline section of the README](../README.md#pipeline), which records the
tokenization rules, the lemmatization and validation strategy, the MWE
thresholds (Dunning G² ≥ 2500, collocation share ≥ 5%, bigram floor of 100
occurrences), and the BP exclusion list. It is a specification, not a
reimplementation — re-running it will not reproduce `out/` byte for byte,
because the ~200-entry hand-curated lemma override table and the
proper-noun OOV heuristic were lost with the code.

`out/dropped_proper_nouns.txt` is a partial record of what that heuristic
removed, and may help in reconstructing it.

## Rebuilding

Expected shape, roughly one script per pipeline stage:

| Stage | Does |
|---|---|
| Count | Stream `data/pt.txt.gz`, tokenize, count unigram surface forms |
| Lemmatize | Map the type inventory to lemmas; apply overrides; validate against the PT dictionary |
| Bigrams | Second corpus pass; score MWE candidates by log-likelihood |
| Filter | Drop BP-leaning lemmas and proper-noun leaks |
| Emit | Rank, normalize per million, write TSV/CSV/Anki TSV |

Prerequisites:

- Python dependencies: `pip install -r ../requirements.txt`
- The corpus at `data/pt.txt.gz` — see [DATA_SOURCES.md](../DATA_SOURCES.md)

When rebuilding, write new output to a separate directory and diff against
`out/` rather than overwriting it. `out/` is the published artifact and the
only evidence of what the original pipeline did.
