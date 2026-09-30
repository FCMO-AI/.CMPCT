from __future__ import annotations

"""Exact same-semantics bounded-drift vs PrefixGraph oracle for Shifted.

Research-only. This benchmark changes no canonical grammar or product selection. It asks
whether the already-hardened generic bounded-drift primitive can retain its historical
physical win after paying complete revision-25 filesystem-control semantics on the exact
deterministic Shifted content family.
"""

import hashlib
import json
import os
from pathlib import Path
import struct
import tempfile
import time

import zstandard as zstd

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from experiments import entropygraph_v030_bounded_drift_container_v1 as BDC
from experiments import entropygraph_v030_canonical_final as CANONICAL
from experiments import entropygraph_v030_product_fs as FS
from experiments.entropygraph_v030_prefixgraph_process_executor import (
    PrefixGraphProcessExecutor,
    SUPPORTED_PREFIX_LEVEL,
)

MAGIC = b"CMPNXBS1"
HEADER = struct.Struct("<8sQQQ32s")
TRAILER = struct.Struct("<32s")
MANIFEST_LEVEL = 12
FIXED_MTIME_NS = 1767225600 * 1_000_000_000  # 2026-01-01T00:00:00Z


def _h(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _encode_semantic_sibling(manifest_raw: bytes, members: list[bytes]) -> bytes:
    """Store full filesystem-v1 semantics plus the exact generic BD container.

    The manifest is an authenticated payload rather than an implicit side assumption.
    This intentionally overpays relative to the admitted implicit-v4 control seam.
    """
    manifest_stored = zstd.ZstdCompressor(level=MANIFEST_LEVEL).compress(manifest_raw)
    content = BDC.encode_container(members)
    header = HEADER.pack(
        MAGIC,
        len(manifest_raw),
        len(manifest_stored),
        len(content),
        _h(manifest_raw),
    )
    body = header + manifest_stored + content
    return body + TRAILER.pack(_h(body))


def _decode_semantic_sibling(blob: bytes) -> tuple[bytes, list[bytes]]:
    if len(blob) < HEADER.size + TRAILER.size:
        raise ValueError("short bounded-drift semantic sibling")
    body, trailer_raw = blob[:-TRAILER.size], blob[-TRAILER.size:]
    (trailer,) = TRAILER.unpack(trailer_raw)
    if _h(body) != trailer:
        raise ValueError("bounded-drift semantic sibling digest mismatch")
    magic, manifest_raw_n, manifest_stored_n, content_n, manifest_digest = HEADER.unpack_from(body, 0)
    if magic != MAGIC:
        raise ValueError("bounded-drift semantic sibling magic mismatch")
    pos = HEADER.size
    end_manifest = pos + manifest_stored_n
    end_content = end_manifest + content_n
    if end_content != len(body):
        raise ValueError("bounded-drift semantic sibling length mismatch")
    manifest_raw = zstd.ZstdDecompressor().decompress(
        body[pos:end_manifest], max_output_size=FS.MAX_MANIFEST_BYTES
    )
    if len(manifest_raw) != manifest_raw_n or _h(manifest_raw) != manifest_digest:
        raise ValueError("bounded-drift semantic manifest identity mismatch")
    members = BDC.decode_all(body[end_manifest:end_content])
    return manifest_raw, members


def _bind_members_to_manifest(manifest_raw: bytes, members: list[bytes]) -> dict[str, bytes]:
    decoded = FS.decode_manifest(
        manifest_raw,
        max_path_bytes=CANONICAL.POLICY.R.MAX_PATH_BYTES,
        max_entries=CANONICAL.MAX_MANIFEST_ENTRIES,
    )
    available: dict[tuple[int, bytes], list[bytes]] = {}
    for member in members:
        available.setdefault((len(member), _h(member)), []).append(member)
    bound: dict[str, bytes] = {}
    for rel, (size, digest) in decoded["regular"].items():
        key = (int(size), bytes(digest))
        bucket = available.get(key)
        if not bucket:
            raise RuntimeError(f"missing bounded-drift content for {rel}")
        bound[rel] = bucket.pop()
    if any(bucket for bucket in available.values()):
        raise RuntimeError("bounded-drift sibling contains unowned regular content")
    return bound


def _treehash(files: dict[str, bytes]) -> str:
    h = hashlib.sha256()
    for rel, data in sorted(files.items()):
        rb = rel.encode("utf-8")
        h.update(len(rb).to_bytes(4, "little"))
        h.update(rb)
        h.update(len(data).to_bytes(8, "little"))
        h.update(data)
    return h.hexdigest()


def _normalize_generated_metadata(root: Path) -> None:
    """Freeze charged filesystem mtimes before either representation observes them."""
    paths = sorted(root.rglob("*"), key=lambda p: (len(p.parts), p.as_posix()), reverse=True)
    for path in paths:
        try:
            os.utime(path, ns=(FIXED_MTIME_NS, FIXED_MTIME_NS), follow_symlinks=False)
        except (NotImplementedError, OSError):
            if not path.is_symlink():
                raise
    os.utime(root, ns=(FIXED_MTIME_NS, FIXED_MTIME_NS))


def _source_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(p for p in root.rglob("*") if p.is_file())
    }


def run(out_path: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-bd-semantic-oracle-") as td:
        work = Path(td)
        suite = work / "hostile"
        HOSTILE.build(suite)
        source = suite / "01_shifted_versions"
        _normalize_generated_metadata(source)
        source_files = _source_files(source)
        expected_source_tree = _treehash(source_files)

        # Bind candidate and control to the exact current r25 filesystem-admission envelope.
        staged = work / "staged"
        prepared = CANONICAL._prepare_profile_tree(source, staged)
        manifest_raw, regular_sources, _manifest_stats = FS.capture_filesystem_manifest(
            source,
            max_path_bytes=CANONICAL.POLICY.R.MAX_PATH_BYTES,
            max_profile_files=CANONICAL.MAX_PROFILE_FILES,
            max_profile_logical_bytes=CANONICAL.MAX_PROFILE_LOGICAL_BYTES,
            max_entries=CANONICAL.MAX_MANIFEST_ENTRIES,
        )
        if prepared["source_manifest_raw"] != manifest_raw:
            raise RuntimeError("candidate/control filesystem-v1 source semantics drift")
        members = [path.read_bytes() for path, _rel in regular_sources]

        started = time.perf_counter()
        candidate_blob = _encode_semantic_sibling(manifest_raw, members)
        candidate_create_s = time.perf_counter() - started
        decoded_manifest_raw, decoded_members = _decode_semantic_sibling(candidate_blob)
        if decoded_manifest_raw != manifest_raw:
            raise RuntimeError("filesystem-v1 semantic bytes changed")
        restored = _bind_members_to_manifest(decoded_manifest_raw, decoded_members)
        restored_tree = _treehash(restored)
        if restored_tree != expected_source_tree:
            raise RuntimeError("bounded-drift semantic sibling changed regular content tree")

        content_blob = BDC.encode_container(members)
        member_facts = [BDC.member_resource_facts(content_blob, i) for i in range(len(members))]
        max_amp = max(row.member_read_amplification for row in member_facts)
        max_decode = max(row.max_decode_unit_bytes for row in member_facts)

        # Same-run exact current PrefixGraph control: private semantic owner, level-15
        # process custody, and the evidenced child-dead-before-G0-G4 lifetime boundary.
        pg = CANONICAL.RC.PG
        if pg.__name__ != "experiments._v030_canonical_prefixgraph":
            raise RuntimeError(f"current PrefixGraph semantic-owner drift: {pg.__name__!r}")
        if pg.build.__module__ != pg.__name__:
            raise RuntimeError("current PrefixGraph build-callable custody drift")
        pg_path = work / "prefixgraph.cmpct"
        with PrefixGraphProcessExecutor() as executor:
            pg_stats = dict(executor.submit(pg.build, staged, pg_path).result())
            pg_receipt = dict(executor.last_receipt or {})
        if pg_receipt.get("semantic_owner") != pg.__name__:
            raise RuntimeError("current PrefixGraph child semantic-owner drift")
        if int(pg_receipt.get("prefix_level", -1)) != SUPPORTED_PREFIX_LEVEL:
            raise RuntimeError("current PrefixGraph child prefix-level drift")
        pg_verify = dict(pg.strong_verify(pg_path))
        staged_tree = pg.treehash(staged)
        if not pg_verify.get("ok") or pg_verify.get("tree_sha256") != staged_tree:
            raise RuntimeError("current PrefixGraph control failed strong verification")
        pg_locality = dict(CANONICAL.RC._prefixgraph_locality(pg_path))
        if not pg_locality.get("passed"):
            raise RuntimeError("current PrefixGraph control failed locality")

        corrupted = bytearray(candidate_blob)
        corrupted[len(corrupted) // 2] ^= 0x01
        corruption_rejected = False
        try:
            _decode_semantic_sibling(bytes(corrupted))
        except Exception:
            corruption_rejected = True
        if not corruption_rejected:
            raise RuntimeError("bounded-drift semantic sibling corruption was not rejected")

        result = {
            "schema": "cmpct-v030-bounded-drift-same-semantics-oracle-v2",
            "source": {
                "suite": "resemblance_hostile_v1",
                "name": "01_shifted_versions",
                "files": len(source_files),
                "logical_bytes": sum(map(len, source_files.values())),
                "tree_sha256": expected_source_tree,
                "filesystem_v1_bytes": len(manifest_raw),
                "filesystem_v1_sha256": hashlib.sha256(manifest_raw).hexdigest(),
                "fixed_mtime_ns": FIXED_MTIME_NS,
                "selected_manifest_encoding": prepared["selected_manifest_encoding"],
                "selected_manifest_bytes": int(prepared["selected_manifest_bytes"]),
            },
            "bounded_drift_semantic_sibling": {
                "archive_bytes": len(candidate_blob),
                "physical_sha256": hashlib.sha256(candidate_blob).hexdigest(),
                "create_s": candidate_create_s,
                "tree_sha256": restored_tree,
                "manifest_semantics_exact": decoded_manifest_raw == manifest_raw,
                "corruption_rejected": corruption_rejected,
                "max_member_read_amplification": max_amp,
                "max_decode_unit_bytes": max_decode,
                "depth": 1,
            },
            "prefixgraph_same_run": {
                **pg_stats,
                "semantic_owner": pg_receipt["semantic_owner"],
                "prefix_level": int(pg_receipt["prefix_level"]),
                "process_receipt_schema": pg_receipt.get("schema"),
                "physical_sha256": hashlib.sha256(pg_path.read_bytes()).hexdigest(),
                "verified": bool(pg_verify.get("ok")),
                "tree_sha256": pg_verify.get("tree_sha256"),
                "max_member_read_amplification": pg_locality["max_member_read_amplification"],
            },
            "delta": {
                "bounded_drift_minus_prefixgraph_bytes": len(candidate_blob) - pg_path.stat().st_size,
            },
            "decision": "PRODUCTIZATION_RUNG_ONLY_IF_STRICT_BYTE_WIN_AND_RESOURCE_SAFE",
            "release_credit": False,
            "claim_boundary": (
                "Research-only same-source/same-filesystem-semantics physical-byte oracle. "
                "The sibling grammar is noncanonical and provides no reader/recovery/native/platform/release credit."
            ),
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        return result


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
