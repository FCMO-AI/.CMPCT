from __future__ import annotations

"""Causal referee: is compressed-byte discovery hiding Office micro-solid headroom?

Mission Lock
------------
H-MS3 kept physical groups locality-bounded (<=3 x 4 KiB pages) but discovered page
relationships from already-compressed raw-DEFLATE bytes. Hosted evidence found only 31
pages with neighbors and the 1,352 B pre-directory grouping gain was erased by the
7,245 B page->group directory.

H-MS3-LD changes exactly one causal layer: candidate discovery. Each physical DEFLATE
page is described by the *logical output bytes produced by DEFLATE tokens whose encoded
bits intersect that physical page*. Bounded CMPCT resemblance sketches/LSH operate on
that logical projection, while the stored objects remain the exact original compressed
4 KiB pages and the same <=3-page micro-solid representation.

Hypothesis: if DEFLATE decorrelation, rather than the micro-solid representation itself,
is hiding useful cross-stream structure, logical-domain discovery should strictly reduce
the complete stream-store bytes versus the same-run compressed-domain H-MS3 control and
may close the frozen v0.29 Office gap. If it does not materially improve the control,
do not tune LSH thresholds; preserve the negative and move the representation question.

Diagnostic only: even a density win earns no locality/release credit until a complete
cold selective reader charges all touched frames, authenticated directory/proofs,
pread/seeks, recovery/corruption, CPU/RSS and native parity.
"""

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import shutil
import time
import zlib

import zstandard as zstd

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from benchmarks import v030_r4_office_similarity_micro_solid_density as MS3
from cmpct.resemblance import lsh_candidates, similarity_sketch
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-logical-domain-micro-solid-density-v1"
PHYSICAL_PAGE_BITS = MS3.PAGE_BYTES * 8


def _logical_signatures(comp: bytes, raw: bytes, parsed: dict, page_count: int) -> list[bytes]:
    """Return content-derived semantic signatures for fixed physical DEFLATE pages.

    A token is charged to every physical page touched by its encoded bit span. This is
    intentionally a discovery-only projection: duplicated signature bytes are never
    stored or credited as representation savings. Token parsing is bounded encoder work;
    the reader never needs to reproduce this decision after the page->group map is stored.
    """
    sigs = [bytearray() for _ in range(page_count)]
    for start, length, _distance, bit0, bit1, _bid in parsed["tokens"]:
        if length <= 0 or bit1 <= bit0:
            continue
        logical = raw[start:start + length]
        if len(logical) != length:
            raise RuntimeError("token logical projection exceeds decoded output")
        p0 = min(page_count - 1, bit0 // PHYSICAL_PAGE_BITS)
        p1 = min(page_count - 1, (bit1 - 1) // PHYSICAL_PAGE_BITS)
        for page in range(p0, p1 + 1):
            sigs[page] += logical
    return [bytes(x) for x in sigs]


def _build_groups(pages: list[MS3.Page], signatures: list[bytes]):
    if len(pages) != len(signatures):
        raise ValueError("page/signature mismatch")
    enc = zstd.ZstdCompressor(level=MS3.ZSTD_LEVEL)
    sketches = [similarity_sketch(s) for s in signatures]
    edges = lsh_candidates(sketches, max_bucket=MS3.LSH_MAX_BUCKET, max_candidates=MS3.LSH_MAX_CANDIDATES)
    neighbors: dict[int, set[int]] = defaultdict(set)
    for edge in edges:
        if edge.target != edge.base:
            neighbors[edge.target].add(edge.base)
            neighbors[edge.base].add(edge.target)

    independent = [MS3._independent_cost(p, enc) for p in pages]
    opportunities: list[tuple[int, tuple[int, ...], int]] = []
    examined_pairs = examined_triples = 0
    for p in range(len(pages)):
        ns = sorted(neighbors.get(p, ()))
        for qi, q in enumerate(ns):
            if q <= p:
                continue
            ids2 = (p, q)
            cost2, _ = MS3._group_cost(ids2, pages, enc)
            saving2 = independent[p] + independent[q] - cost2
            examined_pairs += 1
            if saving2 > 0:
                opportunities.append((saving2, ids2, cost2))
            for r in ns[qi + 1:]:
                if r <= p or r == q:
                    continue
                ids3 = tuple(sorted((p, q, r)))
                if ids3[0] != p:
                    continue
                cost3, _ = MS3._group_cost(ids3, pages, enc)
                saving3 = sum(independent[x] for x in ids3) - cost3
                examined_triples += 1
                if saving3 > 0:
                    opportunities.append((saving3, ids3, cost3))

    opportunities.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    used: set[int] = set()
    chosen: list[tuple[int, ...]] = []
    for _saving, ids, _cost in opportunities:
        if any(i in used for i in ids):
            continue
        chosen.append(ids); used.update(ids)
    for pid in range(len(pages)):
        if pid not in used:
            chosen.append((pid,))
    chosen.sort(key=lambda ids: min(ids))

    groups = []
    placement: dict[int, tuple[int, int]] = {}
    decoded: dict[int, bytes] = {}
    stored = 0
    dec = zstd.ZstdDecompressor()
    for gid, ids in enumerate(chosen):
        cost, payload = MS3._group_cost(ids, pages, enc)
        groups.append((ids, payload)); stored += cost
        raw_len = sum(len(pages[i].data) for i in ids)
        raw = payload if len(payload) == raw_len else dec.decompress(payload, max_output_size=raw_len)
        if len(raw) != raw_len:
            raise RuntimeError("logical-domain group decode length mismatch")
        decoded[gid] = raw
        for member, pid in enumerate(ids):
            placement[pid] = (gid, member)

    return {
        "lsh_edges": len(edges),
        "pages_with_neighbors": len(neighbors),
        "nonempty_logical_signatures": sum(bool(s) for s in signatures),
        "logical_signature_bytes": sum(map(len, signatures)),
        "examined_pairs": examined_pairs,
        "examined_triples": examined_triples,
        "positive_opportunities": len(opportunities),
        "groups": len(groups),
        "multi_page_groups": sum(len(ids) > 1 for ids, _ in groups),
        "grouped_pages": sum(len(ids) for ids, _ in groups if len(ids) > 1),
        "independent_frame_bytes": sum(independent),
        "group_frame_bytes": stored,
        "saving_before_directory_bytes": sum(independent) - stored,
    }, groups, placement, decoded


def _reconstruct(stream_pages, pages, groups, placement, decoded_groups, originals):
    for si, ids in enumerate(stream_pages):
        out = bytearray()
        for pid in ids:
            gid, member = placement[pid]
            member_ids = groups[gid][0]
            raw = decoded_groups[gid]
            start = sum(len(pages[x].data) for x in member_ids[:member])
            out += raw[start:start + len(pages[pid].data)]
        if bytes(out) != originals[si]:
            raise RuntimeError(f"logical-domain stream reconstruction mismatch: {si}")


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_ms3ld_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_ms3ld_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"; neutral.build(corpus); repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    built = SFV4.build_candidate(source, work / "sfv4", work / "sfv4-work")

    stream_hashes = sorted(built["all_streams"])
    pages: list[MS3.Page] = []
    signatures: list[bytes] = []
    stream_pages: list[list[int]] = []
    originals: list[bytes] = []
    parse_cpu0 = time.process_time(); parse_wall0 = time.perf_counter()
    for si, h in enumerate(stream_hashes):
        comp = built["all_streams"][h]; originals.append(comp)
        raw = zlib.decompress(comp, -15); parsed = DEP.parse_tokens(comp)
        local_pages = [comp[o:o + MS3.PAGE_BYTES] for o in range(0, len(comp), MS3.PAGE_BYTES)]
        local_sigs = _logical_signatures(comp, raw, parsed, len(local_pages))
        ids = []
        for pi, (pdata, sig) in enumerate(zip(local_pages, local_sigs)):
            ids.append(len(pages)); pages.append(MS3.Page(si, pi, pdata)); signatures.append(sig)
        stream_pages.append(ids)
    discovery_projection_cpu = time.process_time() - parse_cpu0
    discovery_projection_wall = time.perf_counter() - parse_wall0

    # Exact causal control on identical pages: rerun the already-frozen compressed-byte discovery
    # mechanism in this process rather than comparing across runners.
    c0 = time.process_time(); t0 = time.perf_counter()
    control_stats, _cg, _cp, _cd = MS3._build_micro_solids(pages)
    control_directory = MS3._directory_bytes(stream_pages, _cp, pages)
    control_stream_store = control_stats["group_frame_bytes"] + len(control_directory)
    control_cpu = time.process_time() - c0; control_wall = time.perf_counter() - t0

    l0 = time.process_time(); lt0 = time.perf_counter()
    stats, groups, placement, decoded = _build_groups(pages, signatures)
    directory = MS3._directory_bytes(stream_pages, placement, pages)
    _reconstruct(stream_pages, pages, groups, placement, decoded, originals)
    logical_group_cpu = time.process_time() - l0; logical_group_wall = time.perf_counter() - lt0

    raw_stream = sum(map(len, originals))
    if raw_stream != int(built["all_member_stream_bytes"]):
        raise RuntimeError("all-member stream accounting mismatch")

    sparse = seed = logical_seed = 0
    hashes = sorted({rec["stream_hash"] for rec in built["derived_inventory"].values()})
    for h in hashes:
        comp = built["all_streams"][h]; raw = zlib.decompress(comp, -15); parsed = DEP.parse_tokens(comp)
        anchors, _blocks, sparse_stored = COLD._build_metadata(parsed)
        _seeds, seed_stored, seed_logical = SEED._build_seeds(parsed, anchors, raw)
        sparse += sparse_stored; seed += seed_stored; logical_seed += seed_logical

    sfv4 = int(built["stored_bytes"]); nonstream = sfv4 - raw_stream
    stream_store = stats["group_frame_bytes"] + len(directory)
    candidate = nonstream + stream_store + sparse + seed
    stats["directory_bytes"] = len(directory)
    stats["stream_store_with_directory_bytes"] = stream_store
    stats["net_saving_vs_independent_frames_bytes"] = stats["independent_frame_bytes"] - stream_store

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "02_office_workspace",
        "tree_sha256": PRODUCT.treehash(source),
        "candidate": {
            "page_bytes": MS3.PAGE_BYTES,
            "max_group_pages": MS3.GROUP_PAGES,
            "frame_tax_bytes": MS3.FRAME_TAX,
            "zstd_level": MS3.ZSTD_LEVEL,
            "lsh_max_bucket": MS3.LSH_MAX_BUCKET,
            "lsh_max_candidates": MS3.LSH_MAX_CANDIDATES,
            "discovery_domain": "decoded-output-of-tokens-intersecting-physical-deflate-page",
        },
        "compressed_domain_control": {
            "stream_store_with_directory_bytes": control_stream_store,
            "lsh_edges": control_stats["lsh_edges"],
            "pages_with_neighbors": control_stats["pages_with_neighbors"],
            "saving_before_directory_bytes": control_stats["saving_before_directory_bytes"],
            "cpu_s": control_cpu, "wall_s": control_wall,
        },
        "logical_domain": stats,
        "stream_store": {
            "raw_stream_bytes": raw_stream,
            "stream_store_with_directory_bytes": stream_store,
            "saving_vs_raw_stream_bytes": raw_stream - stream_store,
            "discovery_projection_cpu_s": discovery_projection_cpu,
            "discovery_projection_wall_s": discovery_projection_wall,
            "group_and_verify_cpu_s": logical_group_cpu,
            "group_and_verify_wall_s": logical_group_wall,
        },
        "economics": {
            "sfv4_bytes": sfv4, "sfv4_nonstream_bytes": nonstream,
            "sparse_metadata_bytes": sparse, "seed_metadata_bytes": seed,
            "logical_seed_bytes": logical_seed,
            "candidate_with_locality_metadata_bytes": candidate,
            "accepted_v029_office_bytes": SFV4.ACCEPTED_V029_OFFICE,
            "margin_to_v029_bytes": SFV4.ACCEPTED_V029_OFFICE - candidate,
            "density_feasible": candidate < SFV4.ACCEPTED_V029_OFFICE,
        },
        "hypothesis": {
            "logical_domain_strictly_beats_same_run_compressed_domain": stream_store < control_stream_store,
            "logical_domain_micro_solids_recover_product_density": candidate < SFV4.ACCEPTED_V029_OFFICE,
        },
        "contract": {
            "diagnostic_only": True, "release_credit": False, "locality_credit": False,
            "storage_representation_identical_to_ms3": True,
            "only_causal_layer_changed_is_discovery_signal": True,
            "no_similarity_threshold_sweep": True,
            "content_derived_bounded_discovery": True,
            "measured_economic_admission": True,
            "logical_signature_bytes_not_stored_or_credited": True,
            "selector_changed": False, "production_format_changed": False,
            "all_group_frame_and_directory_bytes_charged": True,
            "remaining_debt": "complete cold-reader locality; authenticated framing/proofs; pread/seeks; corruption/recovery; fresh CPU/RSS; held-out transfer; native parity",
        },
    }


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,default=Path("benchmark-artifacts/v030-r4-office-ms3ld-work")); p.add_argument("--output",type=Path,default=Path("benchmark-artifacts/v030-r4-office-ms3ld.json")); a=p.parse_args()
    d=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(d,indent=2)+"\n")
    print(json.dumps({"compressed_domain_control":d["compressed_domain_control"],"logical_domain":d["logical_domain"],"stream_store":d["stream_store"],"economics":d["economics"],"hypothesis":d["hypothesis"]},indent=2))


if __name__ == "__main__": main()
