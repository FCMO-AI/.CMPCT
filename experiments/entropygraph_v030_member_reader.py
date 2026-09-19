"""Bounded selective-member reader for CMPCT v0.30 new representations.

This module exposes the operation needed for release-performance accounting: reconstruct one named member
without extracting the archive.  It handles the two *new* v0.30 representations directly:

- G0-G4 Geometry-over-Mosaic;
- PrefixGraph depth-1.

Byte-identical v0.29 fallback archives deliberately remain owned by the inherited v0.29 reader surface; their
selective-read semantics do not change in v0.30.  Callers can distinguish that case via
``InheritedRepresentation`` and dispatch to the existing reader rather than silently turning a random read
into full extraction.

Every returned member is bounded by an explicit caller ceiling, authenticated against its stored logical
SHA-256, and reconstructed through the strict promotion-policy reader sessions.

Footnote: returning ``bytes`` necessarily materializes the requested member itself.  The important locality
contract is that the decoder does not materialize unrelated *members* beyond the bounded direct anchor / graph
records required by the selected representation.  Streaming member output can be layered later without
changing archive bytes.
"""
from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_reader as R
from experiments import entropygraph_v030_release_reader_policy as POLICY

# Importing POLICY installs the strict validators into R before sessions open metadata.
POLICY.install_policy()

DEFAULT_MAX_MEMBER_BYTES = 256 * 1024 * 1024


class InheritedRepresentation(RuntimeError):
    """Raised when the selected archive is byte-identical inherited v0.29 rather than a new v0.30 grammar."""


def _g04_member(archive: Path, rel: str, max_output_bytes: int) -> tuple[bytes, dict]:
    R._safe_relpath(rel)
    session = R._G04Session(archive)
    try:
        desc = session.meta["files"].get(rel)
        if desc is None:
            raise KeyError(rel)
        expected_size = int(desc[2])
        expected_hash = desc[3]
        if expected_size > max_output_bytes:
            raise RuntimeError("requested G0-G4 member exceeds caller output budget")

        if desc[0] == "preflate":
            raw = session.record(int(desc[1]))
        elif desc[0] == "nodes":
            output = bytearray()
            for node_id in desc[1]:
                chunk = session.node(int(node_id))
                if len(output) + len(chunk) > max_output_bytes:
                    raise RuntimeError("requested G0-G4 member exceeds caller output budget")
                output.extend(chunk)
            raw = bytes(output)
        else:  # pragma: no cover - promotion admission rejects unknown file descriptors first.
            raise RuntimeError("unsupported G0-G4 member descriptor")

        if len(raw) != expected_size or R.H(raw) != expected_hash:
            raise RuntimeError("G0-G4 selective member integrity")
        return raw, {
            "representation": "g04-overlay",
            "logical_bytes": len(raw),
            "physical_record_reads": session.physical_record_reads,
            "record_cache_bound_bytes": R.MAX_RECORD_CACHE_BYTES,
            "node_cache_bound_bytes": R.MAX_NODE_CACHE_BYTES,
            "max_physical_record_bytes": session.max_physical_record_bytes,
            "max_logical_node_bytes": session.max_logical_node_bytes,
        }
    finally:
        session.close()


def _pg_member(archive: Path, rel: str, max_output_bytes: int) -> tuple[bytes, dict]:
    R._safe_relpath(rel)
    session = R._PGSession(archive)
    try:
        try:
            index = session.meta["files"].index(rel)
        except ValueError as exc:
            raise KeyError(rel) from exc
        expected_size = int(session.records[index][2])
        if expected_size > max_output_bytes:
            raise RuntimeError("requested PrefixGraph member exceeds caller output budget")
        raw = session.file(index)
        if len(raw) > max_output_bytes:
            raise RuntimeError("requested PrefixGraph member exceeds caller output budget")
        return raw, {
            "representation": "prefixgraph",
            "logical_bytes": len(raw),
            "max_member_read_amplification": session.max_member_read_amplification,
            "anchor_cache_bound_bytes": R.MAX_RECORD_CACHE_BYTES,
            "max_file_bytes": session.max_file_bytes,
        }
    finally:
        session.close()


def read_member(
    archive: Path,
    rel: str,
    *,
    max_output_bytes: int = DEFAULT_MAX_MEMBER_BYTES,
    with_stats: bool = False,
):
    if not isinstance(max_output_bytes, int) or isinstance(max_output_bytes, bool) or max_output_bytes <= 0:
        raise ValueError("max_output_bytes must be a positive integer")
    if max_output_bytes > R.MAX_DECLARED_LOGICAL_BYTES:
        raise ValueError("max_output_bytes exceeds hard release-reader policy")

    with archive.open("rb") as stream:
        magic = stream.read(8)
    if magic == R.G04.MAG:
        raw, stats = _g04_member(archive, rel, max_output_bytes)
    elif magic == R.PG.MAGIC:
        raw, stats = _pg_member(archive, rel, max_output_bytes)
    else:
        raise InheritedRepresentation(
            "archive uses inherited v0.29 representation; dispatch selective read to the existing v0.29 reader"
        )
    return (raw, stats) if with_stats else raw
