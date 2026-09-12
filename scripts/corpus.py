"""Streaming access to the gzipped corpus.

The corpus is ~1.1 GB gzipped and is never decompressed to disk.  Lines are
streamed and handed out in fixed-size chunks; chunk boundaries are a pure
function of line number, so every run partitions the corpus identically and
results are reproducible regardless of worker scheduling.
"""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import Any, Iterator, Sequence


def stream_lines(cfg: dict[str, Any]) -> Iterator[str]:
    """Yield corpus lines, honouring run.sample_lines."""
    path = Path(cfg["corpus"]["path"])
    if not path.is_file():
        raise FileNotFoundError(
            f"corpus not found at {path}. See DATA_SOURCES.md for how to download it."
        )
    limit = cfg["run"].get("sample_lines")
    encoding = cfg["corpus"]["encoding"]
    errors = cfg["corpus"]["errors"]
    with gzip.open(path, "rt", encoding=encoding, errors=errors) as fh:
        if limit is None:
            yield from fh
        else:
            for n, line in enumerate(fh):
                if n >= limit:
                    break
                yield line


def chunks(cfg: dict[str, Any]) -> Iterator[list[str]]:
    """Yield lists of lines of size run.chunk_lines, in corpus order."""
    size = cfg["run"]["chunk_lines"]
    buf: list[str] = []
    for line in stream_lines(cfg):
        buf.append(line)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf
