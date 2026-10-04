from __future__ import annotations

"""Office R4 SFV3: exact stream federation plus exact derived loose-file views.

Mission lock
------------
SFV2 established that exact compressed-stream federation removes 5.25 MB from the published r24
Office fallback, but its candidate remains ~4.24 MB above the accepted v0.29/v0.25 floor. Independent
v0.25 physical attribution shows the old winner represents eight loose files as ``inflate_stream``
views and that 82% of Office logical bytes are stream-dependent. SFV2, by contrast, removes ZIP-like
containers from its ordinary base but still stores every loose file in ``base.cmpct``.

Falsifiable hypothesis
----------------------
Without using workload names, paths, hashes, or a historical recipe table, identify any ordinary file
whose exact bytes equal the raw-DEFLATE inflation of a compressed member stream that SFV2 already owns.
Remove only those exact matches from the ordinary base and represent them as authenticated derived-view
records pointing at the existing stream pool. If redundant loose views are the dominant residual Office
mechanism, the complete authenticated candidate should strictly beat the accepted v0.29 Office floor
(5,954,026 B) while reconstructing the exact tree.

Disproof
--------
If exact derived views do not beat that floor after charging all base/pool/manifest/auth bytes, preserve
the negative and attribute the residual before adding resemblance search or tuning thresholds. There is
no threshold sweep: admission requires exact SHA-256 identity after raw-DEFLATE inflation.

Locality is measured, not waived. A derived loose-file 4 KiB read is modeled with the actual current
reader mechanism: inflate the owned raw-DEFLATE stream from its beginning until the requested range is
available. The density hypothesis and the product-locality hypothesis are reported separately. A density
win with >8x selective reconstruction is research evidence only and MUST NOT be promoted as product.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_exact_stream_federation_v2 as SFV2
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-sfv3-derived-views-v1"
ACCEPTED_V029_OFFICE = SFV2.ACCEPTED_V029_OFFICE
REQUEST = SFV2.REQUEST
MAX_SELECTIVE_AMP = 8.0


def _inflate_raw(stream: bytes) -> bytes | None:
    try:
        d = zlib.decompressobj(-15)
        raw = d.decompress(stream) + d.flush()
        if not d.eof:
            return None
        return raw
    except zlib.error:
        return None


def _derived_inventory(root: Path, containers: dict, shared: dict[str, bytes]) -> dict[str, dict]:
    # Index only streams already owned by SFV2. Selection is exact decoded-byte identity; path and
    # historical recipe labels never participate.
    by_raw_hash: dict[str, list[tuple[str, int, bytes]]] = {}
    for stream_hash, stream in shared.items():
        raw = _inflate_raw(stream)
        if raw is None:
            continue
        by_raw_hash.setdefault(SFV2.sha(raw), []).append((stream_hash, len(stream), raw))

    container_paths = {p.resolve() for p in containers}
    out: dict[str, dict] = {}
    for p in sorted(q for q in root.rglob("*") if q.is_file()):
        if p.resolve() in container_paths:
            continue
        raw = p.read_bytes()
        matches = by_raw_hash.get(SFV2.sha(raw), [])
        exact = [m for m in matches if m[2] == raw]
        if not exact:
            continue
        # Choose the cheapest already-owned stream deterministically; no candidate-size audition occurs.
        stream_hash, stream_bytes, _ = min(exact, key=lambda x: (x[1], x[0]))
        out[p.relative_to(root).as_posix()] = {
            "stream_hash": stream_hash,
            "logical_bytes": len(raw),
            "stream_bytes": stream_bytes,
            "metadata": SFV2.statrec(p),
        }
    return out


def _inflate_prefix_cost(stream: bytes, want: int) -> tuple[bytes, int]:
    d = zlib.decompressobj(-15)
    out = bytearray()
    consumed = 0
    pos = 0
    while len(out) < want and pos < len(stream):
        chunk = stream[pos:pos + 4096]
        pos += len(chunk)
        before_tail = len(d.unconsumed_tail)
        produced = d.decompress(chunk, max(0, want - len(out)))
        out.extend(produced)
        # If max_length stopped within this chunk, unconsumed_tail belongs to the current input and was
        # not needed physically for this request. Account only bytes actually consumed by zlib.
        used = len(chunk) - len(d.unconsumed_tail)
        consumed += used
        if d.unconsumed_tail:
            pos -= len(d.unconsumed_tail)
        if d.eof:
            break
        if used == 0 and not produced:
            break
    return bytes(out[:want]), consumed


def _selective_derived_reads(derived: dict[str, dict], shared: dict[str, bytes], root: Path) -> list[dict]:
    rows = []
    for rel, rec in sorted(derived.items()):
        raw = (root / rel).read_bytes()
        stream = shared[rec["stream_hash"]]
        n = min(REQUEST, len(raw))
        starts = sorted({0, max(0, len(raw) // 2 - n // 2), max(0, len(raw) - n)})
        for start in starts:
            want_end = start + n
            prefix, consumed = _inflate_prefix_cost(stream, want_end)
            got = prefix[start:want_end]
            if got != raw[start:want_end]:
                raise RuntimeError(f"derived selective mismatch: {rel}@{start}")
            reconstruction = want_end
            rows.append({
                "path": rel,
                "start": start,
                "requested_bytes": n,
                "compressed_stream_bytes_consumed": consumed,
                "physical_amplification_without_auth_index": consumed / max(1, n),
                "reconstruction_bytes": reconstruction,
                "reconstruction_amplification": reconstruction / max(1, n),
            })
    return rows


def build_candidate(root: Path, out: Path, work: Path) -> dict:
    containers, shared = SFV2.discover(root)
    if not shared:
        raise RuntimeError("no exact shared streams")
    derived = _derived_inventory(root, containers, shared)
    if not derived:
        raise RuntimeError("no exact derived loose-file views")

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
    literal, streams, sidx, templates_abs = SFV2.build_layout(containers, shared)
    templates = {p.relative_to(root).as_posix(): t for p, t in templates_abs.items()}
    manifest = {
        "schema": "cmpct-v030-r4-office-stream-federation-v3-derived-bundle",
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
    (out / "auth.bin").write_bytes(SFV2.MAGIC + b"".join(hashlib.sha256(x).digest() for x in pieces))
    sizes = {p.name: p.stat().st_size for p in out.iterdir() if p.is_file()}
    return {
        "stored_bytes": sum(sizes.values()),
        "component_bytes": sizes,
        "shared_stream_count": len(shared),
        "shared_stream_bytes": len(streams),
        "literal_pool_bytes": len(literal),
        "derived_file_count": len(derived),
        "derived_logical_bytes": sum(x["logical_bytes"] for x in derived.values()),
        "derived_paths": sorted(derived),
        "derived_inventory": derived,
        "shared": shared,
    }


def extract_candidate(bundle: Path, out: Path) -> dict:
    mraw = (bundle / "manifest.json").read_bytes()
    m = json.loads(mraw)
    literal = (bundle / "literal.bin").read_bytes()
    streams = (bundle / "streams.bin").read_bytes()
    base = (bundle / "base.cmpct").read_bytes()
    pieces = [base, literal, streams, mraw]
    if (bundle / "auth.bin").read_bytes() != SFV2.MAGIC + b"".join(hashlib.sha256(x).digest() for x in pieces):
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
        raw = _inflate_raw(stream)
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
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_sfv3_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_sfv3_repair")
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

    cand_dir = work / "candidate"
    t0 = time.perf_counter()
    cs = build_candidate(source, cand_dir, work / "cand-work")
    candidate_wall = time.perf_counter() - t0
    verify = extract_candidate(cand_dir, work / "extract")
    if verify["tree_sha256"] != expected:
        raise RuntimeError("SFV3 exact tree mismatch")

    selective = _selective_derived_reads(cs["derived_inventory"], cs["shared"], source)
    max_phys = max(x["physical_amplification_without_auth_index"] for x in selective) if selective else 0.0
    max_recon = max(x["reconstruction_amplification"] for x in selective) if selective else 0.0
    density_supported = cs["stored_bytes"] < ACCEPTED_V029_OFFICE
    locality_supported = max_phys <= MAX_SELECTIVE_AMP and max_recon <= MAX_SELECTIVE_AMP

    # Do not serialize raw shared stream bytes in the receipt.
    clean_candidate = {k: v for k, v in cs.items() if k not in ("shared", "derived_inventory")}
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
        "candidate": clean_candidate,
        "verify": verify,
        "derived_selective_reads": selective,
        "max_derived_physical_amplification_without_auth_index": max_phys,
        "max_derived_reconstruction_amplification": max_recon,
        "hypothesis": {
            "exact_tree": verify["tree_sha256"] == expected,
            "derived_views_found_without_path_dispatch": cs["derived_file_count"] > 0,
            "density_beats_v030": cs["stored_bytes"] < baseline.stat().st_size,
            "density_beats_v029_floor": density_supported,
            "derived_selective_physical_le_8x_before_auth_index": max_phys <= MAX_SELECTIVE_AMP,
            "derived_selective_reconstruction_le_8x": max_recon <= MAX_SELECTIVE_AMP,
            "product_supported": density_supported and locality_supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "production_format_changed": False,
            "production_selector_changed": False,
            "exact_decoded_byte_identity_only": True,
            "no_workload_name_path_hash_dispatch": True,
            "no_threshold_sweep": True,
            "all_wrapper_bytes_charged": True,
            "derived_locality_measured_not_waived": True,
            "derived_physical_metric_excludes_future_auth_index_and_is_optimistic": True,
        },
        "next_if_density_supported_but_locality_fails": "retain SFV3 density evidence; design bounded authenticated access to derived streams without duplicating full loose views, and require <=8x before promotion",
        "next_if_density_fails": "preserve negative and attribute remaining base/pool bytes before any resemblance search or tuning",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-sfv3-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-sfv3.json"))
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
        "derived_file_count": d["candidate"]["derived_file_count"],
        "derived_logical_bytes": d["candidate"]["derived_logical_bytes"],
        "max_derived_physical_amplification_without_auth_index": d["max_derived_physical_amplification_without_auth_index"],
        "max_derived_reconstruction_amplification": d["max_derived_reconstruction_amplification"],
        "hypothesis": d["hypothesis"],
    }, indent=2))


if __name__ == "__main__":
    main()
