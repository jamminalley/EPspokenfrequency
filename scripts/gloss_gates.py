"""The gate the gloss run has to pass, and reports/gloss_gates.md.

`scripts/quality.py` gates the lists; this gates the glosses. The checks
are all things a machine can settle, and they are deliberately about
provenance and shape rather than about meaning: whether every published row
got a gloss, whether every example sentence is really one of the corpus
lines that were sent and really contains the entry, whether the reply kept
to the form the prompt asked for. Whether a gloss is *right* is a question
for a reader, which is what eval/gloss_review.tsv is for.

Two of the checks fail the run. The rest are counted and reported: an
entry the model declined to illustrate is a legitimate answer, not a bug,
and the useful thing is to know how often it happens.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Sequence

FLAGS = ("vulgar", "bp-leaning", "archaic", "name-like", "uncertain")


class Gate:
    """One check: what it looks for, what it found, and whether that fails."""

    def __init__(self, name: str, what: str, fatal: bool = False,
                 limit: str = "0") -> None:
        self.name, self.what, self.fatal, self.limit = name, what, fatal, limit
        self.hits: list[tuple[Any, str]] = []

    def hit(self, row: dict[str, Any], detail: str = "") -> None:
        self.hits.append((row, detail))

    @property
    def n(self) -> int:
        return len(self.hits)

    @property
    def failed(self) -> bool:
        return self.fatal and bool(self.hits)


def _surfaces_of(row: dict[str, Any], published: dict[str, list[str]]) -> set[str]:
    return set(published.get(row["lemma"], ())) | {row["lemma"]}


def run(results: Sequence[dict[str, Any]], rows: Sequence[dict[str, Any]],
        cfg: dict[str, Any], tokenize, surfaces_of) -> dict[str, Any]:
    """Check a finished gloss run. ``surfaces_of(row)`` gives the inflected
    forms an entry is published from, so an example can be checked to contain
    the entry and not merely to have come back from the right request."""
    g = cfg["gloss"]["gates"]
    gates = {
        "coverage": Gate("coverage", "published rows with no gloss row", fatal=True),
        "verbatim": Gate("verbatim", "examples that are not one of the corpus lines "
                                    "that were sent", fatal=True),
        "gloss_present": Gate("gloss_present", "rows with an empty gloss", fatal=True),
        "translated": Gate("translated", "examples with no English translation",
                           fatal=True),
        "known_flags": Gate("known_flags", "flags outside the prompt's list", fatal=True),
        "unique": Gate("unique", "duplicate (lemma, pos) rows", fatal=True),
        "contains_entry": Gate("contains_entry",
                               "examples that do not contain the entry", fatal=True),
        "senses": Gate("senses", f"glosses with more than {g['max_senses']} senses",
                       limit=str(g["max_senses"])),
        "sense_length": Gate("sense_length",
                             f"senses longer than {g['max_words_per_sense']} words",
                             limit=str(g["max_words_per_sense"])),
        "verbose_sense": Gate("verbose_sense", "senses longer than the 6 words the "
                                               "prompt asks for", limit="6"),
        "no_example": Gate("no_example", "entries the model would not illustrate",
                           limit=f"{g['max_missing_example_share']:.0%} of rows"),
        "model_error": Gate("model_error", "replies that were refused, truncated or "
                                           "unparseable"),
    }

    by_key = {}
    for r in results:
        key = (r["lemma"], r["pos"])
        if key in by_key:
            gates["unique"].hit(r, "second row for this lemma and pos")
        by_key[key] = r
    for row in rows:
        if (row["lemma"], row["pos"]) not in by_key:
            gates["coverage"].hit(row, "no gloss")

    for r in results:
        if r.get("problem"):
            target = "verbatim" if "not one of the sentences" in r["problem"] else None
            if r["problem"].startswith(("refusal", "truncated", "unparseable")):
                target = "model_error"
            gates[target or "model_error"].hit(r, r["problem"])
        if not r["gloss"].strip():
            gates["gloss_present"].hit(r, "empty")
        senses = [s.strip() for s in r["gloss"].split(";") if s.strip()]
        if len(senses) > g["max_senses"]:
            gates["senses"].hit(r, f"{len(senses)} senses")
        for s in senses:
            if len(s.split()) > g["max_words_per_sense"]:
                gates["sense_length"].hit(r, s)
            elif len(s.split()) > 6:
                gates["verbose_sense"].hit(r, s)
        bad = [f for f in r["flags"] if f not in FLAGS]
        if bad:
            gates["known_flags"].hit(r, ", ".join(bad))

        ex = r["example_pt"]
        if not ex:
            gates["no_example"].hit(r, "no sentence fitted"
                                    if r["sentences"] else "no sentence available")
            continue
        if ex not in r["sentences"]:
            gates["verbatim"].hit(r, ex)
        if not r["example_en"].strip():
            gates["translated"].hit(r, ex)
        toks = tokenize(ex)
        if r["is_mwe"]:
            parts = r["lemma"].split()
            ok = any(toks[i:i + len(parts)] == parts
                     for i in range(len(toks) - len(parts) + 1))
        else:
            ok = bool(set(toks) & surfaces_of(r))
        if not ok:
            gates["contains_entry"].hit(r, ex)

    # An entry with nothing to illustrate it is allowed, up to a share.
    share = gates["no_example"].n / max(len(results), 1)
    gates["no_example"].fatal = share > g["max_missing_example_share"]

    flags = Counter(f for r in results for f in r["flags"])
    unflagged = sum(1 for r in results if not r["flags"])
    return {"gates": gates, "flags": flags, "unflagged": unflagged,
            "rows": len(results),
            "entries": len({r["lemma"] for r in results}),
            "with_example": sum(1 for r in results if r["example_pt"]),
            "no_example_share": share,
            "senses": Counter(len([s for s in r["gloss"].split(";") if s.strip()])
                           for r in results),
            "failed": [k for k, v in gates.items() if v.failed]}


def render(res: dict[str, Any], cfg: dict[str, Any], usage_lines: Iterable[str]) -> str:
    g = cfg["gloss"]
    gates = res["gates"]
    out = [
        "# Gloss gates",
        "",
        f"`{g['out_file']}`: **{res['rows']:,} rows**, {res['entries']:,} distinct "
        f"entries, {res['with_example']:,} with an example sentence "
        f"({res['with_example'] / max(res['rows'], 1):.1%}).",
        "",
        f"Written by `python -m scripts.gloss --collect` with model "
        f"`{g['model']}`, effort `{g['effort']}`, thinking `{g['thinking']}`, "
        f"prompt `{g['prompt_path']}`. The glosses are a snapshot of one "
        f"model's answers, not a dictionary: see the review file for what a "
        f"reader made of them.",
        "",
        "## Gates",
        "",
        "| gate | what it counts | limit | found | |",
        "|---|---|---:|---:|---|",
    ]
    for gate in gates.values():
        mark = "**FAIL**" if gate.failed else ("ok" if not gate.n else "noted")
        out.append(f"| `{gate.name}` | {gate.what} | {gate.limit if gate.fatal or gate.limit != '0' else '—'} "
                   f"| {gate.n:,} | {mark} |")
    out += ["",
            ("**Every fatal gate passed.**" if not res["failed"]
             else "**Failed: " + ", ".join(f"`{k}`" for k in res["failed"]) + "**"),
            ""]

    out += ["## Flags", "",
            "Counts are per row; a row can carry more than one.", "",
            "| flag | rows | share |", "|---|---:|---:|"]
    for flag in FLAGS:
        n = res["flags"].get(flag, 0)
        out.append(f"| `{flag}` | {n:,} | {n / max(res['rows'], 1):.2%} |")
    out += [f"| _no flag_ | {res['unflagged']:,} | "
            f"{res['unflagged'] / max(res['rows'], 1):.2%} |", ""]

    out += ["## Senses per gloss", "", "| senses | rows |", "|---:|---:|"]
    for n in sorted(res["senses"]):
        out.append(f"| {n} | {res['senses'][n]:,} |")
    out.append("")

    for gate in gates.values():
        if not gate.n:
            continue
        shown = gate.hits[:15]
        out += [f"<details><summary>{gate.name}: {gate.n:,} "
                f"{'row' if gate.n == 1 else 'rows'}</summary>", "",
                "| rank | lemma | pos | detail |", "|---:|---|---|---|"]
        for row, detail in shown:
            out.append(f"| {row['rank']} | {row['lemma']} | {row['pos']} | "
                       f"{detail.replace('|', '\\|')[:160]} |")
        if gate.n > len(shown):
            out.append(f"| | | | _and {gate.n - len(shown):,} more_ |")
        out += ["", "</details>", ""]

    out += ["## Cost", "", "```"] + list(usage_lines) + ["```", ""]
    return "\n".join(out)
