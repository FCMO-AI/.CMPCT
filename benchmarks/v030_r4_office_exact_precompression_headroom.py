from __future__ import annotations

"""Falsifiable headroom referee for exact DEFLATE precompression on Office.

Why this exists
---------------
H-DICT8 and H-BMAX falsified the independent-frame family. H-MS3 then showed that
recompressing already-compressed DEFLATE pages has essentially no useful economics, and
H-MS3-LD showed that logical-domain discovery improves candidate quality but still cannot
make that storage representation pay for its directory. The next question is therefore
representation-level: can exact DEFLATE normalization expose enough entropy to matter?

CMPCT already carries a pinned, memory-safe Preflate bridge used by the historical v0.28
research engine. This referee reuses that *existing* mechanism rather than inventing a new
codec. Every accepted transform must reconstruct the original OOXML/ZIP bytes exactly.

Hypothesis H-PFLT-H: across the deterministic Office workload, exact precompression has
material gross byte headroom versus the same v0.28 direct-record baseline. A useful signal
for the current R4 debt is at least the frozen Office deficit after H-BMAX (549,285 B).
This threshold does not admit a product representation; it only answers whether exact
normalization has enough byte magnitude to justify a locality-bounded v0.30 design.

Disproof: exact-precompression gross saving < 549,285 B, any failed byte-exact round-trip,
or transform cost so large that it destroys v0.30's creation-compute advantage. We report
CPU/wall and per-file results rather than hiding either failure mode.

No release/locality credit: whole-container Preflate records do not satisfy the v0.30 <=8x
selective-access contract by themselves. A positive result must next be decomposed into a
bounded physical representation with authenticated recovery and a real selective reader.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

from benchmarks import mosaic_v029_generalization_bench as V029
from experiments import entropygraph_v028 as V028
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-exact-precompression-headroom-v1"
FROZEN_HBMAX_OFFICE_GAP = 549_285


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_pflt_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_pflt_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"

    bridge = V028._bridge_path()
    if bridge is None:
        raise RuntimeError("pinned CMPCT preflate bridge unavailable; fail closed")

    rows = []
    total_input = total_direct = total_preflate = total_saving = 0
    attempts = wins = exact = 0
    cpu0 = time.process_time(); wall0 = time.perf_counter()
    for path in sorted(p for p in source.rglob("*") if p.is_file()):
        raw = path.read_bytes()
        suffix = path.suffix.lower()
        if suffix not in V028.PREFLATE_EXTS or not (4096 <= len(raw) <= V028.MAX_DECODE_UNIT):
            continue
        attempts += 1
        direct = V028._direct_cost(raw)
        t0c = time.process_time(); t0w = time.perf_counter()
        packed = V028._preflate_pack(raw, suffix)
        pcpu = time.process_time() - t0c; pwall = time.perf_counter() - t0w
        if packed is None:
            rows.append({
                "path": path.relative_to(source).as_posix(), "suffix": suffix,
                "input_bytes": len(raw), "direct_record_bytes": direct,
                "preflate_supported": False, "pack_cpu_s": pcpu, "pack_wall_s": pwall,
            })
            continue
        t1c = time.process_time(); t1w = time.perf_counter()
        restored = V028._preflate_unpack(packed, len(raw))
        ucpu = time.process_time() - t1c; uwall = time.perf_counter() - t1w
        if restored != raw:
            raise RuntimeError(f"preflate byte-exact reconstruction mismatch: {path}")
        exact += 1
        # Match v0.28's concrete economic admission accounting: physical header plus its
        # conservative 24-byte allowance versus the direct record physical cost.
        preflate_cost = V028.PH.size + len(packed) + 24
        saving = direct - preflate_cost
        admitted = saving > 0
        if admitted:
            wins += 1
            total_saving += saving
        total_input += len(raw)
        total_direct += direct
        total_preflate += min(direct, preflate_cost)
        rows.append({
            "path": path.relative_to(source).as_posix(), "suffix": suffix,
            "input_bytes": len(raw), "input_sha256": _sha(raw),
            "direct_record_bytes": direct, "preflate_payload_bytes": len(packed),
            "preflate_record_bytes": preflate_cost, "saving_if_selected_bytes": max(0, saving),
            "preflate_selected": admitted, "roundtrip_exact": True,
            "pack_cpu_s": pcpu, "pack_wall_s": pwall,
            "unpack_cpu_s": ucpu, "unpack_wall_s": uwall,
        })
    cpu = time.process_time() - cpu0; wall = time.perf_counter() - wall0

    selected_rows = [r for r in rows if r.get("preflate_selected")]
    gross = sum(r["saving_if_selected_bytes"] for r in selected_rows)
    if gross != total_saving:
        raise RuntimeError("preflate saving accounting mismatch")
    rows.sort(key=lambda r: (-int(r.get("saving_if_selected_bytes", 0)), r["path"]))

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "02_office_workspace",
        "tree_sha256": PRODUCT.treehash(source),
        "bridge": {
            "path_name": bridge.name,
            "cargo_lock_authoritative": True,
            "mechanism": "existing pinned CMPCT preflate bridge",
        },
        "summary": {
            "eligible_attempts": attempts,
            "exact_roundtrips": exact,
            "selected_wins": wins,
            "eligible_input_bytes_with_supported_transform": total_input,
            "direct_record_bytes_for_supported_transform": total_direct,
            "selected_portfolio_record_bytes": total_preflate,
            "gross_selected_saving_bytes": gross,
            "frozen_hbmax_office_gap_bytes": FROZEN_HBMAX_OFFICE_GAP,
            "fraction_of_hbmax_gap": gross / FROZEN_HBMAX_OFFICE_GAP,
            "pack_unpack_cpu_s": cpu,
            "pack_unpack_wall_s": wall,
        },
        "files": rows,
        "hypothesis": {
            "byte_exact_for_every_supported_transform": exact == sum(1 for r in rows if r.get("preflate_supported", True) and "preflate_payload_bytes" in r),
            "gross_headroom_reaches_hbmax_gap": gross >= FROZEN_HBMAX_OFFICE_GAP,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "same_existing_preflate_mechanism": True,
            "exact_reconstruction_required": True,
            "direct_baseline_is_v028_direct_record_cost": True,
            "no_threshold_sweep": True,
            "selector_changed": False,
            "production_format_changed": False,
            "remaining_debt": "bounded physical decomposition; selective reader <=8x; authenticated metadata/recovery; fresh RSS; held-out transfer; native/product integration",
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-pflt-headroom-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-pflt-headroom.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"summary": d["summary"], "hypothesis": d["hypothesis"], "top_files": d["files"][:12]}, indent=2))


if __name__ == "__main__":
    main()
