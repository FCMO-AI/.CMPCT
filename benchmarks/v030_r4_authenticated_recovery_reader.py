from __future__ import annotations

"""Archive-rooted payload authentication + single-chunk recovery falsifier for v0.30 R4.

Mission Lock / Referee
======================
The persisted lazy reader at 4fa0201 proved cold exact 4 KiB selective reads with a worst 4.211x
physical amplification, but explicitly left compressed-payload subrange authentication and recovery
unfinished. The reader therefore still received trusted payload bytes.

Hypothesis: retain the exact same 512-byte payload pread granularity and lazy interval algorithm, add
a SHA-256 Merkle commitment over both payload chunks and 8+1 XOR recovery stripes, charge a 32-byte
archive-root commitment on every fresh request, and verify every fetched payload/parity chunk against
that root. Normal exact reads should remain <=8x and the total dual-owner representation should remain
below the frozen v0.29 Analytics size. A single corrupted payload chunk should fail closed without
recovery and reconstruct exactly from authenticated parity + authenticated siblings when recovery is
enabled.

Disproof: any byte mismatch, >32,768 charged physical bytes for a normal 4 KiB request, density margin
loss versus frozen v0.29 Analytics, pristine authentication failure, corrupted payload accepted without
recovery, or failed/unauthenticated reconstruction falsifies this candidate. Chunk size, stripe width,
page size and thresholds are frozen before result-bearing hosted execution; no sweep is allowed.

Scope: diagnostic research only. The Merkle root is modeled as a 32-byte commitment already protected
by the archive's authenticated root metadata. This experiment proves bounded subrange authentication
and one-chunk-per-stripe recovery mechanics, not canonical format/native/platform integration.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import shutil
import struct
import zipfile
import zlib

from benchmarks import v030_r4_deflate_persisted_lazy_reader as BASE

SCHEMA = "cmpct-v030-r4-authenticated-recovery-reader-v1"
BLOCK = BASE.BLOCK
STRIPE_DATA = 8
ROOT_COMMITMENT_BYTES = 32
AUTH_MAGIC = b"ARM1"
AUTH_HEADER = struct.Struct("<4sIIII32s")  # magic, block, payload leaves, parity leaves, tree leaves, root


def _leaf_hash(data: bytes) -> bytes:
    return hashlib.sha256(b"\x00" + data).digest()


def _node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def _xor_into(dst: bytearray, src: bytes) -> None:
    for i, b in enumerate(src):
        dst[i] ^= b


def _write_parity(payload: bytes, parity_path: Path) -> tuple[list[bytes], int]:
    payload_chunks = [payload[i:i + BLOCK] for i in range(0, len(payload), BLOCK)]
    parity_chunks: list[bytes] = []
    for base in range(0, len(payload_chunks), STRIPE_DATA):
        p = bytearray(BLOCK)
        for chunk in payload_chunks[base:base + STRIPE_DATA]:
            _xor_into(p, chunk)
        parity_chunks.append(bytes(p))
    parity_path.write_bytes(b"".join(parity_chunks))
    return payload_chunks, len(parity_chunks)


def _write_auth(auth_path: Path, payload_chunks: list[bytes], parity_path: Path, parity_count: int) -> dict:
    parity_raw = parity_path.read_bytes()
    parity_chunks = [parity_raw[i * BLOCK:(i + 1) * BLOCK] for i in range(parity_count)]
    leaves = [_leaf_hash(c) for c in payload_chunks] + [_leaf_hash(c) for c in parity_chunks]
    tree_leaves = 1 << max(0, (max(1, len(leaves)) - 1).bit_length())
    empty = _leaf_hash(b"")
    nodes = [b""] * (2 * tree_leaves)
    for i in range(tree_leaves):
        nodes[tree_leaves + i] = leaves[i] if i < len(leaves) else empty
    for i in range(tree_leaves - 1, 0, -1):
        nodes[i] = _node_hash(nodes[2 * i], nodes[2 * i + 1])
    root = nodes[1]
    body = b"".join(nodes[1:])
    header = AUTH_HEADER.pack(AUTH_MAGIC, BLOCK, len(payload_chunks), parity_count, tree_leaves, root)
    auth_path.write_bytes(header + body)
    return {
        "stored_bytes": len(header) + len(body),
        "header_bytes": len(header),
        "hash_tree_bytes": len(body),
        "payload_leaves": len(payload_chunks),
        "parity_leaves": parity_count,
        "tree_leaves": tree_leaves,
        "root_sha256": root.hex(),
    }


class AuthStore:
    def __init__(self, path: Path, expected_root: bytes):
        self.fd = os.open(path, os.O_RDONLY)
        self.size = path.stat().st_size
        raw = os.pread(self.fd, AUTH_HEADER.size, 0)
        if len(raw) != AUTH_HEADER.size:
            raise ValueError("short auth header")
        magic, block, self.payload_leaves, self.parity_leaves, self.tree_leaves, root = AUTH_HEADER.unpack(raw)
        if magic != AUTH_MAGIC or block != BLOCK:
            raise ValueError("auth header mismatch")
        if root != expected_root:
            raise ValueError("archive-root commitment mismatch")
        expected_size = AUTH_HEADER.size + (2 * self.tree_leaves - 1) * 32
        if self.size != expected_size:
            raise ValueError("auth tree size mismatch")
        self.root = root
        self.bytes = AUTH_HEADER.size + ROOT_COMMITMENT_BYTES
        self.calls = 1
        self.cache: dict[int, bytes] = {}

    def close(self) -> None:
        os.close(self.fd)

    def _node(self, idx: int) -> bytes:
        if idx == 1:
            return self.root
        got = self.cache.get(idx)
        if got is not None:
            return got
        if not 1 <= idx < 2 * self.tree_leaves:
            raise ValueError("auth node out of range")
        off = AUTH_HEADER.size + (idx - 1) * 32
        got = os.pread(self.fd, 32, off)
        self.calls += 1
        self.bytes += len(got)
        if len(got) != 32:
            raise ValueError("short auth node")
        self.cache[idx] = got
        return got

    def verify(self, leaf_id: int, data: bytes) -> None:
        total = self.payload_leaves + self.parity_leaves
        if not 0 <= leaf_id < total:
            raise ValueError("auth leaf out of range")
        idx = self.tree_leaves + leaf_id
        h = _leaf_hash(data)
        while idx > 1:
            sibling = idx - 1 if idx & 1 else idx + 1
            sh = self._node(sibling)
            h = _node_hash(sh, h) if idx & 1 else _node_hash(h, sh)
            idx //= 2
        if h != self.root:
            raise ValueError("payload authentication failed")


class AuthPreadFile:
    def __init__(self, payload_path: Path, parity_path: Path, auth_path: Path, expected_root: bytes, recover: bool = False):
        self.path = payload_path
        self.fd = os.open(payload_path, os.O_RDONLY)
        self.size = payload_path.stat().st_size
        self.parity_fd = os.open(parity_path, os.O_RDONLY)
        self.auth = AuthStore(auth_path, expected_root)
        self.recover = recover
        self.cache: dict[int, bytes] = {}
        self.payload_bytes = 0
        self.payload_calls = 0
        self.parity_bytes = 0
        self.parity_calls = 0
        self.recoveries = 0

    def close(self) -> None:
        self.auth.close()
        os.close(self.parity_fd)
        os.close(self.fd)

    def __len__(self) -> int:
        return self.size

    def _raw_payload(self, block_id: int) -> bytes:
        off = block_id * BLOCK
        if off >= self.size:
            raise IndexError(block_id)
        got = os.pread(self.fd, min(BLOCK, self.size - off), off)
        self.payload_calls += 1
        self.payload_bytes += len(got)
        if not got:
            raise EOFError("short payload pread")
        return got

    def _parity(self, stripe: int) -> bytes:
        got = os.pread(self.parity_fd, BLOCK, stripe * BLOCK)
        self.parity_calls += 1
        self.parity_bytes += len(got)
        if len(got) != BLOCK:
            raise ValueError("short parity chunk")
        self.auth.verify(self.auth.payload_leaves + stripe, got)
        return got

    def _recover(self, block_id: int) -> bytes:
        stripe = block_id // STRIPE_DATA
        first = stripe * STRIPE_DATA
        p = bytearray(self._parity(stripe))
        for other in range(first, min(first + STRIPE_DATA, self.auth.payload_leaves)):
            if other == block_id:
                continue
            raw = self._raw_payload(other)
            self.auth.verify(other, raw)
            _xor_into(p, raw)
        expected_len = min(BLOCK, self.size - block_id * BLOCK)
        got = bytes(p[:expected_len])
        self.auth.verify(block_id, got)
        self.recoveries += 1
        return got

    def _block(self, block_id: int) -> bytes:
        got = self.cache.get(block_id)
        if got is not None:
            return got
        raw = self._raw_payload(block_id)
        try:
            self.auth.verify(block_id, raw)
            got = raw
        except ValueError:
            if not self.recover:
                raise
            got = self._recover(block_id)
        self.cache[block_id] = got
        return got

    def __getitem__(self, key):
        if isinstance(key, slice):
            start, stop, step = key.indices(self.size)
            if step != 1:
                return bytes(self[i] for i in range(start, stop, step))
            return bytes(self[i] for i in range(start, stop))
        i = int(key)
        if i < 0:
            i += self.size
        if not 0 <= i < self.size:
            raise IndexError(i)
        block_id = i // BLOCK
        return self._block(block_id)[i - block_id * BLOCK]

    def physical_bytes(self) -> int:
        return self.payload_bytes + self.parity_bytes + self.auth.bytes


def _run_one(payload_path: Path, parity_path: Path, auth_path: Path, expected_root: bytes, meta_path: Path, expected: bytes, start: int, recover: bool = False) -> dict:
    payload = AuthPreadFile(payload_path, parity_path, auth_path, expected_root, recover=recover)
    meta = BASE.MetaStore(meta_path)
    try:
        reader = BASE.LAZY.LazyIntervalReader(payload, BASE.MetaSeq(meta, BASE.KIND_ANCHOR), BASE.MetaSeq(meta, BASE.KIND_BLOCK), len(expected))
        end = min(start + BASE.PAGE, len(expected))
        got = reader.read(start, end)
        combined = payload.physical_bytes() + meta.bytes
        return {
            "start": start, "end": end, "exact": got == expected[start:end],
            "payload_and_auth_bytes": payload.physical_bytes(), "metadata_pread_bytes": meta.bytes,
            "physical_bytes": combined, "physical_amplification": combined / max(1, end - start),
            "payload_pread_calls": payload.payload_calls, "auth_pread_calls": payload.auth.calls,
            "parity_pread_calls": payload.parity_calls, "recoveries": payload.recoveries,
            "metadata_pread_calls": meta.calls, "symbols_parsed": reader.symbols_parsed,
            "recursive_calls": reader.recursive_calls, "max_recursion_depth": reader.max_depth,
            "cache_bytes_peak": reader.max_cache_bytes,
        }
    finally:
        payload.close()
        meta.close()


def _run_set(payload_path: Path, parity_path: Path, auth_path: Path, root: bytes, meta_path: Path, expected: bytes, starts: list[int]) -> dict:
    rows = [_run_one(payload_path, parity_path, auth_path, root, meta_path, expected, s) for s in starts]
    failures = sum((not r["exact"]) or r["physical_bytes"] > BASE.LIMIT or r["max_recursion_depth"] > BASE.LAZY.MAX_RECURSION for r in rows)
    return {
        "requests": len(rows), "failures": failures, "all_exact_and_bounded": failures == 0,
        "worst_physical": max(rows, key=lambda r: r["physical_bytes"]),
        "max_payload_pread_calls": max(r["payload_pread_calls"] for r in rows),
        "max_auth_pread_calls": max(r["auth_pread_calls"] for r in rows),
    }


def _flip_payload(src: Path, dst: Path, block_id: int) -> None:
    raw = bytearray(src.read_bytes())
    off = block_id * BLOCK + min(17, max(0, min(BLOCK, len(raw) - block_id * BLOCK) - 1))
    raw[off] ^= 1
    dst.write_bytes(raw)


def _payload_corruption_probes(payload_path: Path, parity_path: Path, auth_path: Path, root: bytes, meta_path: Path, expected: bytes) -> dict:
    corrupt = payload_path.with_name("owner-corrupt.deflate")
    _flip_payload(payload_path, corrupt, 0)
    refused = False
    msg = ""
    try:
        _run_one(corrupt, parity_path, auth_path, root, meta_path, expected, 0, recover=False)
    except Exception as exc:
        refused = True
        msg = f"{type(exc).__name__}: {exc}"
    recovered = _run_one(corrupt, parity_path, auth_path, root, meta_path, expected, 0, recover=True)
    return {
        "corrupted_payload_block": 0,
        "without_recovery_fail_closed": refused,
        "without_recovery_message": msg,
        "with_recovery_exact": recovered["exact"],
        "with_recovery_count": recovered["recoveries"],
        "with_recovery_physical_bytes": recovered["physical_bytes"],
        "with_recovery_physical_amplification": recovered["physical_amplification"],
    }


def _auth_corruption_probe(payload_path: Path, parity_path: Path, auth_path: Path, root: bytes, meta_path: Path, expected: bytes) -> dict:
    corrupt = auth_path.with_name("auth-corrupt.bin")
    raw = bytearray(auth_path.read_bytes())
    # First sibling needed for leaf 0 is tree leaf 1; flip its persisted hash, not the trusted root.
    with auth_path.open("rb") as f:
        header = f.read(AUTH_HEADER.size)
    if len(header) != AUTH_HEADER.size:
        raise ValueError("short auth header in corruption probe")
    magic, _block, _payload_count, _parity_count, tree_leaves, _root = AUTH_HEADER.unpack(header)
    if magic != AUTH_MAGIC:
        raise ValueError("auth magic mismatch in corruption probe")
    sibling_idx = tree_leaves + 1
    off = AUTH_HEADER.size + (sibling_idx - 1) * 32
    raw[off] ^= 1
    corrupt.write_bytes(raw)
    refused = False
    msg = ""
    try:
        _run_one(payload_path, parity_path, corrupt, root, meta_path, expected, 0)
    except Exception as exc:
        refused = True
        msg = f"{type(exc).__name__}: {exc}"
    return {"touched_auth_hash_corrupted": True, "fail_closed": refused, "message": msg, "flipped_offset": off}


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = BASE.V029._load(BASE.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_auth_recovery_neutral")
    repair = BASE.V029._load(BASE.V029.REPAIR_PATH, "r4_auth_recovery_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"
    rel = BASE.DUAL._npz_relation(source)["accepted"]
    npz = source.joinpath(*Path(rel["npz_path"]).parts)
    info, comp, expected, method = BASE.CONE._raw_zip_member(npz, rel["member"])
    if method != zipfile.ZIP_DEFLATED:
        raise RuntimeError("expected DEFLATE")
    parsed = BASE.DEP.parse_tokens(comp)
    if zlib.decompress(comp, -15) != expected or parsed["output_bytes"] != len(expected):
        raise RuntimeError("builder parse mismatch")

    payload_path = work / "owner.deflate"
    payload_path.write_bytes(comp)
    meta_path = work / "sparse.meta"
    meta_stats = BASE._write_metadata(meta_path, parsed)
    parity_path = work / "recovery.parity"
    payload_chunks, parity_count = _write_parity(comp, parity_path)
    auth_path = work / "payload.auth"
    auth_stats = _write_auth(auth_path, payload_chunks, parity_path, parity_count)
    root = bytes.fromhex(auth_stats["root_sha256"])

    added = meta_stats["stored_bytes"] + auth_stats["stored_bytes"] + parity_path.stat().st_size + ROOT_COMMITMENT_BYTES
    candidate = BASE.LAZY.DUAL_OWNER_BYTES + added
    margin = BASE.DUAL.ACCEPTED_V029_ANALYTICS - candidate

    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    fixed = _run_set(payload_path, parity_path, auth_path, root, meta_path, expected, BASE.LAZY.TOKEN.starts(len(expected)))
    unaligned = _run_set(payload_path, parity_path, auth_path, root, meta_path, expected, BASE.LAZY._unaligned_starts(len(expected)))
    payload_corruption = _payload_corruption_probes(payload_path, parity_path, auth_path, root, meta_path, expected)
    auth_corruption = _auth_corruption_probe(payload_path, parity_path, auth_path, root, meta_path, expected)
    rss1 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    supported = (
        margin > 0 and fixed["all_exact_and_bounded"] and unaligned["all_exact_and_bounded"]
        and payload_corruption["without_recovery_fail_closed"] and payload_corruption["with_recovery_exact"]
        and payload_corruption["with_recovery_count"] >= 1 and auth_corruption["fail_closed"]
    )
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "member": {"compressed_bytes": len(comp), "raw_bytes": len(expected), "crc32": info.CRC},
        "storage": {
            "sparse_metadata_bytes": meta_stats["stored_bytes"], "auth_tree_bytes": auth_stats["stored_bytes"],
            "recovery_parity_bytes": parity_path.stat().st_size, "archive_root_commitment_bytes": ROOT_COMMITMENT_BYTES,
            "dual_owner_plus_auth_recovery_bytes": candidate, "accepted_v029_analytics_bytes": BASE.DUAL.ACCEPTED_V029_ANALYTICS,
            "margin_to_v029_bytes": margin, "payload_chunks": len(payload_chunks), "parity_chunks": parity_count,
            "tree_leaves": auth_stats["tree_leaves"], "root_sha256": auth_stats["root_sha256"],
        },
        "fixed_requests": fixed,
        "unaligned_controls": unaligned,
        "payload_corruption_recovery": payload_corruption,
        "auth_corruption": auth_corruption,
        "host_process": {"ru_maxrss_before_kib": rss0, "ru_maxrss_after_kib": rss1, "delta_ru_maxrss_kib": max(0, rss1 - rss0)},
        "hypothesis": {"archive_rooted_auth_and_single_chunk_recovery_preserve_locality_and_density": supported},
        "contract": {
            "diagnostic_only": True, "release_credit": False, "same_lazy_algorithm": True,
            "same_page_bytes": BASE.PAGE, "same_limit_bytes": BASE.LIMIT, "payload_pread_block_bytes_frozen": BLOCK,
            "stripe_data_chunks_frozen": STRIPE_DATA, "no_threshold_sweep": True, "no_product_format_change": True,
            "archive_root_commitment_bytes_charged_per_request": ROOT_COMMITMENT_BYTES,
            "payload_subrange_authentication_complete_for_candidate": True,
            "single_payload_chunk_per_stripe_recovery_complete_for_candidate": True,
            "canonical_archive_integration_complete": False, "native_portable_parity_complete": False,
        },
        "next_if_supported": "generalize the same authenticated recovery reader to held-out NPZ/NPY relations and then integrate under canonical archive/root semantics without changing locality or density gates",
        "next_if_falsified": "preserve the negative and attribute failure to Merkle proof traffic, recovery carrying cost, or representation margin without raising the 8x bound or weakening auth",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-auth-recovery-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-auth-recovery.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps(d, indent=2))


if __name__ == "__main__":
    main()
