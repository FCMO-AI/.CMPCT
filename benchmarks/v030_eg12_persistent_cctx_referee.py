from __future__ import annotations

"""Exact-frame/archive referee for EG12 persistent libzstd CCtx reuse."""

import argparse
import binascii
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_current15_stable_corpus as CURRENT
from benchmarks.v030_eg08_neutral10_transfer import fresh_build
from experiments import entropygraph_v030_federated_persistent_cctx_candidate_v12 as EG12

EG11_MODULE = "experiments.entropygraph_v030_federated_raw_incumbent_fusion_candidate_v11"
EG12_MODULE = "experiments.entropygraph_v030_federated_persistent_cctx_candidate_v12"
NEUTRAL = {"02_office_workspace", "04_analytics_and_database", "05_logs_and_telemetry", "09_ml_artifacts", "10_large_mixed_binary"}
HOSTILE_NAMES = {"01_shifted_versions", "02_false_neighbors", "03_boundary_churn", "05_incompressible"}
LEVELS = (1, 3, 6, 12, 19)
REL = 0.05
ABS_S = 0.003
MATERIAL_REL = 0.03
MATERIAL_ABS_S = 0.5
FRAME_SAMPLE_LIMIT = 16


def H(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def confirmed_reg(base: float, cand: float) -> bool:
    return cand > base * (1.0 + REL) and cand > base + ABS_S


def tail_recovery(archive: Path, source: Path, work: Path) -> bool:
    bad = work / (archive.stem + "-primary-corrupt.cmpct")
    shutil.copyfile(archive, bad)
    raw = bytearray(bad.read_bytes())
    raw[EG12.V25.HDR.size] ^= 1
    bad.write_bytes(raw)
    try:
        return bool(EG12.strong_verify(bad, expected_tree=EG12._treehash(source))["ok"])
    finally:
        bad.unlink(missing_ok=True)


def frame_equivalence(archive: Path) -> dict:
    """Compare both libzstd entry points on deterministic real physical units.

    Complete-archive identity proves selected product bytes. This independent probe also
    checks losing/intermediate level frames so a persistent context cannot hide a changed
    ladder behind the same final winner.
    """
    V25 = EG12.V25
    rows = []
    with EG12.EG11.EG07._engine(archive.resolve()):
        stream, _meta, offsets = V25.open_ar()
        try:
            selected = list(enumerate(offsets))[:FRAME_SAMPLE_LIMIT]
            compressor = EG12._PersistentCompressor()
            try:
                for pi, (offset, codec, usize, csize, crc, expected_sha) in selected:
                    stream.seek(offset)
                    payload = stream.read(csize)
                    raw = V25.zd(payload, usize) if int(codec) == 1 else payload
                    if len(raw) != int(usize) or (binascii.crc32(raw) & 0xFFFFFFFF) != int(crc) or V25.H(raw) != expected_sha:
                        raise RuntimeError(f"EG12 frame probe pack integrity mismatch {pi}")
                    for level in LEVELS:
                        inherited = V25.zc(raw, level)
                        reused = compressor.compress(raw, level)
                        rows.append(
                            {
                                "pack": int(pi),
                                "level": int(level),
                                "raw_bytes": len(raw),
                                "inherited_bytes": len(inherited),
                                "persistent_bytes": len(reused),
                                "exact": inherited == reused,
                            }
                        )
            finally:
                compressor.close()
        finally:
            stream.close()
    mismatches = [r for r in rows if not r["exact"]]
    return {
        "checks": len(rows),
        "packs": len({r["pack"] for r in rows}),
        "levels": list(LEVELS),
        "mismatches": mismatches[:16],
        "all_exact": not mismatches,
    }


def one(family: str, source: Path, item: dict, work: Path) -> dict:
    a11 = work / "eg11.cmpct"
    a12 = work / "eg12.cmpct"
    b11 = fresh_build(EG11_MODULE, source, a11)
    b12 = fresh_build(EG12_MODULE, source, a12)
    l11 = b11["result"]["locality"]
    l12 = b12["result"]["locality"]
    geometry = (
        l11["member_count"] == l12["member_count"]
        and l11["max_decode_unit_bytes"] == l12["max_decode_unit_bytes"]
        and l11["max_member_read_amplification"] == l12["max_member_read_amplification"]
    )
    frames = frame_equivalence(a11)
    stats = b12["result"].get("persistent_cctx", {})
    return {
        "family": family,
        "name": item["name"],
        "tree_sha256": item["tree_sha256"],
        "logical_bytes": item["logical_bytes"],
        "files": item["files"],
        "eg11_bytes": b11["archive_bytes"],
        "eg12_bytes": b12["archive_bytes"],
        "byte_delta": int(b12["archive_bytes"]) - int(b11["archive_bytes"]),
        "eg11_sha256": H(a11),
        "eg12_sha256": H(a12),
        "complete_archive_identity": a11.read_bytes() == a12.read_bytes(),
        "frame_equivalence": frames,
        "eg11_cpu_s": b11["create_cpu_s"],
        "eg12_cpu_s": b12["create_cpu_s"],
        "cpu_ratio": float(b12["create_cpu_s"]) / max(float(b11["create_cpu_s"]), 1e-12),
        "eg11_wall_s": b11["create_wall_s"],
        "eg12_wall_s": b12["create_wall_s"],
        "wall_ratio": float(b12["create_wall_s"]) / max(float(b11["create_wall_s"]), 1e-12),
        "eg11_peak_rss_kib": b11["peak_rss_kib"],
        "eg12_peak_rss_kib": b12["peak_rss_kib"],
        "rss_delta_kib": int(b12["peak_rss_kib"]) - int(b11["peak_rss_kib"]),
        "eg11_strong_verify": bool((b11["result"].get("verified") or {}).get("ok")),
        "eg12_strong_verify": bool((b12["result"].get("verified") or {}).get("ok")),
        "geometry_same": geometry,
        "tail_recovery": tail_recovery(a12, source, work),
        "confirmed_cpu_regression": confirmed_reg(float(b11["create_cpu_s"]), float(b12["create_cpu_s"])),
        "confirmed_wall_regression": confirmed_reg(float(b11["create_wall_s"]), float(b12["create_wall_s"])),
        "compress_calls": int(stats.get("compress_calls") or 0),
        "compress_input_bytes": int(stats.get("compress_input_bytes") or 0),
        "compress_output_bytes": int(stats.get("compress_output_bytes") or 0),
        "max_amp": l12["max_member_read_amplification"],
        "max_decode_unit_bytes": l12["max_decode_unit_bytes"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("eg12-persistent-cctx.json"))
    args = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="cmpct-eg12-cctx-") as td:
        work = Path(td)
        neutral = work / "neutral"
        hostile = work / "hostile"
        nm = CURRENT.build(neutral)
        hm = HOSTILE.build(hostile)
        surfaces = [
            *(("neutral", neutral, x) for x in nm["corpora"] if x["name"] in NEUTRAL),
            *(("hostile", hostile, x) for x in hm["workloads"] if x["name"] in HOSTILE_NAMES),
        ]
        expected = {f"neutral:{x}" for x in NEUTRAL} | {f"hostile:{x}" for x in HOSTILE_NAMES}
        actual = {f"{f}:{x['name']}" for f, _r, x in surfaces}
        if actual != expected:
            raise RuntimeError(f"surface drift expected={sorted(expected)} actual={sorted(actual)}")

        rows = []
        for family, root, item in surfaces:
            w = work / f"{family}-{item['name']}"
            w.mkdir()
            rows.append(one(family, root / item["name"], item, w))

        c11 = sum(float(r["eg11_cpu_s"]) for r in rows)
        c12 = sum(float(r["eg12_cpu_s"]) for r in rows)
        w11 = sum(float(r["eg11_wall_s"]) for r in rows)
        w12 = sum(float(r["eg12_wall_s"]) for r in rows)
        cpu_saved = c11 - c12
        cpu_ratio = c12 / max(c11, 1e-12)
        wall_ratio = w12 / max(w11, 1e-12)
        material = cpu_saved >= MATERIAL_ABS_S or cpu_ratio <= (1.0 - MATERIAL_REL)
        identity_mismatches = [r["name"] for r in rows if not r["complete_archive_identity"] or r["byte_delta"] != 0]
        frame_mismatches = [r["name"] for r in rows if not r["frame_equivalence"]["all_exact"]]
        conditions = {
            "nine_workloads": len(rows) == 9,
            "all_complete_archive_identity": not identity_mismatches,
            "all_zero_byte_delta": all(r["byte_delta"] == 0 for r in rows),
            "all_direct_frames_exact": not frame_mismatches,
            "all_strong_verify": all(r["eg11_strong_verify"] and r["eg12_strong_verify"] for r in rows),
            "all_tail_recovery": all(r["tail_recovery"] for r in rows),
            "all_geometry_same": all(r["geometry_same"] for r in rows),
            "no_confirmed_cpu_regression": not any(r["confirmed_cpu_regression"] for r in rows),
            "no_confirmed_wall_regression": not any(r["confirmed_wall_regression"] for r in rows),
            "no_positive_rss_delta": max((r["rss_delta_kib"] for r in rows), default=0) <= 0,
            "material_cpu_gain": material,
        }
        exact = all(conditions[k] for k in (
            "nine_workloads", "all_complete_archive_identity", "all_zero_byte_delta", "all_direct_frames_exact",
            "all_strong_verify", "all_tail_recovery", "all_geometry_same"
        ))
        if not exact:
            verdict = "EG12_PERSISTENT_CCTX_INVALID"
        elif all(conditions.values()):
            verdict = "EG12_PERSISTENT_CCTX_PASSES"
        else:
            verdict = "EG12_PERSISTENT_CCTX_EXACT_BUT_NOT_PROMOTABLE"

        receipt = {
            "schema": "cmpct-v030-eg12-persistent-cctx-v1",
            "verdict": verdict,
            "conditions": conditions,
            "aggregate_eg11_cpu_s": c11,
            "aggregate_eg12_cpu_s": c12,
            "aggregate_cpu_saved_s": cpu_saved,
            "aggregate_cpu_ratio": cpu_ratio,
            "aggregate_eg11_wall_s": w11,
            "aggregate_eg12_wall_s": w12,
            "aggregate_wall_ratio": wall_ratio,
            "aggregate_byte_delta": sum(int(r["byte_delta"]) for r in rows),
            "identity_mismatches": identity_mismatches,
            "frame_mismatch_workloads": frame_mismatches,
            "direct_frame_checks": sum(int(r["frame_equivalence"]["checks"]) for r in rows),
            "aggregate_compress_calls": sum(int(r["compress_calls"]) for r in rows),
            "max_positive_rss_delta_kib": max((r["rss_delta_kib"] for r in rows), default=0),
            "rows": rows,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
        print(json.dumps(receipt, sort_keys=True))
        if verdict == "EG12_PERSISTENT_CCTX_INVALID":
            raise SystemExit(2)


if __name__ == "__main__":
    main()
