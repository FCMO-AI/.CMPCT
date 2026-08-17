"""CMPCT v0.30 child research — Synthetic Attractor/Phrase Substrate seed (CMPNX15).

This seed tests a representation gap left intentionally open by Mosaic: shared physical basis material does not
have to be an existing 128–512 KiB input node.  Files are partitioned with much finer locally-stable content-
defined phrases; exact phrase identities are shared across the whole tree; unique phrase bytes are arranged into
bounded solid substrate packs; and file parses point directly to phrase ids.

The seed is deliberately simpler than a full string-attractor or grammar compressor.  It exists to answer one
causal question with complete artifact accounting: is a synthetic fine-grained shared substrate worth pursuing
beyond accepted v0.29 once phrase-index, integrity, metadata and pack bytes are all charged?

Prior art is explicit: CDC, dictionary parsing, repetitive-collection grammars and string attractors are not new.
The CMPCT research boundary is a shallow authenticated archive embodiment plus exact-v0.29 tournament and a
later path to combine substrate atoms with Geometry/RSO.

Footnote: phrase packs are <= the inherited 8 MiB decode-unit ceiling.  The seed may still have high selective-
read amplification because a small phrase can live in a large solid pack.  That debt is measured and labelled;
it is not a safety-bound exception and it must be rehabilitated before any promotion.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import tempfile
import time

import msgpack

from cmpct.resemblance import fastcdc
from experiments import entropygraph_v029_release as BASE

H = BASE.H
zc = BASE.zc
zd = BASE.zd
PH = BASE.PH
CODEC_RAW = BASE.CODEC_RAW
CODEC_ZSTD = BASE.CODEC_ZSTD
MAX_DECODE_UNIT = int(BASE.MAX_DECODE_UNIT)
MAX_DECODER_MEMORY = int(BASE.MAX_DECODER_MEMORY)

MAG = b"CMPNX15\0"
TAIL = b"CMN15T\0\0"
HDR = struct.Struct("<8sQQIQQ32s32s")
FTR = struct.Struct("<8sQQ32s32s")
META_LEVEL = 12

AVG_PHRASE_CANDIDATES = (256, 512, 1024, 2048)
MIN_PHRASE = 64
MAX_PHRASE = 8192
MAX_PHRASES = 500_000
MAX_PACK_RAW = MAX_DECODE_UNIT
MAX_FILES = 100_000
ORDERINGS = ("encounter", "lexicographic")


def treehash(root: Path) -> str:
    return BASE.accepted.BASE.treehash(root)


def _merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        return H(b"cmpct-substrate-empty-v1")
    level = [H(b"\x00" + leaf) for leaf in leaves]
    while len(level) > 1:
        if len(level) & 1:
            level.append(level[-1])
        level = [H(b"\x01" + level[index] + level[index + 1]) for index in range(0, len(level), 2)]
    return level[0]


def _compress_record(raw: bytes) -> tuple[int, bytes]:
    payload = zc(raw, 19)
    return (CODEC_ZSTD, payload) if len(payload) < len(raw) else (CODEC_RAW, raw)


def _split(raw: bytes, average: int) -> list[bytes]:
    if not raw:
        return [b""]
    if average not in AVG_PHRASE_CANDIDATES:
        raise ValueError("unsupported substrate phrase average")
    minimum = max(MIN_PHRASE, average // 4)
    maximum = min(MAX_PHRASE, average * 4)
    if len(raw) <= maximum:
        return [raw]
    chunks = fastcdc(raw, min_size=minimum, avg_size=average, max_size=maximum)
    out = [raw[chunk.offset:chunk.offset + chunk.length] for chunk in chunks]
    if b"".join(out) != raw or any(len(part) > maximum for part in out):
        raise RuntimeError("substrate phrase splitter violated exact partition")
    return out


def _collect(root: Path, average: int) -> tuple[list[str], list[bytes], list[list[int]], list[int]]:
    files = sorted(path for path in root.rglob("*") if path.is_file())
    if len(files) > MAX_FILES:
        raise ValueError("substrate file-count ceiling exceeded")
    rels = [path.relative_to(root).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]

    phrases: list[bytes] = []
    digest_to_ids: dict[bytes, list[int]] = {}
    uses: list[int] = []
    file_phrases: list[list[int]] = []
    for raw in raws:
        refs: list[int] = []
        for part in _split(raw, average):
            digest = H(part)
            phrase_id = None
            for candidate_id in digest_to_ids.get(digest, []):
                if phrases[candidate_id] == part:
                    phrase_id = candidate_id
                    break
            if phrase_id is None:
                if len(phrases) >= MAX_PHRASES:
                    raise ValueError("substrate phrase-count ceiling exceeded")
                phrase_id = len(phrases)
                phrases.append(part)
                uses.append(0)
                digest_to_ids.setdefault(digest, []).append(phrase_id)
            uses[phrase_id] += 1
            refs.append(phrase_id)
        file_phrases.append(refs)
    return rels, raws, file_phrases, uses


def _reorder(phrases: list[bytes], file_phrases: list[list[int]], ordering: str) -> tuple[list[bytes], list[list[int]], list[int]]:
    if ordering == "encounter":
        order = list(range(len(phrases)))
    elif ordering == "lexicographic":
        # Footnote: lexicographic order is a cheap physical-layout hypothesis, not semantic sorting.  Related
        # phrase prefixes become adjacent for solid Zstd while exact-cost tournament decides whether the parse
        # id perturbation was worth it.
        order = sorted(range(len(phrases)), key=lambda phrase_id: (phrases[phrase_id], phrase_id))
    else:
        raise ValueError("unsupported substrate ordering")
    remap = {old: new for new, old in enumerate(order)}
    reordered = [phrases[old] for old in order]
    parses = [[remap[phrase_id] for phrase_id in refs] for refs in file_phrases]
    return reordered, parses, order


def _pack_phrases(phrases: list[bytes]) -> tuple[list[tuple[int, int, bytes, int, bytes]], list[list[int]]]:
    records: list[tuple[int, int, bytes, int, bytes]] = []
    locations: list[list[int]] = [[-1, -1, -1] for _ in phrases]
    current_ids: list[int] = []
    current_raw = 0

    def flush() -> None:
        nonlocal current_ids, current_raw
        if not current_ids:
            return
        raw = b"".join(phrases[phrase_id] for phrase_id in current_ids)
        if len(raw) > MAX_PACK_RAW:
            raise RuntimeError("substrate raw pack exceeds decode ceiling")
        codec, payload = _compress_record(raw)
        record_id = len(records)
        records.append((codec, len(raw), payload, binascii.crc32(raw) & 0xFFFFFFFF, H(raw)))
        offset = 0
        for phrase_id in current_ids:
            length = len(phrases[phrase_id])
            locations[phrase_id] = [record_id, offset, length]
            offset += length
        current_ids = []
        current_raw = 0

    for phrase_id, phrase in enumerate(phrases):
        if len(phrase) > MAX_PACK_RAW:
            raise ValueError("individual substrate phrase exceeds decode ceiling")
        if current_ids and current_raw + len(phrase) > MAX_PACK_RAW:
            flush()
        current_ids.append(phrase_id)
        current_raw += len(phrase)
    flush()
    if any(location[0] < 0 for location in locations):
        raise RuntimeError("substrate phrase location missing")
    return records, locations


def _build_one(root: Path, out: Path, average: int, ordering: str) -> dict:
    started = time.perf_counter()
    rels, raws, original_parses, uses = _collect(root, average)
    # Reconstruct encounter-order phrase table once from file partitions so we do not keep a second hidden
    # representation.  The first occurrence of each phrase id is authoritative.
    phrase_table: list[bytes | None] = [None] * len(uses)
    for raw, refs in zip(raws, original_parses):
        parts = _split(raw, average)
        if len(parts) != len(refs):
            raise RuntimeError("substrate phrase parse count drift")
        for phrase_id, part in zip(refs, parts):
            current = phrase_table[phrase_id]
            if current is None:
                phrase_table[phrase_id] = part
            elif current != part:
                raise RuntimeError("substrate phrase identity collision")
    phrases = [part if part is not None else b"" for part in phrase_table]
    ordered, parses, old_order = _reorder(phrases, original_parses, ordering)
    ordered_uses = [uses[old] for old in old_order]
    records, locations = _pack_phrases(ordered)

    files_meta = {}
    for rel, raw, refs in zip(rels, raws, parses):
        files_meta[rel] = [refs, len(raw), H(raw)]
    phrase_meta = [
        [record_id, offset, length, H(ordered[phrase_id]), ordered_uses[phrase_id]]
        for phrase_id, (record_id, offset, length) in enumerate(locations)
    ]
    leaves = [H(record[2]) for record in records]
    merkle = _merkle_root(leaves)
    offsets: list[int] = []
    cursor = 0
    for _, _, payload, _, _ in records:
        offsets.append(cursor)
        cursor += PH.size + len(payload)

    meta = {
        "v": 1,
        "engine": "Synthetic-Phrase-Substrate-v1",
        "files": files_meta,
        "phrases": phrase_meta,
        "record_rel_offsets": offsets,
        "record_leaf_sha256": leaves,
        "tree_sha256": treehash(root),
        "average_phrase": average,
        "ordering": ordering,
        "max_decode_unit": MAX_DECODE_UNIT,
        "max_decoder_memory": MAX_DECODER_MEMORY,
        "max_dependency_depth": 1,
        "locality_debt": "solid phrase packs may exceed promotion read-amplification law; research seed only",
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    if len(meta_raw) > MAX_DECODE_UNIT:
        raise ValueError("substrate metadata exceeds decode ceiling")
    meta_comp = zc(meta_raw, META_LEVEL)
    with out.open("wb") as stream:
        stream.write(HDR.pack(MAG, len(meta_comp), len(meta_raw), len(records), MAX_DECODE_UNIT,
                              MAX_DECODER_MEMORY, H(meta_raw), merkle))
        stream.write(meta_comp)
        for codec, usize, payload, crc, logical_sha in records:
            stream.write(PH.pack(codec, usize, len(payload), crc, logical_sha))
            stream.write(payload)
        stream.write(meta_comp)
        stream.write(FTR.pack(TAIL, len(meta_comp), len(meta_raw), H(meta_raw), merkle))

    logical = sum(map(len, raws))
    unique_raw = sum(map(len, ordered))
    shared_phrase_ids = sum(use > 1 for use in ordered_uses)
    shared_occurrences = sum(use for use in ordered_uses if use > 1)
    exact_dedup_saved = sum(len(ordered[index]) * (use - 1) for index, use in enumerate(ordered_uses) if use > 1)
    worst_amp = 1.0
    for phrase_id, (record_id, _, length) in enumerate(locations):
        if length:
            worst_amp = max(worst_amp, records[record_id][1] / length)
    return {
        "create_s": time.perf_counter() - started,
        "archive_bytes": out.stat().st_size,
        "logical_bytes": logical,
        "files": len(rels),
        "phrases": len(ordered),
        "shared_phrase_ids": shared_phrase_ids,
        "shared_phrase_occurrences": shared_occurrences,
        "unique_phrase_raw_bytes": unique_raw,
        "exact_phrase_dedup_saved_raw_bytes": exact_dedup_saved,
        "physical_records": len(records),
        "metadata_raw_bytes": len(meta_raw),
        "metadata_compressed_bytes": len(meta_comp),
        "average_phrase": average,
        "ordering": ordering,
        "max_dependency_depth": 1,
        "max_decode_unit": MAX_DECODE_UNIT,
        "worst_phrase_read_amplification": worst_amp,
        "locality_debt_open": worst_amp > 8.0,
    }


def _safe_relpath(rel: str) -> PurePosixPath:
    if not rel or "\\" in rel or "\x00" in rel:
        raise RuntimeError("unsafe substrate path syntax")
    parsed = PurePosixPath(rel)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise RuntimeError("unsafe substrate path")
    return parsed


def _decode_meta(comp: bytes, raw_size: int, expected_sha: bytes, expected_merkle: bytes,
                 expected_count: int | None = None) -> tuple[dict, list[int]]:
    if raw_size > MAX_DECODE_UNIT or len(comp) > MAX_DECODE_UNIT:
        raise RuntimeError("substrate metadata exceeds decode ceiling")
    raw = zd(comp, raw_size)
    if H(raw) != expected_sha:
        raise RuntimeError("substrate metadata authentication")
    meta = msgpack.unpackb(raw, raw=False, strict_map_key=False)
    if meta.get("v") != 1 or meta.get("engine") != "Synthetic-Phrase-Substrate-v1":
        raise RuntimeError("unsupported substrate metadata")
    if int(meta.get("max_dependency_depth", 99)) > 1:
        raise RuntimeError("substrate dependency depth exceeds policy")
    if int(meta.get("max_decode_unit", MAX_DECODE_UNIT + 1)) > MAX_DECODE_UNIT:
        raise RuntimeError("substrate decode unit exceeds policy")
    if int(meta.get("max_decoder_memory", MAX_DECODER_MEMORY + 1)) > MAX_DECODER_MEMORY:
        raise RuntimeError("substrate decoder memory exceeds policy")
    leaves = list(meta.get("record_leaf_sha256", []))
    offsets = [int(value) for value in meta.get("record_rel_offsets", [])]
    if expected_count is not None and len(leaves) != expected_count:
        raise RuntimeError("substrate record-count mismatch")
    if len(offsets) != len(leaves) or _merkle_root(leaves) != expected_merkle:
        raise RuntimeError("substrate record table / Merkle mismatch")
    if offsets != sorted(offsets) or any(value < 0 for value in offsets):
        raise RuntimeError("substrate record offsets invalid")
    return meta, offsets


def _open(path: Path):
    stream = path.open("rb")
    primary_error: Exception | None = None
    try:
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("short substrate header")
        magic, mcs, mus, count, max_decode, max_memory, meta_sha, merkle = HDR.unpack(header)
        if magic != MAG or mcs > MAX_DECODE_UNIT or mus > MAX_DECODE_UNIT:
            raise RuntimeError("invalid substrate primary declaration")
        comp = stream.read(mcs)
        if len(comp) != mcs:
            raise RuntimeError("short substrate primary metadata")
        meta, offsets = _decode_meta(comp, mus, meta_sha, merkle, count)
        if int(meta["max_decode_unit"]) != max_decode or int(meta["max_decoder_memory"]) != max_memory:
            raise RuntimeError("substrate header/meta resource mismatch")
        return stream, meta, HDR.size + mcs, offsets
    except Exception as exc:
        primary_error = exc
    try:
        stream.seek(-FTR.size, os.SEEK_END)
        footer_offset = stream.tell()
        footer = stream.read(FTR.size)
        magic, mcs, mus, meta_sha, merkle = FTR.unpack(footer)
        if magic != TAIL or mcs > MAX_DECODE_UNIT or mus > MAX_DECODE_UNIT:
            raise RuntimeError("invalid substrate tail declaration")
        meta_offset = footer_offset - mcs
        if meta_offset < HDR.size:
            raise RuntimeError("substrate tail metadata offset invalid")
        stream.seek(meta_offset)
        comp = stream.read(mcs)
        meta, offsets = _decode_meta(comp, mus, meta_sha, merkle)
        stream.seek(0)
        header = stream.read(HDR.size)
        if len(header) != HDR.size:
            raise RuntimeError("cannot recover substrate record start")
        _, primary_mcs, _, _, _, _, _, _ = HDR.unpack(header)
        if primary_mcs > MAX_DECODE_UNIT:
            raise RuntimeError("substrate primary metadata declaration exceeds bound")
        return stream, meta, HDR.size + primary_mcs, offsets
    except Exception as tail_error:
        stream.close()
        raise RuntimeError(f"no authenticated substrate metadata: primary={primary_error!r}; tail={tail_error!r}") from tail_error


def _materialize(path: Path) -> tuple[dict[str, bytes], dict]:
    stream, meta, record_start, offsets = _open(path)
    leaves = list(meta["record_leaf_sha256"])
    record_cache: dict[int, bytes] = {}

    def record(record_id: int) -> bytes:
        if record_id in record_cache:
            return record_cache[record_id]
        if not 0 <= record_id < len(offsets):
            raise RuntimeError("substrate record id out of bounds")
        stream.seek(record_start + offsets[record_id])
        header = stream.read(PH.size)
        if len(header) != PH.size:
            raise RuntimeError("short substrate physical header")
        codec, usize, csize, crc, logical_sha = PH.unpack(header)
        if usize > MAX_DECODE_UNIT or csize > MAX_DECODE_UNIT + 1024 * 1024:
            raise RuntimeError("substrate physical declaration exceeds bound")
        payload = stream.read(csize)
        if len(payload) != csize or H(payload) != leaves[record_id]:
            raise RuntimeError("substrate payload authentication")
        raw = payload if codec == CODEC_RAW else zd(payload, usize) if codec == CODEC_ZSTD else None
        if raw is None or len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or H(raw) != logical_sha:
            raise RuntimeError("substrate physical integrity")
        record_cache[record_id] = raw
        return raw

    phrases_meta = list(meta.get("phrases", []))
    phrase_cache: dict[int, bytes] = {}

    def phrase(phrase_id: int) -> bytes:
        if phrase_id in phrase_cache:
            return phrase_cache[phrase_id]
        if not 0 <= phrase_id < len(phrases_meta):
            raise RuntimeError("substrate phrase id out of bounds")
        desc = phrases_meta[phrase_id]
        if not isinstance(desc, list) or len(desc) != 5:
            raise RuntimeError("malformed substrate phrase descriptor")
        record_id, offset, length, expected, use_count = desc
        record_id = int(record_id); offset = int(offset); length = int(length); use_count = int(use_count)
        if offset < 0 or length < 0 or use_count < 1 or offset + length > MAX_DECODE_UNIT:
            raise RuntimeError("substrate phrase descriptor out of bounds")
        raw_record = record(record_id)
        if offset + length > len(raw_record):
            raise RuntimeError("substrate phrase exceeds physical record")
        raw = raw_record[offset:offset + length]
        if H(raw) != expected:
            raise RuntimeError("substrate phrase integrity")
        phrase_cache[phrase_id] = raw
        return raw

    output: dict[str, bytes] = {}
    try:
        files = meta.get("files", {})
        if not isinstance(files, dict) or len(files) > MAX_FILES:
            raise RuntimeError("substrate file table out of bounds")
        for rel, desc in files.items():
            if not isinstance(rel, str) or not isinstance(desc, list) or len(desc) != 3:
                raise RuntimeError("malformed substrate file descriptor")
            refs, logical_size, expected = desc
            if not isinstance(refs, list) or len(refs) > MAX_PHRASES:
                raise RuntimeError("substrate file parse out of bounds")
            data = b"".join(phrase(int(phrase_id)) for phrase_id in refs)
            if len(data) != int(logical_size) or H(data) != expected:
                raise RuntimeError("substrate logical file integrity")
            output[rel] = data
    finally:
        stream.close()
    return output, meta


def strong_verify(archive: Path) -> dict:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic != MAG:
        return BASE.strong_verify(archive)
    files, meta = _materialize(archive)
    h = hashlib.sha256()
    for rel in sorted(files):
        rb = rel.encode()
        data = files[rel]
        h.update(len(rb).to_bytes(4, "little")); h.update(rb)
        h.update(len(data).to_bytes(8, "little")); h.update(data)
    got = h.hexdigest()
    if got != meta.get("tree_sha256"):
        raise RuntimeError("substrate tree identity mismatch")
    return {"ok": True, "files": len(files), "tree_sha256": got, "engine": meta.get("engine")}


def extract(archive: Path, dst: Path) -> None:
    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic != MAG:
        BASE.extract(archive, dst)
        return
    files, _ = _materialize(archive)
    shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True)
    resolved_root = dst.resolve()
    for rel, data in files.items():
        safe = _safe_relpath(rel)
        target = dst.joinpath(*safe.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        resolved = target.resolve()
        if resolved != resolved_root and resolved_root not in resolved.parents:
            raise RuntimeError("substrate resolved path escapes destination")
        target.write_bytes(data)


def build_raw(root: Path, out: Path) -> dict:
    """Tournament phrase granularity and physical ordering by complete CMPNX15 bytes."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-substrate-plans-") as td:
        temp = Path(td)
        rows = []
        for average in AVG_PHRASE_CANDIDATES:
            for ordering in ORDERINGS:
                candidate = temp / f"a{average}-{ordering}.cmpct"
                stats = _build_one(root, candidate, average, ordering)
                rows.append((candidate.stat().st_size, average, ordering, candidate, stats))
        rows.sort(key=lambda row: (row[0], row[1], row[2]))
        _, average, ordering, candidate, stats = rows[0]
        shutil.copyfile(candidate, out)
    result = dict(stats)
    result.update({
        "selected_average_phrase": average,
        "selected_ordering": ordering,
        "archive_bytes": out.stat().st_size,
        "plan_trials": len(AVG_PHRASE_CANDIDATES) * len(ORDERINGS),
        "portfolio_create_s": time.perf_counter() - started,
    })
    return result


def build(root: Path, out: Path) -> dict:
    """Complete-artifact portfolio: exact accepted-v0.29 fallback remains authoritative."""
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-substrate-portfolio-") as td:
        temp = Path(td)
        base_path = temp / "v029.cmpct"
        substrate_path = temp / "substrate.cmpct"
        base_stats = BASE.build(root, base_path)
        substrate_stats = build_raw(root, substrate_path)
        base_bytes = base_path.stat().st_size
        substrate_bytes = substrate_path.stat().st_size
        if substrate_bytes < base_bytes:
            shutil.copyfile(substrate_path, out)
            selected = "substrate"
        else:
            shutil.copyfile(base_path, out)
            selected = "v029-fallback"
    return {
        "selected": selected,
        "archive_bytes": out.stat().st_size,
        "v029_bytes": base_bytes,
        "substrate_bytes": substrate_bytes,
        "saving_vs_v029_bytes": base_bytes - out.stat().st_size,
        "raw_substrate_delta_vs_v029_bytes": base_bytes - substrate_bytes,
        "portfolio_create_s": time.perf_counter() - started,
        "v029": base_stats,
        "substrate": substrate_stats,
    }


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT synthetic phrase substrate research seed")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    p = sub.add_parser("extract"); p.add_argument("archive", type=Path); p.add_argument("destination", type=Path)
    p = sub.add_parser("verify"); p.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.cmd == "pack":
        print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "extract":
        extract(args.archive, args.destination); print(json.dumps({"ok": True}, indent=2))
    else:
        print(json.dumps(strong_verify(args.archive), indent=2, default=str))


if __name__ == "__main__":
    _main()
