"""CMPCT v0.30 research seed — exact depth-1 PrefixGraph.

PrefixGraph tests an orthogonal representation hypothesis for version families: one self-contained direct
member can act as a raw-content Zstandard prefix for its siblings.  This is not a trained dictionary and it
is not a semantic patch format; the exact source bytes of a stored anchor are the only reference context.

The oracle deliberately tournaments complete serialized archives across every admissible anchor (bounded by
``MAX_ANCHOR_AUDITIONS``), and every non-anchor member independently keeps ordinary Zstd when raw-prefix
compression loses.  Dependency depth is therefore exactly 0 or 1 and a bad resemblance guess cannot force
a payload regression inside a candidate archive.

Footnote: ``CMPNXP1`` is research-only.  It does not change canonical revision 24.  Reader-visible promotion
would still require integration into the accepted authenticated graph, recovery/native-reader parity,
selective-read accounting, hostile parser tests, and the ordinary release gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import struct
import tempfile
import time

import msgpack
import zstandard as zstd

MAGIC = b"CMPNXP1\0"
TAIL = b"CMPNXP1T"
HEADER = struct.Struct("<8sQQ32s")
FOOTER = struct.Struct("<8sQQ32s")

PAYLOAD_LEVEL = 19
META_LEVEL = 12
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_FILES = 1024
MAX_META_BYTES = 8 * 1024 * 1024
MAX_ANCHOR_AUDITIONS = 32
MIN_PREFIX_PAYLOAD_SAVING = 32


def H(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _treehash_parts(rels: list[str], raws: list[bytes]) -> str:
    h = hashlib.sha256()
    for rel, data in sorted(zip(rels, raws, strict=True), key=lambda item: item[0]):
        rb = rel.encode("utf-8")
        h.update(len(rb).to_bytes(4, "little")); h.update(rb)
        h.update(len(data).to_bytes(8, "little")); h.update(data)
    return h.hexdigest()


def treehash(root: Path) -> str:
    files = sorted(p for p in root.rglob("*") if p.is_file())
    return _treehash_parts(
        [path.relative_to(root).as_posix() for path in files],
        [path.read_bytes() for path in files],
    )


def _compress(raw: bytes) -> bytes:
    return zstd.ZstdCompressor(level=PAYLOAD_LEVEL).compress(raw)


def _prefix_codec(prefix: bytes) -> tuple[zstd.ZstdCompressor, zstd.ZstdCompressionDict]:
    dictionary = zstd.ZstdCompressionDict(prefix, dict_type=zstd.DICT_TYPE_RAWCONTENT)
    return zstd.ZstdCompressor(level=PAYLOAD_LEVEL, dict_data=dictionary), dictionary


def _safe_relpath(rel: str) -> PurePosixPath:
    if not rel or "\\" in rel or "\x00" in rel:
        raise RuntimeError("unsafe PrefixGraph path syntax")
    parsed = PurePosixPath(rel)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise RuntimeError("unsafe PrefixGraph extraction path")
    return parsed


def _anchor_indices(count: int) -> list[int]:
    if count <= MAX_ANCHOR_AUDITIONS:
        return list(range(count))
    # Footnote: large families stay work-bounded.  The sampler spans the ordered family instead of trusting
    # filenames or extensions; exact full-archive bytes still decide among the nominated anchors.
    return sorted({round(i * (count - 1) / (MAX_ANCHOR_AUDITIONS - 1)) for i in range(MAX_ANCHOR_AUDITIONS)})


def _serialize_candidate(
    rels: list[str],
    raws: list[bytes],
    direct_payloads: list[bytes],
    expected_tree: str,
    anchor: int | None,
) -> tuple[bytes, dict]:
    if len(raws) > MAX_FILES:
        raise ValueError("PrefixGraph file-count ceiling exceeded")
    if len(direct_payloads) != len(raws):
        raise ValueError("PrefixGraph direct-payload cache length mismatch")
    prefix_compressor = None
    if anchor is not None:
        prefix_compressor, _ = _prefix_codec(raws[anchor])

    payloads: list[bytes] = []
    records: list[list] = []
    prefix_records = 0
    payload_saving = 0
    for index, (raw, direct) in enumerate(zip(raws, direct_payloads, strict=True)):
        kind = "direct"; base = -1; payload = direct
        if anchor is not None and index != anchor and raw and raws[anchor]:
            assert prefix_compressor is not None
            trial = prefix_compressor.compress(raw)
            if len(direct) - len(trial) >= MIN_PREFIX_PAYLOAD_SAVING:
                kind = "prefix"; base = anchor; payload = trial
                prefix_records += 1; payload_saving += len(direct) - len(trial)
        payloads.append(payload)
        records.append([kind, base, len(raw), len(payload), H(payload), H(raw)])

    meta = {
        "v": 1,
        "engine": "PrefixGraph-depth1-v1",
        "tree_sha256": expected_tree,
        "files": rels,
        "records": records,
        "anchor": -1 if anchor is None else anchor,
        "max_dependency_depth": 1 if prefix_records else 0,
        "max_file_bytes": MAX_FILE_BYTES,
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    if len(meta_raw) > MAX_META_BYTES:
        raise ValueError("PrefixGraph metadata ceiling exceeded")
    meta_comp = zstd.ZstdCompressor(level=META_LEVEL).compress(meta_raw)
    header = HEADER.pack(MAGIC, len(meta_comp), len(meta_raw), H(meta_raw))
    footer = FOOTER.pack(TAIL, len(meta_comp), len(meta_raw), H(meta_raw))
    blob = header + meta_comp + b"".join(payloads) + meta_comp + footer
    return blob, {
        "anchor": anchor,
        "archive_bytes": len(blob),
        "prefix_records": prefix_records,
        "payload_saving_bytes": payload_saving,
        "meta_raw_bytes": len(meta_raw),
        "meta_comp_bytes": len(meta_comp),
    }


def _candidate_key(blob: bytes, stats: dict) -> tuple[int, int]:
    """Return the exact historical PrefixGraph complete-artifact tournament key."""
    anchor = stats["anchor"]
    return len(blob), -1 if anchor is None else int(anchor)


def build(root: Path, out: Path) -> dict:
    started = time.perf_counter()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files or len(files) > MAX_FILES:
        raise ValueError("PrefixGraph requires 1..MAX_FILES regular files")
    rels = [p.relative_to(root).as_posix() for p in files]
    raws = [p.read_bytes() for p in files]
    if any(len(raw) > MAX_FILE_BYTES for raw in raws):
        raise ValueError("PrefixGraph research seed file ceiling exceeded")
    expected_tree = _treehash_parts(rels, raws)

    # Footnote: the direct Zstd-19 floor is anchor-independent.  Compute it exactly once and share those
    # immutable payload bytes across the anchor tournament; recomputing it for every anchor changes no
    # candidate bytes but multiplies encoder CPU by roughly the audition count.
    direct_payloads = [_compress(raw) for raw in raws]
    all_direct, direct_stats = _serialize_candidate(rels, raws, direct_payloads, expected_tree, None)

    # The historical implementation retained every complete candidate blob until the tournament ended.  Only
    # the current exact minimum can possibly matter to the final result, so keep one incumbent and release each
    # losing candidate immediately.  This preserves the complete candidate set, complete-artifact pricing and
    # exact `(archive_bytes, anchor)` tie law while removing O(auditions * archive_bytes) retained candidate
    # ownership.  It is intentionally not an early terminal: every nominated anchor is still fully constructed.
    blob, stats = all_direct, direct_stats
    incumbent_key = _candidate_key(blob, stats)
    for anchor in _anchor_indices(len(raws)):
        candidate_blob, candidate_stats = _serialize_candidate(
            rels, raws, direct_payloads, expected_tree, anchor
        )
        candidate_key = _candidate_key(candidate_blob, candidate_stats)
        if candidate_key < incumbent_key:
            blob, stats = candidate_blob, candidate_stats
            incumbent_key = candidate_key

    out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(blob)
    stats = dict(stats)
    stats.update({
        "archive_bytes": len(blob),
        "all_direct_bytes": len(all_direct),
        "saving_vs_all_direct_bytes": len(all_direct) - len(blob),
        "anchor_auditions": len(_anchor_indices(len(raws))),
        "files": len(files),
        "logical_bytes": sum(map(len, raws)),
        "tree_sha256": expected_tree,
        "create_s": time.perf_counter() - started,
        "max_dependency_depth": 1 if stats["prefix_records"] else 0,
    })
    return stats


def _read(path: Path) -> tuple[dict, list[bytes]]:
    data = path.read_bytes()
    if len(data) < HEADER.size + FOOTER.size:
        raise RuntimeError("short PrefixGraph archive")
    magic, mcs, mus, expected_meta = HEADER.unpack_from(data, 0)
    if magic != MAGIC or mcs > MAX_META_BYTES or mus > MAX_META_BYTES:
        raise RuntimeError("invalid PrefixGraph declaration")
    meta_start = HEADER.size; meta_end = meta_start + mcs
    if meta_end > len(data) - FOOTER.size:
        raise RuntimeError("truncated PrefixGraph metadata")
    meta_raw = zstd.ZstdDecompressor().decompress(data[meta_start:meta_end], max_output_size=mus)
    if len(meta_raw) != mus or H(meta_raw) != expected_meta:
        raise RuntimeError("PrefixGraph metadata authentication")
    meta = msgpack.unpackb(
        meta_raw, raw=False, strict_map_key=False,
        max_array_len=MAX_FILES * 8 + 64, max_map_len=64,
        max_str_len=MAX_META_BYTES, max_bin_len=MAX_META_BYTES,
    )
    records = meta.get("records"); rels = meta.get("files")
    if meta.get("v") != 1 or not isinstance(records, list) or not isinstance(rels, list):
        raise RuntimeError("unsupported PrefixGraph metadata")
    if len(records) != len(rels) or not 1 <= len(records) <= MAX_FILES:
        raise RuntimeError("PrefixGraph record-count mismatch")
    expected_tree = meta.get("tree_sha256")
    if not isinstance(expected_tree, str) or len(expected_tree) != 64:
        raise RuntimeError("PrefixGraph tree identity declaration")

    footer_off = len(data) - FOOTER.size
    tail, tail_mcs, tail_mus, tail_sha = FOOTER.unpack_from(data, footer_off)
    if tail != TAIL or tail_mcs != mcs or tail_mus != mus or tail_sha != expected_meta:
        raise RuntimeError("PrefixGraph tail mismatch")
    tail_meta_start = footer_off - mcs
    if tail_meta_start < meta_end or data[tail_meta_start:footer_off] != data[meta_start:meta_end]:
        raise RuntimeError("PrefixGraph recovery metadata mismatch")

    payload_pos = meta_end; payloads: list[bytes] = []
    for desc in records:
        if not isinstance(desc, list) or len(desc) != 6:
            raise RuntimeError("malformed PrefixGraph record")
        csize = int(desc[3])
        if csize < 0 or csize > MAX_FILE_BYTES + 1024 * 1024 or payload_pos + csize > tail_meta_start:
            raise RuntimeError("PrefixGraph payload boundary")
        payload = data[payload_pos:payload_pos + csize]; payload_pos += csize
        if H(payload) != desc[4]:
            raise RuntimeError("PrefixGraph payload authentication")
        payloads.append(payload)
    if payload_pos != tail_meta_start:
        raise RuntimeError("PrefixGraph physical table is not contiguous")
    return meta, payloads


def _materialize(path: Path) -> tuple[dict[str, bytes], dict]:
    meta, payloads = _read(path); records = meta["records"]; rels = meta["files"]
    cache: dict[int, bytes] = {}

    def decode(index: int) -> bytes:
        if index in cache:
            return cache[index]
        kind, base, usize, _, _, expected = records[index]
        usize = int(usize)
        if usize < 0 or usize > MAX_FILE_BYTES:
            raise RuntimeError("PrefixGraph logical file ceiling")
        if kind == "direct":
            raw = zstd.ZstdDecompressor().decompress(payloads[index], max_output_size=usize)
        elif kind == "prefix":
            base = int(base)
            if not 0 <= base < len(records) or records[base][0] != "direct":
                raise RuntimeError("PrefixGraph depth-1 base violation")
            anchor = decode(base)
            dictionary = zstd.ZstdCompressionDict(anchor, dict_type=zstd.DICT_TYPE_RAWCONTENT)
            raw = zstd.ZstdDecompressor(dict_data=dictionary).decompress(payloads[index], max_output_size=usize)
        else:
            raise RuntimeError("unknown PrefixGraph record kind")
        if len(raw) != usize or H(raw) != expected:
            raise RuntimeError("PrefixGraph logical integrity")
        cache[index] = raw
        return raw

    output: dict[str, bytes] = {}
    for index, rel in enumerate(rels):
        _safe_relpath(rel); output[rel] = decode(index)
    return output, meta


def extract(archive: Path, dst: Path) -> None:
    files, _ = _materialize(archive)
    shutil.rmtree(dst, ignore_errors=True); dst.mkdir(parents=True)
    for rel, raw in files.items():
        safe = _safe_relpath(rel); target = dst.joinpath(*safe.parts)
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)


def strong_verify(archive: Path) -> dict:
    files, meta = _materialize(archive)
    with tempfile.TemporaryDirectory(prefix="cmpct-prefixgraph-verify-") as td:
        root = Path(td)
        for rel, raw in files.items():
            target = root.joinpath(*_safe_relpath(rel).parts); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        got = treehash(root)
    # Footnote: per-file hashes prove local reconstruction, while the authenticated tree declaration binds
    # filenames, ordering, sizes and contents into one source identity.  Both must agree before verification
    # can report success; the outer benchmark remains an independent comparison to the live source tree.
    if got != meta.get("tree_sha256"):
        raise RuntimeError("PrefixGraph tree identity mismatch")
    return {"ok": True, "files": len(files), "tree_sha256": got, "engine": "PrefixGraph-depth1-v1"}


def _main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT v0.30 PrefixGraph research oracle")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("source", type=Path); p.add_argument("archive", type=Path)
    p = sub.add_parser("extract"); p.add_argument("archive", type=Path); p.add_argument("destination", type=Path)
    p = sub.add_parser("verify"); p.add_argument("archive", type=Path)
    args = parser.parse_args()
    if args.cmd == "pack": print(json.dumps(build(args.source, args.archive), indent=2, default=str))
    elif args.cmd == "extract": extract(args.archive, args.destination); print(json.dumps({"ok": True}, indent=2))
    else: print(json.dumps(strong_verify(args.archive), indent=2))


if __name__ == "__main__":
    _main()
