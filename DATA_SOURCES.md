# Data sources

Everything in `out/` is derived from a single input file: the
Portugal-tagged monolingual portion of the **OpenSubtitles 2018** corpus,
distributed by the [OPUS](https://opus.nlpl.eu/) project.

No other corpus, word list, or dictionary contributed frequency counts.
`simplemma` and `pyspellchecker` were used as lemmatization and validation
resources only (see [README.md](README.md#pipeline)).

## The corpus

| | |
|---|---|
| Corpus | OpenSubtitles, OPUS release v2018 |
| Portion | `pt` — the Portugal-tagged monolingual side (OPUS uses `pt_br` for Brazilian Portuguese) |
| File | `pt.txt.gz` |
| Size | 1,097,407,882 bytes (~1.1 GB compressed) |
| SHA-256 | `c8248f19a117a002df52275ce64371098e8e53cc953b654e5eb1cd0408be93e3` |
| Published | 2018-11-17 |
| Homepage | https://opus.nlpl.eu/OpenSubtitles/corpus/version/OpenSubtitles |

As measured by this project's first pass, that file contains 118,469,705
lines, 623,920,347 tokens, and 955,446 unique surface types.

The `pt` tag is the corpus's own metadata, not a verified judgment about
each subtitle file. It is a strong signal of European Portuguese, but it
is not a guarantee — see the Limitations section of the README.

## How to download it

The corpus is **not** in this repository. `data/` is gitignored precisely
so that 1.1 GB of subtitle text never lands in git history. To re-run the
pipeline, fetch it yourself:

```bash
mkdir -p data
curl -L -o data/pt.txt.gz \
  https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/mono/pt.txt.gz
```

Verify you got the same bytes this project used:

```bash
shasum -a 256 data/pt.txt.gz
# expected:
# c8248f19a117a002df52275ce64371098e8e53cc953b654e5eb1cd0408be93e3
```

Leave it gzipped — the pipeline streams it and never needs 4+ GB of
uncompressed text on disk. Expect the download to take a while; it is
served from CSC's object storage in Finland.

If that direct link ever moves, the file is reachable from the OPUS
OpenSubtitles page above: choose release **v2018**, then the **mono**
(monolingual plain text) download for language **pt**.

## Citation

If you use this frequency list in anything you publish, please cite the
underlying corpus — that is the work this project stands on.

**The corpus:**

> Lison, P., & Tiedemann, J. (2016). OpenSubtitles2016: Extracting Large
> Parallel Corpora from Movie and TV Subtitles. In *Proceedings of the
> 10th International Conference on Language Resources and Evaluation
> (LREC 2016)*. Portorož, Slovenia.

```bibtex
@inproceedings{lison2016opensubtitles,
  title     = {{OpenSubtitles2016}: Extracting Large Parallel Corpora
               from Movie and {TV} Subtitles},
  author    = {Lison, Pierre and Tiedemann, J{\"o}rg},
  booktitle = {Proceedings of the 10th International Conference on
               Language Resources and Evaluation (LREC 2016)},
  year      = {2016},
  address   = {Portoro{\v{z}}, Slovenia}
}
```

**The OPUS collection that distributes it:**

> Tiedemann, J. (2012). Parallel Data, Tools and Interfaces in OPUS. In
> *Proceedings of the 8th International Conference on Language Resources
> and Evaluation (LREC 2012)*. Istanbul, Turkey.

```bibtex
@inproceedings{tiedemann2012parallel,
  title     = {Parallel Data, Tools and Interfaces in {OPUS}},
  author    = {Tiedemann, J{\"o}rg},
  booktitle = {Proceedings of the 8th International Conference on
               Language Resources and Evaluation (LREC 2012)},
  year      = {2012},
  address   = {Istanbul, Turkey}
}
```

## Upstream terms

The subtitles themselves are community-contributed material from
[opensubtitles.org](https://www.opensubtitles.org/), redistributed by OPUS
for research use. OPUS asks that you cite the papers above. This project's
derived counts are released under CC BY-SA 4.0 (see [LICENSE](LICENSE)),
which covers this dataset only and grants no rights in the upstream
subtitle text.

## Tools used

| Tool | Role |
|---|---|
| [`simplemma`](https://github.com/adbar/simplemma) | Lookup-based lemmatization of the type inventory |
| [`pyspellchecker`](https://github.com/barrust/pyspellchecker) | PT dictionary used to validate/reject proposed lemmas |
| [`pandas`](https://pandas.pydata.org/) | Table assembly and output formatting |
| [`regex`](https://github.com/mrabarnett/mrab-regex) | Unicode-property-aware Portuguese tokenization |

Pinned in [requirements.txt](requirements.txt).
