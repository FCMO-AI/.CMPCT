from __future__ import annotations

"""Exact-byte parallel recompression proof for the C25EG02 federated candidate.

The selective-effort frontier established two different blockers:
- office needs structural bytes, because C25EG01 cannot cross accepted v0.29 even with every pack at its best effort;
- analytics can cross the byte floor, but the useful higher-effort pack compressions are too expensive when paid
  serially.

C25EG02 attacks the first problem by removing duplicate filesystem/content identity.  This oracle attacks the
second without changing representation semantics: build the ordinary level-1 C25EG02 graph once, then recompress
its already-independent physical packs concurrently using the exact per-pack policy selected by the audited
frontier.  The resulting archive MUST be byte-for-byte identical to the ordinary sequential policy build.

The measured full boundary is intentionally conservative: level-1 construction is paid in full, selected packs
are then recompressed, and the final archive receives one mandatory strong verification.  A future product builder
could avoid the duplicated level-1 compression by parallelizing the final pack-emission stage directly; this
oracle does not credit that unrealized optimization.

Research only: no selector, format, accepted-v0.29 byte, comparator, locality ceiling, native/Android surface or
release authority is modified.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import tempfile
import time

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_federated_compact_effort_oracle as FRONTIER
from benchmarks import v030_federated_selective_effort_oracle as EFFORT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v025 as V25
from experiments import entropygraph_v030_federated_compact_candidate as EG02

MAX_WORKERS = 8


def _h(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


@contextmanager
def _eg02_effort_binding():
    old_candidate = EFFORT.CAND
    old_prepare = EFFORT._prepare
    EFFORT.CAND = EG02
    EFFORT._prepare = FRONTIER._compact_prepare
    try:
        yield
    finally:
        EFFORT.CAND = old_candidate
        EFFORT._prepare = old_prepare


def _baseline_build(source: Path, root: Path) -> tuple[Path, float]:
    profile = root / "profile"
    archive = root / "baseline.c25eg02"
    EG02._prepare_profile(source, profile)
    started = time.perf_counter()
    with EG02._engine(archive, profile):
        V25.build()
    return archive, time.perf_counter() - started


def _raw_packs(archive: Path) -> list[bytes]:
    raws: list[bytes] = []
    with EG02._engine(archive.resolve()):
        handle, _meta, offsets = V25.open_ar()
        try:
            for index, (off, codec, usize, csize, crc, expected_sha) in enumerate(offsets):
                handle.seek(int(off))
                payload = handle.read(int(csize))
                if len(payload) != int(csize):
                    raise RuntimeError(f"truncated baseline pack {index}")
                if int(codec) == 1:
                    raw = V25.zd(payload, int(usize))
                elif int(codec) == 0:
                    raw = payload
                else:
                    raise RuntimeError(f"unsupported baseline pack codec {codec}")
                if len(raw) != int(usize):
                    raise RuntimeError(f"baseline pack size mismatch {index}")
                if (V25.binascii.crc32(raw) & 0xFFFFFFFF) != int(crc) or V25.H(raw) != bytes(expected_sha):
                    raise RuntimeError(f"baseline pack identity mismatch {index}")
                raws.append(raw)
        finally:
            handle.close()
    return raws


def _archive_envelope(archive: Path) -> tuple[bytes, bytes, bytes]:
    with archive.open("rb") as stream:
        header = stream.read(V25.HDR.size)
        if len(header) != V25.HDR.size:
            raise RuntimeError("short C25EG02 header")
        magic, meta_csize, _meta_usize, _pack_count, _meta_sha = V25.HDR.unpack(header)
        if magic != EG02.MAGIC:
            raise RuntimeError("parallel repack input is not C25EG02")
        primary_meta = stream.read(int(meta_csize))
        if len(primary_meta) != int(meta_csize):
            raise RuntimeError("short C25EG02 primary metadata")
        stream.seek(-V25.FTR.size, os.SEEK_END)
        footer = stream.read(V25.FTR.size)
        if len(footer) != V25.FTR.size:
            raise RuntimeError("short C25EG02 footer")
        tail_magic, tail_csize, _tail_usize, _tail_sha = V25.FTR.unpack(footer)
        if tail_magic != EG02.TAIL_MAGIC or int(tail_csize) != int(meta_csize):
            raise RuntimeError("C25EG02 tail metadata declaration mismatch")
        stream.seek(-(V25.FTR.size + int(tail_csize)), os.SEEK_END)
        tail_meta = stream.read(int(tail_csize))
        if tail_meta != primary_meta:
            raise RuntimeError("C25EG02 authenticated metadata copies differ before repack")
    return header, primary_meta, footer


def _parallel_repack(source_archive: Path, output: Path, selection: dict[str, int]) -> dict:
    raws = _raw_packs(source_archive)
    header, meta_comp, footer = _archive_envelope(source_archive)
    normal_zc = V25.zc
    workers = max(1, min(MAX_WORKERS, os.cpu_count() or 1, len(raws)))

    def compress(item: tuple[int, bytes]):
        index, raw = item
        level = int(selection.get(_h(raw), 1))
        compressed = normal_zc(raw, level)
        if len(compressed) + 8 < len(raw):
            codec, payload = 1, compressed
        else:
            codec, payload = 0, raw
        return index, level, codec, raw, payload

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="cmpct-eg02-pack") as pool:
        rows = list(pool.map(compress, enumerate(raws)))
    rows.sort(key=lambda item: item[0])
    compression_s = time.perf_counter() - started

    output.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    with output.open("wb") as stream:
        stream.write(header)
        stream.write(meta_comp)
        for _index, _level, codec, raw, payload in rows:
            stream.write(
                V25.PH.pack(
                    int(codec),
                    len(raw),
                    len(payload),
                    V25.binascii.crc32(raw) & 0xFFFFFFFF,
                    V25.H(raw),
                )
            )
            stream.write(payload)
        stream.write(meta_comp)
        stream.write(footer)
    publication_s = time.perf_counter() - started
    return {
        "workers": workers,
        "pack_count": len(rows),
        "selected_high_effort_packs": sum(1 for _i, level, _c, _r, _p in rows if level != 1),
        "compression_s": compression_s,
        "publication_s": publication_s,
        "repack_s": compression_s + publication_s,
    }


def _sequential_reference(source: Path, root: Path, selection: dict[str, int]) -> dict:
    with _eg02_effort_binding():
        return EFFORT._policy_build(source, root, selection)


def _one(source: Path, root: Path, accepted_v029_bytes: int, frontier_row: dict) -> dict:
    minimum = frontier_row.get("minimum_modeled_effort_to_v029")
    if minimum is None:
        return {
            "label": frontier_row["label"],
            "accepted_v029_bytes": int(accepted_v029_bytes),
            "policy_available": False,
            "reason": "compact frontier has no measured pack-effort policy that crosses accepted v0.29",
        }
    selection = {str(key): int(value) for key, value in minimum["selection"].items()}
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-eg02-parallel-", dir=root) as td:
        work = Path(td)
        stage = EXT._normalized_stage(source, work / "normalized")

        base_archive, base_build_s = _baseline_build(stage, work / "baseline")
        parallel_archive = work / "parallel.c25eg02"
        repack = _parallel_repack(base_archive, parallel_archive, selection)
        started = time.perf_counter()
        verified = EG02.strong_verify(parallel_archive, expected_tree=EG02._treehash(stage))
        verify_s = time.perf_counter() - started
        locality = EG02.locality_report(parallel_archive)
        if not verified.get("ok") or not locality.get("within_release_bounds"):
            raise RuntimeError("parallel C25EG02 policy failed integrity/locality")

        seq_root = work / "sequential"
        seq_root.mkdir()
        sequential = _sequential_reference(stage, seq_root, selection)
        sequential_archive = seq_root / "candidate.c25eg01"
        if not sequential_archive.is_file():
            raise RuntimeError("sequential reference archive was not produced")
        exact_bytes = parallel_archive.read_bytes() == sequential_archive.read_bytes()
        if not exact_bytes:
            raise RuntimeError("parallel repack changed C25EG02 bytes versus sequential policy")

        comparators = frontier_row["comparators"]
        final_bytes = parallel_archive.stat().st_size
        conservative_verified_create_s = base_build_s + float(repack["repack_s"]) + verify_s
        strict = {
            "beats_accepted_v029_size": final_bytes < int(accepted_v029_bytes),
            "beats_zip_size": final_bytes < int(comparators["zip"]["archive_bytes"]),
            "beats_zstd19_size": final_bytes < int(comparators["zstd19"]["archive_bytes"]),
            "conservative_verified_create_beats_zip": conservative_verified_create_s < float(comparators["zip"]["median_create_s"]),
            "conservative_verified_create_beats_zstd19": conservative_verified_create_s < float(comparators["zstd19"]["median_create_s"]),
            "within_release_locality_bounds": bool(locality["within_release_bounds"]),
            "byte_identical_to_sequential_policy": exact_bytes,
        }
        strict["passed"] = all(strict.values())
        return {
            "label": frontier_row["label"],
            "accepted_v029_bytes": int(accepted_v029_bytes),
            "policy_available": True,
            "selection": selection,
            "modeled_serial_extra_ms": int(minimum["modeled_extra_ms"]),
            "archive_bytes": final_bytes,
            "base_level1_build_s": base_build_s,
            "parallel_repack": repack,
            "strong_verify_s": verify_s,
            "conservative_verified_create_s": conservative_verified_create_s,
            "sequential_verified_create_s": float(sequential["verified_create_s"]),
            "parallel_vs_sequential_speedup": float(sequential["verified_create_s"]) / max(conservative_verified_create_s, 1e-12),
            "comparators": comparators,
            "locality": locality,
            "strict": strict,
        }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)

    # Reuse the exact compact structural/effort frontier so the policy is derived rather than hard-coded.
    frontier = FRONTIER.run(work_root / "frontier")
    rows_by_label = {row["label"]: row for row in frontier["rows"]}

    accepted = GENERAL._accepted_v029_rows()
    neutral = GENERAL.V029._load(
        GENERAL.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "cmpct_v030_eg02_parallel_neutral",
    )
    repair = GENERAL.V029._load(GENERAL.V029.REPAIR_PATH, "cmpct_v030_eg02_parallel_repair")
    repair.install_generation_hooks(neutral)
    corpus = work_root / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)

    results = []
    for name in EFFORT.TARGETS:
        label = f"neutral_hostile_v1/{name}"
        source = corpus / name
        key = ("neutral_hostile_v1", name)
        expected_tree = accepted[key]["tree_sha256"]
        if EXT._tree(source) != expected_tree:
            raise RuntimeError(f"frozen source drift for {label}")
        accepted_bytes = int(accepted[key].get("accepted_v029_bytes", accepted[key].get("archive_bytes")))
        row = _one(source, work_root, accepted_bytes, rows_by_label[label])
        results.append(row)
        print(json.dumps({"label": label, "policy_available": row["policy_available"], "strict": row.get("strict")}, separators=(",", ":")), flush=True)

    available = [row for row in results if row["policy_available"]]
    gate = {
        "exact_target_count": len(results) == len(EFFORT.TARGETS),
        "frontier_measurement_valid": bool(frontier["measurement_gate"]["passed"]),
        "all_available_policies_exact_byte_identical": all(row["strict"]["byte_identical_to_sequential_policy"] for row in available),
        "all_available_policies_locality_safe": all(row["strict"]["within_release_locality_bounds"] for row in available),
    }
    gate["passed"] = all(gate.values())
    return {
        "schema": "cmpct-v030-federated-eg02-parallel-repack-v1",
        "candidate": "C25EG02",
        "max_workers": MAX_WORKERS,
        "frontier_schema": frontier["schema"],
        "rows": results,
        "measurement_gate": gate,
        "summary": {
            "policies_available": [row["label"] for row in available],
            "conservative_full_contract_wins": [row["label"] for row in available if row["strict"]["passed"]],
        },
        "claim_boundary": (
            "Research-only exact-byte scheduling proof. The measured conservative boundary pays the ordinary level-1 build, "
            "parallel recompression and one final strong verification; it therefore does not assume an unrealized single-pass "
            "builder. No selector, format grammar, accepted-v0.29 byte, ZIP/Zstd comparator, locality/decode ceiling, native/" 
            "Android surface or release authority is changed."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg02-parallel-repack-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg02-parallel-repack.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "measurement_gate": result["measurement_gate"]}, indent=2))
    if not result["measurement_gate"]["passed"]:
        raise SystemExit("C25EG02 parallel repack measurement invalid")


if __name__ == "__main__":
    main()
