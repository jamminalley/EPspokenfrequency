"""Score the ser/ir rule against both labeled samples, into one report.

`scripts/serir.py` is imported and used exactly as it stands: this module
never edits the rule, its config lists, or the fingerprint that authorises
the rule for the counts (`reports/serir_scores.json`). Running this is the
way to regenerate `reports/serir_scores.md`; `python -m scripts.serir
--score` alone rewrites that file with the development table only.

  sample 1  eval/ser_ir_sample.tsv   development set, `human_label`
            labels proposed by an LLM informant and checked by hand; the
            rule was revised after seeing its errors
  sample 2  eval/ser_ir_sample2.tsv  held-out test set, `tutor_label`
            labeled by a native speaker (Jim's Portuguese tutor), never
            used to shape the rule

    python -m scripts.score_serir
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from scripts import serir

OTHER = "outro"          # the tutor's label for "not this verb"
FORMS = serir.FORMS


def score_heldout(cfg: dict[str, Any], path: str) -> dict[str, Any]:
    """Score the rule, unchanged, against the native speaker's labels."""
    with open(path, encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh, delimiter="\t")
                if (r.get("tutor_label") or "").strip()]
    tags = serir.tag_occurrences([(r["form"], r["sentence"]) for r in rows], cfg)

    per: dict[str, dict[str, int]] = {f: {} for f in FORMS}
    errors: list[tuple[str, str, str, str]] = []
    leaks: list[tuple[str, str, str]] = []
    for r, (_, upos) in zip(rows, tags):
        form, gold = r["form"], r["tutor_label"].strip()
        pred = serir.decide(form, r["sentence"], upos, cfg)
        c = per[form]
        if gold == OTHER:
            c["other"] = c.get("other", 0) + 1
            if pred != "other":
                leaks.append((form, r["sentence"], upos))
            continue
        c["verb"] = c.get("verb", 0) + 1
        if pred == "other":
            c["gated_out"] = c.get("gated_out", 0) + 1
            errors.append((form, r["sentence"], gold, f"not tagged verb ({upos})"))
        elif pred == "?":
            c["abstain"] = c.get("abstain", 0) + 1
        else:
            c["decided"] = c.get("decided", 0) + 1
            if pred == gold:
                c["correct"] = c.get("correct", 0) + 1
            else:
                errors.append((form, r["sentence"], gold, pred))

    tot = {k: sum(c.get(k, 0) for c in per.values())
           for k in ("verb", "decided", "correct", "abstain", "gated_out", "other")}
    return {"per_form": per, "totals": tot, "errors": errors, "leaks": leaks,
            "rows": len(rows),
            "accuracy": tot["correct"] / tot["decided"] if tot["decided"] else 0.0}


def render(res: dict[str, Any], path: str) -> list[str]:
    tot = res["totals"]
    lines = [
        "",
        "## Held-out test set: `" + path + "`",
        "",
        f"100 further corpus lines drawn the same way, 20 per form; {res['rows']}",
        "carry a label. Labeled by a native speaker (Jim's Portuguese tutor),",
        "after the rule was finished: these labels were never used to shape it,",
        "so this is the honest estimate of how the rule behaves on new text.",
        "",
        "| form | verb rows | decided | correct | accuracy | abstained | abstention rate | gated out | `outro` rows | `outro` given a verb |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for f in FORMS + ("all",):
        c = tot if f == "all" else res["per_form"][f]
        v, d, k = c.get("verb", 0), c.get("decided", 0), c.get("correct", 0)
        a, g, o = c.get("abstain", 0), c.get("gated_out", 0), c.get("other", 0)
        leak = len(res["leaks"]) if f == "all" else sum(1 for x in res["leaks"] if x[0] == f)
        name = "**all**" if f == "all" else f"`{f}`"
        acc = f"{k / d:.1%}" if d else "–"
        rate = f"{a / v:.0%}" if v else "–"
        lines.append(f"| {name} | {v} | {d} | {k} | {acc} | {a} | {rate} | {g} | {o} | {leak} |")
    lines += ["", f"**Accuracy on decided verb rows: {res['accuracy']:.1%}** "
              f"({tot['correct']}/{tot['decided']}), abstaining on {tot['abstain']} of "
              f"{tot['verb']}. The rule is not tuned against this set.", ""]
    if res["errors"]:
        lines += ["<details><summary>Errors</summary>", "",
                  "| form | sentence | tutor | rule |", "|---|---|---|---|"]
        for f, sent, gold, pred in res["errors"]:
            lines.append(f"| `{f}` | {sent} | {gold} | {pred} |")
        lines += ["", "</details>", ""]
    return lines


def main() -> None:
    from scripts import config as config_mod

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--dev", default="eval/ser_ir_sample.tsv")
    ap.add_argument("--heldout", default="eval/ser_ir_sample2.tsv")
    ap.add_argument("--report", default="reports/serir_scores.md")
    args = ap.parse_args()
    cfg = config_mod.load(args.config)

    dev = serir.score(cfg, args.dev, args.report)     # rewrites the report and .json
    res = score_heldout(cfg, args.heldout)
    with open(args.report, "a", encoding="utf-8") as fh:
        fh.write("\n".join(render(res, args.heldout)) + "\n")

    import json

    Path(args.report).with_name("serir_scores_heldout.json").write_text(json.dumps(
        {"accuracy": res["accuracy"], "decided": res["totals"]["decided"],
         "correct": res["totals"]["correct"], "verb_rows": res["totals"]["verb"],
         "abstained": res["totals"]["abstain"], "other_leaks": len(res["leaks"]),
         "rule_digest": serir.rule_digest(cfg)}, indent=2), encoding="utf-8")

    print(f"development {dev['accuracy']:.1%} on {dev['totals']['decided']} decided; "
          f"held-out {res['accuracy']:.1%} on {res['totals']['decided']} decided "
          f"of {res['totals']['verb']} verb rows, abstained {res['totals']['abstain']}, "
          f"gated out {res['totals']['gated_out']}, "
          f"outro given a verb: {len(res['leaks'])} of {res['totals']['other']}")


if __name__ == "__main__":
    main()
