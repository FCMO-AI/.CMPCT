from __future__ import annotations

"""Exact streaming-identity verification experiment for ZIP-factor binary-control v3.

The level sweep proved that level-3 C25Z3 is already smaller than both ZIP/Deflate-9 and solid Zstd-19 and that
its builder alone is faster than ZIP, while the mandatory post-build identity verifier pushes complete creation
past ZIP. This oracle attacks only that verifier cost. It does not change archive bytes, grammar, locality,
recovery, candidate selection, or the required verification boundary.

Instead of materializing every reconstructed source ZIP into a fresh BytesIO object and then hashing that complete
allocation, the candidate verifier hashes the exact reconstructed ZIP byte stream incrementally while tracking its
logical length. The emitted byte sequence is identical to BASE._rebuild_zip(); only the transient allocation is
removed. Baseline and candidate must return identical complete identity maps, semantic trees, locality, and decode
bounds. A corrupted archive must still fail closed.

Research evidence only. A positive result does not authorize selector/native/Android/release promotion.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import struct
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
from benchmarks import v030_external_competitors as EXT
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_profile as BASE

ROUNDS = 11
LEVEL = 3
GROUP_SIZE = 7


def _stream_zip_identity(template: dict, dynamics: list[tuple[int, int, int, bytes]]) -> tuple[int, bytes]:
    """Return exact reconstructed ZIP length/SHA without materializing the complete ZIP."""
    if len(dynamics) != len(template["rows"]):
        raise RuntimeError("ZIP-factor dynamic member count mismatch")
    hasher = hashlib.sha256()
    offsets: list[int] = []
    size = 0

    def emit(raw: bytes) -> None:
        nonlocal size
        hasher.update(raw)
        size += len(raw)

    for row, (crc, csize, usize, payload) in zip(template["rows"], dynamics, strict=True):
        if len(payload) != csize:
            raise RuntimeError("ZIP-factor compressed payload length mismatch")
        offsets.append(size)
        emit(struct.pack(
            "<IHHHHHIIIHH",
            BASE.LOCAL,
            row["version"], row["flags"], row["method"], row["mtime"], row["mdate"],
            crc, csize, usize, len(row["name"]), len(row["local_extra"]),
        ))
        emit(row["name"])
        emit(row["local_extra"])
        emit(payload)

    cd_start = size
    for row, (crc, csize, usize, _payload), offset in zip(template["rows"], dynamics, offsets, strict=True):
        emit(struct.pack(
            "<IHHHHHHIIIHHHHHII",
            BASE.CENTRAL,
            row["made"], row["needed"], row["cflags"], row["cmethod"], row["cmtime"], row["cmdate"],
            crc, csize, usize,
            len(row["name"]), len(row["central_extra"]), len(row["central_comment"]),
            row["disk"], row["internal_attr"], row["external_attr"], offset,
        ))
        emit(row["name"])
        emit(row["central_extra"])
        emit(row["central_comment"])

    cd_size = size - cd_start
    count = len(template["rows"])
    emit(struct.pack(
        "<IHHHHIIH",
        BASE.EOCD,
        template["disk"], template["disk_cd"], count, count,
        cd_size, cd_start, len(template["comment"]),
    ))
    emit(template["comment"])
    return size, hasher.digest()


def verify_streaming_and_identities(archive: Path) -> dict:
    manifest_raw, manifest, template_raw, groups = V3._open(archive)
    template = BASE._parse_template(template_raw)
    identities = {FS.FILESYSTEM_MANIFEST: (len(manifest_raw), V3._sha(manifest_raw))}
    seen: set[str] = set()
    max_amp = 1.0
    max_decode = len(manifest_raw)

    for raw_size, expected_group_sha, paths, blob in groups:
        group_raw = V3._decompress(blob, raw_size, "group")
        if V3._sha(group_raw) != expected_group_sha:
            raise RuntimeError("binary-control ZIP-factor group authentication")
        view = memoryview(group_raw)
        if bytes(view[:4]) != V3.GROUP_MAGIC:
            raise RuntimeError("bad binary-control ZIP-factor group magic")
        at = 4
        count, at = BASE._read_uvarint(view, at)
        if count != len(paths):
            raise RuntimeError("binary-control ZIP-factor group count mismatch")
        context = len(template_raw) + len(group_raw)
        if context > V3.MAX_DECODE:
            raise RuntimeError("binary-control ZIP-factor decode-unit ceiling")
        max_decode = max(max_decode, context)

        for rel in paths:
            if rel in seen or rel not in manifest["regular"]:
                raise RuntimeError("binary-control ZIP-factor logical path mismatch")
            dynamics = []
            for _row in template["rows"]:
                if at + 12 > len(view):
                    raise RuntimeError("truncated binary-control ZIP-factor dynamics")
                crc, csize, usize = struct.unpack_from("<III", view, at)
                at += 12
                if csize > V3.MAX_DECODE or at + csize > len(view):
                    raise RuntimeError("truncated binary-control ZIP-factor payload")
                payload = bytes(view[at:at + csize])
                at += csize
                dynamics.append((crc, csize, usize, payload))
            got_size, got_sha = _stream_zip_identity(template, dynamics)
            expected_size, expected_sha = manifest["regular"][rel]
            if got_size != expected_size or got_sha != expected_sha:
                raise RuntimeError(f"binary-control ZIP-factor reconstructed identity mismatch: {rel}")
            amp = context / max(1, got_size)
            if amp > V3.MAX_AMP:
                raise RuntimeError(f"binary-control ZIP-factor locality ceiling: {rel}")
            max_amp = max(max_amp, amp)
            seen.add(rel)
            identities[rel] = (got_size, got_sha)
        if at != len(view):
            raise RuntimeError("binary-control ZIP-factor group trailing bytes")

    if seen != set(manifest["regular"]):
        raise RuntimeError("binary-control ZIP-factor manifest/content membership mismatch")
    return {
        "ok": True,
        "format_revision": V3.REVISION,
        "format_profile": V3.PROFILE,
        "manifest_raw": manifest_raw,
        "manifest": manifest,
        "identities": identities,
        "verified_user_files": len(seen),
        "max_member_read_amplification": max_amp,
        "max_decode_unit_bytes": max_decode,
    }


def _median(values: list[float]) -> float:
    return float(statistics.median(values))


def _candidate(stage: Path, archive: Path, *, streaming: bool) -> dict:
    started = time.perf_counter()
    build = V3.build(stage, archive, level=LEVEL, group_size=GROUP_SIZE)
    build_s = time.perf_counter() - started
    started = time.perf_counter()
    scan = verify_streaming_and_identities(archive) if streaming else V3.verify_and_identities(archive)
    verify_s = time.perf_counter() - started
    return {
        **build,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "build_s": build_s,
        "verify_s": verify_s,
        "create_s": build_s + verify_s,
        "semantic_tree_sha256": CANON._semantic_tree_sha(scan["manifest"]),
        "identities": {
            rel: [int(size), digest.hex()]
            for rel, (size, digest) in sorted(scan["identities"].items())
        },
        "max_amp": float(scan["max_member_read_amplification"]),
        "max_decode": int(scan["max_decode_unit_bytes"]),
    }


def _corruption_rejected(archive: Path) -> bool:
    raw = bytearray(archive.read_bytes())
    if len(raw) < 64:
        raise RuntimeError("ZIP-factor fixture unexpectedly tiny")
    raw[-17] ^= 0x80
    corrupt = archive.with_name("corrupt.cmpct")
    corrupt.write_bytes(raw)
    try:
        verify_streaming_and_identities(corrupt)
    except Exception:
        return True
    return False


def run(work_root: Path, *, rounds: int = ROUNDS) -> dict:
    if rounds < 5 or rounds % 2 == 0:
        raise ValueError("rounds must be an odd integer >=5")
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    CORPUS.build(corpus)
    source = corpus / "04_deflate_family"

    with tempfile.TemporaryDirectory(prefix="cmpct-zf-stream-id-", dir=work_root) as td_raw:
        td = Path(td_raw)
        stage = EXT._normalized_stage(source, td)
        truth = CANON._prepare_profile_tree(stage, td / "truth")
        source_semantic = CANON._semantic_tree_sha(CANON._decode_manifest(truth["manifest_raw"]))

        zip_times: list[float] = []
        zstd_times: list[float] = []
        baseline_rows: list[dict] = []
        streaming_rows: list[dict] = []
        zip_bytes = None
        zstd_bytes = None

        operations = ["zip", "zstd", "baseline", "streaming"]
        for round_index in range(rounds):
            order = operations[round_index % len(operations):] + operations[:round_index % len(operations)]
            round_dir = td / f"round-{round_index:02d}"
            round_dir.mkdir()
            for op in order:
                if op == "zip":
                    row = EXT._zip(stage, round_dir / "base.zip", round_dir / "zip-out")
                    zip_times.append(float(row["create_s"]))
                    zip_bytes = int(row["archive_bytes"])
                elif op == "zstd":
                    row = EXT._tar_zstd(stage, round_dir / "base.tar.zst", round_dir / "zstd-out", round_dir)
                    if not row.get("available"):
                        raise RuntimeError("zstd comparator unavailable")
                    zstd_times.append(float(row["create_s"]))
                    zstd_bytes = int(row["archive_bytes"])
                elif op == "baseline":
                    baseline_rows.append(_candidate(stage, round_dir / "baseline.cmpct", streaming=False))
                else:
                    streaming_rows.append(_candidate(stage, round_dir / "streaming.cmpct", streaming=True))

        if zip_bytes is None or zstd_bytes is None:
            raise RuntimeError("competitor measurements missing")
        if len(baseline_rows) != rounds or len(streaming_rows) != rounds:
            raise RuntimeError("candidate measurements incomplete")

        baseline_sizes = {row["archive_bytes"] for row in baseline_rows}
        stream_sizes = {row["archive_bytes"] for row in streaming_rows}
        baseline_shas = {row["archive_sha256"] for row in baseline_rows}
        stream_shas = {row["archive_sha256"] for row in streaming_rows}
        baseline_ids = {json.dumps(row["identities"], sort_keys=True) for row in baseline_rows}
        stream_ids = {json.dumps(row["identities"], sort_keys=True) for row in streaming_rows}
        semantics = {row["semantic_tree_sha256"] for row in baseline_rows + streaming_rows}
        exact = (
            len(baseline_sizes) == 1
            and baseline_sizes == stream_sizes
            and len(baseline_shas) == 1
            and baseline_shas == stream_shas
            and len(baseline_ids) == 1
            and baseline_ids == stream_ids
            and semantics == {source_semantic}
            and all(row["max_amp"] <= 8.0 and row["max_decode"] <= 8 * 1024 * 1024 for row in baseline_rows + streaming_rows)
        )

        probe = td / "corruption-probe.cmpct"
        V3.build(stage, probe, level=LEVEL, group_size=GROUP_SIZE)
        corruption_rejected = _corruption_rejected(probe)

        baseline_verify = _median([row["verify_s"] for row in baseline_rows])
        stream_verify = _median([row["verify_s"] for row in streaming_rows])
        baseline_create = _median([row["create_s"] for row in baseline_rows])
        stream_create = _median([row["create_s"] for row in streaming_rows])
        zip_create = _median(zip_times)
        zstd_create = _median(zstd_times)
        archive_bytes = int(next(iter(stream_sizes)))
        verify_improvement = (baseline_verify - stream_verify) / baseline_verify if baseline_verify else 0.0

        experiment_valid = exact and corruption_rejected
        promotion_signal = (
            experiment_valid
            and archive_bytes < zip_bytes
            and archive_bytes < zstd_bytes
            and stream_create < zip_create
            and stream_create < zstd_create
            and stream_verify < baseline_verify
        )
        return {
            "schema": "cmpct-v030-zipfactor-streaming-identity-v1",
            "claim_boundary": "research verifier optimization only; no selector/native/Android/release authority",
            "workload": "resemblance_hostile_v1/04_deflate_family",
            "rounds": rounds,
            "level": LEVEL,
            "group_size": GROUP_SIZE,
            "source_semantic_tree_sha256": source_semantic,
            "archive_bytes": archive_bytes,
            "comparators": {
                "zip_deflate9": {"archive_bytes": zip_bytes, "median_create_s": zip_create},
                "tar_zstd19_solid": {"archive_bytes": zstd_bytes, "median_create_s": zstd_create},
            },
            "baseline": {
                "median_build_s": _median([row["build_s"] for row in baseline_rows]),
                "median_verify_s": baseline_verify,
                "median_create_s": baseline_create,
            },
            "streaming": {
                "median_build_s": _median([row["build_s"] for row in streaming_rows]),
                "median_verify_s": stream_verify,
                "median_create_s": stream_create,
                "verify_improvement_fraction": verify_improvement,
            },
            "evidence": {
                "archive_bytes_sha_identical": baseline_sizes == stream_sizes and baseline_shas == stream_shas,
                "complete_identity_map_identical": baseline_ids == stream_ids,
                "semantic_tree_exact": semantics == {source_semantic},
                "locality_decode_bounds_green": all(
                    row["max_amp"] <= 8.0 and row["max_decode"] <= 8 * 1024 * 1024
                    for row in baseline_rows + streaming_rows
                ),
                "corruption_rejected": corruption_rejected,
            },
            "gate": {
                "experiment_valid": experiment_valid,
                "promotion_signal": promotion_signal,
                "four_way_complete_win": (
                    archive_bytes < zip_bytes
                    and archive_bytes < zstd_bytes
                    and stream_create < zip_create
                    and stream_create < zstd_create
                ),
            },
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-zf-stream-id-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-zf-stream-id.json"))
    parser.add_argument("--rounds", type=int, default=ROUNDS)
    args = parser.parse_args()
    result = run(args.work_root, rounds=args.rounds)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "archive_bytes": result["archive_bytes"],
        "comparators": result["comparators"],
        "baseline": result["baseline"],
        "streaming": result["streaming"],
        "evidence": result["evidence"],
        "gate": result["gate"],
    }, indent=2), flush=True)
    if not result["gate"]["experiment_valid"]:
        raise SystemExit("ZIP-factor streaming identity experiment was invalid")


if __name__ == "__main__":
    main()
