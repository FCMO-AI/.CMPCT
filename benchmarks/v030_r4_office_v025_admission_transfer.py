from __future__ import annotations

"""Transfer the mature v0.25 Office container-admission economics into SFV4.

Mission Lock
------------
The source-sealed v0.25 stream-policy attribution showed that the 84 stream roots common
with SFV4 are not compressed more efficiently by v0.25: 3,791,492 logical stream bytes
cost 3,792,128 physical bytes. The structural difference is admission: SFV4 materializes
94 roots / 5,658,164 B, while v0.25 admits five of six candidate containers and materializes
84 roots / 3,791,492 B.

Falsifiable hypothesis
----------------------
Port only v0.25's already-mature, content-derived container admission law into the exact
SFV4 representation. Keep the non-admitted container in the ordinary v0.30 base artifact;
do not drop its bytes or waive its storage. If over-admission is causal, the fully charged
candidate must be smaller than same-input SFV4 while preserving the exact source tree and
all exact decoded loose-file views that SFV4 supplied.

Disproof
--------
Any tree mismatch, derived-view loss, no complete-byte improvement versus SFV4, workload/
path/hash dispatch, threshold change, or hidden removal of a rejected container falsifies
the transfer. This referee grants no locality or release credit; a density win must later
pass held-out transfer and real physical read/auth/recovery gates.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import time

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_exact_stream_federation_v2 as SFV2
from benchmarks import v030_r4_office_sfv3_derived_views as SFV3
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_office_v025_stream_policy_attribution as ATTR
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-v025-admission-transfer-v1"
ACCEPTED_V029_OFFICE = SFV2.ACCEPTED_V029_OFFICE
REQUEST = SFV2.REQUEST
MAX_SELECTIVE_AMP = 8.0


def _admission(root: Path, discovered: dict) -> tuple[dict, dict]:
    files = sorted(p for p in root.rglob("*") if p.is_file())
    raws = {p: p.read_bytes() for p in files}
    zp, stream_containers, member_plain = ATTR.probe(files, raws)

    top: dict[bytes, list[Path]] = {}
    for p in files:
        top.setdefault(ATTR.H(raws[p]), []).append(p)

    admitted: dict = {}
    rows: dict[str, dict] = {}
    for p, z in sorted(zp.items(), key=lambda kv: kv[0].as_posix()):
        shared = sum(
            len(body)
            for hh, body in z["local"].items()
            if len(stream_containers.get(hh, ())) > 1
        )
        seen_plain: set[bytes] = set()
        external = 0
        for ph, _hh, _method, _usize, csize in z["members"]:
            if ph in seen_plain:
                continue
            seen_plain.add(ph)
            if any(tp != p for tp in top.get(ph, ())):
                external += csize
        local_dup = int(z["local_dup"])
        accept = bool(local_dup >= ATTR.LOCAL or shared >= ATTR.MIN or external >= ATTR.MIN)
        rel = p.relative_to(root).as_posix()
        rows[rel] = {
            "local_duplicate_bytes": local_dup,
            "shared_stream_bytes": int(shared),
            "external_exact_view_stream_bytes": int(external),
            "admitted": accept,
        }
        if accept:
            if p not in discovered:
                raise RuntimeError(f"v0.25 admission found container outside SFV4 discovery: {rel}")
            admitted[p] = discovered[p]

    if set(zp) != set(discovered):
        missing = sorted(p.relative_to(root).as_posix() for p in set(discovered) - set(zp))
        extra = sorted(p.relative_to(root).as_posix() for p in set(zp) - set(discovered))
        raise RuntimeError(f"container discovery mismatch missing={missing} extra={extra}")
    return admitted, rows


def _build_candidate(root: Path, out: Path, work: Path) -> dict:
    containers, _shared = SFV2.discover(root)
    admitted, admission_rows = _admission(root, containers)
    if not admitted or len(admitted) == len(containers):
        raise RuntimeError("admission transfer did not exercise both admitted and rejected containers")

    streams = SFV4._all_member_streams(admitted)
    derived = SFV3._derived_inventory(root, admitted, streams)
    if not derived:
        raise RuntimeError("admission transfer produced no exact decoded loose-file views")

    stripped = work / "stripped"
    shutil.copytree(root, stripped)
    container_meta = {}
    for p in admitted:
        rel = p.relative_to(root).as_posix()
        container_meta[rel] = SFV2.statrec(p)
        (stripped / rel).unlink()
    for rel in derived:
        (stripped / rel).unlink()

    base = work / "base.cmpct"
    PRODUCT.build(stripped, base)
    literal, stream_pool, sidx, templates_abs = SFV4._build_all_member_layout(admitted, streams)
    templates = {p.relative_to(root).as_posix(): t for p, t in templates_abs.items()}
    manifest = {
        "schema": "cmpct-v030-r4-office-v025-admission-transfer-bundle-v1",
        "templates": templates,
        "stream_index": sidx,
        "container_metadata": container_meta,
        "derived": derived,
    }

    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(base, out / "base.cmpct")
    (out / "literal.bin").write_bytes(literal)
    (out / "streams.bin").write_bytes(stream_pool)
    mraw = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    (out / "manifest.json").write_bytes(mraw)
    pieces = [(out / "base.cmpct").read_bytes(), literal, stream_pool, mraw]
    (out / "auth.bin").write_bytes(
        SFV4.MAGIC + b"".join(hashlib.sha256(x).digest() for x in pieces)
    )
    sizes = {p.name: p.stat().st_size for p in out.iterdir() if p.is_file()}

    req = []
    for rel, t in templates.items():
        n = min(REQUEST, t["size"])
        for start in sorted({0, max(0, t["size"] // 2 - n // 2), max(0, t["size"] - n)}):
            touch = SFV2.pool_touch_for_range(t, start, n)
            req.append(
                {
                    "path": rel,
                    "start": start,
                    "length": n,
                    "pool_payload_bytes_touched": touch,
                    "pool_touch_amplification": touch / max(1, n),
                }
            )

    rejected = sorted(set(containers) - set(admitted), key=lambda p: p.as_posix())
    rejected_bytes = sum(p.stat().st_size for p in rejected)
    return {
        "stored_bytes": sum(sizes.values()),
        "component_bytes": sizes,
        "candidate_containers": len(containers),
        "admitted_containers": len(admitted),
        "rejected_containers": len(rejected),
        "rejected_source_bytes_retained_in_base_input": rejected_bytes,
        "admission_rows": admission_rows,
        "stream_roots": len(streams),
        "stream_raw_bytes": len(stream_pool),
        "derived_inventory": derived,
        "derived_file_count": len(derived),
        "derived_logical_bytes": sum(x["logical_bytes"] for x in derived.values()),
        "max_ideal_container_pool_touch_amplification": max(
            (r["pool_touch_amplification"] for r in req), default=0.0
        ),
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(
        V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "r4_v025admit_neutral",
    )
    repair = V029._load(V029.REPAIR_PATH, "r4_v025admit_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    expected = PRODUCT.treehash(source)

    sfv4_dir = work / "sfv4"
    t0w = time.perf_counter()
    t0c = time.process_time()
    sfv4 = SFV4.build_candidate(source, sfv4_dir, work / "sfv4-work")
    sfv4_cpu = time.process_time() - t0c
    sfv4_wall = time.perf_counter() - t0w

    cand_dir = work / "candidate"
    t0w = time.perf_counter()
    t0c = time.process_time()
    cand = _build_candidate(source, cand_dir, work / "candidate-work")
    candidate_cpu = time.process_time() - t0c
    candidate_wall = time.perf_counter() - t0w

    verify = SFV4.extract_candidate(cand_dir, work / "extract")
    if verify["tree_sha256"] != expected:
        raise RuntimeError("admission-transfer exact tree mismatch")

    admitted_streams = (cand_dir / "streams.bin").read_bytes()
    derived_reads = SFV3._selective_derived_reads(
        cand["derived_inventory"],
        {
            h: admitted_streams[s["o"] : s["o"] + s["n"]]
            for h, s in json.loads((cand_dir / "manifest.json").read_text())["stream_index"].items()
        },
        source,
    )
    max_dphys = max(
        (x["physical_amplification_without_auth_index"] for x in derived_reads), default=0.0
    )
    max_drecon = max((x["reconstruction_amplification"] for x in derived_reads), default=0.0)

    sfv4_derived = len(sfv4["derived_inventory"])
    exact_views_preserved = cand["derived_file_count"] == sfv4_derived
    smaller_than_sfv4 = cand["stored_bytes"] < int(sfv4["stored_bytes"])
    beats_v029 = cand["stored_bytes"] < ACCEPTED_V029_OFFICE

    clean = {k: v for k, v in cand.items() if k != "derived_inventory"}
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "02_office_workspace",
        "tree_sha256": expected,
        "sfv4": {
            "stored_bytes": int(sfv4["stored_bytes"]),
            "stream_roots": int(sfv4["all_member_unique_stream_count"]),
            "stream_raw_bytes": int(sfv4["all_member_stream_bytes"]),
            "derived_files": sfv4_derived,
            "create_cpu_s": sfv4_cpu,
            "create_wall_s": sfv4_wall,
        },
        "candidate": clean,
        "accepted_v029_office_bytes": ACCEPTED_V029_OFFICE,
        "saving_vs_sfv4_bytes": int(sfv4["stored_bytes"]) - cand["stored_bytes"],
        "margin_vs_v029_bytes": ACCEPTED_V029_OFFICE - cand["stored_bytes"],
        "candidate_create_cpu_s": candidate_cpu,
        "candidate_create_wall_s": candidate_wall,
        "hosted_process_peak_rss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        "verify": verify,
        "max_derived_physical_amplification_without_auth_index": max_dphys,
        "max_derived_reconstruction_amplification": max_drecon,
        "hypothesis": {
            "exact_tree": verify["tree_sha256"] == expected,
            "mixed_admission_exercised": 0 < cand["admitted_containers"] < cand["candidate_containers"],
            "rejected_source_bytes_retained": cand["rejected_source_bytes_retained_in_base_input"] > 0,
            "all_sfv4_derived_views_preserved": exact_views_preserved,
            "mature_admission_reduces_complete_bytes": smaller_than_sfv4,
            "mature_admission_beats_v029_office_floor": beats_v029,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "same_sfv4_exact_representation_for_admitted_containers": True,
            "rejected_containers_remain_in_ordinary_base_artifact": True,
            "v025_thresholds_inherited_without_sweep": {
                "local_duplicate_bytes": ATTR.LOCAL,
                "shared_stream_bytes": ATTR.MIN,
                "external_exact_view_stream_bytes": ATTR.MIN,
            },
            "no_workload_name_path_hash_dispatch": True,
            "production_format_changed": False,
            "production_selector_changed": False,
            "derived_physical_metric_excludes_future_auth_index": True,
            "hosted_process_rss_is_diagnostic_not_fresh_process_attribution": True,
        },
        "next_if_supported": (
            "run generator-distinct/held-out container-admission transfer before product selection; then charge "
            "serialized auth/index, physical pread, recovery, RSS and native parity"
        ),
        "next_if_falsified": (
            "preserve the negative; reject v0.25 admission as the causal fix and attribute the non-admitted "
            "container's ordinary-base representation versus SFV4 stream materialization"
        ),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--work-root",
        type=Path,
        default=Path("benchmark-artifacts/v030-r4-office-v025-admission-transfer-work"),
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path("benchmark-artifacts/v030-r4-office-v025-admission-transfer.json"),
    )
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(
        json.dumps(
            {
                "sfv4": d["sfv4"],
                "candidate": {k: v for k, v in d["candidate"].items() if k != "admission_rows"},
                "accepted_v029_office_bytes": d["accepted_v029_office_bytes"],
                "saving_vs_sfv4_bytes": d["saving_vs_sfv4_bytes"],
                "margin_vs_v029_bytes": d["margin_vs_v029_bytes"],
                "candidate_create_cpu_s": d["candidate_create_cpu_s"],
                "candidate_create_wall_s": d["candidate_create_wall_s"],
                "hosted_process_peak_rss_kib": d["hosted_process_peak_rss_kib"],
                "max_derived_physical_amplification_without_auth_index": d[
                    "max_derived_physical_amplification_without_auth_index"
                ],
                "max_derived_reconstruction_amplification": d[
                    "max_derived_reconstruction_amplification"
                ],
                "hypothesis": d["hypothesis"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
