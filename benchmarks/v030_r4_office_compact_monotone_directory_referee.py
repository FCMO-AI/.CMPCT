from __future__ import annotations

"""Compact monotone locator falsifier for the v0.30 Office three-family locality win.

Mission Lock / Referee
======================
The adjudicated 644 B three-family geometry has only 1,893 B of same-input density margin over
frozen v0.29 and only 382 B of worst-read locality slack. The first concrete serialized-directory
attempt deliberately used one 48 B header per stream/family and 12 B (first,last,absolute_offset)
entries. Before its verdict, its representation already exposed redundant information: group first
keys and physical offsets are monotone, last_key is derivable from the next group boundary for lookup,
and all 82 groups have a deterministic physical order.

Hypothesis
----------
Without changing a single authenticated group byte, encode one global locator in canonical monotone
order. For every stream/family write only delta-coded first_key and delta-coded group-region offset as
canonical uvarints, then compress the complete locator once with the same fixed zlib-9 already used by
CMPCT's research metadata records. Store an identical authenticated primary and tail locator frame and
one fixed 48 B footer/root. A cold selective read receives no free map/cache: it must os.pread the full
primary locator frame plus footer, validate both SHA-256 bindings, locate its group(s), and the exact
stored-byte charge is added to the prior worst whole-group+payload read.

Disproof
--------
The mechanism is false if any existing encoded record cannot be located/recovered exactly from locator
bytes, primary corruption is not rejected with exact tail recovery, group corruption is not detected,
the complete primary locator + footer exceeds the frozen 382 B worst-read slack, or primary+tail+footer
consume the 1,893 B density margin. No locator-size target, group cap, codec level, 4 KiB page, selector,
workload admission or 8x limit may be changed after observing the result. There is no parameter sweep.

A PASS remains diagnostic: payload bytes and semantic ANC1/BST1/SED1 objects are still inherited from
the research prerequisite rather than parsed into a canonical r25 reader. Canonical archive-root trust,
malformed-locator resource bounds, full payload pread, isolated CPU/RSS, held-out transfer and native /
platform parity remain promotion debt.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import zlib

from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_office_three_family_group_locality_referee as THREE
from benchmarks import v030_r4_office_serialized_group_directory_referee as SER

SCHEMA = "cmpct-v030-r4-office-compact-monotone-directory-v1"
PAGE = 4096
LIMIT = 32768
FAMS = ("anchor", "block", "seed")
FAM_ID = {"anchor": 1, "block": 2, "seed": 3}
HDR = SER.HDR
FOOTER = SER.FOOTER


def _read_uvarint(buf: bytes, off: int) -> tuple[int, int]:
    value = 0
    shift = 0
    for _ in range(10):
        if off >= len(buf):
            raise ValueError("truncated uvarint")
        b = buf[off]
        off += 1
        value |= (b & 0x7F) << shift
        if not (b & 0x80):
            return value, off
        shift += 7
    raise ValueError("overlong uvarint")


def _ordered(groups: list[dict]) -> list[dict]:
    return sorted(groups, key=lambda g: (int(g["stream"]), FAM_ID[g["family"]], int(g["index"])))


def _locator_raw(groups: list[dict], rel_off: dict[tuple[int,str,int], int]) -> bytes:
    out = bytearray(b"LOC1")
    streams = sorted({int(g["stream"]) for g in groups})
    out += DEP.uvarint(len(streams))
    for si in streams:
        out += DEP.uvarint(si)
        for fam in FAMS:
            gs = [g for g in groups if int(g["stream"]) == si and g["family"] == fam]
            out += DEP.uvarint(FAM_ID[fam]) + DEP.uvarint(len(gs))
            prev_key = 0
            prev_off = 0
            for n, g in enumerate(gs):
                first = int(g["first"])
                roff = rel_off[(si, fam, int(g["index"]))]
                if n and (first < prev_key or roff < prev_off):
                    raise RuntimeError("non-monotone group ordering")
                out += DEP.uvarint(first - prev_key)
                out += DEP.uvarint(roff - prev_off)
                prev_key, prev_off = first, roff
    return bytes(out)


def _parse_locator(raw: bytes) -> dict[tuple[int,str], list[tuple[int,int]]]:
    if not raw.startswith(b"LOC1"):
        raise ValueError("bad locator magic")
    off = 4
    stream_count, off = _read_uvarint(raw, off)
    result: dict[tuple[int,str], list[tuple[int,int]]] = {}
    id_fam = {v:k for k,v in FAM_ID.items()}
    for _ in range(stream_count):
        si, off = _read_uvarint(raw, off)
        for expected_fam in FAMS:
            fid, off = _read_uvarint(raw, off)
            if fid not in id_fam or id_fam[fid] != expected_fam:
                raise ValueError("locator family order drift")
            count, off = _read_uvarint(raw, off)
            rows = []
            key = 0
            roff = 0
            for _j in range(count):
                dk, off = _read_uvarint(raw, off)
                do, off = _read_uvarint(raw, off)
                key += dk
                roff += do
                rows.append((key, roff))
            result[(si, expected_fam)] = rows
    if off != len(raw):
        raise ValueError("trailing locator bytes")
    return result


def _frame(raw_locator: bytes, group_base: int) -> bytes:
    body = zlib.compress(raw_locator, 9)
    return HDR.pack(b"LOC1", 0, 0, 0, len(body), group_base, hashlib.sha256(body).digest()) + body


def _read_frame(fd: int, off: int) -> tuple[bytes,int,bytes]:
    head = SER._read_exact(fd, HDR.size, off)
    magic, _si, _fam, _count, body_len, group_base, digest = HDR.unpack(head)
    if magic != b"LOC1" or body_len > 1_048_576:
        raise RuntimeError("malformed compact locator header")
    body = SER._read_exact(fd, body_len, off + HDR.size)
    if hashlib.sha256(body).digest() != digest:
        raise ValueError("locator digest mismatch")
    try:
        raw = zlib.decompress(body)
    except zlib.error as exc:
        raise ValueError("locator decompression failed") from exc
    if len(raw) > 1_048_576:
        raise RuntimeError("locator expansion bound exceeded")
    return raw, group_base, head + body


def _locate(rows: list[tuple[int,int]], key: int) -> int:
    candidate = None
    for first, roff in rows:
        if first > key:
            break
        candidate = roff
    if candidate is None:
        raise KeyError(key)
    return candidate


def _serialize(path: Path, groups: list[dict]) -> dict:
    ordered = _ordered(groups)
    rel: dict[tuple[int,str,int], int] = {}
    cursor = 0
    group_bytes = []
    for g in ordered:
        rel[(int(g["stream"]), g["family"], int(g["index"]))] = cursor
        b = SER._group_bytes(g)
        group_bytes.append(b)
        cursor += len(b)

    raw = _locator_raw(groups, rel)
    compressed = zlib.compress(raw, 9)
    primary_size = HDR.size + len(compressed)
    group_base = primary_size
    primary = _frame(raw, group_base)
    if len(primary) != primary_size:
        raise RuntimeError("locator frame size drift")
    tail_off = primary_size + cursor
    footer_off = tail_off + len(primary)
    # Primary and tail frames are identical; the footer trust anchor binds that exact frame.
    root = hashlib.sha256(primary).digest()
    footer = FOOTER.pack(b"FTR1", len(ordered), tail_off, footer_off, root)

    with path.open("wb") as f:
        f.write(primary)
        for b in group_bytes:
            f.write(b)
        f.write(primary)
        f.write(footer)
    return {
        "raw_locator_bytes": len(raw),
        "compressed_locator_body_bytes": len(compressed),
        "locator_frame_bytes": len(primary),
        "primary_offset": 0,
        "tail_offset": tail_off,
        "footer_offset": footer_off,
        "footer_bytes": len(footer),
        "group_base": group_base,
        "group_bytes": cursor,
        "groups": len(ordered),
        "root": root,
        "rel": rel,
    }


def _footer(fd: int, off: int) -> tuple[int,bytes]:
    b = SER._read_exact(fd, FOOTER.size, off)
    magic, _groups, tail, declared, root = FOOTER.unpack(b)
    if magic != b"FTR1" or declared != off:
        raise RuntimeError("malformed locator footer")
    return tail, root


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    prior = THREE.run(work, v029_checkout, worker)
    if not prior["hypothesis"]["three_family_644b_groups_preserve_density_and_8x_locality"]:
        raise RuntimeError("three-family prerequisite no longer passes")

    groups, expected, family_keys = SER._build_groups(work)
    store = work / "compact-monotone-meta.bin"
    layout = _serialize(store, groups)
    prior_group_bytes = int(prior["grouped_storage"]["grouped_sparse_metadata_bytes"]) + int(prior["grouped_storage"]["grouped_selected_seed_bytes"])
    if layout["group_bytes"] != prior_group_bytes:
        raise RuntimeError("group bytes changed under locator experiment")

    recovered = 0
    fd = os.open(store, os.O_RDONLY)
    try:
        tail, root = _footer(fd, layout["footer_offset"])
        raw, group_base, frame = _read_frame(fd, layout["primary_offset"])
        if hashlib.sha256(frame).digest() != root:
            raise RuntimeError("primary locator not bound to footer root")
        loc = _parse_locator(raw)
        for sf, keys in family_keys.items():
            rows = loc[sf]
            for key in keys:
                roff = _locate(rows, key)
                body = SER._read_group(fd, group_base + roff)
                needle = expected[(sf[0], sf[1], key)]
                if needle not in body:
                    raise RuntimeError("locator selected group missing exact encoded record")
                recovered += 1
        raw_t, gb_t, frame_t = _read_frame(fd, tail)
        if gb_t != group_base or frame_t != frame or hashlib.sha256(frame_t).digest() != root or raw_t != raw:
            raise RuntimeError("tail locator is not exact recovery copy")
    finally:
        os.close(fd)

    # Hostile primary corruption: primary fails, tail under the unchanged footer root succeeds.
    bad = bytearray(store.read_bytes())
    bad[HDR.size] ^= 1
    pbad = work / "compact-monotone-primary-corrupt.bin"
    pbad.write_bytes(bad)
    fd = os.open(pbad, os.O_RDONLY)
    try:
        _tail, root = _footer(fd, layout["footer_offset"])
        primary_rejected = False
        try:
            _read_frame(fd, 0)
        except ValueError:
            primary_rejected = True
        raw_tail, _gb, tail_frame = _read_frame(fd, layout["tail_offset"])
        tail_recovers = primary_rejected and hashlib.sha256(tail_frame).digest() == root and raw_tail.startswith(b"LOC1")
    finally:
        os.close(fd)

    # Hostile group corruption remains locally detectable by the unchanged group header/digest.
    first = _ordered(groups)[0]
    first_rel = layout["rel"][(int(first["stream"]), first["family"], int(first["index"]))]
    bad = bytearray(store.read_bytes())
    bad[layout["group_base"] + first_rel + HDR.size] ^= 1
    gbad = work / "compact-monotone-group-corrupt.bin"
    gbad.write_bytes(bad)
    fd = os.open(gbad, os.O_RDONLY)
    try:
        group_corruption_detected = False
        try:
            SER._read_group(fd, layout["group_base"] + first_rel)
        except ValueError:
            group_corruption_detected = True
    finally:
        os.close(fd)

    prior_candidate = int(prior["grouped_storage"]["candidate_plus_grouped_locality_bytes"])
    v029 = int(prior["grouped_storage"]["same_input_v029_bytes"])
    new_storage = 2 * layout["locator_frame_bytes"] + layout["footer_bytes"]
    candidate = prior_candidate + new_storage
    density_margin = v029 - candidate

    prior_worst = int(prior["whole_group_locality"]["worst_fixed_probe"]["combined_bytes"])
    locator_read_charge = layout["locator_frame_bytes"] + layout["footer_bytes"]
    charged_worst = prior_worst + locator_read_charge
    locality_margin = LIMIT - charged_worst
    supported = (
        density_margin > 0 and locality_margin >= 0 and recovered == len(expected)
        and primary_rejected and tail_recovers and group_corruption_detected
    )

    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "source": prior["source"],
        "frozen_v029": prior["frozen_v029"],
        "prerequisite": {
            "candidate_plus_grouped_locality_bytes": prior_candidate,
            "same_input_v029_bytes": v029,
            "density_margin_bytes": int(prior["grouped_storage"]["margin_to_same_input_v029_bytes"]),
            "worst_read_bytes": prior_worst,
            "worst_read_slack_bytes": LIMIT - prior_worst,
            "groups_unchanged": layout["groups"],
            "group_bytes_unchanged": layout["group_bytes"],
        },
        "compact_locator": {
            "raw_locator_bytes": layout["raw_locator_bytes"],
            "compressed_locator_body_bytes": layout["compressed_locator_body_bytes"],
            "locator_frame_bytes_each": layout["locator_frame_bytes"],
            "primary_plus_tail_plus_footer_bytes": new_storage,
            "records_recovered_exactly": recovered,
            "expected_records": len(expected),
            "candidate_bytes_with_locator": candidate,
            "same_input_v029_bytes": v029,
            "density_margin_bytes": density_margin,
        },
        "selective_read": {
            "cold_locator_frame_bytes": layout["locator_frame_bytes"],
            "footer_root_bytes": layout["footer_bytes"],
            "locator_plus_root_charge_bytes": locator_read_charge,
            "prior_worst_group_plus_payload_bytes": prior_worst,
            "charged_worst_read_bytes": charged_worst,
            "locality_limit_bytes": LIMIT,
            "locality_margin_bytes": locality_margin,
            "amplification_vs_4k": charged_worst / PAGE,
        },
        "hostile_controls": {
            "primary_locator_corruption_rejected": primary_rejected,
            "tail_locator_recovery_under_same_root": tail_recovers,
            "group_body_corruption_detected": group_corruption_detected,
        },
        "hypothesis": {
            "compact_monotone_locator_preserves_density_and_8x": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "same_644b_groups": True,
            "same_group_bytes": True,
            "fixed_zlib_level": 9,
            "canonical_uvarint_delta_encoding": True,
            "full_locator_read_and_verified_per_cold_selective_read": True,
            "actual_os_pread_for_locator_and_groups": True,
            "primary_tail_recovery_copy_charged": True,
            "fixed_page_bytes": PAGE,
            "fixed_limit_bytes": LIMIT,
            "no_parameter_or_codec_sweep": True,
            "remaining_debt": "canonical archive-root trust/integration; malformed-locator resource/fuzz matrix; semantic metadata parser objects and full compressed payload pread; isolated CPU/RSS/read throughput; held-out transfer; native/platform parity",
        },
        "next_if_supported": "replace inherited semantic metadata objects with bytes parsed from this locator+group store, pread compressed payload ranges, then attack corruption/resource/held-out/native debt without moving the 8x law",
        "next_if_falsified": "preserve whether storage or cold-read slack failed; do not sweep compression/group caps; redesign physical ownership so locator information is implicit in already-authenticated group/root bytes",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-compact-monotone-directory.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "compact_locator": d["compact_locator"],
        "selective_read": d["selective_read"],
        "hostile_controls": d["hostile_controls"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
