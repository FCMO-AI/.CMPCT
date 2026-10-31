#!/usr/bin/env python3
"""No-CMPCT independent r24 footer/receipt referee for J24I74.

Never imports cmpct. Uses a separately developed prior physical r24 parser as
a stronger control and validates the public Writer's physical chain anew.
"""
from __future__ import annotations

import ast
import copy
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics
import struct
import subprocess
import sys
import tempfile

import msgpack
import zstandard

from j24i70_detached_referee import (
    HEADER, FOOTER, ancestors, footer, scan_physical_blob_records,
)

ROOT = Path(__file__).resolve().parents[1]
PARENT = "a6695ba86d6a5b20eaced4eb8b54768f00724c9b"
PREREG = "42c396eafc26ab5cc6f59b195bf27213037f646b"
LABELS = ("public", "original", "minimal")
EXPECTED_BLOBS = {
    "src/cmpct/reader.py": "29a8be64f3acfb027750351c6a567fd82cf7dc97",
    "research/j24i73_owned_import_cone.py": "8956a17c8f8103e0e620934da8daa4eb9406877b",
    "research/j24g73_reader_open.py": "9b2fa7c2d625cce84597212673c35fba29dcafd5",
    "research/j24i70_detached_referee.py": "235dddde0d7bb52710b69de3dafe7653a5f6d312",
}
DONORS = {
    "reference": ("research/j24g64_mixed_fsmeta_oracle.py", None),
    "admit": ("research/j24g64_mixed_fsmeta_oracle.py", None),
    "factored": ("research/j24g64_mixed_fsmeta_oracle.py", None),
    "owned_factored_fresh": ("research/j24g74_owned_decoder_court.py", None),
    "_index_from_footer": ("research/j24g74_owned_decoder_court.py", "OwnedCMPCT"),
}
ORDERS = ("POM", "PMO", "OPM", "OMP", "MPO", "MOP")
CHAR = {"P": "public", "O": "original", "M": "minimal"}


def require(test, msg):
    if not test:
        raise AssertionError(msg)


def strictly_parsed(p: Path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, "duplicate-json-key")
            out[key] = value
        return out
    return json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=unique)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def n(x):
    require(type(x) is int and x >= 0, "expected-nonnegative-int")
    return x


def func(tree, name, cls=None):
    nodes = tree.body
    if cls:
        options = [node for node in nodes
                   if isinstance(node, ast.ClassDef) and node.name == cls]
        require(len(options) == 1, "missing-donor-class")
        nodes = options[0].body
    options = [node for node in nodes if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(options) == 1, "missing-donor-function:" + name)
    return options[0]


def ast_sha(node):
    return sha(ast.dump(node, include_attributes=False).encode())


def physical_history(data: bytes):
    require(len(data) >= HEADER.size + FOOTER.size, "archive-too-small")
    magic, version, flags, compressed_len, plain_len, physical_span, primary_sha = HEADER.unpack_from(data)
    require(magic == b"CMPCT24\x00" and version == 24, "bad-header")
    require(type(compressed_len) is int and 0 < compressed_len < len(data) and
            0 < plain_len < 32_000_000 and 0 <= physical_span < len(data), "header-bounds")
    primary_plain = zstandard.ZstdDecompressor().decompress(
        data[HEADER.size:HEADER.size + compressed_len], max_output_size=plain_len)
    require(len(primary_plain) == plain_len and
            hashlib.sha256(primary_plain).digest() == primary_sha, "primary-auth")
    primary = msgpack.unpackb(primary_plain, raw=False)
    require(isinstance(primary, dict) and len(primary.get("files", [])) == 128,
            "wrong-real-Builder-root")
    history = ancestors(data, len(data) - FOOTER.size)
    require(len(history) == 64 and history[0]["kind"] == 1 and
            history[-1]["kind"] == 0, "63-signed-generation-depth")
    root = footer(data, history[-1]["position"])["value"]
    require(root == primary, "root-not-primary")
    operations = [footer(data, frame["position"])["value"]["ops"][0]
                  for frame in reversed(history[:-1])]
    require(len(operations) == 63, "wrong-op-count")
    counts = dict(Counter(op[0] for op in operations))
    require(counts == {"ren": 21, "del": 21, "put": 21}, "not-mixed-21x3")

    # Independent path/ordinal interpretation; no published Reader or
    # inherited research replay helper is invoked.
    files = {row[0]: list(row) for row in root["files"]}
    require(len(files) == 128, "duplicate-primary-path")
    original_rows = root["files"]
    xattrs = {}
    for entry in (root.get("fsmeta") or {}).get("xattrs", []):
        require(type(entry[0]) is int and 0 <= entry[0] < len(original_rows),
                "original-xattr-ordinal")
        xattrs[original_rows[entry[0]][0]] = entry[1:]
    for op in operations:
        if op[0] == "ren":
            require(len(op) == 3 and op[1] in files and op[2] not in files,
                    "invalid-replay-rename")
            row = files.pop(op[1])
            row[0] = op[2]
            files[op[2]] = row
            if op[1] in xattrs:
                xattrs[op[2]] = xattrs.pop(op[1])
        elif op[0] == "del":
            require(len(op) == 2 and op[1] in files, "invalid-replay-delete")
            del files[op[1]]
            xattrs.pop(op[1], None)
        elif op[0] == "put":
            require(len(op) == 2 and isinstance(op[1], list) and
                    isinstance(op[1][0], str), "invalid-replay-put")
            files[op[1][0]] = list(op[1])
        else:
            raise AssertionError("unsupported-op")
    require(len(files) == 118, "replay-member-count")
    root_records = scan_physical_blob_records(
        data, primary, HEADER.size + compressed_len)
    require(root_records["decoded_sha_crc_verified"] > 0, "no-physical-blobs-authenticated")
    return {
        "member_names": sorted(files),
        "xattr_names": sorted(xattrs),
        "operations": counts,
        "chain": len(history),
        "root_records": root_records,
        "root_plain_sha256": sha(primary_plain),
        "terminal_sha256": history[0]["sha"],
        "preceding_footer_pos": history[1]["position"],
    }


def validate(root: Path):
    require("cmpct" not in sys.modules, "referee-imported-product")
    r = strictly_parsed(root / "receipt.json")
    require(r["schema"] == "cmpct-j24i74-mixed-import-cone-v1" and
            r["status"] == "PASS_SCIENCE_ONLY" and
            type(r["product_credit"]) is int and r["product_credit"] == 0,
            "non-science-receipt")
    source = r["source"]
    require(source["parent"] == PARENT and source["prereg"] == PREREG,
            "unregistered-ancestry")
    actual_head = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                          cwd=ROOT, text=True).strip()
    require(source["head"] == actual_head, "mismatched-HEAD")
    require(source["source_blobs"] == EXPECTED_BLOBS, "product-source-mismatch")

    mod = (root / "j24i73_ablation_owned.py").read_bytes()
    require(sha(mod) == r["minimal_module"]["sha256"] and
            len(mod) == n(r["minimal_module"]["size"]), "minimal-code-identity")
    tree = ast.parse(mod.decode("utf-8"))
    require(len([node for node in tree.body if isinstance(node, ast.ClassDef)
                 and node.name == "OwnedCMPCT"]) == 1, "minimal-class")
    for name, (path, klass) in DONORS.items():
        donor = ast.parse((ROOT / path).read_text(encoding="utf-8"))
        first = ast_sha(func(donor, name, klass))
        second = ast_sha(func(tree, name, "OwnedCMPCT" if name == "_index_from_footer" else None))
        require(first == second == r["minimal_module"]["donor_ast_sha256"][name],
                "algorithm-AST:" + name)
    physical = r["physical"]
    path = root / physical["file"]
    require(path.name == "mixed.cmpct" and path.is_file(), "missing-physical-archive")
    data = path.read_bytes()
    require(len(data) == n(physical["bytes"]) and sha(data) == physical["sha256"],
            "archive-physical-source")
    require(physical["generation_depth"] == 63 and
            physical["members"] == 118 and
            physical["expected_operations"] == {"ren": 21, "del": 21, "put": 21},
            "claimed-physics")
    require(physical["operating_system"] == source["platform"], "os-source-mismatch")
    require(type(physical["physical_xattrs_required"]) is bool and
            physical["physical_xattrs_required"] == (source["platform"] in ("linux", "darwin")) and
            physical["physical_xattrs_claimed"] == physical["physical_xattrs_required"],
            "false-xattr-host-claim")
    tree_truth = physical_history(data)

    parity = r["parity"]
    require(parity["names"] == tree_truth["member_names"], "real-replayed-names")
    require(set(parity["member_sha256"]) == set(tree_truth["member_names"]),
            "manifest-members")
    require(parity["manifest_sha256"] == sha(msgpack.packb(
        parity["member_sha256"], use_bin_type=True)), "manifest-hash")
    require(parity["preflight_files"] == 118 and parity["archive_preserved"] is True and
            parity["real_sparse_xattrs"] == physical["physical_xattrs_required"],
            "false-public-control")
    require(parity["xattr_path_names"] == tree_truth["xattr_names"],
            "xattr-ordinal-reconstruction")
    if physical["physical_xattrs_required"]:
        require(len(tree_truth["xattr_names"]) > 0, "missing-sparse-xattr-positive")
    require(set(parity["per_reader"]) == set(LABELS), "missing-reader-control")
    for label, case in parity["per_reader"].items():
        require(case["index_sha256"] == parity["index_sha256"] and
                case["depth"] == 63 and case["members"] == 118 and
                case["read_verified"] == 118 and case["extracted_verified"] == 118,
                "incomplete-semantic-check:" + label)
        require(case["route"] == ("owned-fresh-decoder" if label != "public" else None),
                "wrong-owned-route:" + label)
        require(case["physical_xattr_restoration"] is physical["physical_xattrs_required"] and
                case["xattr_metadata_records"] == len(tree_truth["xattr_names"]),
                "unverified-xattrs:" + label)
    inherited = r["inherited_public_vs_factored"]
    require(inherited["archive_sha256"] == physical["sha256"] and
            inherited["index_sha256"] == parity["index_sha256"] and
            inherited["members"] == 118 and inherited["ops"] == tree_truth["operations"] and
            inherited["xattr_records"] == len(tree_truth["xattr_names"]),
            "inherited-differential")

    recovery = r["recovery"]
    require(set(recovery["modes"]) == {"bad-footer-sha", "truncated-footer"}, "missing-recovery")
    for mode, details in recovery["modes"].items():
        original = (data[:-1] + bytes([data[-1] ^ 0xB5]) if mode == "bad-footer-sha"
                    else data[:-17])
        require(details["sha256"] == sha(original) and
                n(details["bytes"]) == len(original), "recovery-source")
        expected_index = {v["index_sha256"] for v in details["per_reader"].values()}
        expected_counts = {v["members"] for v in details["per_reader"].values()}
        require(set(details["per_reader"]) == set(LABELS) and len(expected_index) == 1 and
                len(expected_counts) == 1, "recovery-divergence")
        for label, item in details["per_reader"].items():
            require(item["depth"] == 62 and
                    item["route"] == ("owned-fresh-decoder" if label != "public" else None),
                    "bad-recovery-route")
    require(recovery["short_rejected"] == {name: True for name in LABELS},
            "invalid-archive-accepted")

    charges = r["writer_cost"]
    require(charges["api_calls"] == {"builder": 1, "ren": 21, "del": 21, "put": 21},
            "missing-real-public-api")
    for value in charges["components"].values():
        require(n(value["wall_ns"]) > 0 and n(value["cpu_ns"]) >= 0, "bad-builder-charge")
    for metric in ("wall_ns", "cpu_ns"):
        require(n(charges["overall"][metric]) >=
                sum(item[metric] for item in charges["components"].values()),
                "missing-setup-charge")

    opens = r["open_cost"]
    require(len(opens["raw"]) == 18 and set(opens["medians"]) == set(LABELS),
            "missing-raw-timings")
    require(set(opens["tracemalloc_peak_bytes"]) == set(LABELS), "missing-memory-accounting")
    for label in LABELS:
        samples = [sample for sample in opens["raw"] if sample["label"] == label]
        require(len(samples) == 6, "missing-balanced-timings:" + label)
        require({s["block"] for s in samples} == set(range(6)), "unbalanced")
        for block, order in enumerate(ORDERS):
            row = next(s for s in samples if s["block"] == block)
            require(CHAR[order[[CHAR[c] for c in order].index(label)]] == label,
                    "bad-label")
            require(n(row["wall_ns"]) > 0 and n(row["cpu_ns"]) >= 0, "bad-raw-timing")
        for metric in ("wall_ns", "cpu_ns"):
            result = statistics.median(item[metric] for item in samples)
            require(result == opens["medians"][label][metric], "forged-median")
        require(n(opens["tracemalloc_peak_bytes"][label]) > 0, "missing-heap-measure")
    return {"verdict": "PASS_SCIENCE_ONLY", "head": actual_head,
            "archive_sha256": physical["sha256"], "physical": tree_truth,
            "real_xattr_hosts": physical["physical_xattrs_required"],
            "raw_timing_count": 18, "product_credit": 0}


def adversarial_tests(root: Path):
    """Mutate each independent evidence class; a PASS must be impossible."""
    base = strictly_parsed(root / "receipt.json")
    archive = (root / "mixed.cmpct").read_bytes()
    module = (root / "j24i73_ablation_owned.py").read_bytes()
    cases = [
        ("changed-source", lambda r: r["source"].__setitem__("head", "0" * 40)),
        ("forged-members", lambda r: r["physical"].__setitem__("members", 119)),
        ("forged-op-classes", lambda r: r["physical"].__setitem__(
            "expected_operations", {"ren": 0, "del": 21, "put": 42})),
        ("forged-median", lambda r: r["open_cost"]["medians"]["minimal"].__setitem__(
            "wall_ns", 1)),
        ("missing-measurement", lambda r: r["open_cost"]["raw"].pop()),
        ("false-os-xattr", lambda r: r["physical"].__setitem__(
            "physical_xattrs_required", not r["physical"]["physical_xattrs_required"])),
        ("forged-reader-route", lambda r: r["parity"]["per_reader"]["minimal"].__setitem__(
            "route", "checkpoint")),
    ]
    rejected = []
    with tempfile.TemporaryDirectory(prefix="j24i74-referee-") as td:
        temp = Path(td)
        for label, mutate in cases:
            r = copy.deepcopy(base)
            mutate(r)
            (temp / "receipt.json").write_text(json.dumps(r))
            (temp / "mixed.cmpct").write_bytes(archive)
            (temp / "j24i73_ablation_owned.py").write_bytes(module)
            try:
                validate(temp)
            except (AssertionError, KeyError, ValueError, TypeError, zstandard.ZstdError):
                rejected.append(label)
            else:
                raise AssertionError("forgery accepted: " + label)
        (temp / "receipt.json").write_text(json.dumps(base))
        (temp / "j24i73_ablation_owned.py").write_bytes(module)
        corrupt = archive[:-1] + bytes([archive[-1] ^ 0x01])
        (temp / "mixed.cmpct").write_bytes(corrupt)
        try:
            validate(temp)
        except (AssertionError, KeyError, ValueError, zstandard.ZstdError):
            rejected.append("physical-footer-corruption")
        else:
            raise AssertionError("altered physical archive accepted")
        (temp / "mixed.cmpct").write_bytes(archive)
        corrupt_module = module + b"\n# altered\n"
        (temp / "j24i73_ablation_owned.py").write_bytes(corrupt_module)
        try:
            validate(temp)
        except (AssertionError, KeyError, ValueError):
            rejected.append("forged-source-module")
        else:
            raise AssertionError("altered module accepted")
    require(len(rejected) == len(cases) + 2, "adversarial-coverage")
    return rejected


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "evidence/j24i74").resolve()
    result = validate(root)
    result["forged_cases_rejected"] = adversarial_tests(root)
    require(len(result["forged_cases_rejected"]) == 9, "short-forgery-court")
    (root / "detached-verdict.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps({"verdict": result["verdict"],
                      "footers": result["physical"]["chain"],
                      "forgeries_rejected": len(result["forged_cases_rejected"]),
                      "product_credit": 0, "head": result["head"]}, sort_keys=True))


if __name__ == "__main__":
    main()
