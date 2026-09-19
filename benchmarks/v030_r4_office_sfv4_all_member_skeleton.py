from __future__ import annotations

"""Office R4 SFV4: exact all-member stream skeleton plus exact derived loose-file views.

Mission lock
------------
SFV3 proved that eight loose files are exact decoded views of streams already owned by accepted Office
containers, shrinking the candidate to 6,493,795 B, only 539,769 B above the frozen v0.29 Office floor.
Physical attribution of the frozen v0.25 winner shows the remaining structural difference: once a ZIP-
like container is admitted, v0.25 removes *all* member bodies from its ZIP skeleton, while SFV2/SFV3
remove only member bodies whose compressed bytes repeat. Consequently SFV3 still carries 1,942,348 B
in literal.bin even though the historical ZIP-skeleton role is only a few KiB.

Falsifiable hypothesis
----------------------
Keep exactly the same container discovery surface as SFV2. Once those containers are admitted, extract
every exact member body into one content-addressed pool, deduplicate only by exact SHA-256 identity, and
leave only byte-exact ZIP framing in the literal skeleton. Preserve SFV3's exact decoded loose-file views.
If literal member bodies are the final dominant Office deficit, the complete authenticated research
candidate must strictly beat the frozen v0.29 Office floor of 5,954,026 B.

Disproof
--------
If the fully charged candidate does not beat that floor, preserve the negative and attribute the residual
before adding resemblance search or changing admission. No workload names, path rules, hash allowlists,
recompression, threshold sweep, or historical recipe table participates in selection.

Selective access is not waived. Container range locality is reported as the ideal segment payload touched
by the exact range map; derived loose-file locality retains SFV3's actual prefix-inflate reconstruction
measurement. These are research diagnostics, not physical-I/O promotion evidence.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_exact_stream_federation_v2 as SFV2
from benchmarks import v030_r4_office_sfv3_derived_views as SFV3
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-sfv4-all-member-skeleton-v1"
ACCEPTED_V029_OFFICE = SFV2.ACCEPTED_V029_OFFICE
REQUEST = SFV2.REQUEST
MAX_SELECTIVE_AMP = 8.0
MAGIC = b"R4OSF4\0"


def _all_member_streams(containers: dict) -> dict[str, bytes]:
    streams: dict[str, bytes] = {}
    for _p, rec in containers.items():
        blob = rec["blob"]
        for m in rec["members"]:
            body = blob[m["start"]:m["end"]]
            prior = streams.get(m["hash"])
            if prior is not None and prior != body:
                raise RuntimeError("SHA-256 collision in exact member pool")
            streams[m["hash"]] = body
    return streams


def _build_all_member_layout(containers: dict, streams: dict[str, bytes]):
    literal = bytearray()
    templates = {}
    for p, rec in containers.items():
        blob = rec["blob"]
        pos = 0
        segs = []
        for m in sorted(rec["members"], key=lambda x: x["start"]):
            if m["start"] < pos:
                raise RuntimeError("overlapping ZIP member bodies")
            if m["start"] > pos:
                off = len(literal)
                literal.extend(blob[pos:m["start"]])
                segs.append({"k": "l", "o": off, "n": m["start"] - pos})
            segs.append({"k": "s", "h": m["hash"], "n": m["end"] - m["start"]})
            pos = m["end"]
        if pos < len(blob):
            off = len(literal)
            literal.extend(blob[pos:])
            segs.append({"k": "l", "o": off, "n": len(blob) - pos})
        templates[p] = {"size": len(blob), "segments": segs}

    pool = bytearray()
    sidx = {}
    for h, body in sorted(streams.items()):
        sidx[h] = {"o": len(pool), "n": len(body)}
        pool.extend(body)
    return bytes(literal), bytes(pool), sidx, templates


def build_candidate(root: Path, out: Path, work: Path) -> dict:
    containers, shared = SFV2.discover(root)
    if not shared:
        raise RuntimeError("same SFV2 admission surface found no shared streams")
    all_streams = _all_member_streams(containers)
    derived = SFV3._derived_inventory(root, containers, all_streams)
    if not derived:
        raise RuntimeError("no exact decoded loose-file views")

    stripped = work / "stripped"
    shutil.copytree(root, stripped)
    container_meta = {}
    for p in containers:
        rel = p.relative_to(root).as_posix()
        container_meta[rel] = SFV2.statrec(p)
        (stripped / rel).unlink()
    for rel in derived:
        (stripped / rel).unlink()

    base = work / "base.cmpct"
    PRODUCT.build(stripped, base)
    literal, streams, sidx, templates_abs = _build_all_member_layout(containers, all_streams)
    templates = {p.relative_to(root).as_posix(): t for p, t in templates_abs.items()}
    manifest = {
        "schema": "cmpct-v030-r4-office-stream-federation-v4-all-member-bundle",
        "templates": templates,
        "stream_index": sidx,
        "container_metadata": container_meta,
        "derived": derived,
    }

    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(base, out / "base.cmpct")
    (out / "literal.bin").write_bytes(literal)
    (out / "streams.bin").write_bytes(streams)
    mraw = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    (out / "manifest.json").write_bytes(mraw)
    pieces = [(out / "base.cmpct").read_bytes(), literal, streams, mraw]
    (out / "auth.bin").write_bytes(MAGIC + b"".join(hashlib.sha256(x).digest() for x in pieces))
    sizes = {p.name: p.stat().st_size for p in out.iterdir() if p.is_file()}

    req = []
    for rel, t in templates.items():
        n = min(REQUEST, t["size"])
        for start in sorted({0, max(0, t["size"] // 2 - n // 2), max(0, t["size"] - n)}):
            touch = SFV2.pool_touch_for_range(t, start, n)
            req.append({
                "path": rel,
                "start": start,
                "length": n,
                "pool_payload_bytes_touched": touch,
                "pool_touch_amplification": touch / max(1, n),
            })

    return {
        "stored_bytes": sum(sizes.values()),
        "component_bytes": sizes,
        "shared_stream_count": len(shared),
        "all_member_unique_stream_count": len(all_streams),
        "all_member_stream_bytes": len(streams),
        "additional_unique_stream_bytes_vs_sfv2_shared": len(streams) - sum(len(x) for x in shared.values()),
        "literal_skeleton_bytes": len(literal),
        "derived_file_count": len(derived),
        "derived_logical_bytes": sum(x["logical_bytes"] for x in derived.values()),
        "derived_inventory": derived,
        "all_streams": all_streams,
        "container_selective_requests": req,
        "max_ideal_container_pool_touch_amplification": max((r["pool_touch_amplification"] for r in req), default=0.0),
    }


def extract_candidate(bundle: Path, out: Path) -> dict:
    mraw = (bundle / "manifest.json").read_bytes()
    m = json.loads(mraw)
    literal = (bundle / "literal.bin").read_bytes()
    streams = (bundle / "streams.bin").read_bytes()
    base = (bundle / "base.cmpct").read_bytes()
    pieces = [base, literal, streams, mraw]
    if (bundle / "auth.bin").read_bytes() != MAGIC + b"".join(hashlib.sha256(x).digest() for x in pieces):
        raise RuntimeError("auth mismatch")
    PRODUCT.extract(bundle / "base.cmpct", out)
    for rel, t in m["templates"].items():
        b = SFV2.reconstruct(t, literal, streams, m["stream_index"])
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b)
        md = m["container_metadata"][rel]
        os.chmod(p, int(md["mode"]))
        os.utime(p, ns=(int(md["mtime_ns"]), int(md["mtime_ns"])))
    for rel, drec in m["derived"].items():
        s = m["stream_index"][drec["stream_hash"]]
        stream = streams[s["o"]:s["o"] + s["n"]]
        raw = SFV3._inflate_raw(stream)
        if raw is None or len(raw) != int(drec["logical_bytes"]):
            raise RuntimeError(f"derived inflation failed: {rel}")
        p = out / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)
        md = drec["metadata"]
        os.chmod(p, int(md["mode"]))
        os.utime(p, ns=(int(md["mtime_ns"]), int(md["mtime_ns"])))
    return {
        "tree_sha256": PRODUCT.treehash(out),
        "base_strong_verify": dict(PRODUCT.strong_verify(bundle / "base.cmpct")),
    }


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_sfv4_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_sfv4_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    expected = PRODUCT.treehash(source)

    baseline = work / "baseline.cmpct"
    t0 = time.perf_counter()
    PRODUCT.build(source, baseline)
    baseline_wall = time.perf_counter() - t0

    cand = work / "candidate"
    t0 = time.perf_counter()
    cs = build_candidate(source, cand, work / "cand-work")
    candidate_wall = time.perf_counter() - t0
    verify = extract_candidate(cand, work / "extract")
    if verify["tree_sha256"] != expected:
        raise RuntimeError("SFV4 exact tree mismatch")

    derived_reads = SFV3._selective_derived_reads(cs["derived_inventory"], cs["all_streams"], source)
    max_dphys = max((x["physical_amplification_without_auth_index"] for x in derived_reads), default=0.0)
    max_drecon = max((x["reconstruction_amplification"] for x in derived_reads), default=0.0)
    density_supported = cs["stored_bytes"] < ACCEPTED_V029_OFFICE
    locality_diagnostic = (
        cs["max_ideal_container_pool_touch_amplification"] <= MAX_SELECTIVE_AMP
        and max_dphys <= MAX_SELECTIVE_AMP
        and max_drecon <= MAX_SELECTIVE_AMP
    )

    clean = {k: v for k, v in cs.items() if k not in ("derived_inventory", "all_streams")}
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "tree_sha256": expected,
        "baseline_v030_bytes": baseline.stat().st_size,
        "candidate_bytes": cs["stored_bytes"],
        "accepted_v029_office_bytes": ACCEPTED_V029_OFFICE,
        "saving_vs_v030_bytes": baseline.stat().st_size - cs["stored_bytes"],
        "margin_vs_v029_bytes": ACCEPTED_V029_OFFICE - cs["stored_bytes"],
        "baseline_create_wall_s": baseline_wall,
        "candidate_create_wall_s": candidate_wall,
        "candidate": clean,
        "verify": verify,
        "derived_selective_reads": derived_reads,
        "max_derived_physical_amplification_without_auth_index": max_dphys,
        "max_derived_reconstruction_amplification": max_drecon,
        "hypothesis": {
            "exact_tree": verify["tree_sha256"] == expected,
            "all_member_skeleton_beats_v030": cs["stored_bytes"] < baseline.stat().st_size,
            "all_member_skeleton_beats_v029_floor": density_supported,
            "container_ideal_pool_touch_le_8x": cs["max_ideal_container_pool_touch_amplification"] <= MAX_SELECTIVE_AMP,
            "derived_selective_physical_le_8x_before_auth_index": max_dphys <= MAX_SELECTIVE_AMP,
            "derived_selective_reconstruction_le_8x": max_drecon <= MAX_SELECTIVE_AMP,
            "product_supported": density_supported and locality_diagnostic,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_format_changed": False,
            "production_selector_changed": False,
            "same_sfv2_container_discovery_surface": True,
            "all_member_bodies_exact_identity_only": True,
            "no_workload_name_path_hash_dispatch": True,
            "no_recompression": True,
            "no_threshold_sweep": True,
            "all_wrapper_bytes_charged": True,
            "container_locality_is_ideal_map_not_physical_io": True,
            "derived_physical_metric_excludes_future_auth_index_and_is_optimistic": True,
            "locality_debt_blocks_product_promotion": True,
        },
        "next_if_density_supported": "harden all-member range authentication and solve derived-view <=8x reconstruction without giving back the density margin; then compose exact full matrix",
        "next_if_density_fails": "preserve negative and attribute remaining bytes; do not add resemblance search or change thresholds",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-sfv4-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-sfv4.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, default=str) + "\n")
    print(json.dumps({
        "baseline_v030_bytes": d["baseline_v030_bytes"],
        "candidate_bytes": d["candidate_bytes"],
        "accepted_v029_office_bytes": d["accepted_v029_office_bytes"],
        "saving_vs_v030_bytes": d["saving_vs_v030_bytes"],
        "margin_vs_v029_bytes": d["margin_vs_v029_bytes"],
        "baseline_create_wall_s": d["baseline_create_wall_s"],
        "candidate_create_wall_s": d["candidate_create_wall_s"],
        "component_bytes": d["candidate"]["component_bytes"],
        "shared_stream_count": d["candidate"]["shared_stream_count"],
        "all_member_unique_stream_count": d["candidate"]["all_member_unique_stream_count"],
        "additional_unique_stream_bytes_vs_sfv2_shared": d["candidate"]["additional_unique_stream_bytes_vs_sfv2_shared"],
        "literal_skeleton_bytes": d["candidate"]["literal_skeleton_bytes"],
        "derived_file_count": d["candidate"]["derived_file_count"],
        "derived_logical_bytes": d["candidate"]["derived_logical_bytes"],
        "max_ideal_container_pool_touch_amplification": d["candidate"]["max_ideal_container_pool_touch_amplification"],
        "max_derived_physical_amplification_without_auth_index": d["max_derived_physical_amplification_without_auth_index"],
        "max_derived_reconstruction_amplification": d["max_derived_reconstruction_amplification"],
        "hypothesis": d["hypothesis"],
    }, indent=2))


if __name__ == "__main__":
    main()
