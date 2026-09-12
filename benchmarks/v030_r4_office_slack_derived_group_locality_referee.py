from __future__ import annotations

"""Office slack-derived metadata-group locality referee.

Mission Lock / Referee
======================
The exact-head whole-group referee at 22085c6c1dbcb01df3c7917bea7e9c61b09fc3e2
preserved same-input density but falsified the 8x locality hypothesis narrowly: the worst
4 KiB request touched 30,690 B of compressed payload plus 4,136 B of grouped metadata,
for 34,826 B total (8.50244140625x) against the frozen 32,768 B limit.

Hypothesis
----------
The failure is caused by the 4 KiB metadata grouping geometry, not by the sparse/seed
information itself. Freeze the observed worst payload at 30,690 B. The fixed locality law
therefore leaves 2,078 B for all metadata in that request. With the unchanged 48 B frame
tax, derive exactly one new body bound: 2,030 B. Repack the exact same ANC1/BST1/selected
SED1 records with this body cap, preserve the same seed selector, page size, codec,
admission policy, source-sealed v0.29 comparator and whole-group charging, then rerun the
complete 1,800 fixed-probe and 908 adjacent-page-pair surface.

Disproof
--------
Any reconstruction error, any charged read above 32,768 B, or loss of the same-input
stored-byte win falsifies this derived geometry. No group-size sweep, threshold search,
codec change or 8x relaxation is allowed. In particular, splitting a 4 KiB group may make
a read touch more groups; this referee charges that consequence rather than assuming the
2,030 B arithmetic is sufficient.

A pass remains research evidence only. It still owes a serialized authenticated metadata
store, actual pread/seek accounting, corruption/recovery tests, isolated creation/read
CPU/RSS, held-out transfer, native/platform parity and full release authority.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import zlib

from benchmarks import v030_r4_office_group_charge_locality_referee as BASE

SCHEMA = "cmpct-v030-r4-office-slack-derived-group-locality-v1"
PRIOR_RECEIPT_SHA = "22085c6c1dbcb01df3c7917bea7e9c61b09fc3e2"
PRIOR_WORST_PAYLOAD_BYTES = 30_690
PRIOR_WORST_GROUP_METADATA_BYTES = 4_136
PRIOR_WORST_COMBINED_BYTES = 34_826
LOCALITY_LIMIT_BYTES = 32_768
FRAME_TAX_BYTES = BASE.COLD.FRAME_TAX
METADATA_ALLOWANCE_BYTES = LOCALITY_LIMIT_BYTES - PRIOR_WORST_PAYLOAD_BYTES
DERIVED_GROUP_BODY_LIMIT = METADATA_ALLOWANCE_BYTES - FRAME_TAX_BYTES

if DERIVED_GROUP_BODY_LIMIT != 2_030:
    raise RuntimeError("slack-derived group-body invariant drift")


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
        if len(enc) > DERIVED_GROUP_BODY_LIMIT:
            # A single exact record cannot be split without changing the representation.
            # Fail closed rather than silently exempting it from the preregistered geometry.
            raise RuntimeError(
                f"single metadata record {len(enc)} exceeds derived {DERIVED_GROUP_BODY_LIMIT} B body bound"
            )
        if body and len(body) + len(enc) > DERIVED_GROUP_BODY_LIMIT:
            flush()
        body += enc
        keys.append(key)
    flush()

    key_to_group: dict[int, str] = {}
    group_cost: dict[str, int] = {}
    total = 0
    for gid, gkeys, gbody in groups:
        if len(gbody) > DERIVED_GROUP_BODY_LIMIT:
            raise RuntimeError("derived metadata group exceeds fixed body bound")
        cost = len(gbody) + FRAME_TAX_BYTES
        total += cost
        group_cost[gid] = cost
        for key in gkeys:
            if key in key_to_group:
                raise RuntimeError("duplicate metadata key in grouping")
            key_to_group[key] = gid
    return key_to_group, group_cost, total


def _derived_group_totals(work: Path) -> tuple[int, int]:
    manifest = json.loads((work / "current" / "manifest.json").read_text())
    pool = (work / "current" / "streams.bin").read_bytes()
    hashes = sorted({rec["stream_hash"] for rec in manifest["derived"].values()})
    sparse_total = 0
    seed_total = 0

    for si, h in enumerate(hashes):
        s = manifest["stream_index"][h]
        comp = pool[s["o"] : s["o"] + s["n"]]
        parsed = BASE.DEP.parse_tokens(comp)
        raw = zlib.decompress(comp, -15)
        anchors, blocks, _ = BASE.COLD._build_metadata(parsed)
        seeds, _all_seed, _logical_seed = BASE.SEED._build_seeds(parsed, anchors, raw)

        brecs, arecs = BASE.SUPER._encoded_records(parsed)
        block_records = [(int(r["key"]), r["encoded"]) for r in brecs]
        anchor_records = [(int(r["key"]), r["encoded"]) for r in arecs]
        _bmap, _bcost, btotal = _pack_map(block_records, f"s{si}:b")
        _amap, _acost, atotal = _pack_map(anchor_records, f"s{si}:a")
        sparse_total += btotal + atotal

        pages = len(anchors)
        selected_pages: set[int] = set()
        for p in range(pages):
            a = p * BASE.PAGE
            b = min(len(raw), min(pages, p + 2) * BASE.PAGE)
            reader = BASE.COLD.ColdReader(comp, anchors, blocks, len(raw))
            if reader.read(a, b) != raw[a:b]:
                raise RuntimeError("classifier exactness drift")
            if reader.metadata_bytes() + reader.payload_bytes() > BASE.LIMIT:
                selected_pages.add(p)
                if p + 1 < pages:
                    selected_pages.add(p + 1)

        seed_records: list[tuple[int, bytes]] = []
        for p in sorted(selected_pages):
            if seeds[p] is None:
                continue
            enc = BASE._seed_enc(p, anchors[p], parsed, raw)
            if enc is None or hashlib.sha256(enc).hexdigest() != seeds[p]["frame_sha256"]:
                raise RuntimeError("seed record parity drift")
            seed_records.append((p, enc))
        _smap, _scost, stotal = _pack_map(seed_records, f"s{si}:s")
        seed_total += stotal

    return sparse_total, seed_total


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    original_pack = BASE._pack_map
    original_seedgroup_run = BASE.SEEDGROUP.run

    def patched_seedgroup_run(*args, **kwargs):
        economic = original_seedgroup_run(*args, **kwargs)
        sparse_total, seed_total = _derived_group_totals(work)
        economic["charged_economics"]["grouped_sparse_metadata_bytes"] = sparse_total
        economic["charged_economics"]["grouped_selected_seed_bytes"] = seed_total
        return economic

    BASE._pack_map = _pack_map
    BASE.SEEDGROUP.run = patched_seedgroup_run
    try:
        result = BASE.run(work, v029_checkout, worker)
    finally:
        BASE._pack_map = original_pack
        BASE.SEEDGROUP.run = original_seedgroup_run

    base_hypothesis = bool(result["hypothesis"]["whole_group_accounting_preserves_density_and_8x_locality"])
    result["schema"] = SCHEMA
    result["derived_geometry"] = {
        "prior_receipt_sha": PRIOR_RECEIPT_SHA,
        "prior_worst_payload_bytes": PRIOR_WORST_PAYLOAD_BYTES,
        "prior_worst_group_metadata_bytes": PRIOR_WORST_GROUP_METADATA_BYTES,
        "prior_worst_combined_bytes": PRIOR_WORST_COMBINED_BYTES,
        "fixed_locality_limit_bytes": LOCALITY_LIMIT_BYTES,
        "metadata_allowance_bytes": METADATA_ALLOWANCE_BYTES,
        "unchanged_frame_tax_bytes": FRAME_TAX_BYTES,
        "derived_group_body_limit_bytes": DERIVED_GROUP_BODY_LIMIT,
        "parameter_sweep": False,
    }
    result["hypothesis"] = {
        "slack_derived_2030b_groups_preserve_density_and_8x_locality": base_hypothesis
    }
    result["contract"]["derived_from_prior_measured_slack"] = True
    result["contract"]["group_body_limit_bytes"] = DERIVED_GROUP_BODY_LIMIT
    result["contract"]["release_credit"] = False
    result["contract"]["locality_credit"] = False
    result["next_if_supported"] = (
        "serialize this exact 2030 B grouped metadata geometry with conservative authenticated directory/root semantics, "
        "then execute actual pread reads before selector admission"
    )
    result["next_if_falsified"] = (
        "preserve the negative and inspect whether failure comes from multi-group fanout or density tax; "
        "do not sweep group sizes or relax 8x"
    )
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-slack-derived-group-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-slack-derived-group-locality.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "derived_geometry": d["derived_geometry"],
        "grouped_storage": d["grouped_storage"],
        "whole_group_locality": {k: v for k, v in d["whole_group_locality"].items() if k != "rows"},
        "profile": d["profile"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
