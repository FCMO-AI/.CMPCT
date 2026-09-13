from __future__ import annotations

"""Referee for deriving r24 micro-pack geometry directly from the frozen <=8x locality law.

Mission: docs/V030_R24_LOCALITY_DERIVED_MICROPACK_MISSION_2026-09-12.md
Research-only. No canonical builder policy is modified by this module.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import time

from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r25_membership_complete_artifact_referee as MEMBERSHIP
from cmpct import builder as BUILDER
from cmpct import codec as R24
from experiments import entropygraph_v030_r24_compact_control_profile as CC
from experiments import entropygraph_v030_release_product as PRODUCT

LOCALITY_BUDGET = 8.0
MAX_DECODE_UNIT = 8 * 1024 * 1024


class LocalityDerivedBuilder(BUILDER.Builder):
    """Mature r24 builder with only micro-pack grouping replaced by an 8x-derived law."""

    def _build_micro_packs(self):
        refs = {}
        for row in self.files:
            if row[1] != R24.K_FILE or not row[6] or row[6][0] != R24.S_BLOB:
                continue
            h = bytes(row[6][1])
            refs.setdefault(h, []).append(row)

        eligible = []
        for h, rows in refs.items():
            c = self.cands.get(h)
            if c is None or c.deflates or len(c.raw) > self.micro_pack_max_file:
                continue
            if not any(x in BUILDER.TEXT_EXT for x in c.hints):
                continue
            eligible.append((h, c))

        buckets = {}
        for h, c in eligible:
            ext = next((x for x in sorted(c.hints) if x in BUILDER.TEXT_EXT), ".text")
            buckets.setdefault(ext, []).append((h, c))

        emitted_groups = []

        def flush(group):
            if len(group) < 2:
                return
            buf = bytearray()
            slots = {}
            for h, c in group:
                off = len(buf)
                buf += c.raw
                slots[h] = (off, len(c.raw))
            first_size = len(group[0][1].raw)
            if len(buf) > int(LOCALITY_BUDGET * first_size):
                raise RuntimeError("locality-derived group exceeds 8x smallest-member law")
            ph = self.add_content(bytes(buf), ".cmpct-pack")
            for h, (off, ln) in slots.items():
                for row in refs[h]:
                    row[6] = [R24.S_PACK, ph, off, ln]
            for h in slots:
                if h != ph:
                    self.cands.pop(h, None)
            emitted_groups.append({
                "members": len(group),
                "raw_bytes": len(buf),
                "smallest_member_bytes": first_size,
                "max_raw_amplification": len(buf) / max(1, first_size),
            })

        for _ext, items in sorted(buckets.items()):
            items.sort(key=lambda hc: (len(hc[1].raw), hc[0]))
            group = []
            used = 0
            cap = 0
            for h, c in items:
                size = len(c.raw)
                if not group:
                    group = [(h, c)]
                    used = size
                    cap = int(LOCALITY_BUDGET * max(1, size))
                    continue
                if used + size > cap:
                    flush(group)
                    group = [(h, c)]
                    used = size
                    cap = int(LOCALITY_BUDGET * max(1, size))
                else:
                    group.append((h, c))
                    used += size
            flush(group)
        self._locality_derived_groups = emitted_groups


def _build_with(builder: BUILDER.Builder, out: Path) -> dict:
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    stats = dict(builder.build(out))
    return {
        **stats,
        "archive_bytes": out.stat().st_size,
        "build_cpu_s": time.process_time() - started_cpu,
        "build_wall_s": time.perf_counter() - started_wall,
    }


def _parse_r24(path: Path) -> tuple[dict, bytes]:
    index, data, _physical = CC._source_r24_parts(path)
    return index, data


def _pack_locality(index: dict) -> dict:
    packs = {}
    for row in index.get("files", []):
        if int(row[1]) != R24.K_FILE or not row[6] or int(row[6][0]) != R24.S_PACK:
            continue
        _tag, pi, off, ln = row[6]
        pi = int(pi); off = int(off); ln = int(ln)
        usize = int(index["blobs"][pi][1])
        amp = usize / max(1, ln)
        packs.setdefault(pi, {"usize": usize, "members": []})["members"].append((off, ln, amp))
    amps = [amp for pack in packs.values() for _off, _ln, amp in pack["members"]]
    weighted_num = sum(pack["usize"] * ln for pack in packs.values() for _off, ln, _amp in pack["members"])
    weighted_den = sum(ln * ln for pack in packs.values() for _off, ln, _amp in pack["members"])
    return {
        "pack_count": len(packs),
        "member_count": len(amps),
        "max_member_amplification": max(amps, default=1.0),
        "weighted_member_amplification": weighted_num / max(1, weighted_den),
        "max_decode_unit_bytes": max((pack["usize"] for pack in packs.values()), default=0),
        "locality_pass": max(amps, default=1.0) <= LOCALITY_BUDGET and max((pack["usize"] for pack in packs.values()), default=0) <= MAX_DECODE_UNIT,
    }


def _build_variants(source: Path, work: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    rows = {}

    current = work / "current-release-r24.cmpct"
    rows["current_release_r24"] = dict(PRODUCT._locality_bounded_r24_build(source, current))
    current_index, _ = _parse_r24(current)
    rows["current_release_r24"]["locality"] = _pack_locality(current_index)
    rows["current_release_r24"]["strong_tree_exact"] = bool(PRODUCT.strong_verify(current).get("ok"))

    independent = work / "independent-r24.cmpct"
    ib = BUILDER.Builder(source, deflate_reuse_min=0, workers=1)
    ib.micro_pack_max_file = 0
    rows["independent_r24"] = _build_with(ib, independent)
    independent_index, _ = _parse_r24(independent)
    rows["independent_r24"]["locality"] = _pack_locality(independent_index)
    rows["independent_r24"]["strong_tree_exact"] = bool(PRODUCT.strong_verify(independent).get("ok"))

    derived = work / "locality-derived-r24.cmpct"
    db = LocalityDerivedBuilder(source, deflate_reuse_min=0, workers=1)
    db.micro_pack_max_file = PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES
    rows["derived_r24"] = _build_with(db, derived)
    rows["derived_r24"]["derived_groups"] = list(getattr(db, "_locality_derived_groups", []))
    derived_index, derived_data = _parse_r24(derived)
    rows["derived_r24"]["locality"] = _pack_locality(derived_index)
    dv = PRODUCT.strong_verify(derived)
    rows["derived_r24"]["strong_tree_exact"] = bool(dv.get("ok"))
    rows["derived_r24"]["tree_sha256"] = dv.get("tree_sha256")

    compact = work / "derived-c25cc01.cmpct"
    cc_started_cpu = time.process_time(); cc_started_wall = time.perf_counter()
    cc_stats = dict(CC._write_profile(derived, compact))
    rows["derived_c25cc01"] = {
        **cc_stats,
        "archive_bytes": compact.stat().st_size,
        "transform_cpu_s": time.process_time() - cc_started_cpu,
        "transform_wall_s": time.perf_counter() - cc_started_wall,
    }
    cc_parsed = CC._parse(compact)
    if cc_parsed["index"] != derived_index or cc_parsed["data"] != derived_data:
        raise RuntimeError("C25CC01 changed derived r24 semantics/data")

    candidate = work / "derived-membership.cmpct"
    candidate_stats = MEMBERSHIP._write_candidate(derived, candidate)
    verify_work = work / "candidate-verify"
    verify_work.mkdir(parents=True, exist_ok=True)
    candidate_verify = MEMBERSHIP._verify_candidate(
        candidate, derived_index, str(dv["tree_sha256"]), verify_work
    )
    parsed = MEMBERSHIP._parse_candidate_bytes(candidate.read_bytes())
    hostile = MEMBERSHIP._hostile_table(derived_index)
    rows["derived_membership"] = {
        **candidate_stats,
        **candidate_verify,
        "archive_bytes": candidate.stat().st_size,
        "physical_payload_unchanged": parsed["data"] == derived_data,
        "hostile_fail_closed": hostile,
        "hostile_all_pass": bool(hostile) and all(hostile.values()),
    }
    return rows


def _one(source: Path, work: Path, name: str) -> dict:
    rows = _build_variants(source, work)
    candidate = rows["derived_membership"]
    cc = rows["derived_c25cc01"]
    independent = rows["independent_r24"]
    derived = rows["derived_r24"]
    return {
        "variants": rows,
        "candidate_saving_vs_derived_c25cc01_bytes": int(cc["archive_bytes"]) - int(candidate["archive_bytes"]),
        "candidate_saving_vs_independent_r24_bytes": int(independent["archive_bytes"]) - int(candidate["archive_bytes"]),
        "derived_saving_vs_independent_r24_bytes": int(independent["archive_bytes"]) - int(derived["archive_bytes"]),
        "candidate_beats_c25cc01": int(candidate["archive_bytes"]) < int(cc["archive_bytes"]),
        "candidate_beats_independent_r24": int(candidate["archive_bytes"]) < int(independent["archive_bytes"]),
        "locality_derived_pass": bool(derived["locality"]["locality_pass"]),
        "candidate_payload_unchanged_from_derived": bool(candidate["physical_payload_unchanged"]),
        "strong_trees_exact": bool(independent["strong_tree_exact"] and derived["strong_tree_exact"] and candidate["strong_tree_exact"]),
        "tail_recovery_pass": bool(candidate["primary_corruption_tail_recovery"]),
        "hostile_pass": bool(candidate["hostile_all_pass"]),
    }


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    corpus = work_root / "corpus"
    ATTR._build_sources(corpus)
    rows = {name: _one(corpus / name, work_root / "work" / name, name) for name in ("01_developer_repository", "08_many_tiny_files")}
    gate = {
        "derived_locality_pass_both": all(r["locality_derived_pass"] for r in rows.values()),
        "candidate_beats_c25cc01_both": all(r["candidate_beats_c25cc01"] for r in rows.values()),
        "candidate_beats_independent_r24_both": all(r["candidate_beats_independent_r24"] for r in rows.values()),
        "candidate_payload_unchanged_both": all(r["candidate_payload_unchanged_from_derived"] for r in rows.values()),
        "strong_trees_exact_both": all(r["strong_trees_exact"] for r in rows.values()),
        "tail_recovery_both": all(r["tail_recovery_pass"] for r in rows.values()),
        "hostile_fail_closed_both": all(r["hostile_pass"] for r in rows.values()),
    }
    verdict = "LOCALITY_DERIVED_MICROPACK_EARNED" if all(gate.values()) else "RETIRE_OR_REDESIGN_LOCALITY_DERIVED_MICROPACK"
    return {
        "schema": "cmpct-v030-r24-locality-derived-micropack-v1",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "locality_budget": LOCALITY_BUDGET,
        "workloads": rows,
        "gate": gate,
        "verdict": verdict,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r24-locality-derived-micropack-work"))
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r24-locality-derived-micropack.json"))
    args = ap.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps({"verdict": result["verdict"], "gate": result["gate"], "workloads": result["workloads"]}, indent=2, default=str), flush=True)


if __name__ == "__main__":
    main()
