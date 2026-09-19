from __future__ import annotations

"""Concrete serialized-directory falsifier for the v0.30 Office three-family locality win.

Mission Lock / Referee
======================
The exact-head three-family receipt at 7ab14e2d78377b97b5357879b9d6a9ca1b80384a
put the same-input Office candidate at 5,952,133 B, only 1,893 B below frozen v0.29,
while the worst 4 KiB read touched 32,386 B, only 382 B below the frozen 32,768 B
(8x) limit. That receipt charged 48 B per metadata group but still gifted the map from
(anchor/block/seed key) to physical group.

Hypothesis
----------
A deliberately simple, self-contained physical directory can make that map real without
changing the exact 644 B three-family grouping: one 12 B (first_key,last_key,absolute_offset)
entry per group, one 48 B SHA-256 directory header per stream/family, an authenticated tail
copy of every directory, and one fixed 48 B footer/root locator. Group records themselves use
an exact 48 B header containing identity, body length and SHA-256, so their stored bytes are
byte-for-byte equal to the 48 B tax already charged by the prior referee.

For every group, write actual bytes, locate it only through bytes read with os.pread, verify
its SHA-256, and recover its exact constituent encoded records. Corrupt one primary directory
and require fallback to the authenticated tail copy; corrupt one group body and require local
integrity failure. Recompute same-input stored bytes and conservatively charge, for each prior
selective read, the footer once plus every complete primary directory needed by the three
metadata families in addition to the already measured group+payload bytes.

Disproof
--------
The representation is falsified if serialized group bytes differ from the prior accounting,
any record cannot be recovered exactly, primary-directory corruption does not recover from the
tail, group corruption is not detected, total stored bytes are >= frozen v0.29, or the charged
4 KiB read exceeds 32,768 B. No directory compression, varint packing, caching assumption,
group-size change, threshold sweep or 8x relaxation is allowed after seeing the result.

This is intentionally a cheap lower-complexity gate before building a product reader. A FAIL
means the free-map debt is material and the next design must remove or amortize it structurally;
a PASS would still owe canonical integration, full payload pread, parser/resource attacks,
fresh-process CPU/RSS, held-out transfer and native/platform parity.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import zlib

from benchmarks import v030_r4_office_three_family_group_locality_referee as THREE
from benchmarks import v030_r4_office_group_charge_locality_referee as BASE

SCHEMA = "cmpct-v030-r4-office-serialized-group-directory-v1"
GROUP_BODY_LIMIT = THREE.DERIVED_GROUP_BODY_LIMIT
LIMIT = THREE.LOCALITY_LIMIT_BYTES
PAGE = 4096
HDR = struct.Struct(">4sBBHII32s")  # exactly the already-charged 48 B group/header tax
DIRENT = struct.Struct(">III")       # first_key, last_key, absolute group offset
FOOTER = struct.Struct(">4sIII32s")  # 48 B fixed tail locator/root record
assert HDR.size == 48 and FOOTER.size == 48 and DIRENT.size == 12
FAMILY = {"anchor": 1, "block": 2, "seed": 3}


def _pack(records: list[tuple[int, bytes]], stream_i: int, family: str) -> list[dict]:
    groups: list[dict] = []
    keys: list[int] = []
    body = bytearray()

    def flush() -> None:
        nonlocal keys, body
        if not body:
            return
        if len(body) > GROUP_BODY_LIMIT:
            raise RuntimeError("group body exceeds frozen 644 B geometry")
        groups.append({
            "stream": stream_i,
            "family": family,
            "index": len(groups),
            "first": keys[0],
            "last": keys[-1],
            "keys": list(keys),
            "body": bytes(body),
        })
        keys = []
        body = bytearray()

    for key, enc in records:
        if len(enc) > GROUP_BODY_LIMIT:
            raise RuntimeError("single record exceeds frozen group geometry")
        if body and len(body) + len(enc) > GROUP_BODY_LIMIT:
            flush()
        keys.append(int(key))
        body += enc
    flush()
    return groups


def _group_bytes(g: dict) -> bytes:
    body = g["body"]
    head = HDR.pack(
        b"GRP1", g["stream"], FAMILY[g["family"]], g["index"],
        len(body), g["first"], hashlib.sha256(body).digest(),
    )
    return head + body


def _dir_header(stream_i: int, family: str, count: int, body: bytes) -> bytes:
    return HDR.pack(b"DIR1", stream_i, FAMILY[family], count, len(body), 0, hashlib.sha256(body).digest())


def _read_exact(fd: int, n: int, off: int) -> bytes:
    b = os.pread(fd, n, off)
    if len(b) != n:
        raise RuntimeError(f"short pread {len(b)} != {n} at {off}")
    return b


def _parse_dir(fd: int, off: int) -> tuple[list[tuple[int,int,int]], int]:
    h = _read_exact(fd, HDR.size, off)
    magic, _si, _fam, count, body_len, _zero, digest = HDR.unpack(h)
    if magic != b"DIR1" or body_len != count * DIRENT.size:
        raise RuntimeError("malformed directory header")
    body = _read_exact(fd, body_len, off + HDR.size)
    if hashlib.sha256(body).digest() != digest:
        raise ValueError("directory digest mismatch")
    rows = [DIRENT.unpack_from(body, i * DIRENT.size) for i in range(count)]
    return rows, HDR.size + body_len


def _read_group(fd: int, group_off: int) -> bytes:
    h = _read_exact(fd, HDR.size, group_off)
    magic, _si, _fam, _idx, body_len, _first, digest = HDR.unpack(h)
    if magic != b"GRP1" or body_len > GROUP_BODY_LIMIT:
        raise RuntimeError("malformed group header")
    body = _read_exact(fd, body_len, group_off + HDR.size)
    if hashlib.sha256(body).digest() != digest:
        raise ValueError("group digest mismatch")
    return body


def _locate(rows: list[tuple[int,int,int]], key: int) -> int:
    for first, last, off in rows:
        if first <= key <= last:
            return off
    raise KeyError(key)


def _build_groups(work: Path) -> tuple[list[dict], dict, dict]:
    manifest = json.loads((work / "current" / "manifest.json").read_text())
    pool = (work / "current" / "streams.bin").read_bytes()
    hashes = sorted({rec["stream_hash"] for rec in manifest["derived"].values()})
    groups: list[dict] = []
    expected: dict[tuple[int,str,int], bytes] = {}
    family_keys: dict[tuple[int,str], list[int]] = {}

    for si, h in enumerate(hashes):
        s = manifest["stream_index"][h]
        comp = pool[s["o"]:s["o"]+s["n"]]
        parsed = BASE.DEP.parse_tokens(comp)
        raw = zlib.decompress(comp, -15)
        anchors, blocks, _ = BASE.COLD._build_metadata(parsed)
        seeds, _all_seed, _logical_seed = BASE.SEED._build_seeds(parsed, anchors, raw)
        brecs, arecs = BASE.SUPER._encoded_records(parsed)
        records = {
            "block": [(int(r["key"]), r["encoded"]) for r in brecs],
            "anchor": [(int(r["key"]), r["encoded"]) for r in arecs],
        }

        pages = len(anchors)
        selected: set[int] = set()
        for p in range(pages):
            a = p * PAGE
            b = min(len(raw), min(pages, p + 2) * PAGE)
            r = BASE.COLD.ColdReader(comp, anchors, blocks, len(raw))
            if r.read(a, b) != raw[a:b]:
                raise RuntimeError("classifier exactness drift")
            if r.metadata_bytes() + r.payload_bytes() > BASE.LIMIT:
                selected.add(p)
                if p + 1 < pages:
                    selected.add(p + 1)
        seed_records: list[tuple[int, bytes]] = []
        for p in sorted(selected):
            if seeds[p] is None:
                continue
            enc = BASE._seed_enc(p, anchors[p], parsed, raw)
            if enc is None or hashlib.sha256(enc).hexdigest() != seeds[p]["frame_sha256"]:
                raise RuntimeError("seed record parity drift")
            seed_records.append((p, enc))
        records["seed"] = seed_records

        for fam in ("anchor", "block", "seed"):
            family_keys[(si, fam)] = [k for k, _ in records[fam]]
            for k, enc in records[fam]:
                expected[(si, fam, k)] = enc
            groups.extend(_pack(records[fam], si, fam))
    return groups, expected, family_keys


def _serialize(path: Path, groups: list[dict]) -> dict:
    families = sorted({(g["stream"], g["family"]) for g in groups})
    by_family = {sf: [g for g in groups if (g["stream"], g["family"]) == sf] for sf in families}

    # Primary directory sizes are known before offsets; group offsets follow them.
    primary_sizes = {sf: HDR.size + DIRENT.size * len(gs) for sf, gs in by_family.items()}
    primary_total = sum(primary_sizes.values())
    group_offsets: dict[tuple[int,str,int], int] = {}
    cursor = primary_total
    for sf in families:
        for g in by_family[sf]:
            group_offsets[(g["stream"], g["family"], g["index"])] = cursor
            cursor += HDR.size + len(g["body"])
    groups_end = cursor

    primary: dict[tuple[int,str], bytes] = {}
    for sf in families:
        rows = bytearray()
        for g in by_family[sf]:
            rows += DIRENT.pack(g["first"], g["last"], group_offsets[(g["stream"], g["family"], g["index"])])
        primary[sf] = _dir_header(sf[0], sf[1], len(by_family[sf]), bytes(rows)) + bytes(rows)

    tail_start = groups_end
    tail_offsets: dict[tuple[int,str], int] = {}
    cursor = tail_start
    for sf in families:
        tail_offsets[sf] = cursor
        cursor += len(primary[sf])
    footer_off = cursor
    dir_root_material = b"".join(hashlib.sha256(primary[sf]).digest() for sf in families)
    root = hashlib.sha256(dir_root_material).digest()
    footer = FOOTER.pack(b"FTR1", len(families), tail_start, footer_off, root)

    with path.open("wb") as f:
        for sf in families:
            f.write(primary[sf])
        for sf in families:
            for g in by_family[sf]:
                f.write(_group_bytes(g))
        for sf in families:
            f.write(primary[sf])
        f.write(footer)

    primary_offsets: dict[tuple[int,str], int] = {}
    c = 0
    for sf in families:
        primary_offsets[sf] = c
        c += len(primary[sf])
    if path.stat().st_size != footer_off + FOOTER.size:
        raise RuntimeError("serialized size drift")
    return {
        "families": families,
        "primary": primary,
        "primary_offsets": primary_offsets,
        "tail_offsets": tail_offsets,
        "group_offsets": group_offsets,
        "group_bytes": sum(HDR.size + len(g["body"]) for g in groups),
        "primary_dir_bytes": sum(len(x) for x in primary.values()),
        "tail_dir_bytes": sum(len(x) for x in primary.values()),
        "footer_bytes": FOOTER.size,
        "total_bytes": path.stat().st_size,
        "root": root,
    }


def run(work: Path, v029_checkout: Path, worker: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    prior = THREE.run(work, v029_checkout, worker)
    if not prior["hypothesis"]["three_family_644b_groups_preserve_density_and_8x_locality"]:
        raise RuntimeError("three-family prerequisite no longer passes")

    groups, expected, family_keys = _build_groups(work)
    store = work / "group-meta.bin"
    layout = _serialize(store, groups)

    # Prior grouped bytes must equal concrete group bytes exactly: only the free directory/root is new.
    prior_groups = int(prior["grouped_storage"]["grouped_sparse_metadata_bytes"]) + int(prior["grouped_storage"]["grouped_selected_seed_bytes"])
    if layout["group_bytes"] != prior_groups:
        raise RuntimeError(f"group serialization parity drift {layout['group_bytes']} != {prior_groups}")

    recovered = 0
    fd = os.open(store, os.O_RDONLY)
    try:
        for sf in layout["families"]:
            rows, _ = _parse_dir(fd, layout["primary_offsets"][sf])
            for key in family_keys[sf]:
                body = _read_group(fd, _locate(rows, key))
                needle = expected[(sf[0], sf[1], key)]
                if needle not in body:
                    raise RuntimeError("serialized group did not recover exact encoded record")
                recovered += 1
    finally:
        os.close(fd)

    # Corruption controls: primary directory must fail then tail must recover; group body must fail locally.
    mutable = bytearray(store.read_bytes())
    sf0 = layout["families"][0]
    p0 = layout["primary_offsets"][sf0]
    mutable[p0 + HDR.size] ^= 1
    corrupt_primary = work / "corrupt-primary.bin"
    corrupt_primary.write_bytes(mutable)
    fd = os.open(corrupt_primary, os.O_RDONLY)
    try:
        primary_failed = False
        try:
            _parse_dir(fd, p0)
        except ValueError:
            primary_failed = True
        tail_rows, _ = _parse_dir(fd, layout["tail_offsets"][sf0])
        tail_recovered = primary_failed and bool(tail_rows)
    finally:
        os.close(fd)

    g0 = groups[0]
    goff = layout["group_offsets"][(g0["stream"], g0["family"], g0["index"])]
    mutable = bytearray(store.read_bytes())
    mutable[goff + HDR.size] ^= 1
    corrupt_group = work / "corrupt-group.bin"
    corrupt_group.write_bytes(mutable)
    fd = os.open(corrupt_group, os.O_RDONLY)
    try:
        group_corruption_detected = False
        try:
            _read_group(fd, goff)
        except ValueError:
            group_corruption_detected = True
    finally:
        os.close(fd)

    extra_storage = layout["primary_dir_bytes"] + layout["tail_dir_bytes"] + layout["footer_bytes"]
    prior_candidate = int(prior["grouped_storage"]["candidate_plus_grouped_locality_bytes"])
    v029 = int(prior["grouped_storage"]["same_input_v029_bytes"])
    serialized_candidate = prior_candidate + extra_storage
    density_margin = v029 - serialized_candidate

    # Conservative selective charge: fixed footer plus complete primary directory for every family.
    # This intentionally assumes no free archive-open cache. It is a falsifier for the simple layout.
    dir_bytes_by_family = {sf[1]: 0 for sf in layout["families"]}
    for sf in layout["families"]:
        dir_bytes_by_family[sf[1]] = max(dir_bytes_by_family[sf[1]], len(layout["primary"][sf]))
    conservative_directory_touch = FOOTER.size + sum(dir_bytes_by_family.values())
    prior_worst = int(prior["whole_group_locality"]["worst_fixed_probe"]["combined_bytes"])
    charged_worst = prior_worst + conservative_directory_touch
    locality_margin = LIMIT - charged_worst

    supported = (
        density_margin > 0 and locality_margin >= 0 and tail_recovered and group_corruption_detected and recovered == len(expected)
    )
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "source": prior["source"],
        "frozen_v029": prior["frozen_v029"],
        "prerequisite": {
            "prior_source_commit": prior["source_commit"],
            "prior_candidate_bytes": prior_candidate,
            "prior_margin_to_v029_bytes": int(prior["grouped_storage"]["margin_to_same_input_v029_bytes"]),
            "prior_worst_read_bytes": prior_worst,
            "prior_locality_slack_bytes": LIMIT - prior_worst,
            "prior_locality_failures": int(prior["whole_group_locality"]["locality_failures"]),
        },
        "serialized_store": {
            "groups": len(groups),
            "families": len(layout["families"]),
            "records_recovered_exactly": recovered,
            "expected_records": len(expected),
            "group_bytes_already_charged": layout["group_bytes"],
            "primary_directory_bytes": layout["primary_dir_bytes"],
            "tail_recovery_directory_bytes": layout["tail_dir_bytes"],
            "footer_root_bytes": layout["footer_bytes"],
            "new_storage_bytes_beyond_prior_receipt": extra_storage,
            "serialized_candidate_bytes": serialized_candidate,
            "same_input_v029_bytes": v029,
            "margin_to_v029_bytes": density_margin,
        },
        "selective_directory_charge": {
            "footer_bytes_per_cold_read": FOOTER.size,
            "max_primary_directory_bytes_by_family": dir_bytes_by_family,
            "conservative_directory_touch_bytes": conservative_directory_touch,
            "prior_worst_group_plus_payload_bytes": prior_worst,
            "charged_worst_read_bytes": charged_worst,
            "locality_limit_bytes": LIMIT,
            "locality_margin_bytes": locality_margin,
            "amplification_vs_4k": charged_worst / PAGE,
        },
        "hostile_controls": {
            "primary_directory_corruption_detected": primary_failed,
            "tail_directory_recovery_exact": tail_recovered,
            "group_body_corruption_detected": group_corruption_detected,
        },
        "hypothesis": {
            "simple_serialized_directory_preserves_density_and_8x": supported,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "fixed_group_body_bytes": GROUP_BODY_LIMIT,
            "fixed_page_bytes": PAGE,
            "fixed_limit_bytes": LIMIT,
            "actual_os_pread_for_metadata": True,
            "same_group_record_bytes": True,
            "primary_and_tail_directory_copies_charged": True,
            "footer_root_charged": True,
            "no_caching_assumption": True,
            "no_parameter_or_codec_sweep": True,
            "remaining_debt": "full payload pread and cold parser objects; exact archive-root trust semantics; resource-bounded malformed-directory tests; fresh-process CPU/RSS; held-out transfer; native/platform parity",
        },
        "next_if_supported": "replace gifted metadata objects with parser output from this byte store and execute the full payload+metadata reader through pread before selector admission",
        "next_if_falsified": "preserve the free-map lower bound; design an implicit/sharded locator that derives offsets without full-family directory reads or duplicated directory bulk, then preregister its bytes before implementation",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-serialized-group-directory-work"))
    p.add_argument("--v029-checkout", type=Path, required=True)
    p.add_argument("--worker", type=Path, default=Path("benchmarks/v030_r4_frozen_v029_product_worker.py"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-serialized-group-directory.json"))
    a = p.parse_args()
    d = run(a.work_root, a.v029_checkout, a.worker)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "serialized_store": d["serialized_store"],
        "selective_directory_charge": d["selective_directory_charge"],
        "hostile_controls": d["hostile_controls"],
        "hypothesis": d["hypothesis"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
