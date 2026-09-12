"""Pass 2: bigram collection for MWEs, plus sampled sentence contexts.

README pipeline step 3: "Second corpus pass for bigram collection
(restricted to surface forms with >= 100 occurrences); MWE candidates
retained by log-likelihood ratio (Dunning G^2 >= 2500) and collocation
share >= 5%."

Both jobs that need a second scan are done in the same pass:

1. Bigram counts over adjacent tokens within a line (never across lines).
2. Reservoir-sampled sentence contexts per surface type, which the
   context-sensitive lemmatizer backends need.

Determinism.  Context selection keeps the K sentences with the smallest
BLAKE2b digest of (seed, type, sentence).  That is a pure function of
content, so it is independent of chunk order, worker scheduling and how
many workers ran -- unlike a random reservoir, which would need a shared
RNG stream to be reproducible.

Memory.  A bigram is encoded as one int (left_id * n_vocab + right_id)
rather than a tuple of strings.  At fixed chunk boundaries, pairs seen
fewer than ``prune_min_count`` times are dropped; since min_g2 requires
counts in the thousands this cannot affect the surviving MWEs, and because
the checkpoints are tied to chunk numbers it stays deterministic.
"""

from __future__ import annotations

import hashlib
import heapq
import math
import multiprocessing as mp
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from scripts import corpus
from scripts.tokenizer import Tokenizer

_TOKENIZER: Tokenizer | None = None
_VOCAB: dict[str, int] = {}
_NVOCAB: int = 0
_CTX_TYPES: frozenset[str] = frozenset()
_CTX_K: int = 0
_SEED: int = 0


def _init_worker(
    tok_cfg: dict[str, Any],
    vocab: dict[str, int],
    ctx_types: frozenset[str],
    ctx_k: int,
    seed: int,
) -> None:
    global _TOKENIZER, _VOCAB, _NVOCAB, _CTX_TYPES, _CTX_K, _SEED
    _TOKENIZER = Tokenizer(tok_cfg)
    _VOCAB = vocab
    _NVOCAB = len(vocab) + 1
    _CTX_TYPES = ctx_types
    _CTX_K = ctx_k
    _SEED = seed


def _ctx_digest(seed: int, surface: str, sentence: str) -> int:
    h = hashlib.blake2b(
        f"{seed}\x00{surface}\x00{sentence}".encode("utf-8"), digest_size=8
    )
    return int.from_bytes(h.digest(), "big")


def _process_chunk(lines: list[str]) -> tuple[Counter, dict[str, list[tuple[int, str]]]]:
    """Count bigrams and collect context candidates for one chunk."""
    assert _TOKENIZER is not None
    pairs: Counter = Counter()
    ctx: dict[str, list[tuple[int, str]]] = defaultdict(list)
    tokenize = _TOKENIZER.tokenize
    vocab = _VOCAB
    nv = _NVOCAB

    for line in lines:
        toks = tokenize(line)
        if not toks:
            continue
        # Bigrams: both constituents must clear the frequency floor.
        prev_id = vocab.get(toks[0], -1)
        for tok in toks[1:]:
            cur_id = vocab.get(tok, -1)
            if prev_id >= 0 and cur_id >= 0:
                pairs[prev_id * nv + cur_id] += 1
            prev_id = cur_id
        # Contexts: one sentence can serve several types.
        if _CTX_TYPES:
            sentence = line.strip()
            if sentence:
                for tok in set(toks):
                    if tok in _CTX_TYPES:
                        ctx[tok].append((_ctx_digest(_SEED, tok, sentence), sentence))

    # Keep only the K best per type before returning, to bound IPC volume.
    trimmed = {t: heapq.nsmallest(_CTX_K, v) for t, v in ctx.items()}
    return pairs, trimmed


@dataclass
class BigramResult:
    pairs: Counter = field(default_factory=Counter)
    contexts: dict[str, list[str]] = field(default_factory=dict)
    n_bigrams: int = 0
    elapsed_s: float = 0.0


def bigram_pass(
    cfg: dict[str, Any],
    unigram_counts: Mapping[str, int],
    progress: bool = True,
) -> BigramResult:
    """Run pass 2.  ``unigram_counts`` comes from pass 1."""
    bg = cfg["bigrams"]
    lem_ctx = cfg["lemmatizer"]["context"]
    floor = bg["min_constituent_count"]

    # Vocabulary: surface forms clearing the floor, ordered by count desc
    # then lexicographically, so ids are stable across runs.
    qualifying = sorted(
        (w for w, c in unigram_counts.items() if c >= floor),
        key=lambda w: (-unigram_counts[w], w),
    )
    vocab = {w: i for i, w in enumerate(qualifying)}
    nv = len(vocab) + 1

    ctx_types: frozenset[str] = frozenset()
    ctx_k = 0
    if lem_ctx.get("enabled"):
        ctx_k = lem_ctx["samples_per_type"]
        ctx_types = frozenset(qualifying[: lem_ctx["max_types"]])

    if progress:
        print(
            f"  pass2: {len(vocab):,} qualifying types (>= {floor}), "
            f"context for {len(ctx_types):,} types x {ctx_k}",
            file=sys.stderr,
        )

    started = time.monotonic()
    pairs: Counter = Counter()
    ctx_best: dict[str, list[tuple[int, str]]] = defaultdict(list)

    ctxm = mp.get_context("spawn")
    with ctxm.Pool(
        processes=cfg["run"]["workers"],
        initializer=_init_worker,
        initargs=(cfg["tokenizer"], vocab, ctx_types, ctx_k, cfg["run"]["seed"]),
    ) as pool:
        stream = corpus.chunks(cfg)
        for i, (chunk_pairs, chunk_ctx) in enumerate(
            pool.imap(_process_chunk, stream, chunksize=1), start=1
        ):
            pairs.update(chunk_pairs)
            for surface, cands in chunk_ctx.items():
                merged = heapq.nsmallest(ctx_k, ctx_best[surface] + cands)
                ctx_best[surface] = merged
            if bg["prune_every_chunks"] and i % bg["prune_every_chunks"] == 0:
                before = len(pairs)
                pairs = Counter(
                    {k: v for k, v in pairs.items() if v >= bg["prune_min_count"]}
                )
                if progress:
                    print(
                        f"  pass2 chunk {i:5d}  pairs {before:,} -> {len(pairs):,} (pruned)",
                        file=sys.stderr,
                        flush=True,
                    )

    # Decode ids back to surface pairs.
    inverse = {i: w for w, i in vocab.items()}
    decoded: Counter = Counter()
    for code, count in pairs.items():
        left, right = divmod(code, nv)
        decoded[(inverse[left], inverse[right])] = count

    contexts = {
        surface: [sent for _, sent in sorted(best)]
        for surface, best in ctx_best.items()
    }
    return BigramResult(
        pairs=decoded,
        contexts=contexts,
        n_bigrams=sum(decoded.values()),
        elapsed_s=time.monotonic() - started,
    )


# -- MWE scoring ----------------------------------------------------------


def log_likelihood(o11: int, r1: int, c1: int, n: int) -> float:
    """Dunning's G^2 for a 2x2 contingency table.

    o11  count of the bigram
    r1   count of the left word in left position
    c1   count of the right word in right position
    n    total bigram count
    """
    o12 = r1 - o11
    o21 = c1 - o11
    o22 = n - o11 - o12 - o21
    if min(o11, o12, o21, o22) < 0:
        return 0.0
    total = 0.0
    for obs, exp in (
        (o11, r1 * c1 / n),
        (o12, r1 * (n - c1) / n),
        (o21, (n - r1) * c1 / n),
        (o22, (n - r1) * (n - c1) / n),
    ):
        if obs > 0 and exp > 0:
            total += obs * math.log(obs / exp)
    return 2.0 * total


def score_mwes(
    cfg: dict[str, Any],
    result: BigramResult,
    unigram_counts: Mapping[str, int],
) -> list[dict[str, Any]]:
    """Retain MWE candidates by G^2 and collocation share."""
    bg = cfg["bigrams"]
    n = result.n_bigrams
    left_totals: Counter = Counter()
    right_totals: Counter = Counter()
    for (left, right), count in result.pairs.items():
        left_totals[left] += count
        right_totals[right] += count

    fixes = cfg.get("fixes", {})
    check_constituents = fixes.get("mwe_constituent_check", False)
    whitelist = set(fixes.get("mwe_constituent_whitelist", ()))
    vocab: frozenset[str] | None = None
    if check_constituents:
        from scripts.lemmas import pt_dictionary

        vocab = pt_dictionary(cfg["lemmatizer"].get("spellchecker_lang", "pt"))

    kept: list[dict[str, Any]] = []
    for (left, right), count in result.pairs.items():
        g2 = log_likelihood(count, left_totals[left], right_totals[right], n)
        if g2 < bg["min_g2"]:
            continue
        denom = min(unigram_counts.get(left, 1), unigram_counts.get(right, 1))
        share = count / denom if denom else 0.0
        if share < bg["min_collocation_share"]:
            continue
        if check_constituents:
            assert vocab is not None
            if any(
                part not in vocab and part not in whitelist for part in (left, right)
            ):
                continue
        kept.append(
            {
                "mwe": f"{left} {right}",
                "left": left,
                "right": right,
                "raw_freq": count,
                "g2": g2,
                "share": share,
            }
        )
    # Deterministic order: frequency desc, then alphabetical.
    kept.sort(key=lambda d: (-d["raw_freq"], d["mwe"]))
    return kept
