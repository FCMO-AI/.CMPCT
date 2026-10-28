from __future__ import annotations

"""Complete-artifact referee for compact S_PACK membership in the r25 compact-control line.

Mission: docs/V030_R25_MEMBERSHIP_PRODUCT_INTEGRATION_MISSION_2026-09-12.md
Research-only: this emits a candidate wrapper and reconstructs mature r24 semantics for independent verification.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import time

import msgpack

from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r24_compact_control_oracle as CONTROL
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT

MAGIC = b"C25MG01\0"
TAIL_MAGIC = b"C25MGT1\0"
REVISION = 25
OPEN_REPS = 7
FLOORS = {
    "01_developer_repository": 8_052,
    "08_many_tiny_files": 16_602,
}


class CandidateError(RuntimeError):
    pass


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _candidate_compact(index: dict) -> tuple[dict, dict]:
    compact = copy.deepcopy(CONTROL._compact_index(index))
    by_pack: dict[int, list[tuple[int, int, int]]] = {}
    for fi, row in enumerate(index["files"]):
        if int(row[1]) != R24.K_FILE:
            continue
        storage = row[6]
        if not storage or int(storage[0]) != R24.S_PACK:
            continue
        _tag, pi, offset, length = storage
        by_pack.setdefault(int(pi), []).append((fi, int(offset), int(length)))

    groups: list[list] = []
    implicit_files: set[int] = set()
    rejected_packs: list[int] = []
    for pi, members in sorted(by_pack.items()):
        members.sort(key=lambda item: (item[1], item[0]))
        try:
            blob_usize = int(index["blobs"][pi][1])
        except (IndexError, TypeError, ValueError) as exc:
            raise CandidateError("invalid S_PACK blob reference") from exc
        cursor = 0
        encoded_members: list[list[int]] = []
        valid = True
        for fi, offset, length in members:
            if offset != cursor or length < 0:
                valid = False
                break
            encoded_members.append([fi, length])
            cursor += length
        if not valid or cursor != blob_usize:
            rejected_packs.append(pi)
            continue
        groups.append([pi, encoded_members])
        implicit_files.update(fi for fi, _off, _len in members)

    for fi in sorted(implicit_files):
        encoded = compact["f"][fi]
        if len(encoded) < 6 or encoded[3] is None:
            raise CandidateError("compact row cannot surrender S_PACK ownership")
        encoded[3] = None

    compact["g"] = groups
    return compact, {
        "eligible_groups": len(groups),
        "implicit_members": len(implicit_files),
        "rejected_noncontiguous_packs": rejected_packs,
        "all_spack_members": sum(len(v) for v in by_pack.values()),
    }


def _expand_candidate(compact: dict, *, version: int, features: list) -> dict:
    if not isinstance(compact, dict) or "g" not in compact:
        raise CandidateError("missing membership groups")
    groups = compact["g"]
    if not isinstance(groups, list) or len(groups) > 4096:
        raise CandidateError("membership group bound")
    rows = compact.get("f")
    blobs = compact.get("b")
    if not isinstance(rows, list) or not isinstance(blobs, list):
        raise CandidateError("invalid compact control tables")

    restored = copy.deepcopy(compact)
    restored.pop("g", None)
    seen_packs: set[int] = set()
    seen_files: set[int] = set()
    total_members = 0
    for group in groups:
        if not isinstance(group, list) or len(group) != 2:
            raise CandidateError("membership group shape")
        pi, members = group
        if isinstance(pi, bool) or not isinstance(pi, int) or pi < 0 or pi >= len(blobs):
            raise CandidateError("membership pack reference")
        if pi in seen_packs:
            raise CandidateError("duplicate membership pack")
        seen_packs.add(pi)
        if not isinstance(members, list) or not members:
            raise CandidateError("empty membership group")
        blob_usize = int(blobs[pi][1])
        cursor = 0
        for member in members:
            if not isinstance(member, list) or len(member) != 2:
                raise CandidateError("membership member shape")
            fi, length = member
            if isinstance(fi, bool) or not isinstance(fi, int) or fi < 0 or fi >= len(rows):
                raise CandidateError("membership file reference")
            if fi in seen_files:
                raise CandidateError("duplicate membership file")
            seen_files.add(fi)
            if isinstance(length, bool) or not isinstance(length, int) or length < 0:
                raise CandidateError("membership length")
            if cursor > blob_usize or length > blob_usize - cursor:
                raise CandidateError("membership pack overflow")
            encoded = restored["f"][fi]
            if len(encoded) < 6 or encoded[3] is not None:
                raise CandidateError("membership ownership collision")
            encoded[3] = [R24.S_PACK, pi, cursor, length]
            cursor += length
            total_members += 1
            if total_members > 65536:
                raise CandidateError("membership member bound")
        if cursor != blob_usize:
            raise CandidateError("membership cumulative size mismatch")

    # No row may silently lose storage ownership.
    for encoded in restored["f"]:
        kind = int(encoded[0])
        if kind not in (R24.K_DIR, R24.K_HARDLINK) and encoded[3] is None:
            raise CandidateError("unowned regular-file storage")
    return CONTROL._expand_index(restored, version=version, features=features)


def _candidate_control(index: dict) -> tuple[bytes, dict, dict]:
    compact, stats = _candidate_compact(index)
    expanded = _expand_candidate(compact, version=int(index["v"]), features=list(index["features"]))
    if expanded != index:
        raise CandidateError("candidate compact control does not reconstruct exact r24 index")
    envelope = {"x": list(index["features"]), "c": compact}
    raw = msgpack.packb(envelope, use_bin_type=True)
    if len(raw) > CC.MAX_CONTROL_RAW_BYTES:
        raise CandidateError("candidate control exceeds raw bound")
    level, comp = CC._compress_control(raw)
    return comp, {**stats, "raw_bytes": len(raw), "comp_bytes": len(comp), "level": level}, expanded


def _write_candidate(source_r24: Path, out: Path) -> dict:
    index, data, physical = CC._source_r24_parts(source_r24)
    locality = CC._audit_s_pack_locality(index)
    tick_wall = time.perf_counter()
    tick_cpu = time.process_time()
    comp, membership, expanded = _candidate_control(index)
    transform_cpu = time.process_time() - tick_cpu
    transform_wall = time.perf_counter() - tick_wall
    digest = _sha(msgpack.packb({"x": list(index["features"]), "c": _candidate_compact(index)[0]}, use_bin_type=True))
    # Recompute once only for digest clarity; verify compression bytes correspond to the same raw object.
    compact, _ = _candidate_compact(index)
    raw = msgpack.packb({"x": list(index["features"]), "c": compact}, use_bin_type=True)
    if R24.zd(comp, len(raw)) != raw:
        raise CandidateError("candidate compressed control roundtrip failed")
    digest = _sha(raw)
    header = R24.HDR.pack(MAGIC, REVISION, 0, len(comp), len(raw), len(data), digest)
    footer = R24.FTR.pack(TAIL_MAGIC, 0, 1, 0, 0, len(comp), len(raw), 0, digest)
    payload = header + comp + data + comp + footer
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(payload)
    return {
        "archive_bytes": len(payload),
        "source_r24_bytes": int(physical["archive_bytes"]),
        "physical_data_bytes": len(data),
        "physical_data_sha256": hashlib.sha256(data).hexdigest(),
        "control_comp_bytes_per_copy": len(comp),
        "control_raw_bytes": len(raw),
        "control_level": membership["level"],
        "membership": membership,
        "transform_cpu_s": transform_cpu,
        "transform_wall_s": transform_wall,
        "semantic_index_exact": expanded == index,
        "locality": locality,
    }


def _parse_candidate_bytes(payload: bytes) -> dict:
    if len(payload) < R24.HDR.size + R24.FTR.size:
        raise CandidateError("truncated candidate")
    magic, version, _flags, pc, raw_bytes, data_bytes, psha = R24.HDR.unpack_from(payload, 0)
    if magic != MAGIC or int(version) != REVISION:
        raise CandidateError("candidate magic/revision")
    footer_off = len(payload) - R24.FTR.size
    fmagic, _a, _b, _c, _d, tc, traw, _r, tsha = R24.FTR.unpack_from(payload, footer_off)
    if fmagic != TAIL_MAGIC:
        raise CandidateError("candidate tail magic")
    ps = R24.HDR.size
    pe = ps + int(pc)
    ts = footer_off - int(tc)
    if pe + int(data_bytes) != ts:
        raise CandidateError("candidate span accounting")

    decoded = None
    recovery = None
    for comp, declared_raw, digest, label in (
        (payload[ps:pe], int(raw_bytes), psha, "primary"),
        (payload[ts:footer_off], int(traw), tsha, "tail"),
    ):
        try:
            if declared_raw < 0 or declared_raw > CC.MAX_CONTROL_RAW_BYTES:
                raise CandidateError("candidate raw-size bound")
            raw = R24.zd(comp, declared_raw)
            if _sha(raw) != digest:
                raise CandidateError("candidate control SHA")
            obj = msgpack.unpackb(raw, raw=False, strict_map_key=False)
            if not isinstance(obj, dict) or set(obj) != {"x", "c"}:
                raise CandidateError("candidate envelope")
            index = _expand_candidate(obj["c"], version=R24.VERSION, features=list(obj["x"]))
            decoded = index
            recovery = label
            break
        except Exception:
            continue
    if decoded is None:
        raise CandidateError("both candidate controls invalid")
    return {
        "index": decoded,
        "data": payload[pe:ts],
        "recovery_source": recovery,
    }


def _verify_candidate(path: Path, expected_index: dict, expected_tree: str, work: Path) -> dict:
    payload = path.read_bytes()
    wall_samples = []
    cpu_samples = []
    parsed = None
    for _ in range(OPEN_REPS):
        tw = time.perf_counter(); tc = time.process_time()
        parsed = _parse_candidate_bytes(payload)
        cpu_samples.append(time.process_time() - tc); wall_samples.append(time.perf_counter() - tw)
    assert parsed is not None
    if parsed["index"] != expected_index:
        raise CandidateError("candidate parse index drift")
    rebuilt = work / "candidate-expanded-r24.cmpct"
    rebuilt.write_bytes(CC._rebuild_r24_bytes(parsed))
    verify = PRODUCT.strong_verify(rebuilt)
    if not verify.get("ok") or verify.get("tree_sha256") != expected_tree:
        raise CandidateError("candidate mature-reader strong verification failed")

    # Corrupt the primary control only and require authenticated tail recovery.
    corrupt = bytearray(payload)
    _m, _v, _f, pc, _rb, _db, _sh = R24.HDR.unpack_from(corrupt, 0)
    if int(pc) < 3:
        raise CandidateError("candidate primary control unexpectedly tiny")
    corrupt[R24.HDR.size + int(pc) // 2] ^= 0x01
    recovered = _parse_candidate_bytes(bytes(corrupt))
    if recovered["recovery_source"] != "tail" or recovered["index"] != expected_index:
        raise CandidateError("candidate tail recovery failed")
    return {
        "strong_tree_exact": True,
        "semantic_index_exact": True,
        "primary_corruption_tail_recovery": True,
        "median_open_expand_cpu_s": statistics.median(cpu_samples),
        "median_open_expand_wall_s": statistics.median(wall_samples),
    }


def _hostile_table(index: dict) -> dict[str, bool]:
    compact, _ = _candidate_compact(index)
    tests: dict[str, dict] = {}
    if compact["g"]:
        duplicate_pack = copy.deepcopy(compact); duplicate_pack["g"].append(copy.deepcopy(duplicate_pack["g"][0])); tests["duplicate_pack"] = duplicate_pack
        bad_file = copy.deepcopy(compact); bad_file["g"][0][1][0][0] = len(compact["f"]); tests["bad_file_index"] = bad_file
        mismatch = copy.deepcopy(compact); mismatch["g"][0][1][-1][1] = max(0, int(mismatch["g"][0][1][-1][1]) - 1); tests["size_mismatch"] = mismatch
        duplicate_file = copy.deepcopy(compact); duplicate_file["g"][0][1].append(copy.deepcopy(duplicate_file["g"][0][1][0])); tests["duplicate_file"] = duplicate_file
    results = {}
    for name, obj in tests.items():
        try:
            _expand_candidate(obj, version=int(index["v"]), features=list(index["features"]))
        except Exception:
            results[name] = True
        else:
            results[name] = False
    return results


def _one(source: Path, work: Path, name: str) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    r24 = work / "source-r24.cmpct"
    PRODUCT._locality_bounded_r24_build(source, r24)
    source_verify = PRODUCT.strong_verify(r24)
    if not source_verify.get("ok"):
        raise CandidateError("source r24 verification failed")
    index, data, _physical = CC._source_r24_parts(r24)

    baseline = work / "baseline-c25cc01.cmpct"
    baseline_stats = CC._write_profile(r24, baseline)
    candidate = work / "candidate-c25mg01.cmpct"
    candidate_stats = _write_candidate(r24, candidate)
    candidate_verify = _verify_candidate(candidate, index, str(source_verify["tree_sha256"]), work)
    hostile = _hostile_table(index)

    baseline_parsed = CC._parse(baseline)
    if baseline_parsed["index"] != index or baseline_parsed["data"] != data:
        raise CandidateError("baseline compact-control semantic drift")
    candidate_parsed = _parse_candidate_bytes(candidate.read_bytes())
    if candidate_parsed["data"] != data:
        raise CandidateError("candidate changed physical payload span")

    saving = baseline.stat().st_size - candidate.stat().st_size
    floor = FLOORS[name]
    locality = candidate_stats["locality"]
    locality_pass = (
        float(locality["max_s_pack_member_amplification"]) <= CC.MAX_MEMBER_READ_AMPLIFICATION
        and int(locality["max_s_pack_decode_unit_bytes"]) <= CC.MAX_DECODE_UNIT_BYTES
    )
    return {
        "source_r24_bytes": r24.stat().st_size,
        "baseline_c25cc01_bytes": baseline.stat().st_size,
        "candidate_bytes": candidate.stat().st_size,
        "saving_vs_c25cc01_bytes": saving,
        "materiality_floor_bytes": floor,
        "materiality_pass": saving >= floor,
        "baseline_control_comp_bytes_per_copy": int(baseline_stats["compact_control_comp_bytes_per_copy"]),
        "candidate_control_comp_bytes_per_copy": int(candidate_stats["control_comp_bytes_per_copy"]),
        "candidate_control_raw_bytes": int(candidate_stats["control_raw_bytes"]),
        "physical_data_bytes": len(data),
        "physical_data_sha256": hashlib.sha256(data).hexdigest(),
        "physical_payload_unchanged": candidate_parsed["data"] == data,
        "eligible_groups": int(candidate_stats["membership"]["eligible_groups"]),
        "implicit_members": int(candidate_stats["membership"]["implicit_members"]),
        "all_spack_members": int(candidate_stats["membership"]["all_spack_members"]),
        "rejected_noncontiguous_packs": candidate_stats["membership"]["rejected_noncontiguous_packs"],
        "candidate_transform_cpu_s": float(candidate_stats["transform_cpu_s"]),
        "candidate_transform_wall_s": float(candidate_stats["transform_wall_s"]),
        "median_open_expand_cpu_s": float(candidate_verify["median_open_expand_cpu_s"]),
        "median_open_expand_wall_s": float(candidate_verify["median_open_expand_wall_s"]),
        "semantic_index_exact": bool(candidate_verify["semantic_index_exact"]),
        "strong_tree_exact": bool(candidate_verify["strong_tree_exact"]),
        "primary_corruption_tail_recovery": bool(candidate_verify["primary_corruption_tail_recovery"]),
        "hostile_fail_closed": hostile,
        "hostile_all_pass": bool(hostile) and all(hostile.values()),
        "locality": locality,
        "locality_pass": locality_pass,
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpus = work_root / "corpus"
    ATTR._build_sources(corpus)
    rows = {name: _one(corpus / name, work_root / "work" / name, name) for name in FLOORS}
    gate = {
        "complete_artifact_materiality_both": all(row["materiality_pass"] for row in rows.values()),
        "semantic_index_exact_both": all(row["semantic_index_exact"] for row in rows.values()),
        "strong_tree_exact_both": all(row["strong_tree_exact"] for row in rows.values()),
        "physical_payload_unchanged_both": all(row["physical_payload_unchanged"] for row in rows.values()),
        "tail_recovery_both": all(row["primary_corruption_tail_recovery"] for row in rows.values()),
        "hostile_fail_closed_both": all(row["hostile_all_pass"] for row in rows.values()),
        "locality_preserved_both": all(row["locality_pass"] for row in rows.values()),
    }
    verdict = "R25_MEMBERSHIP_COMPLETE_ARTIFACT_EARNED" if all(gate.values()) else "RETIRE_OR_REDESIGN_R25_MEMBERSHIP_INTEGRATION"
    return {
        "schema": "cmpct-v030-r25-membership-complete-artifact-v1",
        "experiment_valid": True,
        "release_credit": False,
        "format_changed": False,
        "rss_claim": False,
        "workloads": rows,
        "gate": gate,
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-membership-complete-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-membership-complete.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps({"verdict": result["verdict"], "gate": result["gate"], "workloads": result["workloads"]}, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
