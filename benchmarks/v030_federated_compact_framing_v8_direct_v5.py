from __future__ import annotations

"""RAM-backed C25EG08 office frontier.

The v4 experiment attempted to intercept the historical engine's final archive ``open(..., 'wb')`` and replace it
with a BytesIO.  That was too low in the semantic stack: the EG05/EG06/EG07 finalizers deliberately reopen the
just-built archive through ordinary ``Path`` I/O so they can authenticate and rewrite the embedded filesystem
control plane.  Capturing the initial write therefore made the legitimate finalizer read a path that never existed.

This v5 experiment keeps that semantic-owner contract intact while still removing physical disk I/O.  The raw-final
EG07 working archive lives on Linux tmpfs (``/dev/shm``), so every ordinary pathlib/open/recovery/finalization path
remains real and testable, but the intermediate bytes never touch persistent/block-backed storage.  After the
fully finalized EG07 envelope is read from tmpfs, the already-proved exact final-pack levels are compressed once in
parallel and final C25EG08 framing is emitted directly to the measured output.

The evidence is intentionally explicit: there is one *RAM-backed semantic staging publication*, zero disk-backed
intermediate publications, zero recompressed-EG07 publication, and one final EG08 publication.  Timing receives
credit only after the complete EG08 bytes/SHA match the ordinary serial selected-effort reference exactly, followed
by mandatory strong verification and locality audit.

Research-only: selector admission, native/Android parity, all-15 external/generalization/runtime authority and the
strict release lock remain mandatory before production promotion.
"""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import tempfile
import time

from benchmarks import v030_federated_compact_framing_v8_direct_v4 as V4
from benchmarks import v030_federated_embedded_fs_v7_effort_oracle as EG07_EFFORT
from benchmarks import v030_federated_selective_effort_oracle as EFFORT
from experiments import entropygraph_v025 as V25


def _tmpfs_capture_raw_final_eg07(stage: Path, root: Path) -> tuple[bytes, float]:
    """Build/finalize EG07 through its real Path I/O contract on RAM-backed tmpfs."""

    root.mkdir(parents=True, exist_ok=True)
    shm = Path("/dev/shm")
    if not shm.is_dir():
        raise RuntimeError("direct-memory EG08 evidence requires Linux /dev/shm tmpfs")
    profile, _ = EG07_EFFORT._prepare(stage, root / "profile-stage")
    original_zc = V25.zc

    def raw_final(raw: bytes, requested: int = 19) -> bytes:
        requested = int(requested)
        if requested < 19:
            # Preserve every graph/search audition at the existing level-1 candidate policy.
            return original_zc(raw, min(requested, 1))
        # Final packs remain raw in the authenticated EG07 staging envelope and are compressed once below by v4.
        return raw

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-", dir=shm) as td:
        virtual_archive = Path(td) / "semantic-stage.c25eg07"
        with V4.BASE._eg07_effort_bindings():
            with EFFORT._engine(virtual_archive, profile, raw_final):
                V25.build()
        if not virtual_archive.is_file():
            raise RuntimeError("RAM-backed EG07 semantic staging archive was not published")
        blob = virtual_archive.read_bytes()
    elapsed = time.perf_counter() - started
    if not blob:
        raise RuntimeError("RAM-backed EG08 build captured no finalized EG07 bytes")
    return blob, elapsed


@contextmanager
def _tmpfs_capture_patch():
    original = V4._capture_raw_final_eg07
    V4._capture_raw_final_eg07 = _tmpfs_capture_raw_final_eg07
    try:
        yield
    finally:
        V4._capture_raw_final_eg07 = original


def run(work_root: Path) -> dict:
    with _tmpfs_capture_patch():
        result = dict(V4.run(work_root))
    result["schema"] = "cmpct-v030-eg08-direct-office-v5"
    result["schedule"] = "tmpfs-semantic-stage-plus-direct-exact-eg08-emission"
    measured = dict(result["measured_candidate"])
    measured["direct_memory"] = {
        "raw_final_eg07_disk_publication": False,
        "raw_final_eg07_ram_staging_publications": 1,
        "recompressed_eg07_disk_publication": False,
        "separate_compaction_pass": False,
        "final_eg08_publications": 1,
        "semantic_finalization_path_preserved": True,
        "ram_backend": "/dev/shm",
    }
    result["measured_candidate"] = measured
    boundary = dict(result["single_pass_boundary"])
    boundary.update(
        {
            "raw_final_graph_captured_in_memory": True,
            "raw_final_graph_capture_backend": "linux-tmpfs-/dev/shm",
            "semantic_staging_publications": 1,
            "disk_backed_intermediate_publications": 0,
            "intermediate_archive_publications": 1,
            "final_eg08_publications": 1,
            "historical_finalize_path_preserved": True,
        }
    )
    result["single_pass_boundary"] = boundary
    result["claim_boundary"] = (
        "Research-only RAM-backed C25EG08 office scheduling evidence. Historical graph/search auditions and the "
        "EG05/EG06/EG07 semantic finalization path are unchanged. The raw-final authenticated working archive is "
        "published once on Linux tmpfs so ordinary pathlib finalization/recovery semantics remain real without "
        "block-backed disk I/O; no recompressed EG07 archive or separate compaction artifact is published. Final "
        "packs are compressed once at the exact selected levels and final C25EG08 bytes receive timing credit only "
        "after byte/SHA identity with the ordinary serial selected-effort archive plus mandatory strong verification "
        "and locality audit. Native/Android, selector, all-15 external/generalization/runtime and strict release "
        "authority remain mandatory before promotion."
    )
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-direct-v5-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-direct-v5.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "minimum_modeled_effort": result["minimum_modeled_effort"],
                "measured_candidate": result["measured_candidate"],
                "single_pass_boundary": result["single_pass_boundary"],
                "comparators": result["comparators"],
                "measurement_gate": result["measurement_gate"],
            },
            indent=2,
        ),
        flush=True,
    )
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("RAM-backed direct C25EG08 office frontier failed")


if __name__ == "__main__":
    main()
