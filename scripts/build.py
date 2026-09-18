"""Pipeline entry point.

    python -m scripts.build --config config.yaml
    python -m scripts.build --sample 2000000          # dev run
    python -m scripts.build --set fixes.diacritic_folding=true --stage 2

Runs the five README steps in order, writes every output named in the
config, and produces COMPARISON.md, QUALITY.md and build_stats.json.
Outputs go to paths.out_dir; `out/` is never written to.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from scripts import bigrams as bigrams_mod
from scripts import compare as compare_mod
from scripts import config as config_mod
from scripts import conventions as conventions_mod
from scripts import counts as counts_mod
from scripts import emit as emit_mod
from scripts import eval_lemmas as eval_mod
from scripts import filters as filters_mod
from scripts import lemmas as lemmas_mod
from scripts import quality as quality_mod
from scripts.postag import PosTagger


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def aggregate_lemmas(
    surface_counts: dict[str, int], lemma_map: dict[str, str]
) -> dict[str, int]:
    """Sum surface counts onto their lemmas, deterministically."""
    out: Counter = Counter()
    for surface in sorted(surface_counts):
        out[lemma_map.get(surface, surface)] += surface_counts[surface]
    return dict(out)


def run(cfg: dict[str, Any]) -> dict[str, Any]:
    started = time.monotonic()
    out_dir = config_mod.out_dir(cfg)
    out_dir.mkdir(parents=True, exist_ok=True)
    stats: dict[str, Any] = {"stage": cfg["run"]["stage"]}

    import simplemma

    stats["simplemma_version"] = simplemma.__version__

    # -- step 1: tokenize and count ---------------------------------------
    _log("step 1: unigram pass")
    uni = counts_mod.unigram_pass_cached(cfg)
    stats["fingerprint"] = uni.fingerprint()
    fingerprint_rows = counts_mod.compare_fingerprint(uni, cfg)
    _log(f"  {uni.n_tokens:,} tokens, {uni.n_types:,} types")

    # -- step 3 (scan): bigrams, contexts, casing -------------------------
    # Runs before step 2 because the lemmatizer wants the sampled contexts.
    _log("step 3a: bigram + context pass")
    bg = bigrams_mod.bigram_pass_cached(cfg, uni.counts)
    stats["bigram_pairs"] = len(bg.pairs)
    stats["context_types"] = len(bg.contexts)
    _log(f"  {len(bg.pairs):,} distinct pairs, contexts for {len(bg.contexts):,} types")

    # -- step 2: lemmatize -------------------------------------------------
    _log(f"step 2: lemmatize ({cfg['lemmatizer']['backend']})")
    types = sorted(uni.counts)
    backend = lemmas_mod.get_backend(cfg["lemmatizer"]["backend"], cfg)

    tier = cfg["lemmatizer"].get("tiered", {})
    if tier.get("enabled"):
        limit = max(hi for _, hi in cfg["output"]["bands"])
        min_count = tier.get("primary_min_count")
        if min_count is None:
            # Count at the last published rank, as a surface-level proxy,
            # divided by the safety factor. Conservative: surfaces well
            # below the cutoff still qualify, because several surfaces can
            # aggregate onto one lemma.
            ordered = sorted(uni.counts.values(), reverse=True)
            at_limit = ordered[limit - 1] if len(ordered) >= limit else 1
            min_count = max(at_limit // tier.get("safety_factor", 10), 1)
        stats["tier_min_count"] = min_count
        backend = lemmas_mod.TieredBackend(
            backend, lemmas_mod.SimplemmaBackend(), uni.counts, min_count
        )
        _log(f"  tier threshold: surface count >= {min_count:,}")

    lemma_map = lemmas_mod.build_lemma_map(cfg, types, bg.contexts, backend=backend)

    conv_log = None
    if cfg["run"]["stage"] >= 2 and cfg["conventions"].get("enabled"):
        # Before closure: closure uses the map as its own oracle, so it then
        # respects the conventions instead of undoing them.
        simple = lemmas_mod.SimplemmaBackend()
        cache: dict[str, str] = {}

        def relemmatize(word: str) -> str:
            if word not in cache:
                cache[word] = simple.lemmatize_types([word])[word]
            return cache[word]

        lemma_map, conv_log = conventions_mod.apply(
            lemma_map, cfg, lemmas_mod.in_dictionary, relemmatize
        )
        stats["conventions"] = conv_log.summary(uni.counts)
        for name, info in stats["conventions"].items():
            _log(f"  convention {name}: {info['surfaces']:,} surfaces, "
                 f"{info['tokens']:,} tokens")

    if cfg["fixes"].get("lemma_closure"):
        lemma_map, redirects = lemmas_mod.close_lemma_map(
            lemma_map, lemmas_mod.SimplemmaBackend(), bg.contexts
        )
        stats["lemma_closure_iterations"] = True
        stats["lemma_closure_redirects"] = len(redirects)
        _log(f"  closure: merged {len(redirects):,} lemmas onto other entries")
    stats["lemmatized_types"] = len(lemma_map)
    lemma_counts = aggregate_lemmas(uni.counts, lemma_map)
    _log(f"  {len(lemma_counts):,} lemmas from {len(types):,} types")

    # -- step 3 (score): MWEs ---------------------------------------------
    _log("step 3b: MWE scoring")
    mwes = bigrams_mod.score_mwes(cfg, bg, uni.counts)
    stats["mwes_retained"] = len(mwes)
    _log(f"  {len(mwes):,} MWEs retained")

    # -- step 4: filters ---------------------------------------------------
    _log("step 4: filters")
    if cfg["fixes"].get("diacritic_folding"):
        lemma_counts, fold_log = filters_mod.fold_diacritics(
            lemma_counts, cfg, lemmas_mod.in_dictionary
        )
        stats["diacritic_folded"] = len(fold_log)
        _log(f"  folded {len(fold_log):,} unaccented forms")

    cap_ratios = {w: bg.cap_ratio(w) for w in lemma_counts}
    kept, flog = filters_mod.apply(
        lemma_counts, cap_ratios, cfg, lemmas_mod.in_dictionary
    )
    stats["bp_excluded"] = len(flog.bp_excluded)
    stats["proper_nouns_dropped"] = len(flog.proper_nouns)
    _log(f"  dropped {len(flog.proper_nouns):,} proper nouns, "
         f"{len(flog.bp_excluded)} BP lemmas")

    # -- step 5: rank and emit --------------------------------------------
    _log("step 5: rank and emit")
    tagger = PosTagger.load()
    limit = max(hi for _, hi in cfg["output"]["bands"])
    entries = emit_mod.rank_entries(kept, mwes, uni.n_tokens, tagger, limit)
    written = emit_mod.write_all(entries, cfg, out_dir)
    written += emit_mod.write_dropped(flog, cfg, out_dir)
    stats["entries"] = len(entries)
    _log(f"  wrote {len(written)} files to {out_dir}/")

    # -- quality report ----------------------------------------------------
    _log("quality report")
    # Use the lemma map itself as the oracle, so the check asks "is this
    # inventory closed under the lemmatizer that built it?" rather than
    # under some other backend, which would report spurious duplicates.
    entry_lemmas = [e.lemma for e in entries if not e.is_mwe]
    relemma = {w: lemma_map.get(w, w) for w in entry_lemmas}
    suspects = quality_mod.find_suspects(
        entries, cfg, lambda w: relemma.get(w, w),
        closed_class=frozenset(tagger.closed)
        | frozenset(conventions_mod.protected_forms(cfg)
                    if cfg["run"]["stage"] >= 2 and cfg["conventions"].get("enabled")
                    else ()),
    )
    quality_mod.write_tsv(suspects, out_dir / cfg["paths"]["reports"]["quality_tsv"])
    quality_text = quality_mod.render_report(suspects, cfg)
    (out_dir / cfg["paths"]["reports"]["quality"]).write_text(quality_text, encoding="utf-8")
    stats["suspects"] = len(suspects)
    _log(f"  {len(suspects):,} suspect duplicate entries")

    # -- gold-set evaluation ----------------------------------------------
    # Score the lemma map this build actually published -- backend, gate,
    # conventions and closure together -- not a backend in isolation. The
    # backend-by-backend comparison lives in backend_scores.md.
    _log("gold-set evaluation")
    try:
        gold_rows, gold_meta = eval_mod.load_gold(cfg)
        label = f"pipeline, stage {cfg['run']['stage']} ({cfg['lemmatizer']['backend']})"
        result = eval_mod.score(gold_rows, lemma_map)
        gold_text = eval_mod.render({label: result}, gold_meta)
        stats["gold"] = {label: result["accuracy"]}
    except FileNotFoundError as exc:
        gold_text = f"_Gold set unavailable: {exc}_"
        stats["gold"] = None

    # -- comparison report -------------------------------------------------
    _log("comparison report")
    band_reports = []
    original_dir = Path(cfg["paths"]["original_dir"])
    for (lo, hi), spec in zip(cfg["output"]["bands"], cfg["output"]["files"]):
        orig = compare_mod.read_band(original_dir / f"{spec['stem']}.tsv")
        rebuilt = compare_mod.read_band(out_dir / f"{spec['stem']}.tsv")
        if orig and rebuilt:
            band_reports.append(
                (f"ranks {lo}-{hi}", compare_mod.compare_bands(orig, rebuilt, hi))
            )
    baseline_reports = []
    baseline_dir = Path(cfg["paths"].get("baseline_dir", ""))
    if cfg["run"]["stage"] >= 2 and baseline_dir.is_dir() and baseline_dir != out_dir:
        for (lo, hi), spec in zip(cfg["output"]["bands"], cfg["output"]["files"]):
            base = compare_mod.read_band(baseline_dir / f"{spec['stem']}.tsv")
            rebuilt = compare_mod.read_band(out_dir / f"{spec['stem']}.tsv")
            if base and rebuilt:
                baseline_reports.append(
                    (f"ranks {lo}-{hi}", compare_mod.compare_bands(base, rebuilt, hi))
                )

    conventions_text = ""
    if conv_log is not None:
        conventions_text = compare_mod.render_conventions(conv_log, uni.counts, entries)

    report = compare_mod.render(
        cfg, fingerprint_rows, band_reports, quality_text, gold_text, stats,
        baseline_reports=baseline_reports, conventions_text=conventions_text,
    )
    (out_dir / cfg["paths"]["reports"]["comparison"]).write_text(report, encoding="utf-8")

    stats["elapsed_s"] = round(time.monotonic() - started, 1)
    (out_dir / cfg["paths"]["reports"]["stats"]).write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # The gate runs last so that the reports are always written first: a
    # failing build must still leave the evidence behind.
    quality_mod.enforce(suspects, cfg)
    return stats


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--sample", type=int, default=None)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--stage", type=int, default=None, choices=(1, 2))
    ap.add_argument("--set", action="append", default=[], metavar="PATH=VALUE")
    args = ap.parse_args()

    def coerce(text: str) -> Any:
        low = text.lower()
        if low in ("true", "false"):
            return low == "true"
        if low in ("null", "none"):
            return None
        try:
            return int(text)
        except ValueError:
            return text

    cfg = config_mod.load(args.config)
    overrides: dict[str, Any] = {}
    if args.sample is not None:
        overrides["run.sample_lines"] = args.sample
    if args.workers is not None:
        overrides["run.workers"] = args.workers
    if args.stage is not None:
        overrides["run.stage"] = args.stage
        if args.stage == 2:
            overrides["quality.fail_on_suspects"] = True
    for item in args.set:
        path, _, raw = item.partition("=")
        overrides[path] = coerce(raw)
    if overrides:
        cfg = config_mod.with_overrides(cfg, overrides)

    try:
        stats = run(cfg)
    except quality_mod.QualityGateFailure as exc:
        print(f"\nQUALITY GATE FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
