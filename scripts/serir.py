"""A next-word rule for ser/ir, and the sample to evaluate it on.

`foi`, `fui`, `fomos`, `foram` and `fora` are preterite (or pluperfect)
forms of both *ser* ("was") and *ir* ("went"). Stanza assigns them to *ser*
almost regardless of context -- all 50 sampled uses of `fui` and `fomos`,
including *fui ao Paquistão* -- so the tagger cannot split them.

This module implements a rule based on the word that follows the form. It
is NOT applied to the counts: it is evaluated first, against a hand-labeled
random sample (eval/ser_ir_sample.tsv).

The rule, in order:

  ser  nothing follows -- end of line or punctuation  (Foi.)
  ir   next word is a, ao, à, aos, às, para, embora, até, lá or ali
  ser  next word is a past participle                 (foi feito)
  ir   next word is an infinitive                     (fui buscar)
  ser  next word starts a noun phrase or is an adjective, noun or
       pronoun                                         (foi o melhor, foi ele)
  ?    anything else: adverbs (fui logo / foi muito bom), prepositions not
       listed above (foi com ele / foi por isso), conjunctions -- the rule
       abstains rather than guess

An enclitic reflexive is skipped first (foi-se embora -> embora -> ir).

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
    clitic = _ENCLITIC.match(rest)
    if clitic:
        rest = rest[clitic.end():]
    if _NOTHING.match(rest):
        return "ser", "nothing follows"
    w = _WORD.search(rest)
    if not w:
        return "ser", "nothing follows"
    nxt = w.group(0).lower()

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


def main() -> None:
    from scripts import config as config_mod

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=20260912)
    ap.add_argument("--out", default="eval/ser_ir_sample.tsv")
    ap.add_argument("--force", action="store_true",
                    help="overwrite even if human labels have been entered")
    args = ap.parse_args()
    cfg = config_mod.load(args.config)

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
