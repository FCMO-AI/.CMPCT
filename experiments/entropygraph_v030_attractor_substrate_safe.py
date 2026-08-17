"""Hostile-input safety facade for the v0.30 Synthetic Phrase Substrate seed.

CMPNX15's first writer already bounded physical records to <=8 MiB, but a hostile authenticated metadata table
could reference those phrases many times and make the research reader materialize an arbitrarily large logical
file/tree.  That is a resource-safety violation, not acceptable breakthrough debt.

This facade preflights the authenticated metadata *before* the original materializer joins any phrase bytes.
It additionally makes the complete research container canonical enough to reason about production promotion:
record offsets must describe one contiguous physical region before the authenticated tail copy, phrase locations
must fit the declared physical records, file paths are rejected during verification rather than only extraction,
and phrase use counts must exactly match the authenticated file parses.

The limits are intentionally conservative for the current public research corpus.  A future streaming reader
may raise logical archive capacity without raising peak memory, but it must do so by changing the execution
model rather than by deleting these bounds.

Footnote: the historical CMPNX15 implementation remains untouched as derivation evidence.  Benchmark and
strong-verification entrypoints import this facade first, so malformed-but-authenticated archives cannot use an
old permissive parse while productionization work is still deciding whether the substrate deserves integration.
"""
from __future__ import annotations

import os

from experiments import entropygraph_v030_attractor_substrate as S

MAX_LOGICAL_FILE = 64 * 1024 * 1024
MAX_MATERIALIZED_TREE = 256 * 1024 * 1024
MAX_TOTAL_REFERENCES = 1_000_000
MAX_RECORDS = 64

_original_materialize = S._materialize


def _bytes32(value, label: str) -> bytes:
    if not isinstance(value, (bytes, bytearray)) or len(value) != 32:
        raise RuntimeError(f"invalid substrate {label} hash")
    return bytes(value)


def _canonical_physical_layout(stream, meta: dict, record_start: int, offsets: list[int]) -> list[int]:
    """Validate the entire record span without materializing logical files.

    Footnote: merely authenticating the offsets array is insufficient when the archive producer is untrusted.
    The writer emits records contiguously, followed immediately by a duplicate authenticated metadata copy and
    footer.  Requiring that exact shape prevents offsets from pointing into metadata/footer bytes and prevents
    overlapping/aliased physical records from creating alternate encodings of the same logical archive.
    """
    if len(offsets) > MAX_RECORDS:
        raise RuntimeError("substrate record-count resource bound exceeded")
    leaves = list(meta.get("record_leaf_sha256", []))
    if len(leaves) != len(offsets):
        raise RuntimeError("substrate record table length mismatch")
    for leaf in leaves:
        _bytes32(leaf, "payload leaf")

    stream.seek(0, os.SEEK_END)
    file_size = stream.tell()
    if file_size < S.FTR.size:
        raise RuntimeError("short substrate footer")
    footer_offset = file_size - S.FTR.size
    stream.seek(footer_offset)
    footer = stream.read(S.FTR.size)
    if len(footer) != S.FTR.size:
        raise RuntimeError("short substrate footer")
    magic, tail_mcs, tail_mus, tail_sha, tail_merkle = S.FTR.unpack(footer)
    if magic != S.TAIL or tail_mcs > S.MAX_DECODE_UNIT or tail_mus > S.MAX_DECODE_UNIT:
        raise RuntimeError("invalid substrate authenticated tail declaration")
    tail_meta_offset = footer_offset - tail_mcs
    if tail_meta_offset < record_start:
        raise RuntimeError("substrate tail overlaps physical record region")
    stream.seek(tail_meta_offset)
    tail_comp = stream.read(tail_mcs)
    if len(tail_comp) != tail_mcs:
        raise RuntimeError("short substrate tail metadata")
    tail_meta, tail_offsets = S._decode_meta(tail_comp, tail_mus, tail_sha, tail_merkle)
    if tail_meta != meta or tail_offsets != offsets:
        raise RuntimeError("substrate primary/recovered metadata disagrees with authenticated tail")

    cursor = 0
    record_usizes: list[int] = []
    for record_id, offset in enumerate(offsets):
        if offset != cursor:
            raise RuntimeError("substrate physical records are not canonical contiguous records")
        stream.seek(record_start + offset)
        header = stream.read(S.PH.size)
        if len(header) != S.PH.size:
            raise RuntimeError("short substrate physical header during preflight")
        codec, usize, csize, _crc, logical_sha = S.PH.unpack(header)
        if codec not in {S.CODEC_RAW, S.CODEC_ZSTD}:
            raise RuntimeError("unsupported substrate physical codec")
        if usize > S.MAX_DECODE_UNIT or csize > usize:
            raise RuntimeError("substrate physical declaration exceeds canonical bounds")
        if codec == S.CODEC_RAW and csize != usize:
            raise RuntimeError("non-canonical substrate RAW physical length")
        if codec == S.CODEC_ZSTD and csize >= usize:
            raise RuntimeError("non-canonical substrate Zstd physical length")
        _bytes32(logical_sha, "physical logical")
        payload = stream.read(csize)
        if len(payload) != csize or S.H(payload) != leaves[record_id]:
            raise RuntimeError("substrate payload authentication during preflight")
        cursor += S.PH.size + csize
        if record_start + cursor > tail_meta_offset:
            raise RuntimeError("substrate physical record overlaps authenticated tail metadata")
        record_usizes.append(int(usize))
    if record_start + cursor != tail_meta_offset:
        raise RuntimeError("substrate physical span does not end at authenticated tail metadata")
    return record_usizes


def _preflight(path) -> None:
    stream, meta, record_start, offsets = S._open(path)
    try:
        record_usizes = _canonical_physical_layout(stream, meta, record_start, offsets)
        phrases = meta.get("phrases", [])
        if not isinstance(phrases, list) or len(phrases) > S.MAX_PHRASES:
            raise RuntimeError("substrate phrase table resource bound exceeded")
        unique_bytes = 0
        declared_uses: list[int] = []
        phrase_lengths: list[int] = []
        for desc in phrases:
            if not isinstance(desc, list) or len(desc) != 5:
                raise RuntimeError("malformed substrate phrase descriptor")
            record_id, offset, length, expected, use_count = desc
            record_id = int(record_id); offset = int(offset); length = int(length); use_count = int(use_count)
            _bytes32(expected, "phrase")
            if not 0 <= record_id < len(record_usizes):
                raise RuntimeError("substrate phrase record id out of bounds")
            if offset < 0 or length < 0 or length > S.MAX_PHRASE or use_count < 1:
                raise RuntimeError("substrate phrase resource declaration out of bounds")
            if offset + length > record_usizes[record_id]:
                raise RuntimeError("substrate phrase exceeds declared physical record")
            unique_bytes += length
            if unique_bytes > MAX_MATERIALIZED_TREE:
                raise RuntimeError("substrate unique phrase bytes exceed materialization budget")
            phrase_lengths.append(length)
            declared_uses.append(use_count)

        files = meta.get("files", {})
        if not isinstance(files, dict) or len(files) > S.MAX_FILES:
            raise RuntimeError("substrate file table resource bound exceeded")
        tree_bytes = 0
        references = 0
        actual_uses = [0] * len(phrases)
        for rel, desc in files.items():
            if not isinstance(rel, str) or not isinstance(desc, list) or len(desc) != 3:
                raise RuntimeError("malformed substrate file descriptor")
            S._safe_relpath(rel)
            refs, logical_size, expected = desc
            _bytes32(expected, "file logical")
            logical_size = int(logical_size)
            if logical_size < 0 or logical_size > MAX_LOGICAL_FILE:
                raise RuntimeError("substrate logical file materialization bound exceeded")
            if not isinstance(refs, list) or len(refs) > S.MAX_PHRASES:
                raise RuntimeError("substrate file parse resource bound exceeded")
            references += len(refs)
            if references > MAX_TOTAL_REFERENCES:
                raise RuntimeError("substrate total reference budget exceeded")
            computed_size = 0
            for value in refs:
                phrase_id = int(value)
                if not 0 <= phrase_id < len(phrases):
                    raise RuntimeError("substrate file phrase id out of bounds")
                actual_uses[phrase_id] += 1
                computed_size += phrase_lengths[phrase_id]
                if computed_size > logical_size:
                    raise RuntimeError("substrate file parse exceeds declared logical size")
            if computed_size != logical_size:
                raise RuntimeError("substrate file parse length disagrees with logical size")
            tree_bytes += logical_size
            if tree_bytes > MAX_MATERIALIZED_TREE:
                raise RuntimeError("substrate tree materialization budget exceeded")
        if actual_uses != declared_uses:
            raise RuntimeError("substrate phrase use counts disagree with file parses")
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
    "canonical_contiguous_records": True,
    "verify_paths_before_materialization": True,
    "reconcile_phrase_use_counts": True,
}
