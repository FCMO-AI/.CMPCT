from __future__ import annotations

"""Attest compact-r24 policy in the actual byte-owning child process.

The regression proves both policy changes through emitted revision-24 structure rather than trusting
candidate declaration constants alone:

* medium ``.bin`` files are micro-packed by the canonical release child but remain direct blobs
  under the compact candidate; and
* a small exact Deflate stream is retained as VZIP mode 0 by canonical release policy but falls back
  to deterministic mode 2 regeneration under the compact 64 KiB reuse floor.

The candidate child must also report effective Builder-visible state matching those observed bytes.
Parent-only module rebinding or stale metadata is therefore insufficient to make this test pass.
"""

from pathlib import Path
import zipfile

from cmpct.codec import S_PACK, S_VZIP
from cmpct.reader import CMPCT
from experiments.entropygraph_v030_r24_process_prebuild import R24PrebuildProcess


CANONICAL_WORKER = "experiments.entropygraph_v030_r24_process_prebuild"
CANDIDATE_WORKER = "experiments.entropygraph_v030_r24_compact_candidate_prebuild"


def _build(root: Path, out: Path, worker_module: str) -> dict:
    with R24PrebuildProcess(root, out, timeout_s=60, worker_module=worker_module) as proc:
        return proc.result()


def _make_policy_probe(root: Path) -> None:
    # Eight medium binary members fit one 384 KiB locality-derived pack when .bin admission is
    # enabled. Each payload is unique so dedup cannot mask the storage decision.
    for i in range(8):
        payload = bytes([i]) * (48 * 1024 - 64) + bytes(range(64))
        (root / f"medium-{i:02d}.bin").write_bytes(payload)

    # A normal level-6 Deflate member whose exact compressed stream is far below 64 KiB.
    # Canonical release policy (reuse floor 0) retains the stream as mode 0; compact policy
    # (reuse floor 64 KiB) reconstructs it deterministically as mode 2.
    with zipfile.ZipFile(
        root / "small-stream.zip",
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as zf:
        zf.writestr("payload.txt", ("alpha beta gamma delta\n" * 8192).encode())


def _shape(archive: Path) -> dict:
    with CMPCT(archive) as reader:
        reader.verify()
        bins = [row for row in reader.files if row[0].endswith(".bin")]
        zip_row = reader.by["small-stream.zip"]
        assert zip_row[6][0] == S_VZIP
        recipe = reader.recipes[zip_row[6][1]]
        payloads = recipe[2]
        assert len(payloads) == 1
        return {
            "bin_storage_kinds": [row[6][0] for row in bins],
            "vzip_mode": int(payloads[0][2]),
            "vzip_compressed_bytes": int(payloads[0][4]),
        }


def test_compact_r24_policy_reaches_byte_owning_child_and_changes_expected_structure(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    _make_policy_probe(root)

    canonical = tmp_path / "canonical.cmpct"
    candidate = tmp_path / "candidate.cmpct"
    canonical_stats = _build(root, canonical, CANONICAL_WORKER)
    candidate_stats = _build(root, candidate, CANDIDATE_WORKER)

    canonical_shape = _shape(canonical)
    candidate_shape = _shape(candidate)

    assert canonical_stats["deflate_reuse_min_release_bytes"] == 0
    assert candidate_stats["r24_prebuild_effective_policy"] == {
        "candidate": "v030-compact-r24-release-policy-v1",
        "deflate_reuse_min_bytes": 64 * 1024,
        "build_reported_deflate_reuse_min_bytes": 64 * 1024,
        "micro_pack_max_file_release_bytes": 256 * 1024,
        "builder_text_ext_is_release_view": True,
        "medium_binary_packing": False,
        "hints_equal_original": True,
        "medium_terminal_disabled": True,
    }

    # Structural proof of the medium-binary policy at the final byte owner.
    assert len(canonical_shape["bin_storage_kinds"]) == 8
    assert all(kind == S_PACK for kind in canonical_shape["bin_storage_kinds"])
    assert all(kind != S_PACK for kind in candidate_shape["bin_storage_kinds"])

    # Structural proof of the exact-Deflate retention floor at the final byte owner.
    assert canonical_shape["vzip_compressed_bytes"] < 64 * 1024
    assert candidate_shape["vzip_compressed_bytes"] == canonical_shape["vzip_compressed_bytes"]
    assert canonical_shape["vzip_mode"] == 0
    assert candidate_shape["vzip_mode"] == 2
