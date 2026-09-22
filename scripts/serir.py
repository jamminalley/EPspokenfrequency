"""A next-word rule for ser/ir, and the sample to evaluate it on.

`foi`, `fui`, `fomos`, `foram` and `fora` are preterite (or pluperfect)
forms of both *ser* ("was") and *ir* ("went"). Stanza assigns them to *ser*
almost regardless of context -- all 50 sampled uses of `fui` and `fomos`,
including *fui ao Paquistão* -- so the tagger cannot split them.

This module implements a rule based on the words around the form. It
runs only on occurrences Stanza tags VERB or AUX -- the adverb *fora*
("outside") never reaches it -- and is measured against a hand-checked
random sample (eval/ser_ir_sample.tsv; `--score` writes
reports/serir_scores.md).

The rule, in order:

  ir   an attached reflexive                          (foi-se, fomos-nos)
  ir   lá, cá, ali or aí just before the form         (já lá fui)
  ser  nothing follows -- end of line or punctuation  (Foi.)
  ser  a / à + determiner or possessive: the article  (qual foi a tua defesa)
       -- unless the noun after it is a destination   (fui à minha casa -> ir)
  ir   next word is a, ao, à, aos, às, para, embora, até, lá or ali
  ser  next word is a past participle                 (foi feito)
  ir   next word is an infinitive                     (fui buscar)
  ser  next word starts a noun phrase or is an adjective, noun or
       pronoun                                         (foi o melhor, foi ele)
  ?    anything else: adverbs (fui logo / foi muito bom), prepositions not
       listed above (foi com ele / foi por isso), conjunctions -- the rule
       abstains, and the form's own ser/ir ratio among the decided
       occurrences is used instead

    python -m scripts.serir --n 100 --seed 20260912   # write the sample
"""

from __future__ import annotations

import argparse
import random
import re
from pathlib import Path
from typing import Any

import regex

FORMS = ("foi", "fui", "fomos", "foram", "fora")
IR_NEXT = frozenset({"a", "ao", "à", "aos", "às", "para", "embora", "até", "lá", "ali"})
REFLEXIVE = frozenset({"me", "te", "se", "nos", "vos"})
NOUN_PHRASE_START = frozenset({
    "o", "os", "as", "um", "uma", "uns", "umas",
    "este", "esta", "estes", "estas", "esse", "essa", "esses", "essas",
    "aquele", "aquela", "aqueles", "aquelas", "isto", "isso", "aquilo",
    "meu", "minha", "meus", "minhas", "teu", "tua", "teus", "tuas",
    "seu", "sua", "seus", "suas", "nosso", "nossa", "nossos", "nossas",
    "vosso", "vossa", "vossos", "vossas", "todo", "toda", "todos", "todas",
    "tudo", "nada", "algo", "alguém", "ninguém", "outro", "outra",
})
_PARTICIPLE = re.compile(r"(?:ad|id|íd)(?:o|a|os|as)$")
_WORD = regex.compile(r"\p{L}+")
_FORM = {f: regex.compile(rf"(?<!\p{{L}}){f}(?!\p{{L}})", regex.IGNORECASE) for f in FORMS}
_ENCLITIC = regex.compile(r"^-(me|te|se|nos|vos)(?!\p{L})", regex.IGNORECASE)
_PREV_WORD = regex.compile(r"(\p{L}+)\s*$")
IR_BEFORE = frozenset({"lá", "cá", "ali", "aí"})
ARTICLE_AFTER_A = frozenset({
    "o", "os", "as", "um", "uma", "uns", "umas",
    "este", "esta", "estes", "estas", "esse", "essa", "esses", "essas",
    "aquele", "aquela", "aqueles", "aquelas",
    "meu", "minha", "meus", "minhas", "teu", "tua", "teus", "tuas",
    "seu", "sua", "seus", "suas", "nosso", "nossa", "nossos", "nossas",
    "vosso", "vossa", "vossos", "vossas",
})
_NOTHING = regex.compile(r"^\s*(?:$|[.!?…,;:\"'»)\]-])")


def rule_guess(form: str, sentence: str, cfg: dict[str, Any]) -> tuple[str, str]:
    """(guess, reason) for the first occurrence of `form` in `sentence`.
    guess is 'ser', 'ir' or '?' (the rule abstains)."""
    from scripts.lemmas import in_dictionary
    from scripts.postag import PosTagger

    m = _FORM[form].search(sentence)
    if not m:
        return "?", "form not found"
    rest = sentence[m.end():]
    if _ENCLITIC.match(rest):
        return "ir", "attached reflexive"
    prev = _PREV_WORD.search(sentence[:m.start()])
    if prev and prev.group(1).lower() in IR_BEFORE:
        return "ir", f"'{prev.group(1).lower()}' before"
    if _NOTHING.match(rest):
        return "ser", "nothing follows"
    words = [w.lower() for w in _WORD.findall(rest)[:3]]
    if not words:
        return "ser", "nothing follows"
    nxt = words[0]

    if nxt in ("a", "à") and len(words) > 1 and words[1] in ARTICLE_AFTER_A:
        noun = words[2] if len(words) > 2 else ""
        if noun in set(cfg["serir"]["destination_nouns"]):
            return "ir", f"destination '{noun}'"
        return "ser", f"article '{nxt} {words[1]}'"

    irregular = set(cfg["fixes"].get("irregular_participles", ()))
    if nxt in IR_NEXT:
        return "ir", f"followed by '{nxt}'"
    if _PARTICIPLE.search(nxt) or nxt in irregular:
        return "ser", f"participle '{nxt}'"
    if nxt.endswith(("ar", "er", "ir", "ôr")) and len(nxt) >= 3 and in_dictionary(nxt):
        return "ir", f"infinitive '{nxt}'"
    if nxt in NOUN_PHRASE_START:
        return "ser", f"noun phrase '{nxt}'"
    tag = PosTagger.load().tag(nxt)
    if tag in ("noun", "adj", "unk", "pron", "det", "num"):
        return "ser", f"{tag} '{nxt}'"
    return "?", f"{tag} '{nxt}'"


def sample(cfg: dict[str, Any], n: int, seed: int) -> tuple[list[tuple[str, str]], dict[str, int]]:
    """n corpus lines containing the forms, n/5 per form, drawn uniformly at
    random from the whole corpus (reservoir sampling, fixed seed)."""
    from scripts import corpus

    per = n // len(FORMS)
    rng = random.Random(seed)
    reservoirs: dict[str, list[tuple[int, str]]] = {f: [] for f in FORMS}
    seen = {f: 0 for f in FORMS}
    prefilter = regex.compile(r"(?<!\p{L})(foi|fui|fomos|foram|fora)(?!\p{L})", regex.IGNORECASE)
    for lineno, line in enumerate(corpus.stream_lines(cfg)):
        found = {m.group(1).lower() for m in prefilter.finditer(line)}
        for form in found:
            seen[form] += 1
            res = reservoirs[form]
            item = (lineno, line.strip())
            if len(res) < per:
                res.append(item)
            else:
                j = rng.randrange(seen[form])
                if j < per:
                    res[j] = item
    out: list[tuple[str, str]] = []
    for form in FORMS:
        for _, sentence in sorted(reservoirs[form]):
            out.append((form, sentence))
    return out, seen


_VERB = ("VERB", "AUX")


def tag_occurrences(items: list[tuple[str, str]], cfg: dict[str, Any]) -> list[tuple[str, str]]:
    """Stanza's (lemma, upos) for the first occurrence of each form in each
    sentence, with the build's pipeline settings. ('', '') if not found."""
    import stanza
    from stanza import Document

    nlp = stanza.Pipeline(lang=cfg["lemmatizer"]["stanza_lang"],
                          processors="tokenize,mwt,pos,lemma", verbose=False,
                          tokenize_no_ssplit=True)
    docs = nlp.bulk_process([Document([], text=sent) for _, sent in items])
    out: list[tuple[str, str]] = []
    for (form, _), doc in zip(items, docs):
        hit = ("", "")
        for sent in doc.sentences:
            for w in sent.words:
                if w.text.lower() == form:
                    hit = ((w.lemma or "").lower(), w.upos or "")
                    break
            if hit != ("", ""):
                break
        out.append(hit)
    return out


def decide(form: str, sentence: str, upos: str, cfg: dict[str, Any]) -> str:
    """'other' if Stanza does not tag the occurrence as a verb; otherwise
    the rule's 'ser', 'ir' or '?'."""
    if upos not in _VERB:
        return "other"
    return rule_guess(form, sentence, cfg)[0]


def score(cfg: dict[str, Any], gold_path: str, out_path: str) -> dict[str, Any]:
    """Score the rule against the hand-checked sample; write the table."""
    import csv

    with open(gold_path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    tags = tag_occurrences([(r["form"], r["sentence"]) for r in rows], cfg)
    per: dict[str, dict[str, int]] = {f: {} for f in FORMS}
    errors: list[tuple[str, str, str, str]] = []
    leaks: list[tuple[str, str, str]] = []
    for r, (_, upos) in zip(rows, tags):
        form, gold = r["form"], r["human_label"].strip()
        pred = decide(form, r["sentence"], upos, cfg)
        c = per[form]
        if gold == "other":
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
    acc = tot["correct"] / tot["decided"] if tot["decided"] else 0.0
    lines = [
        "# ser / ir rule: score against the hand-checked sample",
        "",
        f"`{gold_path}`: 100 random corpus lines, 20 per form. Gold labels were",
        "proposed by an LLM acting as a European Portuguese informant and checked",
        "independently by hand, with disputed rows reviewed (see eval/README.md).",
        "",
        "The rule runs only on occurrences Stanza tags VERB or AUX; anything else",
        "is `other` and never reaches it. Accuracy is on the verb rows the rule",
        "decided; abstentions fall back, in the counts, to the form's own ser/ir",
        "ratio among decided occurrences.",
        "",
        "| form | verb rows | decided | correct | accuracy | abstained | abstention rate | gated out | `other` rows | `other` given a verb |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for f in FORMS + ("all",):
        c = tot if f == "all" else per[f]
        v, d, k = c.get("verb", 0), c.get("decided", 0), c.get("correct", 0)
        a, g, o = c.get("abstain", 0), c.get("gated_out", 0), c.get("other", 0)
        leak = len(leaks) if f == "all" else sum(1 for x in leaks if x[0] == f)
        name = "**all**" if f == "all" else f"`{f}`"
        lines.append(
            f"| {name} | {v} | {d} | {k} | {k / d:.1%} | {a} | "
            f"{a / v:.0%} | {g} | {o} | {leak} |" if d and v else
            f"| {name} | {v} | {d} | {k} | – | {a} | – | {g} | {o} | {leak} |")
    lines += ["", f"**Accuracy on decided verb rows: {acc:.1%}** "
              f"({tot['correct']}/{tot['decided']}); threshold for applying the rule "
              f"to the counts: {cfg['serir']['min_accuracy']:.0%}.", ""]
    if errors:
        lines += ["## Errors", "", "| form | sentence | gold | rule |", "|---|---|---|---|"]
        for f, sent, gold, pred in errors:
            lines.append(f"| `{f}` | {sent} | {gold} | {pred} |")
        lines.append("")
    if leaks:
        lines += ["## `other` rows that reached the rule", "", "| form | sentence | Stanza tag |",
                  "|---|---|---|"]
        for f, sent, upos in leaks:
            lines.append(f"| `{f}` | {sent} | {upos} |")
        lines.append("")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    import json

    Path(out_path).with_suffix(".json").write_text(json.dumps(
        {"accuracy": acc, "decided": tot["decided"], "correct": tot["correct"],
         "verb_rows": tot["verb"], "abstained": tot["abstain"],
         "other_leaks": len(leaks), "rule_digest": rule_digest(cfg)}, indent=2),
        encoding="utf-8")
    return {"accuracy": acc, "totals": tot, "per_form": per, "leaks": leaks, "errors": errors}


def rule_digest(cfg: dict[str, Any]) -> str:
    """Digest of the rule as it stands -- this module's source plus the
    config lists it reads. A score only vouches for the rule it was
    computed with; any change means rescoring before the counts use it."""
    import hashlib
    import json

    h = hashlib.sha256(Path(__file__).read_bytes())
    h.update(json.dumps({"destinations": cfg["serir"]["destination_nouns"],
                         "participles": cfg["fixes"].get("irregular_participles", [])},
                        sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()[:16]


def load_score(path: str) -> dict[str, Any] | None:
    import json

    p = Path(path).with_suffix(".json")
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def counts_joint(cfg: dict[str, Any], log=print) -> dict[str, "Counter"]:
    """Per-occurrence (lemma, upos) votes for each form, for the counts.

    `serir.sample_per_form` random corpus lines per form are tagged by
    Stanza. Non-verb occurrences keep Stanza's reading (fora, ADV); verb
    occurrences go through the rule; abstentions are shared out in the
    form's own ser/ir ratio among the occurrences the rule decided.
    Cached, since drawing the sample takes a pass over the corpus.
    """
    import gzip
    import hashlib
    import json
    from collections import Counter

    sc = cfg["serir"]
    key = hashlib.sha256(json.dumps(
        {"n": sc["sample_per_form"], "seed": sc["seed"], "corpus": cfg["corpus"]["path"],
         "lang": cfg["lemmatizer"]["stanza_lang"]}, sort_keys=True).encode()).hexdigest()[:16]
    cache = Path(cfg["paths"]["cache_dir"]) / f"serir_{key}.json.gz"
    if cache.is_file():
        log(f"  ser/ir: reusing cache {cache}")
        with gzip.open(cache, "rt", encoding="utf-8") as fh:
            data = json.load(fh)
    else:
        rows, _ = sample(cfg, sc["sample_per_form"] * len(FORMS), sc["seed"])
        log(f"  ser/ir: tagging {len(rows):,} sampled lines")
        tags = tag_occurrences(rows, cfg)
        data = [[f, sent, lemma, upos] for (f, sent), (lemma, upos) in zip(rows, tags)]
        cache.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(cache, "wt", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False)

    return {form: joint_from_tagged(form, [(s, l, u) for f, s, l, u in data if f == form], cfg)
            for form in FORMS}


def joint_from_tagged(
    form: str, tagged: list[tuple[str, str, str]], cfg: dict[str, Any]
) -> "Counter":
    """(lemma, upos) votes for one form from (sentence, stanza_lemma, upos)
    triples. Abstentions are shared out in the form's own ser/ir ratio among
    the occurrences the rule decided -- per form, not globally. So are
    non-verb tags on forms with no non-verb reading (serir.nonverb_forms)."""
    from collections import Counter

    joint: Counter = Counter()
    abstain: Counter = Counter()
    real_nonverb = form in set(cfg["serir"].get("nonverb_forms", ()))
    for sent, lemma, upos in tagged:
        if not upos:
            continue
        guess = decide(form, sent, upos, cfg)
        if guess == "other" and real_nonverb:
            joint[(lemma or form, upos)] += 1
        elif guess == "other":
            # A form with no non-verb reading: the tag is a tagger error.
            abstain["AUX"] += 1
        elif guess == "?":
            abstain[upos] += 1
        else:
            joint[(guess, upos)] += 1
    ser = sum(n for (l, _), n in joint.items() if l == "ser")
    ir = sum(n for (l, _), n in joint.items() if l == "ir")
    for upos, n in abstain.items():
        if ser + ir:
            joint[("ser", upos)] += n * ser / (ser + ir)
            joint[("ir", upos)] += n * ir / (ser + ir)
    return joint


def main() -> None:
    from scripts import config as config_mod

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20260912)
    ap.add_argument("--out", default="eval/ser_ir_sample.tsv")
    ap.add_argument("--force", action="store_true",
                    help="overwrite even if human labels have been entered")
    ap.add_argument("--score", action="store_true",
                    help="score the rule against the labeled sample instead")
    ap.add_argument("--report", default="reports/serir_scores.md")
    args = ap.parse_args()
    cfg = config_mod.load(args.config)

    if args.score:
        res = score(cfg, args.out, args.report)
        t = res["totals"]
        print(f"accuracy {res['accuracy']:.1%} on {t['decided']} decided of {t['verb']} verb rows; "
              f"abstained {t['abstain']}; gated out {t['gated_out']}; "
              f"other rows given a verb: {len(res['leaks'])} of {t['other']}")
        return

    out = Path(args.out)
    if out.is_file() and not args.force:
        import csv

        with out.open(encoding="utf-8", newline="") as fh:
            if any((r.get("human_label") or "").strip()
                   for r in csv.DictReader(fh, delimiter="\t")):
                raise SystemExit(f"{out} has human labels; refusing to overwrite (--force)")

    rows, seen = sample(cfg, args.n, args.seed)
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("form\tsentence\trule_guess\thuman_label\n")
        for form, sentence in rows:
            guess, _ = rule_guess(form, sentence, cfg)
            clean = sentence.replace("\t", " ")
            fh.write(f"{form}\t{clean}\t{guess}\t\n")
    print(f"{len(rows)} rows -> {out}")
    for f in FORMS:
        print(f"  {f:6} {seen[f]:>10,} lines in the corpus")


if __name__ == "__main__":
    main()
