from __future__ import annotations

"""Direct-memory C25EG08 office frontier.

The v3 exact-byte proof established the correct single-final-compression schedule, but its timed boundary still
published three physical artifacts on the way to the final candidate: a raw-final EG07 archive, a recompressed
EG07 archive, and finally the compact EG08 archive.  The measured candidate was already strictly smaller than
accepted v0.29, ZIP and Zstd, but missed ZIP creation wall-clock by ~96 ms on the controlled runner.

This v4 proof removes only that intermediate physical I/O.  The unchanged historical graph/search builder writes
its raw-final EG07 envelope into an in-memory authenticated capture.  Final physical packs are then compressed
once, concurrently, at the exact previously selected levels and written directly in C25EG08 framing.  Metadata,
payload choices, recovery copies, CRC32/SHA-256 identities, graph/search auditions and locality semantics are
unchanged.  The direct-memory result receives timing credit only when the complete final C25EG08 bytes and SHA-256
are identical to the ordinary serial selected-effort reference.

Research-only: native/Android parity, selector admission, all-15 external/generalization/runtime authority and the
strict release lock remain mandatory before any production promotion.
"""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import builtins
import hashlib
import io
import json
import os
from pathlib import Path
import time

from benchmarks import v030_federated_compact_framing_v8_direct as BASE
from benchmarks import v030_federated_embedded_fs_v7_effort_oracle as EG07_EFFORT
from benchmarks import v030_federated_selective_effort_oracle as EFFORT
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_compact_framing_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

MAX_WORKERS = 8


class _Capture(io.BytesIO):
    """BytesIO that survives the builder's ``with open(...):`` close boundary."""

    def close(self) -> None:  # pragma: no cover - behavior is exercised by the full frozen-corpus lane.
        self.flush()

    def really_close(self) -> None:
        super().close()


@contextmanager
def _module_open_capture(target: Path, capture: _Capture):
    """Intercept only V25's final archive publication; all unrelated file opens stay ordinary."""

    had_open = "open" in V25.__dict__
    previous = V25.__dict__.get("open")
    resolved_target = target.resolve()

    def intercepted(file, mode="r", *args, **kwargs):
        try:
            same = Path(file).resolve() == resolved_target
        except (TypeError, ValueError, OSError):
            same = False
        if same and mode == "wb":
            capture.seek(0)
            capture.truncate(0)
            return capture
        return builtins.open(file, mode, *args, **kwargs)

    V25.open = intercepted
    try:
        yield
    finally:
        if had_open:
            V25.open = previous
        else:
            delattr(V25, "open")


def _capture_raw_final_eg07(stage: Path, root: Path) -> tuple[bytes, float]:
    """Run the unchanged graph/search path while retaining its raw-final physical envelope in memory."""

    root.mkdir(parents=True, exist_ok=True)
    profile, _ = EG07_EFFORT._prepare(stage, root / "profile-stage")
    virtual_archive = root / "captured-raw-final.c25eg07"
    original_zc = V25.zc
    capture = _Capture()

    def raw_final(raw: bytes, requested: int = 19) -> bytes:
        requested = int(requested)
        if requested < 19:
            # Preserve every search/audition request at the existing level-1 candidate policy.
            return original_zc(raw, min(requested, 1))
        # Final packs are authenticated by raw CRC32/SHA-256 and compressed once below at the exact selected level.
        return raw

    started = time.perf_counter()
    try:
        with _module_open_capture(virtual_archive, capture):
            with BASE._eg07_effort_bindings():
                with EFFORT._engine(virtual_archive, profile, raw_final):
                    V25.build()
        blob = capture.getvalue()
    finally:
        capture.really_close()
    elapsed = time.perf_counter() - started
    if not blob:
        raise RuntimeError("direct-memory EG08 build captured no raw-final EG07 bytes")
    return blob, elapsed


def _raw_eg07_parts(blob: bytes) -> tuple[bytes, bytes, bytes, list[bytes]]:
    """Authenticate the captured EG07 envelope and return metadata plus raw physical packs."""

    if len(blob) < V25.HDR.size + V25.FTR.size:
        raise RuntimeError("captured EG07 envelope is truncated")
    magic, mcs, mus, pack_count, digest = V25.HDR.unpack_from(blob, 0)
    if magic != EG07.MAGIC:
        raise RuntimeError("captured envelope is not C25EG07")
    meta_start = V25.HDR.size
    meta_end = meta_start + int(mcs)
    meta_comp = blob[meta_start:meta_end]
    if len(meta_comp) != int(mcs):
        raise RuntimeError("captured EG07 metadata is truncated")
    meta_raw = V25.zd(meta_comp, int(mus))
    if V25.H(meta_raw) != bytes(digest):
        raise RuntimeError("captured EG07 metadata authentication failed")

    pos = meta_end
    raws: list[bytes] = []
    for index in range(int(pack_count)):
        if pos + V25.PH.size > len(blob) - V25.FTR.size:
            raise RuntimeError(f"captured EG07 pack header {index} is truncated")
        codec, usize, csize, crc, expected_sha = V25.PH.unpack_from(blob, pos)
        pos += V25.PH.size
        end = pos + int(csize)
        payload = blob[pos:end]
        if len(payload) != int(csize):
            raise RuntimeError(f"captured EG07 pack payload {index} is truncated")
        if int(codec) == 1:
            raw = V25.zd(payload, int(usize))
        elif int(codec) == 0:
            raw = payload
        else:
            raise RuntimeError(f"captured EG07 pack {index} uses unsupported codec {codec}")
        if len(raw) != int(usize):
            raise RuntimeError(f"captured EG07 pack {index} size mismatch")
        if (V25.binascii.crc32(raw) & 0xFFFFFFFF) != int(crc) or V25.H(raw) != bytes(expected_sha):
            raise RuntimeError(f"captured EG07 pack {index} identity mismatch")
        raws.append(raw)
        pos = end

    tail_meta_start = len(blob) - V25.FTR.size - int(mcs)
    if pos != tail_meta_start:
        raise RuntimeError("captured EG07 physical/tail boundary mismatch")
    if blob[pos : pos + int(mcs)] != meta_comp:
        raise RuntimeError("captured EG07 metadata copies differ")
    tail, tmcs, tmus, tdigest = V25.FTR.unpack_from(blob, len(blob) - V25.FTR.size)
    if tail != EG07.TAIL_MAGIC or int(tmcs) != int(mcs) or int(tmus) != int(mus) or tdigest != digest:
        raise RuntimeError("captured EG07 authenticated tail disagrees with primary metadata")
    return meta_comp, meta_raw, bytes(digest), raws


def _direct_emit_eg08(raw_eg07: bytes, output: Path, selection: dict[str, int]) -> dict:
    """Compress each final pack once and publish the exact C25EG08 envelope directly."""

    meta_comp, _meta_raw, meta_digest, raws = _raw_eg07_parts(raw_eg07)
    workers = max(1, min(MAX_WORKERS, os.cpu_count() or 1, len(raws)))
    normal_zc = V25.zc

    def compress(item: tuple[int, bytes]):
        index, raw = item
        level = int(selection.get(hashlib.sha256(raw).hexdigest(), 1))
        compressed = normal_zc(raw, level)
        if len(compressed) + 8 < len(raw):
            codec, payload = 1, compressed
        else:
            codec, payload = 0, raw
        return index, level, codec, raw, payload

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="cmpct-eg08-direct-pack") as pool:
        rows = list(pool.map(compress, enumerate(raws)))
    rows.sort(key=lambda item: item[0])
    compression_s = time.perf_counter() - started

    started = time.perf_counter()
    parts = [EG08.HDR.pack(EG08.MAGIC, len(meta_comp), meta_digest), meta_comp]
    for _index, _level, codec, raw, payload in rows:
        parts.extend(
            (
                EG08.PH.pack(
                    int(codec),
                    len(payload),
                    V25.binascii.crc32(raw) & 0xFFFFFFFF,
                    V25.H(raw),
                ),
                payload,
            )
        )
    parts.extend((meta_comp, EG08.FTR.pack(EG08.TAIL_MAGIC, len(meta_comp), meta_digest)))
    final = b"".join(parts)
    output.write_bytes(final)
    publication_s = time.perf_counter() - started
    return {
        "workers": workers,
        "pack_count": len(rows),
        "selected_high_effort_packs": sum(1 for _i, level, _c, _r, _p in rows if level != 1),
        "compression_s": compression_s,
        "publication_s": publication_s,
        "direct_emit_s": compression_s + publication_s,
        "archive_bytes": len(final),
    }


def _direct_memory_selected(stage: Path, root: Path, selection: dict[str, int], reference_bytes: bytes) -> dict:
    raw_eg07, graph_build_s = _capture_raw_final_eg07(stage, root / "capture")
    eg08_archive = root / "direct.c25eg08"
    emit = _direct_emit_eg08(raw_eg07, eg08_archive, selection)

    started = time.perf_counter()
    verified = EG08.strong_verify(eg08_archive, expected_tree=EG07._treehash(stage))
    verify_s = time.perf_counter() - started
    locality = EG08.locality_report(eg08_archive)
    if not verified.get("ok"):
        raise RuntimeError("direct-memory EG08 candidate failed strong verification")
    if not locality.get("within_release_bounds"):
        raise RuntimeError("direct-memory EG08 candidate exceeded frozen locality/decode limits")

    raw = eg08_archive.read_bytes()
    exact_bytes = raw == reference_bytes
    if not exact_bytes:
        raise RuntimeError("direct-memory EG08 emission changed bytes versus serial selected policy")
    return {
        "archive_bytes": len(raw),
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "level1_build_s": graph_build_s,
        "parallel_repack": {
            "workers": emit["workers"],
            "pack_count": emit["pack_count"],
            "selected_high_effort_packs": emit["selected_high_effort_packs"],
            "compression_s": emit["compression_s"],
            "publication_s": emit["publication_s"],
            "repack_s": emit["direct_emit_s"],
        },
        "compact_s": 0.0,
        "strong_verify_s": verify_s,
        "verified_create_s": graph_build_s + float(emit["direct_emit_s"]) + verify_s,
        "exact_bytes_vs_serial": exact_bytes,
        "framing": {
            "profile": "federated-eg08-direct-memory-framing",
            "archive_bytes": len(raw),
            "pack_count": emit["pack_count"],
            "intermediate_repacked_eg07_written": False,
            "intermediate_compaction_pass": False,
        },
        "verified": verified,
        "locality": locality,
        "direct_memory": {
            "raw_eg07_captured_in_memory": True,
            "raw_eg07_bytes": len(raw_eg07),
            "final_archive_publications": 1,
            "intermediate_archive_publications": 0,
        },
    }


@contextmanager
def _direct_memory_patch():
    original = BASE._parallel_selected
    BASE._parallel_selected = _direct_memory_selected
    try:
        yield
    finally:
        BASE._parallel_selected = original


def run(work_root: Path) -> dict:
    with _direct_memory_patch():
        result = dict(BASE.run(work_root))
    result["schema"] = "cmpct-v030-eg08-direct-office-v4"
    result["schedule"] = "in-memory-raw-final-graph-plus-direct-exact-eg08-emission"
    measured = dict(result["measured_candidate"])
    measured["direct_memory"] = {
        "raw_final_eg07_disk_publication": False,
        "recompressed_eg07_disk_publication": False,
        "separate_compaction_pass": False,
        "final_eg08_publications": 1,
    }
    result["measured_candidate"] = measured
    result["single_pass_boundary"] = {
        "graph_search_changed": False,
        "probe_compression_changed": False,
        "final_pack_compressed_once": True,
        "exact_serial_archive_identity_required": True,
        "raw_final_graph_captured_in_memory": True,
        "intermediate_archive_publications": 0,
        "final_eg08_publications": 1,
    }
    result["claim_boundary"] = (
        "Research-only direct-memory C25EG08 office scheduling evidence. Historical graph/search and all probe "
        "compression are unchanged. The raw-final authenticated EG07 envelope is captured in memory, final packs "
        "are compressed once at the exact selected levels, and C25EG08 is published directly with no intermediate "
        "recompressed EG07 or compaction pass. Timing receives credit only after exact byte/SHA identity with the "
        "ordinary serial selected-effort archive plus mandatory strong verification and locality audit. Native/" 
        "Android parity, selector admission, all-15 external/generalization/runtime authorities and strict release "
        "lock remain mandatory before promotion."
    )
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-direct-v4-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-direct-v4.json"))
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
        raise SystemExit("direct-memory C25EG08 office frontier failed")


if __name__ == "__main__":
    main()
