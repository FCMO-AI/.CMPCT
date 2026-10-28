from __future__ import annotations

"""Density referee for content-related, locality-bounded Office micro-solids.

Mission Lock
------------
H-BMAX falsified the hypothesis that larger *independent* contiguous frames recover the
missing Office density: the largest slab derivable from the existing 8x/4 KiB law still
left the complete locality-charged candidate 549,285 B above frozen v0.29 Office.

H-MS3: if a material part of the missing density comes from repeated structure *between*
small physical regions rather than merely longer context inside one stream, then packing
at most three content-related 4 KiB pages into one independently decodable micro-solid
should recover additional bytes while preserving a bounded physical unit.

Candidate discovery is deterministic and content-derived: existing CMPCT resemblance
sketches/LSH nominate a bounded set of neighbors. Similarity never grants admission.
Every proposed pair/triple is actually encoded and is accepted only when its complete
frame bytes are strictly smaller than the same pages stored independently. There is no
Office pathname/type rule and no similarity threshold sweep.

This is a density referee, not locality or release evidence. A logical selective read can
need several compressed-stream ranges, so the <=3-page physical group bound alone does
not prove the complete <=8x product contract. A surviving mechanism must next be tested
through the cold selective reader with serialized directory/auth proof, pread/seeks,
corruption/recovery, fresh CPU/RSS and native parity charged.
"""

import argparse
from collections import defaultdict
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import time
import zlib

import zstandard as zstd

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from cmpct.resemblance import lsh_candidates, similarity_sketch
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-similarity-micro-solid-density-v1"
PAGE_BYTES = 4096
GROUP_PAGES = 3
FRAME_TAX = 53
ZSTD_LEVEL = 3
# Discovery bounds inherit the reusable resemblance primitive defaults explicitly so this
# referee cannot silently become an all-pairs search on hostile/equal inputs.
LSH_MAX_BUCKET = 48
LSH_MAX_CANDIDATES = 8

# A direct request crossing two logical pages can touch at most two page groups *for the
# raw stream-page layer*. This is only a structural bound and intentionally grants no
# complete selective-read credit.
DIRECT_TWO_GROUP_RAW_UPPER = 2 * GROUP_PAGES * PAGE_BYTES
assert DIRECT_TWO_GROUP_RAW_UPPER == 24576


@dataclass(frozen=True)
class Page:
    stream_index: int
    page_index: int
    data: bytes


def _varint(n: int) -> bytes:
    if n < 0:
        raise ValueError("negative varint")
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)
    return bytes(out)


def _payload(data: bytes, enc: zstd.ZstdCompressor) -> bytes:
    z = enc.compress(data)
    return z if len(z) < len(data) else data


def _independent_cost(page: Page, enc: zstd.ZstdCompressor) -> int:
    return len(_payload(page.data, enc)) + FRAME_TAX


def _group_cost(ids: tuple[int, ...], pages: list[Page], enc: zstd.ZstdCompressor) -> tuple[int, bytes]:
    raw = b"".join(pages[i].data for i in ids)
    payload = _payload(raw, enc)
    return len(payload) + FRAME_TAX, payload


def _directory_bytes(stream_pages: list[list[int]], placement: dict[int, tuple[int, int]], pages: list[Page]) -> bytes:
    """Serialize the exact page->(group,member,length) map charged by this referee.

    Stream identity/order already exists in the SFV4 skeleton. This directory therefore
    only records, per stream, how its fixed logical pages map into micro-solid frames.
    """
    out = bytearray(b"MSD1")
    out += _varint(len(stream_pages))
    for ids in stream_pages:
        out += _varint(len(ids))
        for pid in ids:
            gid, member = placement[pid]
            out += _varint(gid)
            out.append(member)
            out += _varint(len(pages[pid].data))
    return bytes(out)


def _build_micro_solids(pages: list[Page]) -> tuple[dict, list[tuple[tuple[int, ...], bytes]], dict[int, tuple[int, int]], bytes]:
    enc = zstd.ZstdCompressor(level=ZSTD_LEVEL)
    sketches = [similarity_sketch(p.data) for p in pages]
    edges = lsh_candidates(sketches, max_bucket=LSH_MAX_BUCKET, max_candidates=LSH_MAX_CANDIDATES)

    neighbors: dict[int, set[int]] = defaultdict(set)
    for edge in edges:
        if edge.target == edge.base:
            continue
        neighbors[edge.target].add(edge.base)
        neighbors[edge.base].add(edge.target)

    independent = [_independent_cost(p, enc) for p in pages]
    opportunities: list[tuple[int, tuple[int, ...], int]] = []
    examined_pairs = examined_triples = 0

    # Candidate generation stays bounded by the LSH neighborhood. Actual compressed bytes
    # decide admission; sketch strength never substitutes for economics.
    for p in range(len(pages)):
        ns = sorted(neighbors.get(p, ()))
        for qi, q in enumerate(ns):
            if q <= p:
                continue
            ids2 = (p, q)
            cost2, _ = _group_cost(ids2, pages, enc)
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
                cost3, _ = _group_cost(ids3, pages, enc)
                saving3 = sum(independent[x] for x in ids3) - cost3
                examined_triples += 1
                if saving3 > 0:
                    opportunities.append((saving3, ids3, cost3))

    # Maximum-saving-first is deterministic and corpus-agnostic. It is not globally optimal
    # set packing, so any negative result is conservative with respect to a more expensive
    # optimizer; this referee tests whether a cheap bounded mechanism has useful headroom.
    opportunities.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    used: set[int] = set()
    chosen: list[tuple[int, ...]] = []
    for _saving, ids, _cost in opportunities:
        if any(i in used for i in ids):
            continue
        chosen.append(ids)
        used.update(ids)
    for pid in range(len(pages)):
        if pid not in used:
            chosen.append((pid,))

    chosen.sort(key=lambda ids: min(ids))
    groups: list[tuple[tuple[int, ...], bytes]] = []
    placement: dict[int, tuple[int, int]] = {}
    stored = 0
    grouped_pages = 0
    grouped_saving_before_directory = 0
    for gid, ids in enumerate(chosen):
        cost, payload = _group_cost(ids, pages, enc)
        groups.append((ids, payload))
        stored += cost
        if len(ids) > 1:
            grouped_pages += len(ids)
            grouped_saving_before_directory += sum(independent[i] for i in ids) - cost
        for member, pid in enumerate(ids):
            placement[pid] = (gid, member)

    # Independently reconstruct every stream from decoded groups. Builder/decoder agreement is
    # not product conformance evidence, but it catches accounting or member-boundary mistakes
    # before this diagnostic is allowed to influence research direction.
    decoded: dict[int, bytes] = {}
    dec = zstd.ZstdDecompressor()
    for gid, (ids, payload) in enumerate(groups):
        raw_len = sum(len(pages[i].data) for i in ids)
        if len(payload) == raw_len:
            raw = payload
        else:
            raw = dec.decompress(payload, max_output_size=raw_len)
        if len(raw) != raw_len:
            raise RuntimeError("micro-solid decoded length mismatch")
        decoded[gid] = raw

    return {
        "lsh_edges": len(edges),
        "pages_with_neighbors": len(neighbors),
        "examined_pairs": examined_pairs,
        "examined_triples": examined_triples,
        "positive_opportunities": len(opportunities),
        "groups": len(groups),
        "multi_page_groups": sum(1 for ids, _ in groups if len(ids) > 1),
        "grouped_pages": grouped_pages,
        "independent_frame_bytes": sum(independent),
        "group_frame_bytes": stored,
        "saving_before_directory_bytes": sum(independent) - stored,
        "chosen_group_saving_before_directory_bytes": grouped_saving_before_directory,
    }, groups, placement, decoded


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_ms3_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_ms3_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    built = SFV4.build_candidate(source, work / "sfv4", work / "sfv4-work")

    stream_hashes = sorted(built["all_streams"])
    pages: list[Page] = []
    stream_pages: list[list[int]] = []
    original_by_stream: list[bytes] = []
    for si, h in enumerate(stream_hashes):
        comp = built["all_streams"][h]
        original_by_stream.append(comp)
        ids: list[int] = []
        for pi, off in enumerate(range(0, len(comp), PAGE_BYTES)):
            ids.append(len(pages))
            pages.append(Page(si, pi, comp[off:off + PAGE_BYTES]))
        stream_pages.append(ids)

    c0 = time.process_time(); t0 = time.perf_counter()
    stats, groups, placement, decoded_groups = _build_micro_solids(pages)
    directory = _directory_bytes(stream_pages, placement, pages)

    # Reconstruct original raw-Deflate streams exactly from group payloads + charged directory mapping.
    for si, ids in enumerate(stream_pages):
        out = bytearray()
        for pid in ids:
            gid, member = placement[pid]
            member_ids = groups[gid][0]
            raw = decoded_groups[gid]
            start = sum(len(pages[x].data) for x in member_ids[:member])
            end = start + len(pages[pid].data)
            out += raw[start:end]
        if bytes(out) != original_by_stream[si]:
            raise RuntimeError(f"micro-solid stream reconstruction mismatch: {si}")
    cpu = time.process_time() - c0
    wall = time.perf_counter() - t0

    raw_stream = sum(len(x) for x in original_by_stream)
    if raw_stream != int(built["all_member_stream_bytes"]):
        raise RuntimeError("all-member stream accounting mismatch")

    # Preserve the current derived-stream selective reconstruction metadata so economics remain
    # comparable to the prior 4 KiB, page-seed, H-DICT8 and H-BMAX referees.
    sparse = seed = logical_seed = 0
    hashes = sorted({rec["stream_hash"] for rec in built["derived_inventory"].values()})
    for h in hashes:
        comp = built["all_streams"][h]
        raw = zlib.decompress(comp, -15)
        parsed = DEP.parse_tokens(comp)
        anchors, _blocks, sparse_stored = COLD._build_metadata(parsed)
        _seeds, seed_stored, seed_logical = SEED._build_seeds(parsed, anchors, raw)
        sparse += sparse_stored
        seed += seed_stored
        logical_seed += seed_logical

    sfv4 = int(built["stored_bytes"])
    nonstream = sfv4 - raw_stream
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
            "page_bytes": PAGE_BYTES,
            "max_group_pages": GROUP_PAGES,
            "frame_tax_bytes": FRAME_TAX,
            "zstd_level": ZSTD_LEVEL,
            "lsh_max_bucket": LSH_MAX_BUCKET,
            "lsh_max_candidates": LSH_MAX_CANDIDATES,
            "direct_two_group_raw_upper_bound_bytes": DIRECT_TWO_GROUP_RAW_UPPER,
        },
        "discovery_and_groups": stats,
        "stream_store": {
            "raw_stream_bytes": raw_stream,
            "stream_store_with_directory_bytes": stream_store,
            "saving_vs_raw_stream_bytes": raw_stream - stream_store,
            "encode_and_verify_cpu_s": cpu,
            "encode_and_verify_wall_s": wall,
        },
        "economics": {
            "sfv4_bytes": sfv4,
            "sfv4_nonstream_bytes": nonstream,
            "sparse_metadata_bytes": sparse,
            "seed_metadata_bytes": seed,
            "logical_seed_bytes": logical_seed,
            "candidate_with_locality_metadata_bytes": candidate,
            "accepted_v029_office_bytes": SFV4.ACCEPTED_V029_OFFICE,
            "margin_to_v029_bytes": SFV4.ACCEPTED_V029_OFFICE - candidate,
            "density_feasible": candidate < SFV4.ACCEPTED_V029_OFFICE,
        },
        "hypothesis": {
            "similarity_micro_solids_recover_product_density": candidate < SFV4.ACCEPTED_V029_OFFICE,
            "mechanism_improves_independent_page_frames": stats["net_saving_vs_independent_frames_bytes"] > 0,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "no_similarity_threshold_sweep": True,
            "content_derived_bounded_discovery": True,
            "measured_economic_admission": True,
            "selector_changed": False,
            "production_format_changed": False,
            "all_group_frame_and_directory_bytes_charged": True,
            "remaining_debt": "complete cold-reader touched-frame accounting; serialized authenticated product framing/proofs; pread/seeks; corruption/recovery; fresh CPU/RSS; held-out cross-workload transfer; native parity",
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-ms3-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-ms3.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"candidate": d["candidate"], "discovery_and_groups": d["discovery_and_groups"], "stream_store": d["stream_store"], "economics": d["economics"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
