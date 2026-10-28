from __future__ import annotations

"""Office gated-seed superframe economic referee.

Mission Lock / Referee
======================
The exact branch-and-bound page-seed referee established a clean split:

* 291/908 adjacent page pairs require seed mode under the unchanged 32,768 B law;
* selecting only those debt-bearing neighborhoods closes locality on all 1,800 fixed probes
  (0 exact/locality/certificate failures; worst 31,528 B = 7.697x);
* 280/413 available seed records are selected, costing 26,354 B as individually framed records;
* current admission + grouped sparse metadata + those individual seed frames loses same-input
  source-sealed v0.29 by 8,379 B.

The selected seed records themselves contain only 12,914 B of compressed bodies; 13,440 B is
280 repeated 48 B authentication/directory charges. This referee tests the mechanism-level claim
that the locality result can keep the exact same selected SED1 records while amortizing only their
proof/framing traffic, exactly as the separately adjudicated ANC1/BST1 sparse-superframe result did.

Hypothesis
----------
Reconstruct the exact zlib-9 SED1 byte strings already implied by the existing seed builder, verify
length+SHA parity for every selected record, and concatenate them per stream into deterministic
superframes with body <= one existing 4 KiB page. Pay one unchanged 48 B auth/directory charge per
superframe. Do not alter seed selection, seed bytes, page size, 8x law, DEFLATE bytes, admission,
codec, or sparse metadata. The same-input candidate plus adjudicated grouped sparse metadata plus
grouped selected seeds must remain strictly smaller than frozen source-sealed v0.29.

Disproof
--------
Any selected-record parity mismatch, selected-page/count/byte mismatch against the authoritative
gated-seed referee, body >4 KiB, or non-positive same-input v0.29 margin falsifies the mechanism.
No parameter sweep is permitted.

A pass is economic composition evidence only. The current locality reader still counts individual
metadata records, not actual serialized superframe reads. Product credit requires one physical
reader that deserializes/authenticates grouped sparse+seed frames from bytes, charges whole groups,
payload pread/seeks and proofs, preserves recovery/corruption behavior and <=8x locality, and pays
CPU/RSS/native/platform/held-out-transfer debt.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import time
import zlib

from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_gated_page_seed_referee as GATED
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED

SCHEMA = "cmpct-v030-r4-office-gated-seed-superframe-economic-v1"
PAGE = COLD.PAGE
LIMIT = 8 * PAGE


def _merge(rs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return SEED._merge(rs)


def _encode_seed_record(page: int, anchor: dict, parsed: dict, raw: bytes) -> bytes | None:
    tokens = parsed["tokens"]
    page_end = min((page + 1) * PAGE, len(raw))
    out_start = anchor["token_start"]
    # Deterministic direct scan is deliberately simple; referee cost is not product cost.
    need: list[tuple[int, int]] = []
    for start, length, distance, _bit0, _bit1, _bid in tokens:
        if start < out_start:
            continue
        if start >= page_end:
            break
        if distance:
            seed_len = min(distance, length)
            src0 = start - distance
            src1 = src0 + seed_len
            if src0 < out_start:
                need.append((src0, min(src1, out_start)))
    merged = _merge(need)
    if not merged:
        return None
    frame = bytearray(b"SED1")
    frame += DEP.uvarint(page) + DEP.uvarint(len(merged))
    prev = 0
    for a, b in merged:
        frame += DEP.uvarint(a - prev) + DEP.uvarint(b - a) + raw[a:b]
        prev = a
    return zlib.compress(bytes(frame), 9)


def _pack(records: list[tuple[int, bytes]], stream_sha256: str) -> list[dict]:
    groups: list[dict] = []
    body = bytearray()
    pages: list[int] = []

    def flush() -> None:
        nonlocal body, pages
        if not body:
            return
        if len(body) > PAGE:
            raise RuntimeError("seed superframe exceeded fixed 4 KiB body bound")
        groups.append({
            "stream_sha256": stream_sha256,
            "first_page": pages[0],
            "last_page": pages[-1],
            "records": len(pages),
            "body_bytes": len(body),
            "stored_bytes": len(body) + COLD.FRAME_TAX,
            "body_sha256": hashlib.sha256(body).hexdigest(),
        })
        body = bytearray()
        pages = []

    for page, enc in records:
        if len(enc) > PAGE:
            raise RuntimeError("one selected seed record exceeds fixed superframe body bound")
        if body and len(body) + len(enc) > PAGE:
            flush()
        body += enc
        pages.append(page)
    flush()
    return groups


def _rss_bytes() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    t0c = time.process_time()
    t0w = time.perf_counter()
    gated = GATED.run(work, v029_checkout, worker)
    bnb = gated["branch_and_bound"]
    if bnb["exact_failures"] or bnb["locality_failures"] or bnb["certificate_failures"]:
        raise RuntimeError("authoritative gated-seed locality prerequisite no longer closes")

    manifest = json.loads((work / "current" / "manifest.json").read_text())
    pool = (work / "current" / "streams.bin").read_bytes()
    hashes = sorted({rec["stream_hash"] for rec in manifest["derived"].values()})

    selected_pages_total = 0
    selected_individual_stored = 0
    selected_body_total = 0
    all_groups: list[dict] = []
    rows = []

    for h in hashes:
        s = manifest["stream_index"][h]
        comp = pool[s["o"] : s["o"] + s["n"]]
        parsed = DEP.parse_tokens(comp)
        raw = zlib.decompress(comp, -15)
        anchors, blocks, _sparse = COLD._build_metadata(parsed)
        seeds, _all_seed_stored, _logical = SEED._build_seeds(parsed, anchors, raw)

        unsafe_pair_starts: set[int] = set()
        selected_pages: set[int] = set()
        pages = len(anchors)
        for p in range(pages):
            a = p * PAGE
            b = min(len(raw), min(pages, p + 2) * PAGE)
            r = COLD.ColdReader(comp, anchors, blocks, len(raw))
            if r.read(a, b) != raw[a:b]:
                raise RuntimeError("pair classifier became byte-inexact")
            if r.metadata_bytes() + r.payload_bytes() > LIMIT:
                unsafe_pair_starts.add(p)
                selected_pages.add(p)
                if p + 1 < pages:
                    selected_pages.add(p + 1)

        records: list[tuple[int, bytes]] = []
        stream_individual = 0
        for p in sorted(selected_pages):
            inherited = seeds[p]
            if inherited is None:
                continue
            enc = _encode_seed_record(p, anchors[p], parsed, raw)
            if enc is None:
                raise RuntimeError("selected inherited seed disappeared during exact reconstruction")
            if hashlib.sha256(enc).hexdigest() != inherited["frame_sha256"]:
                raise RuntimeError("selected seed byte parity mismatch")
            if len(enc) + COLD.FRAME_TAX != inherited["frame_bytes"]:
                raise RuntimeError("selected seed length parity mismatch")
            records.append((p, enc))
            stream_individual += inherited["frame_bytes"]

        groups = _pack(records, h)
        body = sum(len(enc) for _p, enc in records)
        grouped = sum(g["stored_bytes"] for g in groups)
        selected_pages_total += len(records)
        selected_individual_stored += stream_individual
        selected_body_total += body
        all_groups.extend(groups)
        rows.append({
            "stream_sha256": h,
            "selected_seed_pages": len(records),
            "selected_seed_body_bytes": body,
            "selected_seed_individual_frame_bytes": stream_individual,
            "seed_superframes": len(groups),
            "seed_superframe_bytes": grouped,
            "largest_seed_superframe_body_bytes": max((g["body_bytes"] for g in groups), default=0),
        })

    if selected_pages_total != bnb["selected_seed_pages"]:
        raise RuntimeError("selected seed page count differs from authoritative gated referee")
    if selected_individual_stored != bnb["selected_seed_stored_bytes"]:
        raise RuntimeError("selected seed byte total differs from authoritative gated referee")

    grouped_tax = len(all_groups) * COLD.FRAME_TAX
    grouped_seed_bytes = selected_body_total + grouped_tax
    current_bytes = int(gated["charged_economics"]["candidate_before_locality_metadata_bytes"])
    sparse_bytes = int(gated["charged_economics"]["grouped_sparse_metadata_bytes"])
    v029_bytes = int(gated["charged_economics"]["same_input_v029_bytes"])
    candidate = current_bytes + sparse_bytes + grouped_seed_bytes
    margin = v029_bytes - candidate
    max_body = max((g["body_bytes"] for g in all_groups), default=0)
    supported = margin > 0 and max_body <= PAGE

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "source": gated["source"],
        "frozen_v029": gated["frozen_v029"],
        "locality_prerequisite": {
            "pair_certificates": bnb["pair_certificates"],
            "unsafe_pairs": bnb["unsafe_pairs"],
            "fixed_requests": bnb["fixed_requests"],
            "exact_failures": bnb["exact_failures"],
            "locality_failures": bnb["locality_failures"],
            "certificate_failures": bnb["certificate_failures"],
            "worst_fixed_probe": bnb["worst_fixed_probe"],
            "worst_page_pair_certificate": bnb["worst_page_pair_certificate"],
        },
        "selected_seed_superframes": {
            "selected_seed_pages": selected_pages_total,
            "individual_frame_bytes": selected_individual_stored,
            "record_body_bytes": selected_body_total,
            "repeated_individual_tax_bytes": selected_pages_total * COLD.FRAME_TAX,
            "groups": len(all_groups),
            "group_tax_bytes": grouped_tax,
            "stored_grouped_seed_bytes": grouped_seed_bytes,
            "saved_vs_individual_seed_frames_bytes": selected_individual_stored - grouped_seed_bytes,
            "largest_group_body_bytes": max_body,
            "largest_group_stored_bytes": max((g["stored_bytes"] for g in all_groups), default=0),
            "rows": rows,
            "groups_detail": all_groups,
        },
        "charged_economics": {
            "candidate_before_locality_metadata_bytes": current_bytes,
            "grouped_sparse_metadata_bytes": sparse_bytes,
            "grouped_selected_seed_bytes": grouped_seed_bytes,
            "candidate_plus_grouped_locality_bytes": candidate,
            "same_input_v029_bytes": v029_bytes,
            "margin_to_same_input_v029_bytes": margin,
        },
        "referee_profile": {
            "cpu_s_including_prerequisite_and_reclassification": time.process_time() - t0c,
            "wall_s_including_prerequisite_and_reclassification": time.perf_counter() - t0w,
            "hosted_process_peak_rss_bytes": _rss_bytes(),
        },
        "hypothesis": {
            "exact_selected_seed_records_group_within_same_input_density_margin": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "fixed_page_bytes": PAGE,
            "fixed_limit_bytes": LIMIT,
            "same_selected_seed_records": True,
            "same_seed_selector": True,
            "same_admission_candidate": True,
            "same_grouped_sparse_metadata": True,
            "same_input_source_sealed_v029": True,
            "no_parameter_or_codec_sweep": True,
            "remaining_debt": "one physical serialized reader charging whole sparse+seed superframes and payload pread/seeks/proofs; corruption/recovery; isolated creation CPU/RSS; hostile held-out transfer; native/platform parity",
        },
        "next_if_supported": "build one serialized authenticated grouped-metadata cold reader and charge whole-group reads plus payload ranges under <=8x",
        "next_if_falsified": "preserve exact seed-body lower bound and redesign restart state; do not move page size or 8x law",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-gated-seed-superframe-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-gated-seed-superframe.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "locality_prerequisite": d["locality_prerequisite"],
        "selected_seed_superframes": {k:v for k,v in d["selected_seed_superframes"].items() if k not in {"rows","groups_detail"}},
        "charged_economics": d["charged_economics"],
        "referee_profile": d["referee_profile"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
