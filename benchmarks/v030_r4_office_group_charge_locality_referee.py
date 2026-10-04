from __future__ import annotations

"""Office whole-superframe locality referee.

Mission Lock / Referee
======================
Economic referees show that amortizing the 48 B digest+directory tax can make the same-input Office
admission candidate fit below source-sealed v0.29. The branch-and-bound seed referee separately shows
that selected page seeds can close logical/physical reconstruction under the fixed 8x law when metadata
is charged as independently addressable records.

Those two facts do NOT imply one physical candidate: grouping records reduces stored bytes but may
increase selective-read I/O because touching one record can require fetching its whole superframe.

Hypothesis
----------
Keep the exact same ANC1/BST1 records, locality-debt seed selector and exact selected SED1 records.
Pack each record family per stream in deterministic <=4 KiB superframes. For every fixed <=4 KiB
Office probe and every adjacent-page superset, run the unchanged COLD/SEED reconstruction, then charge
unique compressed payload bytes PLUS the complete stored bytes of every metadata superframe containing
an anchor/block/seed record actually touched by that read. A group is charged once even if several of
its records are used. The result must be byte-exact, <=32,768 B, and the same-input stored candidate
must remain below source-sealed v0.29.

Disproof
--------
Any exactness failure, whole-group charged read >32,768 B, grouped stored candidate >= v0.29, or change
of page size/8x/admission/codec/selector falsifies this 4 KiB grouping geometry. No group-size sweep is
allowed. If locality fails, the excess itself defines the next causal bound; do not relax 8x.

This remains an intermediate physical-accounting referee: groups are represented by exact bytes and
record->group maps built by the benchmark, not yet read with os.pread from a canonical archive. A pass
still owes serialization/parser corruption tests, authenticated root/proofs, recovery, actual seeks,
fresh-process CPU/RSS, native/platform parity and held-out transfer.
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
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED
from benchmarks import v030_r4_office_sparse_anchor_cold_reader_transfer as TRANSFER
from benchmarks import v030_r4_office_sparse_superframe_economic_referee as SUPER
from benchmarks import v030_r4_office_gated_seed_superframe_economic_referee as SEEDGROUP

SCHEMA = "cmpct-v030-r4-office-group-charge-locality-v1"
PAGE = COLD.PAGE
LIMIT = 8 * PAGE


def _pack_map(records: list[tuple[int, bytes]], prefix: str) -> tuple[dict[int, str], dict[str, int], int]:
    groups: list[tuple[str, list[int], bytes]] = []
    keys: list[int] = []
    body = bytearray()

    def flush() -> None:
        nonlocal keys, body
        if not body:
            return
        gid = f"{prefix}:{len(groups)}"
        groups.append((gid, list(keys), bytes(body)))
        keys = []
        body = bytearray()

    for key, enc in records:
        if len(enc) > PAGE:
            raise RuntimeError("single metadata record exceeds 4 KiB group body")
        if body and len(body) + len(enc) > PAGE:
            flush()
        body += enc
        keys.append(key)
    flush()

    key_to_group: dict[int, str] = {}
    group_cost: dict[str, int] = {}
    total = 0
    for gid, gkeys, gbody in groups:
        if len(gbody) > PAGE:
            raise RuntimeError("metadata group exceeds fixed body bound")
        cost = len(gbody) + COLD.FRAME_TAX
        total += cost
        group_cost[gid] = cost
        for k in gkeys:
            if k in key_to_group:
                raise RuntimeError("duplicate metadata key in grouping")
            key_to_group[k] = gid
    return key_to_group, group_cost, total


def _seed_enc(page: int, anchor: dict, parsed: dict, raw: bytes) -> bytes | None:
    return SEEDGROUP._encode_seed_record(page, anchor, parsed, raw)


def _charge_groups(reader, amap, bmap, smap, costs) -> int:
    gids: set[str] = set()
    for p in reader.anchor_frames:
        gids.add(amap[p])
    for bid in reader.block_frames:
        gids.add(bmap[bid])
    if isinstance(reader, SEED.SeedReader):
        for p in reader.seed_frames:
            gids.add(smap[p])
    return sum(costs[g] for g in gids)


def _rss_bytes() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    t0c = time.process_time()
    t0w = time.perf_counter()

    economic = SEEDGROUP.run(work, v029_checkout, worker)
    if not economic["hypothesis"]["exact_selected_seed_records_group_within_same_input_density_margin"]:
        raise RuntimeError("gated-seed grouped economics prerequisite is not supported")

    manifest = json.loads((work / "current" / "manifest.json").read_text())
    pool = (work / "current" / "streams.bin").read_bytes()
    hashes = sorted({rec["stream_hash"] for rec in manifest["derived"].values()})

    exact_failures = 0
    locality_failures = 0
    pair_failures = 0
    fixed_requests = 0
    pair_requests = 0
    worst_probe = None
    worst_pair = None
    grouped_sparse_total = 0
    grouped_seed_total = 0
    rows = []

    for si, h in enumerate(hashes):
        s = manifest["stream_index"][h]
        comp = pool[s["o"] : s["o"] + s["n"]]
        parsed = DEP.parse_tokens(comp)
        raw = zlib.decompress(comp, -15)
        anchors, blocks, _old_sparse = COLD._build_metadata(parsed)
        seeds, _all_seed, _logical_seed = SEED._build_seeds(parsed, anchors, raw)

        brecs, arecs = SUPER._encoded_records(parsed)
        block_records = [(int(r["key"]), r["encoded"]) for r in brecs]
        anchor_records = [(int(r["key"]), r["encoded"]) for r in arecs]
        bmap, bcost, btotal = _pack_map(block_records, f"s{si}:b")
        amap, acost, atotal = _pack_map(anchor_records, f"s{si}:a")
        if btotal + atotal != sum(
            r["superframe_bytes"] for r in economic["locality_prerequisite"].get("rows", [])
        ) if False else btotal + atotal:
            pass  # structural placeholder intentionally unreachable; exact global parity asserted below.

        pages = len(anchors)
        unsafe: set[int] = set()
        selected_pages: set[int] = set()
        for p in range(pages):
            a = p * PAGE
            b = min(len(raw), min(pages, p + 2) * PAGE)
            r = COLD.ColdReader(comp, anchors, blocks, len(raw))
            if r.read(a, b) != raw[a:b]:
                raise RuntimeError("classifier exactness drift")
            if r.metadata_bytes() + r.payload_bytes() > LIMIT:
                unsafe.add(p)
                selected_pages.add(p)
                if p + 1 < pages:
                    selected_pages.add(p + 1)

        seed_records: list[tuple[int, bytes]] = []
        gated_seeds = [None] * pages
        for p in sorted(selected_pages):
            if seeds[p] is None:
                continue
            enc = _seed_enc(p, anchors[p], parsed, raw)
            if enc is None or hashlib.sha256(enc).hexdigest() != seeds[p]["frame_sha256"]:
                raise RuntimeError("seed record parity drift")
            seed_records.append((p, enc))
            gated_seeds[p] = seeds[p]
        smap, scost, stotal = _pack_map(seed_records, f"s{si}:s")

        costs = {**bcost, **acost, **scost}
        grouped_sparse_total += btotal + atotal
        grouped_seed_total += stotal
        stream_worst = 0
        stream_pair_worst = 0

        # Adjacent page-pair sufficient-condition surface under WHOLE-GROUP accounting.
        for p in range(pages):
            a = p * PAGE
            b = min(len(raw), min(pages, p + 2) * PAGE)
            seed_mode = p in unsafe
            r = SEED.SeedReader(comp, anchors, blocks, gated_seeds, len(raw)) if seed_mode else COLD.ColdReader(comp, anchors, blocks, len(raw))
            got = r.read(a, b)
            combined = r.payload_bytes() + _charge_groups(r, amap, bmap, smap, costs)
            pair_requests += 1
            if got != raw[a:b] or combined > LIMIT:
                pair_failures += 1
            stream_pair_worst = max(stream_pair_worst, combined)
            q = {"stream_sha256": h, "pair_start_page": p, "combined_bytes": combined,
                 "amplification_vs_4k_contract": combined / PAGE, "seed_mode": seed_mode,
                 "payload_bytes": r.payload_bytes(), "group_metadata_bytes": combined-r.payload_bytes()}
            if worst_pair is None or combined > worst_pair["combined_bytes"]:
                worst_pair = q

        # Inherited fixed aligned/tail/boundary hostile surface.
        for start in TRANSFER._starts(len(raw)):
            end = min(start + PAGE, len(raw))
            p0 = start // PAGE
            p1 = (end - 1) // PAGE
            seed_mode = (p0 in unsafe) if p1 != p0 else (p0 in unsafe or (p0 > 0 and (p0 - 1) in unsafe))
            r = SEED.SeedReader(comp, anchors, blocks, gated_seeds, len(raw)) if seed_mode else COLD.ColdReader(comp, anchors, blocks, len(raw))
            got = r.read(start, end)
            payload = r.payload_bytes()
            meta = _charge_groups(r, amap, bmap, smap, costs)
            combined = payload + meta
            fixed_requests += 1
            if got != raw[start:end]:
                exact_failures += 1
            if combined > LIMIT:
                locality_failures += 1
            stream_worst = max(stream_worst, combined)
            q = {"stream_sha256": h, "start": start, "end": end, "combined_bytes": combined,
                 "amplification": combined / max(1,end-start), "seed_mode": seed_mode,
                 "payload_bytes": payload, "group_metadata_bytes": meta}
            if worst_probe is None or combined > worst_probe["combined_bytes"]:
                worst_probe = q

        rows.append({
            "stream_sha256": h,
            "pages": pages,
            "unsafe_pairs": len(unsafe),
            "selected_seed_records": len(seed_records),
            "sparse_grouped_bytes": btotal + atotal,
            "seed_grouped_bytes": stotal,
            "worst_pair_bytes": stream_pair_worst,
            "worst_fixed_probe_bytes": stream_worst,
        })

    expected_sparse = int(economic["charged_economics"]["grouped_sparse_metadata_bytes"])
    expected_seed = int(economic["charged_economics"]["grouped_selected_seed_bytes"])
    if grouped_sparse_total != expected_sparse:
        raise RuntimeError(f"sparse group-byte parity drift {grouped_sparse_total} != {expected_sparse}")
    if grouped_seed_total != expected_seed:
        raise RuntimeError(f"seed group-byte parity drift {grouped_seed_total} != {expected_seed}")

    current = int(economic["charged_economics"]["candidate_before_locality_metadata_bytes"])
    v029 = int(economic["charged_economics"]["same_input_v029_bytes"])
    candidate = current + grouped_sparse_total + grouped_seed_total
    margin = v029 - candidate
    supported = exact_failures == 0 and locality_failures == 0 and pair_failures == 0 and margin > 0

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "source": economic["source"],
        "frozen_v029": economic["frozen_v029"],
        "grouped_storage": {
            "candidate_before_locality_metadata_bytes": current,
            "grouped_sparse_metadata_bytes": grouped_sparse_total,
            "grouped_selected_seed_bytes": grouped_seed_total,
            "candidate_plus_grouped_locality_bytes": candidate,
            "same_input_v029_bytes": v029,
            "margin_to_same_input_v029_bytes": margin,
        },
        "whole_group_locality": {
            "fixed_requests": fixed_requests,
            "pair_requests": pair_requests,
            "exact_failures": exact_failures,
            "locality_failures": locality_failures,
            "pair_failures": pair_failures,
            "worst_fixed_probe": worst_probe,
            "worst_page_pair": worst_pair,
            "rows": rows,
        },
        "profile": {
            "cpu_s_including_prerequisites": time.process_time()-t0c,
            "wall_s_including_prerequisites": time.perf_counter()-t0w,
            "hosted_process_peak_rss_bytes": _rss_bytes(),
        },
        "hypothesis": {"whole_group_accounting_preserves_density_and_8x_locality": supported},
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "fixed_page_bytes": PAGE,
            "fixed_limit_bytes": LIMIT,
            "same_records": True,
            "same_seed_selector": True,
            "whole_touched_groups_charged": True,
            "no_parameter_or_codec_sweep": True,
            "remaining_debt": "serialize+pread these exact groups; parser corruption and auth-root/proof/recovery; isolated creation/read CPU/RSS; held-out hostile transfer; native/platform parity",
        },
        "next_if_supported": "serialize exact grouped metadata store with conservative directory+SHA256 semantics and execute it through actual pread before any selector admission",
        "next_if_falsified": "derive a smaller group-body bound from measured locality slack and retest one causally derived geometry; do not sweep or relax 8x",
    }


def _rss_bytes() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument('--work-root',type=Path,default=Path('benchmark-artifacts/v030-r4-office-group-charge-work'))
    p.add_argument('--v029-checkout',type=Path,required=True)
    p.add_argument('--worker',type=Path,default=Path('benchmarks/v030_r4_frozen_v029_product_worker.py'))
    p.add_argument('--output',type=Path,default=Path('benchmark-artifacts/v030-r4-office-group-charge-locality.json'))
    a=p.parse_args()
    d=run(a.work_root,a.v029_checkout,a.worker)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'grouped_storage':d['grouped_storage'],'whole_group_locality':{k:v for k,v in d['whole_group_locality'].items() if k!='rows'},'profile':d['profile'],'hypothesis':d['hypothesis']},sort_keys=True))

if __name__=='__main__':
    main()
