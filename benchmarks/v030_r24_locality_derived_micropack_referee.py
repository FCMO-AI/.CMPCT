from __future__ import annotations

"""Locality-derived r24 micro-pack referee.

Mission: docs/V030_R24_LOCALITY_DERIVED_MICROPACK_MISSION_2026-09-12.md
Research-only.  The independent arm shares the exact release scan policy with the
candidate and disables only ``_build_micro_packs``; otherwise the release scan's
container-pack geometry would be changed by the same ``micro_pack_max_file`` knob
and the experiment would not be one-variable.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

from cmpct import builder as BUILDER
from cmpct import codec as R24
from experiments import entropygraph_v030_release_product as PRODUCT
from experiments import entropygraph_v030_r24_compact_control_profile as CC
from benchmarks import v030_compact_pack_control_attribution as ATTR
from benchmarks import v030_r25_membership_complete_artifact_referee as MEMBERSHIP

LOCALITY_BUDGET = 8.0
MAX_DECODE_UNIT = 8 * 1024 * 1024


class NoMicroPackBuilder(BUILDER.Builder):
    """Shared-scan causal control: suppress only micro-pack construction."""

    def _build_micro_packs(self):
        self._no_micro_pack_control = True


class LocalityDerivedBuilder(BUILDER.Builder):
    """Group text blobs only while every member remains within the 8x contract."""

    def _build_micro_packs(self):
        self._locality_derived_groups = []
        max_file = int(self.micro_pack_max_file)
        if max_file <= 0:
            return

        buckets: dict[str, list[tuple[bytes, BUILDER.Candidate]]] = {}
        for h, c in list(self.cands.items()):
            if len(c.raw) > max_file or c.deflates:
                continue
            exts = {hint[1].lower() for hint in c.hints if hint and hint[1]}
            if len(exts) != 1:
                continue
            ext = next(iter(exts))
            if not ext or not BUILDER._is_text_like(c.raw[:4096], ext):
                continue
            buckets.setdefault(ext, []).append((h, c))

        for ext, items in sorted(buckets.items()):
            items.sort(key=lambda hc: (len(hc[1].raw), hc[0]))
            group: list[tuple[bytes, BUILDER.Candidate]] = []
            group_raw = 0

            def flush() -> None:
                nonlocal group, group_raw
                if len(group) >= 2:
                    raw = b"".join(c.raw for _h, c in group)
                    pack_hash = hashlib.sha256(raw).digest()
                    if pack_hash not in self.cands:
                        pack_cand = BUILDER.Candidate(raw, BUILDER.ext_class(ext))
                        pack_cand.hints.add((f".cmpct-locality-pack-{ext or 'none'}", ext))
                        self.cands[pack_hash] = pack_cand
                    off = 0
                    for h, c in group:
                        for fi, _fext in c.hints:
                            self.files[fi][6] = (R24.S_PACK, pack_hash, off, len(c.raw))
                        off += len(c.raw)
                    for h, _c in group:
                        self.cands.pop(h, None)
                    self._locality_derived_groups.append({
                        "ext": ext,
                        "members": len(group),
                        "raw_bytes": len(raw),
                        "min_member_bytes": min(len(c.raw) for _h, c in group),
                        "max_member_bytes": max(len(c.raw) for _h, c in group),
                    })
                group = []
                group_raw = 0

            for item in items:
                size = len(item[1].raw)
                if size <= 0:
                    flush()
                    continue
                if not group:
                    group = [item]
                    group_raw = size
                    continue
                smallest = len(group[0][1].raw)
                if group_raw + size > int(LOCALITY_BUDGET * max(1, smallest)):
                    flush()
                    group = [item]
                    group_raw = size
                else:
                    group.append(item)
                    group_raw += size
            flush()


def _build_with(builder: BUILDER.Builder, out: Path) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    started_cpu = time.process_time(); started_wall = time.perf_counter()
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
    release_max = int(PRODUCT.R24_RELEASE_MICRO_MAX_FILE_BYTES)

    current = work / "current-release-r24.cmpct"
    rows["current_release_r24"] = dict(PRODUCT._locality_bounded_r24_build(source, current))
    current_index, _ = _parse_r24(current)
    rows["current_release_r24"]["locality"] = _pack_locality(current_index)
    rows["current_release_r24"]["strong_tree_exact"] = bool(PRODUCT.strong_verify(current).get("ok"))

    independent = work / "independent-r24.cmpct"
    ib = NoMicroPackBuilder(source, deflate_reuse_min=0, workers=1)
    ib.micro_pack_max_file = release_max
    rows["independent_r24"] = _build_with(ib, independent)
    rows["independent_r24"]["control"] = "shared-release-scan-plus-noop-micropack-v2"
    independent_index, _ = _parse_r24(independent)
    rows["independent_r24"]["locality"] = _pack_locality(independent_index)
    rows["independent_r24"]["strong_tree_exact"] = bool(PRODUCT.strong_verify(independent).get("ok"))

    derived = work / "locality-derived-r24.cmpct"
    db = LocalityDerivedBuilder(source, deflate_reuse_min=0, workers=1)
    db.micro_pack_max_file = release_max
    rows["derived_r24"] = _build_with(db, derived)
    rows["derived_r24"]["control"] = "shared-release-scan-plus-derived-micropack-v2"
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
        "hostile_all_pass": (not hostile) or all(hostile.values()),
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
        "schema": "cmpct-v030-r24-locality-derived-micropack-v2",
        "experiment_valid": True,
        "release_credit": False,
        "canonical_builder_changed": False,
        "control": "shared-release-scan-plus-noop-micropack-v2",
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
