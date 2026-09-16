from __future__ import annotations

from pathlib import Path

import msgpack
import pytest
import zstandard as zstd

from experiments import entropygraph_v030_prefixgraph as PG
from experiments import entropygraph_v030_release_admission as A
from experiments import entropygraph_v030_release_reader_policy as POLICY


def _locality_hostile_archive(path: Path) -> None:
    """Write authenticated metadata whose depth-1 dependency is structurally valid but 10x to read."""
    records = [
        ["direct", -1, 9, 1, PG.H(b"d"), PG.H(b"a" * 9)],
        ["prefix", 0, 1, 1, PG.H(b"p"), PG.H(b"b")],
    ]
    meta = {
        "v": 1,
        "engine": "PrefixGraph-depth1-v1",
        "tree_sha256": "0" * 64,
        "files": ["anchor.bin", "tiny.bin"],
        "records": records,
        "anchor": 0,
        "max_dependency_depth": 1,
        "max_file_bytes": PG.MAX_FILE_BYTES,
    }
    raw = msgpack.packb(meta, use_bin_type=True)
    comp = zstd.ZstdCompressor(level=1).compress(raw)
    digest = PG.H(raw)
    path.write_bytes(
        PG.HEADER.pack(PG.MAGIC, len(comp), len(raw), digest)
        + comp
        + b"dp"
        + comp
        + PG.FOOTER.pack(PG.TAIL, len(comp), len(raw), digest)
    )


def test_locality_rejection_is_negative_evidence_not_admission_crash(tmp_path: Path) -> None:
    archive = tmp_path / "hostile-prefixgraph.cmpct"
    _locality_hostile_archive(archive)

    locality = A.prefixgraph_locality(archive)
    assert locality["passed"] is False
    assert locality["max_member_read_amplification"] == pytest.approx(10.0)
    assert locality["prefix_records"] == 1
    assert locality["payload_bytes_materialized_for_locality"] == 0
    assert locality["accounting_source"] == "authenticated-metadata-only-admission-preflight"

    # The separation is intentional: admission accounting can record the rejected candidate, while the strict
    # release reader still refuses to open it.  A future refactor must not turn evidence visibility into promotion.
    POLICY.install_policy()
    with pytest.raises(RuntimeError, match="selective-read amplification exceeds release policy"):
        POLICY.R._pg_open(archive)


def test_admission_preflight_preserves_tail_metadata_recovery(tmp_path: Path) -> None:
    archive = tmp_path / "tail-prefixgraph.cmpct"
    _locality_hostile_archive(archive)
    blob = bytearray(archive.read_bytes())
    blob[0] ^= 0x01  # damage only the primary magic; authenticated tail metadata must remain usable for accounting.
    archive.write_bytes(blob)

    locality = A.prefixgraph_locality(archive)
    assert locality["passed"] is False
    assert locality["recovered_from_tail"] is True
    assert locality["max_member_read_amplification"] == pytest.approx(10.0)
