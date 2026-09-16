from __future__ import annotations

"""Cross-frontier structural-locality admission for Office SFV4 derived views.

Mission Lock / Referee
======================
SFV4's eight exact loose-file views are raw-DEFLATE inflations of streams already owned by the Office
stream pool, but prefix inflation costs up to ~132.6x for a 4 KiB read. The Analytics line now has a
workload-independent structural certificate that rejects DEFLATE streams whose transitive dependency
span can exceed the frozen 8x decoded-work bound without relying on paths, hashes, or compression ratio.

Hypothesis: the same certificate admits the exact SFV4-derived streams, because their compressed JPEG
payloads should have shallow DEFLATE copy dependency even though prefix inflation is expensive. If all
exact derived streams are certified, Office can reuse the sparse authenticated reader mechanism rather
than inventing an Office-only restart format.

Disproof: any exact derived stream is rejected by the frozen structural certificate, any identity round
trip fails, or admission requires path/hash/workload dispatch. A pass is only decoded-dependency evidence:
it does NOT claim <=8x physical I/O, authenticated range proofs, recovery, or product promotion. Those
must be charged in a separate persisted reader gate.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import time
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_exact_stream_federation_v2 as SFV2
from benchmarks import v030_r4_office_sfv3_derived_views as SFV3
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_deflate_structural_locality_admission as ADMIT

SCHEMA = "cmpct-v030-r4-office-derived-structural-admission-v1"


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_derived_admission_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_derived_admission_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"

    containers, _shared = SFV2.discover(source)
    all_streams = SFV4._all_member_streams(containers)
    derived = SFV3._derived_inventory(source, containers, all_streams)
    if not derived:
        raise RuntimeError("no exact Office derived streams")

    rows = []
    total_cpu = 0.0
    total_wall = 0.0
    for rel, rec in sorted(derived.items()):
        stream = all_streams[rec["stream_hash"]]
        raw = (source / rel).read_bytes()
        if zlib.decompress(stream, -15) != raw:
            raise RuntimeError("derived identity mismatch")
        t0 = time.perf_counter()
        proof = ADMIT.prove(stream)
        outer_wall = time.perf_counter() - t0
        total_cpu += float(proof["cpu_s"])
        total_wall += float(proof["wall_s"])
        rows.append({
            "logical_bytes": len(raw),
            "compressed_bytes": len(stream),
            "accepted": bool(proof["accepted"]),
            "worst_enclosing_dependency_span_bytes": int(proof["worst_enclosing_dependency_span_bytes"]),
            "worst_enclosing_span_amplification": float(proof["worst_enclosing_span_amplification"]),
            "decoded_bytes_scanned": int(proof["decoded_bytes_scanned"]),
            "windows_checked": int(proof["windows_checked"]),
            "cpu_s": float(proof["cpu_s"]),
            "wall_s": float(proof["wall_s"]),
            "outer_wall_s": outer_wall,
            "ru_maxrss_delta_kib": int(proof["ru_maxrss_delta_kib"]),
            "max_monotonic_queue_entries": int(proof["max_monotonic_queue_entries"]),
            "full_parent_array_materialized": bool(proof["full_parent_array_materialized"]),
            "decoded_payload_materialized": bool(proof["decoded_payload_materialized"]),
        })

    accepted = sum(r["accepted"] for r in rows)
    supported = accepted == len(rows)
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "derived_stream_count": len(rows),
        "accepted_stream_count": accepted,
        "rejected_stream_count": len(rows) - accepted,
        "logical_bytes": sum(r["logical_bytes"] for r in rows),
        "compressed_bytes": sum(r["compressed_bytes"] for r in rows),
        "max_certificate_span_bytes": max(r["worst_enclosing_dependency_span_bytes"] for r in rows),
        "max_certificate_amplification": max(r["worst_enclosing_span_amplification"] for r in rows),
        "sum_certificate_cpu_s": total_cpu,
        "sum_certificate_wall_s": total_wall,
        "rows": rows,
        "hypothesis": {"all_exact_office_derived_streams_structurally_admitted": supported},
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "same_frozen_8x_certificate": True,
            "path_hash_workload_dispatch": False,
            "compression_ratio_selector": False,
            "physical_io_le_8x_proven": False,
            "authenticated_range_proofs_proven": False,
            "recovery_proven": False,
            "canonical_integration_proven": False,
        },
        "next_if_supported": "reuse the persisted authenticated sparse reader on these exact stream identities and charge stream-pool range mapping, Merkle proofs, recovery parity, framing, and reconstruction work end-to-end",
        "next_if_falsified": "preserve the rejection and keep prefix/fallback semantics; do not weaken 8x or add Office path rules",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-derived-admission-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-derived-admission.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({k: d[k] for k in ("derived_stream_count", "accepted_stream_count", "rejected_stream_count", "logical_bytes", "compressed_bytes", "max_certificate_span_bytes", "max_certificate_amplification", "sum_certificate_cpu_s", "sum_certificate_wall_s", "hypothesis")}, indent=2))


if __name__ == "__main__":
    main()
