"""Hostile-input safety facade for the v0.30 Synthetic Phrase Substrate seed.

CMPNX15's first writer already bounded physical records to <=8 MiB, but a hostile authenticated metadata table
could reference those phrases many times and make the research reader materialize an arbitrarily large logical
file/tree.  That is a resource-safety violation, not acceptable breakthrough debt.

This facade preflights the authenticated metadata *before* the original materializer joins any phrase bytes.
The limits are intentionally conservative for the current public research corpus.  A future streaming reader
may raise logical archive capacity without raising peak memory, but it must do so by changing the execution
model rather than by deleting these bounds.
"""
from __future__ import annotations

from experiments import entropygraph_v030_attractor_substrate as S

MAX_LOGICAL_FILE = 64 * 1024 * 1024
MAX_MATERIALIZED_TREE = 256 * 1024 * 1024
MAX_TOTAL_REFERENCES = 1_000_000
MAX_RECORDS = 64

_original_materialize = S._materialize


def _preflight(path) -> None:
    stream, meta, _, offsets = S._open(path)
    try:
        if len(offsets) > MAX_RECORDS:
            raise RuntimeError("substrate record-count resource bound exceeded")
        phrases = meta.get("phrases", [])
        if not isinstance(phrases, list) or len(phrases) > S.MAX_PHRASES:
            raise RuntimeError("substrate phrase table resource bound exceeded")
        unique_bytes = 0
        for desc in phrases:
            if not isinstance(desc, list) or len(desc) != 5:
                raise RuntimeError("malformed substrate phrase descriptor")
            _, offset, length, _, use_count = desc
            offset = int(offset); length = int(length); use_count = int(use_count)
            if offset < 0 or length < 0 or length > S.MAX_PHRASE or use_count < 1:
                raise RuntimeError("substrate phrase resource declaration out of bounds")
            unique_bytes += length
            if unique_bytes > MAX_MATERIALIZED_TREE:
                raise RuntimeError("substrate unique phrase bytes exceed materialization budget")

        files = meta.get("files", {})
        if not isinstance(files, dict) or len(files) > S.MAX_FILES:
            raise RuntimeError("substrate file table resource bound exceeded")
        tree_bytes = 0
        references = 0
        for rel, desc in files.items():
            if not isinstance(rel, str) or not isinstance(desc, list) or len(desc) != 3:
                raise RuntimeError("malformed substrate file descriptor")
            refs, logical_size, _ = desc
            logical_size = int(logical_size)
            if logical_size < 0 or logical_size > MAX_LOGICAL_FILE:
                raise RuntimeError("substrate logical file materialization bound exceeded")
            if not isinstance(refs, list) or len(refs) > S.MAX_PHRASES:
                raise RuntimeError("substrate file parse resource bound exceeded")
            references += len(refs)
            tree_bytes += logical_size
            if references > MAX_TOTAL_REFERENCES:
                raise RuntimeError("substrate total reference budget exceeded")
            if tree_bytes > MAX_MATERIALIZED_TREE:
                raise RuntimeError("substrate tree materialization budget exceeded")
    finally:
        stream.close()


def _bounded_materialize(path):
    _preflight(path)
    return _original_materialize(path)


S._materialize = _bounded_materialize

build_raw = S.build_raw
build = S.build
extract = S.extract
strong_verify = S.strong_verify
treehash = S.treehash
MAX_DECODE_UNIT = S.MAX_DECODE_UNIT
RESOURCE_LIMITS = {
    "max_decode_unit": S.MAX_DECODE_UNIT,
    "max_logical_file": MAX_LOGICAL_FILE,
    "max_materialized_tree": MAX_MATERIALIZED_TREE,
    "max_total_references": MAX_TOTAL_REFERENCES,
    "max_records": MAX_RECORDS,
    "max_phrases": S.MAX_PHRASES,
    "max_phrase_bytes": S.MAX_PHRASE,
}
