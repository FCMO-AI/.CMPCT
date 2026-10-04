from __future__ import annotations

"""Same-geometry compression-effort referee for the Office v0.30 frontier.

Mission lock: docs/V030_OFFICE_SAME_GEOMETRY_EFFORT_MISSION_LOCK_2026-09-13.md

This experiment never changes a physical pack boundary, reconstruction relationship,
stream offset, filesystem-control representation, or locality geometry. It decodes the
current authenticated physical packs once and prices those exact raw units at fixed Zstd
effort levels. Counterfactual bytes are attribution only, not product archives.
"""

import argparse
import binascii
import hashlib
import json
from pathlib import Path
import resource
import tempfile
import time

from benchmarks import v030_current15_stable_corpus as CORPUS
from benchmarks.v030_office_physical_economics_referee import (
    embedded_copy,
    frozen_v029,
    parsed,
    physical_base,
    profile_controls,
    timed,
    verify_controlled,
)
from experiments import entropygraph_v030_federated_embedded_fs_candidate_v5 as EG05

LEVELS = (1, 3, 6, 12, 19)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_exact_packs(archive: Path) -> tuple[dict, list[dict]]:
    """Return authenticated metadata plus exact current payload/raw bytes for each pack."""
    V25 = EG05.V25
    rows: list[dict] = []
    with EG05._engine(archive.resolve()):
        stream, meta, offsets = V25.open_ar()
        try:
            for pi, (offset, codec, usize, csize, crc, expected_sha) in enumerate(offsets):
                stream.seek(offset)
                payload = stream.read(csize)
                if len(payload) != csize:
                    raise RuntimeError(f"truncated pack {pi}")
                raw = V25.zd(payload, usize) if codec == 1 else payload
                if len(raw) != usize:
                    raise RuntimeError(f"pack {pi} size mismatch")
                if (binascii.crc32(raw) & 0xFFFFFFFF) != crc:
                    raise RuntimeError(f"pack {pi} CRC mismatch")
                if V25.H(raw) != expected_sha:
                    raise RuntimeError(f"pack {pi} SHA mismatch")
                rows.append(
                    {
                        "index": pi,
                        "codec": int(codec),
                        "usize": int(usize),
                        "csize": int(csize),
                        "raw_sha256": _sha(raw),
                        "payload_sha256": _sha(payload),
                        "raw": raw,
                        "payload": payload,
                    }
                )
        finally:
            stream.close()
    return dict(meta), rows


def _stream_roles(meta: dict, pack_count: int) -> tuple[set[int], set[int]]:
    stream_packs = [(int(start), int(pi), int(size)) for start, pi, size in meta.get("stream_packs", [])]
    stream_indices = {pi for _start, pi, _size in stream_packs}
    if any(pi < 0 or pi >= pack_count for pi in stream_indices):
        raise RuntimeError("stream pack index outside pack table")

    # In v0.25, streams backing derived loose files are hot roots and stay raw to avoid
    # adding another decompression layer before the inverse inflate. Derive that role from
    # authenticated reconstruction recipes rather than filename/workload identity.
    hot_ranges: list[tuple[int, int]] = []
    for _path, desc in meta.get("files", []):
        if isinstance(desc, list) and desc and desc[0] == "inflate_stream":
            start, size = int(desc[1]), int(desc[2])
            hot_ranges.append((start, start + size))

    hot_indices: set[int] = set()
    for slab_start, pi, slab_size in stream_packs:
        slab_end = slab_start + slab_size
        if any(not (slab_end <= start or slab_start >= end) for start, end in hot_ranges):
            hot_indices.add(pi)
    return stream_indices, hot_indices


def _counterfactual(rows: list[dict], hot: set[int], *, level: int, policy: str) -> dict:
    V25 = EG05.V25
    cpu0 = time.process_time(); wall0 = time.perf_counter()
    total = 0
    changed = 0
    compressed = 0
    saved_payload = 0
    pack_rows = []
    for row in rows:
        pi = int(row["index"]); raw = row["raw"]
        current_csize = int(row["csize"]); current_codec = int(row["codec"])
        if policy == "existing-codec-only" and current_codec == 0:
            codec = 0; payload_size = len(raw); exact_payload = None
        elif policy == "cold-audition" and pi in hot:
            codec = 0; payload_size = len(raw); exact_payload = None
        else:
            comp = V25.zc(raw, level)
            if policy == "existing-codec-only":
                codec = 1
                payload_size = len(comp)
            else:
                codec = 1 if len(comp) + 8 < len(raw) else 0
                payload_size = len(comp) if codec else len(raw)
            exact_payload = comp if codec == 1 else None
        if codec == 1:
            compressed += 1
        if codec != current_codec or payload_size != current_csize:
            changed += 1
        saved_payload += current_csize - payload_size
        total += V25.PH.size + payload_size
        pack_rows.append(
            {
                "index": pi,
                "hot_stream_root": pi in hot,
                "current_codec": current_codec,
                "current_payload_bytes": current_csize,
                "counterfactual_codec": codec,
                "counterfactual_payload_bytes": payload_size,
                "payload_delta_bytes": payload_size - current_csize,
                "counterfactual_payload_sha256": _sha(exact_payload) if exact_payload is not None else None,
            }
        )
    return {
        "policy": policy,
        "level": level,
        "physical_region_bytes": total,
        "payload_bytes_recovered": saved_payload,
        "changed_packs": changed,
        "compressed_packs": compressed,
        "cpu_s": time.process_time() - cpu0,
        "wall_s": time.perf_counter() - wall0,
        "packs": pack_rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v029-checkout", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("office-same-geometry-effort.json"))
    args = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="cmpct-office-effort-") as td:
        work = Path(td)
        corpus = work / "corpus"
        manifest = CORPUS.build(corpus)
        source = corpus / "02_office_workspace"
        office_manifest = next(x for x in manifest["corpora"] if x["name"] == source.name)

        profile = work / "profile"
        v1_raw, _implicit_raw, fs_stats = profile_controls(source, profile)
        base = work / "physical-base.cmpct"
        base_stats, base_cpu, base_wall = timed(lambda: physical_base(profile, base))
        b = work / "B-explicit.cmpct"
        b_frame = embedded_copy(base, b, v1_raw)
        bp = parsed(b)
        b_verify = verify_controlled("B", b, source, v1_raw, implicit=False)

        meta, rows = _load_exact_packs(base)
        stream_indices, hot_indices = _stream_roles(meta, len(rows))
        current_physical = sum(EG05.V25.PH.size + int(r["csize"]) for r in rows)
        if current_physical != int(bp["physical_region_bytes"]):
            raise RuntimeError(
                f"OFFICE_EFFORT_ATTRIBUTION_INVALID: physical accounting {current_physical} != {bp['physical_region_bytes']}"
            )

        # Level 1 on already-compressed units must reproduce the current payload bytes exactly.
        level1 = _counterfactual(rows, hot_indices, level=1, policy="existing-codec-only")
        if int(level1["physical_region_bytes"]) != current_physical:
            raise RuntimeError("OFFICE_EFFORT_ATTRIBUTION_INVALID: level-1 size identity failed")
        for current, cf in zip(rows, level1["packs"], strict=True):
            if int(current["codec"]) == 1:
                if cf["counterfactual_payload_sha256"] != current["payload_sha256"]:
                    raise RuntimeError(
                        f"OFFICE_EFFORT_ATTRIBUTION_INVALID: level-1 bitstream mismatch pack {current['index']}"
                    )

        v029 = frozen_v029(source, work / "v029.cmpct", args.v029_checkout)
        b_bytes = int(bp["archive_bytes"])
        v029_bytes = int(v029["archive_bytes"])
        regret = b_bytes - v029_bytes
        if regret <= 0:
            raise RuntimeError("OFFICE_EFFORT_ATTRIBUTION_INVALID: no positive Office regret")

        results: dict[str, dict[str, dict]] = {}
        for policy in ("existing-codec-only", "cold-audition", "all-audition"):
            by_level: dict[str, dict] = {}
            for level in LEVELS:
                row = _counterfactual(rows, hot_indices, level=level, policy=policy)
                delta_physical = int(row["physical_region_bytes"]) - current_physical
                complete_bytes = b_bytes + delta_physical
                recovered = b_bytes - complete_bytes
                row.update(
                    {
                        "B_equivalent_complete_bytes": complete_bytes,
                        "bytes_recovered_vs_B": recovered,
                        "remaining_regret_vs_v029_bytes": complete_bytes - v029_bytes,
                        "fraction_of_B_regret_recovered": recovered / regret,
                    }
                )
                by_level[str(level)] = row
            results[policy] = by_level

        e19 = int(results["cold-audition"]["19"]["bytes_recovered_vs_B"])
        fraction = e19 / regret
        if fraction >= 0.80:
            verdict = "OFFICE_EFFORT_DOMINATES_PHYSICAL_REGRET"
        elif fraction >= 0.25:
            verdict = "OFFICE_EFFORT_MATERIAL_BUT_NOT_DOMINANT"
        else:
            verdict = "OFFICE_GEOMETRY_RELATIONSHIPS_DOMINATE"

        pack_summary = [
            {
                "index": int(r["index"]),
                "codec": int(r["codec"]),
                "usize": int(r["usize"]),
                "csize": int(r["csize"]),
                "raw_sha256": r["raw_sha256"],
                "payload_sha256": r["payload_sha256"],
                "stream_pack": int(r["index"]) in stream_indices,
                "hot_stream_root": int(r["index"]) in hot_indices,
            }
            for r in rows
        ]

        out = {
            "schema": "v030-office-same-geometry-effort-v1",
            "verdict": verdict,
            "office_tree_sha256": office_manifest["tree_sha256"],
            "logical_bytes": office_manifest["logical_bytes"],
            "files": office_manifest["files"],
            "frozen_v029": v029,
            "current_B": {
                "archive_bytes": b_bytes,
                "physical_region_bytes": current_physical,
                "components": bp,
                "framing": b_frame,
                "verification": b_verify,
                "shared_base_create_cpu_s": base_cpu,
                "shared_base_create_wall_s": base_wall,
                "build_stats": base_stats,
            },
            "B_regret_vs_v029_bytes": regret,
            "pack_count": len(rows),
            "stream_pack_count": len(stream_indices),
            "hot_stream_root_pack_count": len(hot_indices),
            "max_raw_decode_unit_bytes": max((int(r["usize"]) for r in rows), default=0),
            "pack_identity": pack_summary,
            "counterfactuals": results,
            "level19_cold_audition_recovery_fraction": fraction,
            "level19_cold_audition_bytes_recovered": e19,
            "filesystem_stats": fs_stats,
            "process_peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
            "counterfactuals_are_product_archives": False,
        }
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
