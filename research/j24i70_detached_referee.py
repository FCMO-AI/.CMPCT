#!/usr/bin/env python3
"""No-CMPCT J24I70 receipt and physical-footer referee; rejects forged claims."""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path
import statistics
import struct
import sys
import binascii
import zlib

import msgpack
import zstandard

FOOTER = struct.Struct("<8sBBBBQQQ32s")
HEADER = struct.Struct("<8sHHQQQ32s")
BLOB = struct.Struct("<4sBBHQQII32s")
ROOT_PREREG = "9b2cf6ab6d02eee9ead8e58ab1d733ee2aedb9d5"
SOURCE_PARENT = "347a62b443bf7c880ed2b86af5d8be7159ee2480"
REFERENCE = "129edec976efe8bb604584517de39553487fec34"
LABELS = {"public", "factored", "owned", "delete_only"}
NAMES = {"A", "B", "C"}
ROUTES = {
    "A": {"factored": "factored", "owned": "owned-fresh-decoder", "delete_only": "onepass-owned-delete"},
    "B": {"factored": "checkpoint", "owned": "checkpoint", "delete_only": "checkpoint"},
    "C": {"factored": "factored", "owned": "owned-fresh-decoder", "delete_only": "onepass-owned-delete"},
}


def check(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def footer(raw: bytes, pos: int) -> dict:
    check(0 <= pos and pos + FOOTER.size <= len(raw), "footer-bounds")
    magic, kind, codec, flags, reserved, cs, us, prev, digest = FOOTER.unpack_from(raw, pos)
    check(magic == b"CMPTF24\x00" and kind in (0, 1), "footer-magic/kind")
    check(flags == reserved == 0 and 0 < cs <= pos and 0 < us < 64_000_000, "footer-size/flags")
    check(0 <= prev < pos, "footer-parent")
    payload = raw[pos - cs:pos]
    if codec == 1:
        expanded = zstandard.ZstdDecompressor().decompress(payload, max_output_size=us)
    else:
        check(codec == 0, "footer-codec")
        expanded = payload
    check(len(expanded) == us and hashlib.sha256(expanded).digest() == digest, "footer-sha")
    value = msgpack.unpackb(expanded, raw=False)
    check(isinstance(value, dict), "footer-map")
    return {"kind": kind, "prev": prev, "value": value, "sha": sha(expanded)}


def ancestors(raw: bytes, pos: int) -> list[dict]:
    visited = set()
    output = []
    for _ in range(66):
        check(pos not in visited, "footer-loop")
        visited.add(pos)
        row = footer(raw, pos)
        output.append({"position": pos, "kind": row["kind"], "prev": row["prev"], "sha": row["sha"]})
        if row["kind"] == 0:
            check("files" in row["value"], "missing-root-index")
            return output
        check(row["prev"] > 0, "delta-without-parent")
        pos = row["prev"]
    raise AssertionError("footer-depth")


def scan_physical_blob_records(raw: bytes, primary: dict, record_base: int) -> dict:
    """Validate actual CMA4 headers and all natively supported uncompressed bodies.

    This is independent of CMPCT imports. The unsupported-codec count is explicit;
    no claim of strong logical digest validation is made for that subclass.
    """
    blobs = primary.get("blobs")
    check(isinstance(blobs, list), "primary-blobs")
    check(len(blobs) <= 100_000, "physical-record-bound")
    decoded = 0
    unsupported = {}
    spans = []
    for i, item in enumerate(blobs):
        check(isinstance(item, list) and len(item) == 5, "blob-index-shape")
        off, usize, csize, codec, meta_len = item
        check(all(type(v) is int and v >= 0 for v in item), "blob-index-types")
        check(usize <= 64_000_000 and csize <= 64_000_000 and meta_len <= 64_000_000,
              "blob-index-size")
        pos = record_base + off
        end = pos + BLOB.size + meta_len + csize
        check(record_base <= pos and end <= len(raw), "blob-physical-bounds")
        (magic, physical_codec, flags, reserved, physical_usize, physical_csize,
         physical_meta, crc, digest) = BLOB.unpack_from(raw, pos)
        check(magic == b"CMA4" and flags == reserved == 0, "blob-header-magic/flags")
        check((physical_codec, physical_usize, physical_csize, physical_meta) ==
              (codec, usize, csize, meta_len), "blob-header-index-consistency")
        spans.append((pos, end))
        body = raw[pos+BLOB.size+meta_len:end]
        try:
            if codec == 0:
                unpacked = body
            elif codec == 1:
                unpacked = zstandard.ZstdDecompressor().decompress(body, max_output_size=usize)
            elif codec == 4:
                unpacked = zlib.decompress(body, wbits=-15)
            else:
                unsupported[str(codec)] = unsupported.get(str(codec), 0) + 1
                continue
        except (zstandard.ZstdError, zlib.error, ValueError):
            raise AssertionError("blob-decompression-"+str(i))
        check(len(unpacked) == usize, "blob-uncompressed-size")
        check(binascii.crc32(unpacked) & 0xffffffff == crc, "blob-CRC32")
        check(hashlib.sha256(unpacked).digest() == digest, "blob-SHA256")
        decoded += 1
    spans.sort()
    check(all(prev[1] <= next_[0] for prev, next_ in zip(spans, spans[1:])),
          "overlapping-physical-records")
    return {"total": len(blobs), "decoded_sha_crc_verified": decoded,
            "unsupported_codec_counts": unsupported}


def physical_check(a: bytes, b: bytes, c: bytes) -> dict:
    check(b.startswith(a), "checkpoint-not-append")
    check(len(b) == len(c) and c[:-1] == b[:-1] and c[-1] != b[-1],
          "corrupt-tail-is-not-single-byte")
    check(len(a) >= HEADER.size, "header-size")
    magic, version, flags, cs, us, span, digest = HEADER.unpack_from(a)
    check(magic == b"CMPCT24\x00" and version == 24, "primary-magic")
    check(0 < cs <= len(a) - HEADER.size and 0 < us < 64_000_000, "primary-index-size")
    payload = zstandard.ZstdDecompressor().decompress(
        a[HEADER.size:HEADER.size + cs], max_output_size=us)
    check(len(payload) == us and hashlib.sha256(payload).digest() == digest, "primary-index-sha")
    primary = msgpack.unpackb(payload, raw=False)
    check(isinstance(primary.get("files"), list), "primary-files")
    verified_blobs = scan_physical_blob_records(a, primary, HEADER.size + cs)
    check(verified_blobs["decoded_sha_crc_verified"] > 0, "no-verified-physical-records")
    a_hist = ancestors(a, len(a) - FOOTER.size)
    b_hist = ancestors(b, len(b) - FOOTER.size)
    check(len(a_hist) == 64 and len(b_hist) == 1, "footer-chain-length")
    check(b_hist[0]["kind"] == 0 and b_hist[0]["prev"] == a_hist[0]["position"],
          "checkpoint-ancestry")
    check(a_hist[0]["kind"] == 1 and a_hist[-1]["kind"] == 0, "history-shape")
    try:
        footer(c, len(c) - FOOTER.size)
    except (AssertionError, ValueError, zstandard.ZstdError, msgpack.ExtraData):
        damaged_rejected = True
    else:
        damaged_rejected = False
    check(damaged_rejected, "damaged-tail-accepted")
    check(sha(c[:len(a)]) == sha(a), "recovery-prefix-differs")
    return {"a_footers": len(a_hist), "b_terminal_checkpoint": True,
            "corrupt_b_tail_rejected": True, "source_root_files": len(primary["files"]),
            "primary_sha256": sha(payload),
            "physical_blobs": verified_blobs}


def validate(receipt: dict, root: Path) -> dict:
    check(receipt["schema"] == "cmpct-j24i70-cross-owner-v1" and receipt["status"] == "PASS",
          "receipt-schema/status")
    check(receipt["product_credit"] == 0, "false-product-credit")
    source = receipt["source"]
    check(source["prereg"] == ROOT_PREREG and source["parent"] == SOURCE_PARENT
          and source["reference_head"] == REFERENCE, "source-identity")
    check(set(receipt["cases"]) == {"4096", "8192"}, "families")
    checked = {}
    for family, case in receipt["cases"].items():
        n = int(family)
        expected_members = n - 63
        check(case["members"] == expected_members, "member-count")
        assert set(case["copied"]) == set(case["physical"]) == NAMES
        raw = {}
        for key in NAMES:
            info, copyinfo = case["physical"][key], case["copied"][key]
            check(copyinfo["relative"] == f"{n}-{key}.cmpct", "file-name")
            path = root / copyinfo["relative"]
            check(path.is_file(), "archive-not-retained")
            data = path.read_bytes()
            check(type(info["size"]) is int and type(copyinfo["size"]) is int, "file-size-type")
            check(len(data) == info["size"] == copyinfo["size"], "file-size")
            check(sha(data) == info["sha256"] == copyinfo["sha256"], "file-sha")
            raw[key] = data
        physics = physical_check(raw["A"], raw["B"], raw["C"])
        tax = len(raw["B"]) - len(raw["A"])
        check(tax == case["checkpoint_extra_bytes"] and tax > 0, "byte-tax")
        check(math.isclose(tax / len(raw["A"]), case["checkpoint_overhead_ratio"],
                           rel_tol=1e-12), "byte-tax-ratio")
        timings = case["timings"]
        check(set(timings["files"]) == NAMES, "timed-files")
        for key in NAMES:
            run = timings["files"][key]
            samples = run["raw"]
            check(len(samples) == 32 and set(s["variant"] for s in samples) == LABELS, "raw-count")
            for label in LABELS:
                selected = [s for s in samples if s["variant"] == label]
                check(len(selected) == 8 and set(s["block"] for s in selected) == {0, 1}, "samples/variant")
                for row in selected:
                    check(number(row["wall_ns"]) and row["wall_ns"] > 0 and
                          number(row["cpu_ns"]) and row["cpu_ns"] >= 0, "timer-number")
                    if label in ROUTES[key]:
                        check(row["route"] == ROUTES[key][label], "measured-route")
                for metric in ("wall_ns", "cpu_ns"):
                    got = statistics.median(x[metric] for x in selected)
                    check(math.isclose(got, run["medians"][metric][label], rel_tol=1e-12),
                          "median-forgery")
                for block in (0, 1):
                    got = statistics.median(s["wall_ns"] for s in selected if s["block"] == block)
                    check(math.isclose(got, run["block_wall_medians"][str(block)][label],
                                       rel_tol=1e-12), "block-forgery")
            check(set(run["medians"]["wall_ns"]) == LABELS, "median-variants")
        wall = {k: v["medians"]["wall_ns"] for k, v in timings["files"].items()}
        cpu = {k: v["medians"]["cpu_ns"] for k, v in timings["files"].items()}
        expected_ratios = {
            "public_A_over_owned_A_wall": wall["A"]["public"] / wall["A"]["owned"],
            "public_A_over_delete_A_wall": wall["A"]["public"] / wall["A"]["delete_only"],
            "owned_A_over_public_B_wall": wall["A"]["owned"] / wall["B"]["public"],
            "delete_A_over_public_B_wall": wall["A"]["delete_only"] / wall["B"]["public"],
            "owned_A_over_delete_A_wall": wall["A"]["owned"] / wall["A"]["delete_only"],
            "public_A_over_owned_A_cpu": cpu["A"]["public"] / cpu["A"]["owned"],
            "owned_A_over_public_B_cpu": cpu["A"]["owned"] / cpu["B"]["public"],
        }
        for key, val in expected_ratios.items():
            check(math.isclose(val, timings["ratios"][key], rel_tol=1e-12), "ratio-forgery")
        for filekey in NAMES:
            for label in LABELS:
                sem = case["semantics"][filekey][label]
                check(sem["member_count"] == expected_members and
                      sem["verified_members"] == expected_members, "semantic-count")
                if label in ROUTES[filekey]:
                    check(sem["route"] == ROUTES[filekey][label], "semantic-route")
        test = case["predictions"]
        check(test["owned_speedup_at_least_2"] is (expected_ratios["public_A_over_owned_A_wall"] >= 2),
              "predicted-speedup")
        check(test["owned_within_1p5_checkpoint"] is
              (expected_ratios["owned_A_over_public_B_wall"] <= 1.5), "predicted-checkpoint")
        check(test["cpu_sign_consistent"] is
              (expected_ratios["public_A_over_owned_A_cpu"] > 1), "predicted-cpu")
        check(test["checkpoint_byte_tax_positive"] is True, "predicted-byte-tax")
        checked[family] = physics
    actual = all(c["predictions"]["owned_speedup_at_least_2"] and
                 c["predictions"]["owned_within_1p5_checkpoint"] and
                 c["predictions"]["cpu_sign_consistent"]
                 for c in receipt["cases"].values())
    check(receipt["hypothesis"]["all_semantics_passed"] is True and
          receipt["hypothesis"]["owned_narrow_checkpoint_economics"] is actual,
          "hypothesis-forgery")
    return checked


def self_test(receipt: dict, root: Path) -> dict:
    validate(receipt, root)
    tactics = (
        ("source", lambda x: x["source"].update(prereg="0" * 40)),
        ("product-credit", lambda x: x.update(product_credit=1)),
        ("physical-hash", lambda x: x["cases"]["4096"]["copied"]["A"].update(sha256="0" * 64)),
        ("physical-size", lambda x: x["cases"]["4096"]["physical"]["B"].update(size=True)),
        ("median", lambda x: x["cases"]["4096"]["timings"]["files"]["A"]["medians"]["wall_ns"].update(owned=1.0)),
        ("ratio", lambda x: x["cases"]["8192"]["timings"]["ratios"].update(owned_A_over_public_B_wall=0.1)),
        ("route", lambda x: x["cases"]["8192"]["semantics"]["A"]["owned"].update(route="fallback")),
        ("raw-sample", lambda x: x["cases"]["4096"]["timings"]["files"]["A"]["raw"].pop()),
        ("prediction", lambda x: x["cases"]["8192"]["predictions"].update(owned_speedup_at_least_2="PASS")),
        ("hypothesis", lambda x: x["hypothesis"].update(owned_narrow_checkpoint_economics="PASS")),
    )
    refused = {}
    for title, mutate in tactics:
        forged = copy.deepcopy(receipt)
        mutate(forged)
        try:
            validate(forged, root)
        except (AssertionError, KeyError, TypeError, ValueError, ZeroDivisionError):
            refused[title] = True
        else:
            raise AssertionError("forged receipt accepted: " + title)
    return refused


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: j24i70_detached_referee.py evidence-directory")
    root = Path(sys.argv[1])
    text = (root / "receipt.json").read_text()
    duplicate_keys = []
    def no_duplicates(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                duplicate_keys.append(key)
            out[key] = value
        return out
    receipt = json.loads(text, object_pairs_hook=no_duplicates)
    check(not duplicate_keys, "duplicate-json-keys")
    checked = validate(receipt, root)
    refused = self_test(receipt, root)
    result = {"status": "PASS", "product_credit": 0, "physical": checked,
              "adversarial_refusals": refused, "referee_sha256": sha(Path(__file__).read_bytes()),
              "original_receipt_sha256": sha(text.encode())}
    (root / "detached-referee.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print("J24I70_DETACHED", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
