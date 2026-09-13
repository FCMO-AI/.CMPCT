from __future__ import annotations

"""Bounded wire referee for r25 implicit contiguous small-file membership.

Mission: docs/V030_R25_IMPLICIT_MEMBERSHIP_MISSION_2026-09-12.md
Research-only. CMPNX5 is used only as a source of exact pack/member relationships.
"""

import argparse
import copy
import json
from pathlib import Path
import shutil

import msgpack

from benchmarks import v030_compact_pack_control_attribution as ATTR
from experiments import entropygraph_v025 as V25

VERSION = 1
FRAME_RESERVE_PER_COPY = 16
MAX_GROUPS = 4096
MAX_MEMBERS = 65536
MAX_PATH_BYTES = 4096
MAX_LOGICAL_BYTES = 1 << 40
PRIOR_SAVINGS = {
    "01_developer_repository": 16_162,
    "08_many_tiny_files": 33_278,
}
RETAIN_FLOORS = {
    name: int(value * 0.75) for name, value in PRIOR_SAVINGS.items()
}


def _read_archive(archive: Path) -> tuple[dict, bytes, list[int]]:
    raw = archive.read_bytes()
    magic, mcs, mus, npacks, mh = V25.HDR.unpack_from(raw, 0)
    if magic != V25.MAG:
        raise RuntimeError("unexpected v0.25 archive magic")
    mc = raw[V25.HDR.size:V25.HDR.size + mcs]
    mb = V25.zd(mc, mus)
    if V25.H(mb) != mh:
        raise RuntimeError("metadata authentication failed")
    meta = msgpack.unpackb(mb, raw=False)
    if int(meta.get("pack_count", -1)) != int(npacks):
        raise RuntimeError("pack-count drift")
    pos = V25.HDR.size + mcs
    usizes: list[int] = []
    for _ in range(int(npacks)):
        codec, usize, csize, _crc, _hh = V25.PH.unpack_from(raw, pos)
        del codec
        usizes.append(int(usize))
        pos += V25.PH.size + int(csize)
    return meta, mc, usizes


def _wire_from_meta(meta: dict) -> list:
    groups = []
    for pi, entries in meta.get("micro", []):
        groups.append([int(pi), [[str(path), int(length)] for path, length in entries]])
    groups.sort(key=lambda row: row[0])
    return [VERSION, groups]


def _decode_wire(
    wire: object,
    *,
    pack_usizes: list[int],
    max_groups: int = MAX_GROUPS,
    max_members: int = MAX_MEMBERS,
    max_path_bytes: int = MAX_PATH_BYTES,
    max_logical_bytes: int = MAX_LOGICAL_BYTES,
) -> dict[str, tuple[int, int, int]]:
    if not isinstance(wire, list) or len(wire) != 2 or wire[0] != VERSION:
        raise RuntimeError("membership-v1 shape/version")
    groups = wire[1]
    if not isinstance(groups, list) or len(groups) > max_groups:
        raise RuntimeError("membership-v1 group bound")

    lookup: dict[str, tuple[int, int, int]] = {}
    seen_packs: set[int] = set()
    member_count = 0
    logical_total = 0
    for group in groups:
        if not isinstance(group, list) or len(group) != 2:
            raise RuntimeError("membership-v1 group shape")
        pi, entries = group
        if isinstance(pi, bool) or not isinstance(pi, int) or pi < 0 or pi >= len(pack_usizes):
            raise RuntimeError("membership-v1 pack id")
        if pi in seen_packs:
            raise RuntimeError("membership-v1 duplicate pack")
        seen_packs.add(pi)
        if not isinstance(entries, list) or not entries:
            raise RuntimeError("membership-v1 empty/non-list members")

        offset = 0
        for item in entries:
            if not isinstance(item, list) or len(item) != 2:
                raise RuntimeError("membership-v1 member shape")
            path, length = item
            if not isinstance(path, str) or not path or "\\" in path or path.startswith("/"):
                raise RuntimeError("membership-v1 path syntax")
            if len(path.encode("utf-8")) > max_path_bytes or any(part in ("", ".", "..") for part in path.split("/")):
                raise RuntimeError("membership-v1 path bound")
            if path in lookup:
                raise RuntimeError("membership-v1 duplicate path")
            if isinstance(length, bool) or not isinstance(length, int) or length < 0:
                raise RuntimeError("membership-v1 member length")
            if offset > pack_usizes[pi] or length > pack_usizes[pi] - offset:
                raise RuntimeError("membership-v1 pack overflow")
            lookup[path] = (pi, offset, length)
            offset += length
            member_count += 1
            logical_total += length
            if member_count > max_members or logical_total > max_logical_bytes:
                raise RuntimeError("membership-v1 global resource bound")
        if offset != pack_usizes[pi]:
            raise RuntimeError("membership-v1 cumulative pack size mismatch")
    return lookup


def _explicit_lookup(meta: dict) -> dict[str, tuple[int, int, int]]:
    out: dict[str, tuple[int, int, int]] = {}
    expanded = ATTR._expand_micro(meta)
    for path, desc in expanded.get("files", []):
        if (
            isinstance(desc, list) and len(desc) == 3 and desc[0] == "plain"
            and isinstance(desc[1], list) and len(desc[1]) == 1
            and isinstance(desc[1][0], list) and len(desc[1][0]) == 4
            and desc[1][0][0] == "slice"
        ):
            _tag, pi, offset, length = desc[1][0]
            out[str(path)] = (int(pi), int(offset), int(length))
    return out


def _candidate_meta(meta: dict, wire: list) -> dict:
    candidate = copy.deepcopy(meta)
    candidate["membership_v1"] = wire
    candidate["micro"] = []
    return candidate


def _hostile_cases(valid_wire: list, pack_usizes: list[int]) -> dict[str, bool]:
    cases: dict[str, object] = {}
    cases["bad_version"] = [2, valid_wire[1]]
    cases["bad_shape"] = [VERSION, valid_wire[1], []]

    if valid_wire[1]:
        g0 = copy.deepcopy(valid_wire[1][0])
        cases["unknown_pack"] = [VERSION, [[len(pack_usizes), g0[1]]]]
        cases["duplicate_pack"] = [VERSION, [g0, copy.deepcopy(g0)]]
        if g0[1]:
            dup = copy.deepcopy(valid_wire)
            dup[1][0][1].append(copy.deepcopy(dup[1][0][1][0]))
            cases["duplicate_path"] = dup
            wrong = copy.deepcopy(valid_wire)
            wrong[1][0][1][-1][1] = max(0, int(wrong[1][0][1][-1][1]) - 1)
            cases["size_mismatch"] = wrong
            bad_path = copy.deepcopy(valid_wire)
            bad_path[1][0][1][0][0] = "../escape"
            cases["unsafe_path"] = bad_path

    results = {}
    for name, wire in cases.items():
        try:
            _decode_wire(wire, pack_usizes=pack_usizes)
        except RuntimeError:
            results[name] = True
        else:
            results[name] = False
    return results


def _one(source: Path, root: Path, name: str) -> dict:
    archive = root / "archive.cmpct"
    root.mkdir(parents=True, exist_ok=True)
    old_root, old_out = V25.ROOT, V25.OUT
    try:
        V25.ROOT, V25.OUT = source, archive
        build_stats = dict(V25.build())
        verify = dict(V25.strong_verify())
    finally:
        V25.ROOT, V25.OUT = old_root, old_out
    if not verify.get("ok") or verify["tree_sha256"] != V25.treehash(source):
        raise RuntimeError("source strong verification failed")

    meta, compact_mc, pack_usizes = _read_archive(archive)
    wire = _wire_from_meta(meta)
    lookup = _decode_wire(wire, pack_usizes=pack_usizes)
    explicit = _explicit_lookup(meta)
    micro_paths = {str(path) for _pi, entries in meta.get("micro", []) for path, _n in entries}
    expected = {path: explicit[path] for path in micro_paths}
    if lookup != expected:
        raise RuntimeError("membership-v1 semantic reconstruction drift")

    expanded = ATTR._expand_micro(meta)
    expanded_raw = msgpack.packb(expanded, use_bin_type=True)
    expanded_comp = V25.zc(expanded_raw, 12)
    candidate = _candidate_meta(meta, wire)
    candidate_raw = msgpack.packb(candidate, use_bin_type=True)
    candidate_comp = V25.zc(candidate_raw, 12)

    explicit_archive = archive.stat().st_size + 2 * (len(expanded_comp) - len(compact_mc))
    candidate_archive = archive.stat().st_size + 2 * (len(candidate_comp) - len(compact_mc)) + 2 * FRAME_RESERVE_PER_COPY
    saving = explicit_archive - candidate_archive
    hostile = _hostile_cases(wire, pack_usizes)
    floor = RETAIN_FLOORS[name]

    return {
        "source_archive_bytes": archive.stat().st_size,
        "counterfactual_explicit_archive_bytes": explicit_archive,
        "candidate_charged_archive_bytes": candidate_archive,
        "candidate_stored_saving_vs_explicit_bytes": saving,
        "prior_attributed_saving_bytes": PRIOR_SAVINGS[name],
        "retained_saving_fraction": saving / PRIOR_SAVINGS[name],
        "retained_saving_floor_bytes": floor,
        "compact_source_meta_comp_bytes": len(compact_mc),
        "candidate_meta_raw_bytes": len(candidate_raw),
        "candidate_meta_comp_bytes": len(candidate_comp),
        "expanded_meta_raw_bytes": len(expanded_raw),
        "expanded_meta_comp_bytes": len(expanded_comp),
        "framing_reserve_total_bytes": 2 * FRAME_RESERVE_PER_COPY,
        "groups": len(wire[1]),
        "members": len(lookup),
        "lookup_exact": True,
        "payload_packs_unchanged": True,
        "strong_tree_exact": True,
        "hostile_fail_closed": hostile,
        "hostile_all_pass": bool(hostile) and all(hostile.values()),
        "saving_floor_pass": saving >= floor,
        "build_stats": build_stats,
        "tree_sha256": verify["tree_sha256"],
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    corpus = work_root / "corpus"
    ATTR._build_sources(corpus)
    rows = {name: _one(corpus / name, work_root / "artifacts" / name, name) for name in PRIOR_SAVINGS}
    gate = {
        "semantic_reconstruction_exact": all(row["lookup_exact"] for row in rows.values()),
        "hostile_cases_fail_closed": all(row["hostile_all_pass"] for row in rows.values()),
        "payload_packs_unchanged": all(row["payload_packs_unchanged"] for row in rows.values()),
        "strong_trees_exact": all(row["strong_tree_exact"] for row in rows.values()),
        "retains_75pct_saving_both_workloads": all(row["saving_floor_pass"] for row in rows.values()),
    }
    verdict = "R25_IMPLICIT_MEMBERSHIP_WIRE_EARNED" if all(gate.values()) else "RETIRE_R25_IMPLICIT_MEMBERSHIP_WIRE"
    return {
        "schema": "cmpct-v030-r25-implicit-membership-wire-v1",
        "experiment_valid": True,
        "release_credit": False,
        "workloads": rows,
        "gate": gate,
        "verdict": verdict,
        "contract": {
            "version": VERSION,
            "frame_reserve_per_authenticated_copy_bytes": FRAME_RESERVE_PER_COPY,
            "max_groups": MAX_GROUPS,
            "max_members": MAX_MEMBERS,
            "max_path_bytes": MAX_PATH_BYTES,
            "max_logical_bytes": MAX_LOGICAL_BYTES,
            "direct_lookup_built_during_authenticated_control_decode": True,
            "pack_integrity_and_recovery_owned_elsewhere": True,
            "no_path_extension_workload_identity_admission": True,
            "canonical_format_changed": False,
            "release_credit": False,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r25-implicit-membership-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r25-implicit-membership.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps({"verdict": result["verdict"], "workloads": result["workloads"], "gate": result["gate"]}, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
