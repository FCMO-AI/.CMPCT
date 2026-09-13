from __future__ import annotations

"""Causal attribution of EG08 low-yield ladder work.

Preregistered by docs/V030_EG08_LOW_YIELD_WORK_ATTRIBUTION_LOCK_2026-09-13.md.
This benchmark changes no archive decision. It reconstructs the frozen EG08 ladder
from EG07 packs, times each rung, and requires exact equality with the actual EG08
physical payload selected for every pack.
"""

import argparse
import binascii
import hashlib
import json
from pathlib import Path
import tempfile
import time

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_current15_stable_corpus as CURRENT
from benchmarks.v030_eg08_neutral10_transfer import fresh_build
from experiments import entropygraph_v030_federated_adaptive_effort_candidate_v8 as EG08
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

EG07_MODULE = "experiments.entropygraph_v030_federated_embedded_fs_candidate_v7"
EG08_MODULE = "experiments.entropygraph_v030_federated_adaptive_effort_candidate_v8"
TARGET_NEUTRAL = "10_large_mixed_binary"
TARGET_HOSTILE = "05_incompressible"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_packs(archive: Path) -> tuple[list[dict], dict]:
    owner = EG07.EG06.EG05
    V25 = owner.V25
    packs: list[dict] = []
    with EG07._engine(archive.resolve()):
        stream, meta, offsets = V25.open_ar()
        try:
            for pi, (offset, codec, usize, csize, crc, expected_sha) in enumerate(offsets):
                stream.seek(offset)
                payload = stream.read(csize)
                if len(payload) != csize:
                    raise RuntimeError(f"truncated pack {pi}")
                raw = V25.zd(payload, usize) if int(codec) == 1 else payload
                if len(raw) != int(usize):
                    raise RuntimeError(f"pack-size mismatch {pi}")
                if (binascii.crc32(raw) & 0xFFFFFFFF) != int(crc):
                    raise RuntimeError(f"pack CRC mismatch {pi}")
                if V25.H(raw) != expected_sha:
                    raise RuntimeError(f"pack SHA mismatch {pi}")
                packs.append({
                    "index": pi,
                    "codec": int(codec),
                    "usize": int(usize),
                    "csize": int(csize),
                    "crc": int(crc),
                    "sha": expected_sha,
                    "raw": raw,
                    "payload": payload,
                })
        finally:
            stream.close()
    return packs, dict(meta)


def _reconstruct(eg07_archive: Path, eg08_archive: Path) -> dict:
    owner = EG07.EG06.EG05
    V25 = owner.V25
    uncapped_zc = V25.zc
    base_packs, meta = _load_packs(eg07_archive)
    actual_packs, meta8 = _load_packs(eg08_archive)
    if len(base_packs) != len(actual_packs):
        raise RuntimeError("EG07/EG08 pack-count drift")
    stream_indices, hot_indices = EG08._stream_roles(meta, len(base_packs))
    stream8, hot8 = EG08._stream_roles(meta8, len(actual_packs))
    if stream_indices != stream8 or hot_indices != hot8:
        raise RuntimeError("EG07/EG08 stream-role drift")

    calls: list[dict] = []
    pack_rows: list[dict] = []
    mismatches: list[dict] = []
    early_stops = 0

    for row, actual in zip(base_packs, actual_packs):
        pi = int(row["index"])
        raw = row["raw"]
        best_codec = int(row["codec"])
        best_payload = row["payload"]
        best_size = len(best_payload)
        best_level: int | None = None
        local_calls: list[dict] = []

        if pi not in hot_indices:
            for level in EG08.EFFORT_LADDER:
                cpu0 = time.process_time_ns(); wall0 = time.perf_counter_ns()
                comp = uncapped_zc(raw, level)
                wall_ns = time.perf_counter_ns() - wall0; cpu_ns = time.process_time_ns() - cpu0
                if len(comp) + 8 < len(raw):
                    candidate_codec = 1; candidate_payload = comp
                else:
                    candidate_codec = 0; candidate_payload = raw
                candidate_size = len(candidate_payload)
                call = {
                    "pack": pi,
                    "level": int(level),
                    "cpu_ns": int(cpu_ns),
                    "wall_ns": int(wall_ns),
                    "candidate_codec": candidate_codec,
                    "candidate_storage_bytes": candidate_size,
                    "candidate_payload_sha256": _sha(candidate_payload),
                    "became_strict_best": False,
                    "tied_best": False,
                    "stopped_after": False,
                }
                if candidate_size <= best_size:
                    if candidate_size < best_size:
                        best_codec = candidate_codec
                        best_payload = candidate_payload
                        best_size = candidate_size
                        best_level = int(level)
                        call["became_strict_best"] = True
                    else:
                        call["tied_best"] = True
                    local_calls.append(call); calls.append(call)
                    continue
                call["stopped_after"] = True
                local_calls.append(call); calls.append(call); early_stops += 1
                break

        same = (
            best_codec == int(actual["codec"])
            and best_size == int(actual["csize"])
            and best_payload == actual["payload"]
        )
        if not same:
            mismatches.append({
                "pack": pi,
                "reconstructed_codec": best_codec,
                "actual_codec": int(actual["codec"]),
                "reconstructed_size": best_size,
                "actual_size": int(actual["csize"]),
                "reconstructed_sha256": _sha(best_payload),
                "actual_sha256": _sha(actual["payload"]),
            })

        # Classify each call after the final selected payload is known. A call is
        # final-selected only if its candidate bytes equal the actual stored bytes
        # and that storage differs from the EG07 incumbent. Everything else is
        # discarded work, split into superseded-best vs never-best for diagnosis.
        changed = int(actual["codec"]) != int(row["codec"]) or actual["payload"] != row["payload"]
        for call in local_calls:
            candidate_is_final = (
                changed
                and int(call["candidate_codec"]) == int(actual["codec"])
                and int(call["candidate_storage_bytes"]) == int(actual["csize"])
                and call["candidate_payload_sha256"] == _sha(actual["payload"])
            )
            if candidate_is_final:
                call["outcome"] = "final_selected"
            elif call["became_strict_best"] or call["tied_best"]:
                call["outcome"] = "superseded"
            else:
                call["outcome"] = "rejected"

        pack_rows.append({
            "pack": pi,
            "raw_bytes": len(raw),
            "hot_stream_root": pi in hot_indices,
            "stream_pack": pi in stream_indices,
            "eg07_codec": int(row["codec"]),
            "eg07_bytes": int(row["csize"]),
            "eg08_codec": int(actual["codec"]),
            "eg08_bytes": int(actual["csize"]),
            "saved_bytes": int(row["csize"]) - int(actual["csize"]),
            "selected_level": best_level,
            "call_count": len(local_calls),
            "exact_payload_identity": same,
        })

    def agg(outcome: str) -> dict:
        xs = [x for x in calls if x.get("outcome") == outcome]
        return {
            "calls": len(xs),
            "cpu_s": sum(int(x["cpu_ns"]) for x in xs) / 1e9,
            "wall_s": sum(int(x["wall_ns"]) for x in xs) / 1e9,
        }

    selected = agg("final_selected")
    superseded = agg("superseded")
    rejected = agg("rejected")
    total_cpu = selected["cpu_s"] + superseded["cpu_s"] + rejected["cpu_s"]
    total_wall = selected["wall_s"] + superseded["wall_s"] + rejected["wall_s"]
    discarded_cpu = superseded["cpu_s"] + rejected["cpu_s"]
    discarded_wall = superseded["wall_s"] + rejected["wall_s"]
    return {
        "pack_count": len(base_packs),
        "stream_pack_count": len(stream_indices),
        "hot_stream_root_pack_count": len(hot_indices),
        "effort_calls": len(calls),
        "early_stops": early_stops,
        "changed_packs": sum(1 for x in pack_rows if x["saved_bytes"] != 0 or x["eg07_codec"] != x["eg08_codec"]),
        "stored_bytes_saved": sum(int(x["saved_bytes"]) for x in pack_rows),
        "mismatches": mismatches,
        "exact_all_pack_payloads": not mismatches,
        "final_selected": selected,
        "superseded": superseded,
        "rejected": rejected,
        "total_measured_cpu_s": total_cpu,
        "total_measured_wall_s": total_wall,
        "discarded_cpu_s": discarded_cpu,
        "discarded_wall_s": discarded_wall,
        "discarded_cpu_share": discarded_cpu / max(total_cpu, 1e-12),
        "discarded_wall_share": discarded_wall / max(total_wall, 1e-12),
        "packs": pack_rows,
    }


def _one(family: str, source: Path, item: dict, work: Path) -> dict:
    a7 = work / "eg07.cmpct"; a8 = work / "eg08.cmpct"
    b7 = fresh_build(EG07_MODULE, source, a7)
    b8 = fresh_build(EG08_MODULE, source, a8)
    attr = _reconstruct(a7, a8)
    l7 = b7["result"]["locality"]; l8 = b8["result"]["locality"]
    geometry = (
        l7["member_count"] == l8["member_count"]
        and l7["max_decode_unit_bytes"] == l8["max_decode_unit_bytes"]
        and l7["max_member_read_amplification"] == l8["max_member_read_amplification"]
    )
    return {
        "family": family,
        "name": item["name"],
        "tree_sha256": item["tree_sha256"],
        "logical_bytes": item["logical_bytes"],
        "files": item["files"],
        "eg07_bytes": b7["archive_bytes"],
        "eg08_bytes": b8["archive_bytes"],
        "actual_saved_bytes": int(b7["archive_bytes"]) - int(b8["archive_bytes"]),
        "build_strong_verify_eg07": bool((b7["result"].get("verified") or {}).get("ok")),
        "build_strong_verify_eg08": bool((b8["result"].get("verified") or {}).get("ok")),
        "geometry_same": geometry,
        "max_amp": l8["max_member_read_amplification"],
        "max_decode_unit_bytes": l8["max_decode_unit_bytes"],
        "attribution": attr,
    }


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, default=Path("eg08-low-yield-work-attribution.json")); args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-low-yield-") as td:
        work = Path(td); neutral = work / "neutral"; hostile = work / "hostile"
        nm = CURRENT.build(neutral); hm = HOSTILE.build(hostile)
        targets = [
            ("neutral", neutral, next(x for x in nm["corpora"] if x["name"] == TARGET_NEUTRAL)),
            ("hostile", hostile, next(x for x in hm["workloads"] if x["name"] == TARGET_HOSTILE)),
        ]
        rows = []
        for family, root, item in targets:
            w = work / f"{family}-{item['name']}"; w.mkdir(); rows.append(_one(family, root / item["name"], item, w))

        valid = all(
            r["build_strong_verify_eg07"]
            and r["build_strong_verify_eg08"]
            and r["geometry_same"]
            and r["attribution"]["exact_all_pack_payloads"]
            and int(r["actual_saved_bytes"]) == int(r["attribution"]["stored_bytes_saved"])
            for r in rows
        )
        if not valid:
            verdict = "EG08_LOW_YIELD_ATTRIBUTION_INVALID"
        else:
            discarded_dominates = [r["attribution"]["discarded_cpu_share"] > 0.5 for r in rows]
            if all(discarded_dominates):
                verdict = "EG08_LOW_YIELD_REJECTED_WORK_DOMINATES"
            elif not any(discarded_dominates):
                verdict = "EG08_LOW_YIELD_SELECTED_WORK_DOMINATES"
            else:
                verdict = "EG08_LOW_YIELD_MIXED_WORK"

        out = {
            "schema": "v030-eg08-low-yield-work-attribution-v1",
            "verdict": verdict,
            "workloads": rows,
            "valid": valid,
            "aggregate_effort_calls": sum(int(r["attribution"]["effort_calls"]) for r in rows),
            "aggregate_final_selected_calls": sum(int(r["attribution"]["final_selected"]["calls"]) for r in rows),
            "aggregate_superseded_calls": sum(int(r["attribution"]["superseded"]["calls"]) for r in rows),
            "aggregate_rejected_calls": sum(int(r["attribution"]["rejected"]["calls"]) for r in rows),
            "aggregate_measured_cpu_s": sum(float(r["attribution"]["total_measured_cpu_s"]) for r in rows),
            "aggregate_discarded_cpu_s": sum(float(r["attribution"]["discarded_cpu_s"]) for r in rows),
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
