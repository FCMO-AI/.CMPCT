from __future__ import annotations

"""Office sparse-metadata superframe economic referee.

Mission Lock / Referee
======================
The exact same-input referee proved that the admission candidate beats frozen source-sealed
v0.29 by 50,680 B before locality metadata, but loses by 35,785 B after charging the existing
86,465 B independently-framed sparse index. Of those sparse bytes, 31,937 B are compressed
record bodies and 54,528 B are the repeated 48 B authentication/directory charge on 1,136
small records.

Hypothesis
----------
The *same* ANC1/BST1 metadata records, encoded with the *same* per-record zlib-9 payloads,
can be packed into deterministic authenticated metadata superframes whose body is bounded by
one existing 4 KiB page. One 48 B authentication+directory charge is then paid per superframe,
not per tiny record. If this is the dominant exported cost, candidate + grouped sparse metadata
must remain smaller than frozen source-sealed v0.29 on the identical repaired Office tree.

This is not a new compression codec and it does not alter the record information. The referee
reconstructs every ANC1/BST1 zlib stream independently and requires exact length+SHA parity with
the existing cold-reader builder before it may count grouping economics.

Disproof
--------
The hypothesis is false if: any reconstructed metadata record differs from the existing builder;
a single compressed record cannot fit the fixed 4 KiB superframe-body bound; any emitted group
exceeds that bound; candidate + grouped metadata is not smaller than same-input frozen v0.29;
or grouping requires changing page size, the 8x law, stream admission, codec, or record grammar.

A supported economic result still grants NO locality/release credit. A real reader must next
serialize/parse/authenticate these groups from bytes, charge group reads + compressed payload,
prove corruption/recovery behavior and <=8x physical access, and measure CPU/RSS/native parity.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import zlib

from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_same_input_sparse_budget_referee as BASE

SCHEMA = "cmpct-v030-r4-office-sparse-superframe-economic-v1"
GROUP_BODY_LIMIT = COLD.PAGE  # structural: one existing logical page, never swept


def _encoded_records(parsed: dict) -> tuple[list[dict], list[dict]]:
    """Recreate COLD's exact record payloads and preserve its canonical ordering."""
    tokens = parsed["tokens"]
    blocks = parsed["blocks"]
    first_token_bit: list[int | None] = [None] * len(blocks)
    for _start, _length, _distance, bit0, _bit1, bid in tokens:
        if first_token_bit[bid] is None:
            first_token_bit[bid] = bit0

    block_records: list[dict] = []
    for b in blocks:
        fb = first_token_bit[b["id"]]
        if fb is None:
            raise RuntimeError("empty DEFLATE block unsupported by inherited sparse prototype")
        raw = bytearray(b"BST1")
        raw += DEP.uvarint(b["id"])
        raw.append(b["type"])
        raw += DEP.uvarint(b["out_start"])
        raw += DEP.uvarint(b["out_end"] - b["out_start"])
        raw += DEP.uvarint(fb)
        if b["type"] == 2:
            llp = DEP.pack_nibbles(b["ll_lengths"])
            ddp = DEP.pack_nibbles(b["dd_lengths"])
            raw += DEP.uvarint(len(b["ll_lengths"])) + DEP.uvarint(len(llp)) + llp
            raw += DEP.uvarint(len(b["dd_lengths"])) + DEP.uvarint(len(ddp)) + ddp
        enc = zlib.compress(bytes(raw), 9)
        block_records.append({
            "kind": "block",
            "key": b["id"],
            "encoded": enc,
            "sha256": hashlib.sha256(enc).hexdigest(),
        })

    pages = (parsed["output_bytes"] + COLD.PAGE - 1) // COLD.PAGE
    anchor_records: list[dict] = []
    ti = 0
    for page in range(pages):
        pos = page * COLD.PAGE
        while ti + 1 < len(tokens) and tokens[ti][0] + tokens[ti][1] <= pos:
            ti += 1
        start, length, _distance, bit0, _bit1, bid = tokens[ti]
        if not (start <= pos < start + length):
            raise RuntimeError("failed to locate page token anchor")
        raw = b"ANC1" + DEP.uvarint(page) + DEP.uvarint(start) + DEP.uvarint(bit0) + DEP.uvarint(bid)
        enc = zlib.compress(raw, 9)
        anchor_records.append({
            "kind": "anchor",
            "key": page,
            "encoded": enc,
            "sha256": hashlib.sha256(enc).hexdigest(),
        })
    return block_records, anchor_records


def _assert_inherited_parity(parsed: dict, block_records: list[dict], anchor_records: list[dict]) -> tuple[list[dict], list[dict], int]:
    anchors, blocks, stored = COLD._build_metadata(parsed)
    if len(block_records) != len(blocks) or len(anchor_records) != len(anchors):
        raise RuntimeError("reconstructed sparse record count differs from inherited builder")
    for ours, inherited in zip(block_records, blocks, strict=True):
        if ours["key"] != inherited["id"]:
            raise RuntimeError("block record order/key drift")
        if len(ours["encoded"]) + COLD.FRAME_TAX != inherited["frame_bytes"]:
            raise RuntimeError("block encoded length drift")
        if ours["sha256"] != inherited["frame_sha256"]:
            raise RuntimeError("block encoded bytes drift")
    for ours, inherited in zip(anchor_records, anchors, strict=True):
        if ours["key"] != inherited["page"]:
            raise RuntimeError("anchor record order/key drift")
        if len(ours["encoded"]) + COLD.FRAME_TAX != inherited["frame_bytes"]:
            raise RuntimeError("anchor encoded length drift")
        if ours["sha256"] != inherited["frame_sha256"]:
            raise RuntimeError("anchor encoded bytes drift")
    return anchors, blocks, stored


def _pack_kind(records: list[dict], stream_sha256: str, kind: str) -> list[dict]:
    """Pack concatenated self-terminating zlib streams under a fixed 4 KiB body ceiling."""
    groups: list[dict] = []
    body = bytearray()
    keys: list[int] = []

    def flush() -> None:
        nonlocal body, keys
        if not body:
            return
        if len(body) > GROUP_BODY_LIMIT:
            raise RuntimeError("superframe body exceeded fixed page bound")
        groups.append({
            "stream_sha256": stream_sha256,
            "kind": kind,
            "first_key": keys[0],
            "last_key": keys[-1],
            "records": len(keys),
            "body_bytes": len(body),
            "stored_bytes": len(body) + COLD.FRAME_TAX,
            "body_sha256": hashlib.sha256(body).hexdigest(),
        })
        body = bytearray()
        keys = []

    for rec in records:
        enc = rec["encoded"]
        if len(enc) > GROUP_BODY_LIMIT:
            raise RuntimeError("one inherited sparse record exceeds fixed superframe body bound")
        if body and len(body) + len(enc) > GROUP_BODY_LIMIT:
            flush()
        body += enc
        keys.append(int(rec["key"]))
    flush()
    return groups


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)

    # Reuse the previous exact same-input court unchanged. It leaves the measured current artifact
    # under work/current, which this referee inspects rather than rebuilding with different semantics.
    base = BASE.run(work, v029_checkout, worker)
    if base["hypothesis"]["current_individual_frame_sparse_metadata_fits_same_input_margin"]:
        raise RuntimeError("prerequisite collision disappeared; superframe rehabilitation no longer justified")
    if not base["hypothesis"]["current_smaller_than_v029_before_locality_metadata"]:
        raise RuntimeError("current admission candidate no longer has a same-input density win to preserve")

    manifest = json.loads((work / "current" / "manifest.json").read_text())
    pool = (work / "current" / "streams.bin").read_bytes()
    hashes = sorted({rec["stream_hash"] for rec in manifest["derived"].values()})

    all_groups: list[dict] = []
    rows: list[dict] = []
    exact_record_body_total = 0
    inherited_sparse_total = 0
    inherited_record_count = 0

    for h in hashes:
        s = manifest["stream_index"][h]
        comp = pool[s["o"] : s["o"] + s["n"]]
        parsed = DEP.parse_tokens(comp)
        raw = zlib.decompress(comp, -15)
        if parsed["output_bytes"] != len(raw):
            raise RuntimeError("DEFLATE parse/output mismatch")

        block_records, anchor_records = _encoded_records(parsed)
        anchors, blocks, inherited_stored = _assert_inherited_parity(parsed, block_records, anchor_records)
        groups = _pack_kind(block_records, h, "block") + _pack_kind(anchor_records, h, "anchor")
        body = sum(len(r["encoded"]) for r in block_records) + sum(len(r["encoded"]) for r in anchor_records)
        grouped = sum(g["stored_bytes"] for g in groups)
        records = len(block_records) + len(anchor_records)

        exact_record_body_total += body
        inherited_sparse_total += inherited_stored
        inherited_record_count += records
        all_groups.extend(groups)
        rows.append({
            "stream_sha256": h,
            "compressed_bytes": len(comp),
            "raw_bytes": len(raw),
            "anchors": len(anchors),
            "block_states": len(blocks),
            "records": records,
            "compressed_record_body_bytes": body,
            "inherited_individual_frame_bytes": inherited_stored,
            "superframes": len(groups),
            "superframe_bytes": grouped,
            "superframe_tax_bytes": len(groups) * COLD.FRAME_TAX,
            "largest_superframe_body_bytes": max(g["body_bytes"] for g in groups),
        })

    if exact_record_body_total != base["sparse_metadata"]["compressed_record_body_bytes"]:
        raise RuntimeError("record-body total does not match exact prerequisite receipt")
    if inherited_sparse_total != base["sparse_metadata"]["stored_bytes"]:
        raise RuntimeError("inherited sparse total does not match exact prerequisite receipt")
    if inherited_record_count != base["sparse_metadata"]["records"]:
        raise RuntimeError("record count does not match exact prerequisite receipt")

    grouped_tax = len(all_groups) * COLD.FRAME_TAX
    grouped_sparse = exact_record_body_total + grouped_tax
    current_bytes = int(base["current_admission"]["stored_bytes"])
    v029_bytes = int(base["frozen_v029"]["stored_bytes"])
    charged = current_bytes + grouped_sparse
    margin = v029_bytes - charged
    max_body = max(g["body_bytes"] for g in all_groups)
    max_stored = max(g["stored_bytes"] for g in all_groups)
    supported = margin > 0 and max_body <= GROUP_BODY_LIMIT

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "source": base["source"],
        "frozen_v029": {
            "source_sha": base["frozen_v029"]["frozen_source_sha"],
            "source_sealed": base["frozen_v029"]["source_sealed"],
            "reconstruction_exact": base["frozen_v029"]["reconstruction_exact"],
            "stored_bytes": v029_bytes,
        },
        "current_admission": {
            "stored_bytes": current_bytes,
            "exact": base["current_admission"]["exact"],
            "tree_sha256": base["current_admission"]["tree_sha256"],
            "create_cpu_s": base["current_admission"]["create_cpu_s"],
            "create_wall_s": base["current_admission"]["create_wall_s"],
            "hosted_process_peak_rss_bytes": base["current_admission"]["hosted_process_peak_rss_bytes"],
        },
        "prerequisite_collision": {
            "direct_margin_bytes": base["direct_same_input_density"]["current_margin_bytes"],
            "individual_frame_sparse_bytes": inherited_sparse_total,
            "individual_frame_charged_margin_bytes": base["charged_economics"]["margin_to_same_input_v029_bytes"],
            "records": inherited_record_count,
            "record_body_bytes": exact_record_body_total,
            "repeated_frame_tax_bytes": base["sparse_metadata"]["per_record_auth_directory_tax_bytes"],
        },
        "superframe": {
            "body_limit_bytes": GROUP_BODY_LIMIT,
            "auth_directory_tax_bytes_per_group": COLD.FRAME_TAX,
            "groups": len(all_groups),
            "record_body_bytes_unchanged": exact_record_body_total,
            "group_tax_bytes": grouped_tax,
            "stored_sparse_metadata_bytes": grouped_sparse,
            "largest_group_body_bytes": max_body,
            "largest_group_stored_bytes": max_stored,
            "max_two_group_metadata_touch_bytes": 2 * max_stored,
            "rows": rows,
            "groups_detail": all_groups,
        },
        "charged_economics": {
            "candidate_plus_grouped_sparse_bytes": charged,
            "margin_to_same_input_v029_bytes": margin,
            "saved_vs_individual_sparse_bytes": inherited_sparse_total - grouped_sparse,
        },
        "hypothesis": {
            "same_record_payloads_reproduced_exactly": True,
            "all_group_bodies_within_fixed_page_bound": max_body <= GROUP_BODY_LIMIT,
            "grouped_sparse_metadata_fits_same_input_margin": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "fixed_page_bytes": COLD.PAGE,
            "fixed_8x_law": True,
            "same_record_grammar": True,
            "same_per_record_zlib_payloads": True,
            "same_admission_candidate": True,
            "frozen_v029_source_sealed": True,
            "no_parameter_or_codec_sweep": True,
            "integrity_grouping_not_yet_productized": True,
            "recovery_grouping_not_yet_productized": True,
        },
        "next_if_supported": "serialize authenticated 4KiB metadata superframes and run a cold byte-source reader; charge whole groups, payload pread, auth root/proofs, recovery, CPU and RSS under the unchanged 8x law",
        "next_if_falsified": "preserve the proof-traffic lower bound and abandon simple sparse-record grouping; seek a lower-information locality index without changing 4KiB/8x semantics",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-sparse-superframe-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-sparse-superframe.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "prerequisite_collision": d["prerequisite_collision"],
        "superframe": {k: v for k, v in d["superframe"].items() if k not in {"rows", "groups_detail"}},
        "charged_economics": d["charged_economics"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
