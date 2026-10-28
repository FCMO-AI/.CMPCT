#!/usr/bin/env python3
"""J24G08: source-exact O10R depth ceilings versus #650 cache fallback.

Independent research only. This script builds physical archives once using #650,
then tests unchanged installed Readers from #650 and #365 in separate venvs.
No Reader internals are replaced; only the decode call counter is instrumented.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch

import msgpack


PAYLOAD = (b"J24G08 unchanged authenticated content\\x00" * 97)
RESULT_DIR = "j24g08-artifacts"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def orphan_tail(original: bytes, n: int, chained: bool) -> bytes:
    from cmpct.codec import FMAGIC, FTR, sha
    assert n in (4, 140)
    raw = bytearray(original)
    payload = msgpack.packb({"blobs": [], "ops": []}, use_bin_type=True)
    prev = 0
    for _ in range(n):
        footer_pos = len(raw) + len(payload)
        raw.extend(payload)
        raw.extend(FTR.pack(FMAGIC, 1, 0, 0, 0,
                            len(payload), len(payload),
                            prev if chained else 0, sha(payload)))
        prev = footer_pos
    assert len(payload) + FTR.size == 81
    assert len(raw) == len(original) + 81 * n
    return bytes(raw)


def make(artifacts: Path) -> None:
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.transactions import append_rename

    specimens = artifacts / "specimens"
    specimens.mkdir(parents=True, exist_ok=True)
    source = artifacts / "source"
    source.mkdir(exist_ok=True)
    (source / "owner.bin").write_bytes(PAYLOAD)
    os.utime(source / "owner.bin", ns=(1_700_000_000_000_000_000,) * 2)
    os.utime(source, ns=(1_700_000_000_000_000_000,) * 2)
    first = specimens / "valid1.cmpct"
    Builder(source).build(first)
    append_rename(first, "owner.bin", "renamed.bin")

    second = specimens / "valid2.cmpct"
    shutil.copyfile(first, second)
    append_rename(second, "renamed.bin", "twice.bin")
    third = specimens / "valid3.cmpct"
    shutil.copyfile(second, third)
    append_rename(third, "twice.bin", "thrice.bin")

    for label, n, chained in (("orphan4", 4, True),
                              ("orphan140", 140, True),
                              ("flat140", 140, False)):
        (specimens / f"{label}.cmpct").write_bytes(
            orphan_tail(first.read_bytes(), n, chained)
        )

    cases = [
        {"name": "valid1", "path": "valid1.cmpct", "member": "renamed.bin",
         "depth": 1, "max_depth": 2, "family": "committed"},
        {"name": "valid2", "path": "valid2.cmpct", "member": "twice.bin",
         "depth": 2, "max_depth": 2, "family": "committed"},
        {"name": "valid3", "path": "valid3.cmpct", "member": "thrice.bin",
         "depth": 3, "max_depth": 2, "family": "committed"},
        {"name": "orphan4", "path": "orphan4.cmpct", "member": "renamed.bin",
         "depth": 1, "max_depth": 2, "family": "chained-orphan"},
        {"name": "orphan140", "path": "orphan140.cmpct", "member": "renamed.bin",
         "depth": 1, "max_depth": None, "family": "chained-orphan"},
        {"name": "orphan140_loose", "path": "orphan140.cmpct", "member": "renamed.bin",
         "depth": 1, "max_depth": 256, "family": "chained-orphan"},
        {"name": "flat140", "path": "flat140.cmpct", "member": "renamed.bin",
         "depth": 1, "max_depth": 2, "family": "flat-orphan"},
    ]
    for case in cases:
        physical = specimens / case["path"]
        case["physical_sha256"] = sha256(physical.read_bytes())
        case["physical_bytes"] = physical.stat().st_size
    with CMPCT(first) as archive:
        assert archive.read("renamed.bin") == PAYLOAD
        assert archive.delta_depth == 1
        first_footer = archive.latest_footer_pos
    with CMPCT(second) as archive:
        assert archive.read("twice.bin") == PAYLOAD
        assert archive.delta_depth == 2
    with CMPCT(third) as archive:
        assert archive.read("thrice.bin") == PAYLOAD
        assert archive.delta_depth == 3
    manifest = {
        "source": "exact Builder/Writer installed on #650",
        "first_committed_footer": first_footer,
        "logical_sha256": sha256(PAYLOAD),
        "cases": cases,
        "physical_archive_generated_once": True,
        "format": "r24",
        "release_credit": 0,
    }
    (artifacts / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"phase": "make", "manifest": manifest}, sort_keys=True))


def assess(artifacts: Path, variant: str) -> None:
    from cmpct.reader import CMPCT

    manifest = json.loads((artifacts / "manifest.json").read_text())
    original_decode = CMPCT._decode_generation_payload
    results = []
    for spec in manifest["cases"]:
        if spec["max_depth"] is None:
            os.environ.pop("CMPCT_MAX_DELTA_DEPTH", None)
        else:
            os.environ["CMPCT_MAX_DELTA_DEPTH"] = str(spec["max_depth"])
        physical = artifacts / "specimens" / spec["path"]
        assert sha256(physical.read_bytes()) == spec["physical_sha256"]
        assert physical.stat().st_size == spec["physical_bytes"]
        calls = [0]
        def counted(self, *args, **kwargs):
            calls[0] += 1
            return original_decode(self, *args, **kwargs)
        row = {
            "case": spec["name"],
            "family": spec["family"],
            "physical_sha256": spec["physical_sha256"],
            "max_delta_depth": spec["max_depth"] or 128,
            "decode_calls": None,
            "result": None,
        }
        with patch.object(CMPCT, "_decode_generation_payload", counted):
            try:
                with CMPCT(physical) as archive:
                    member = spec["member"]
                    exact = archive.read(member)
                    assert exact == PAYLOAD
                    assert sha256(exact) == manifest["logical_sha256"]
                    assert archive.read_range(member, 11, 71) == PAYLOAD[11:82]
                    archive.verify()
                    assert archive.delta_depth == spec["depth"]
                    if spec["family"] != "committed":
                        assert archive.latest_footer_pos == manifest["first_committed_footer"]
                    row["result"] = "RECOVERED"
                    row["selected_footer"] = archive.latest_footer_pos
                    row["delta_depth"] = archive.delta_depth
                    row["logical_sha256"] = sha256(exact)
            except Exception as exc:
                row["result"] = "RAISED"
                row["exception_type"] = type(exc).__name__
                row["exception_text"] = str(exc)
        row["decode_calls"] = calls[0]
        results.append(row)
        print(json.dumps({"phase": "assess", "variant": variant, "case": row}, sort_keys=True))
    doc = {
        "variant": variant,
        "physical_manifest_sha256": sha256((artifacts / "manifest.json").read_bytes()),
        "cases": results,
        "release_credit": 0,
    }
    (artifacts / f"{variant}.json").write_text(json.dumps(doc, indent=2) + "\n")


def referee(artifacts: Path) -> None:
    manifest = json.loads((artifacts / "manifest.json").read_text())
    cache = json.loads((artifacts / "cache.json").read_text())
    o10r = json.loads((artifacts / "o10r.json").read_text())
    assert cache["physical_manifest_sha256"] == o10r["physical_manifest_sha256"]
    spec = {x["name"]: x for x in manifest["cases"]}
    a = {x["case"]: x for x in cache["cases"]}
    b = {x["case"]: x for x in o10r["cases"]}
    assert a.keys() == b.keys() == spec.keys()
    for name in spec:
        assert a[name]["physical_sha256"] == b[name]["physical_sha256"] == spec[name]["physical_sha256"]
    expected = {
        "cache": {"valid1": "RECOVERED", "valid2": "RECOVERED",
                  "valid3": "RECOVERED", "orphan4": "RECOVERED",
                  "orphan140": "RECOVERED", "orphan140_loose": "RECOVERED",
                  "flat140": "RECOVERED"},
        "o10r": {"valid1": "RECOVERED", "valid2": "RECOVERED",
                 "valid3": "RAISED", "orphan4": "RAISED",
                 "orphan140": "RAISED", "orphan140_loose": "RECOVERED",
                 "flat140": "RECOVERED"},
    }
    observed = {
        "cache": {n: r["result"] for n, r in a.items()},
        "o10r": {n: r["result"] for n, r in b.items()},
    }
    for n in ("valid3", "orphan4", "orphan140"):
        assert b[n]["exception_type"] == "ResourceLimitError", b[n]
    decision = ("O10R_DEPTH_LIMIT_KILLS_OLDER_COMMITTED_FALLBACK_ON_ORPHAN_TAIL"
                if observed == expected else "PREDICTION_DISCONFIRMED_OR_AMBIGUOUS")
    output = {
        "decision": decision,
        "expected": expected,
        "observed": observed,
        "cache_calls": {n: r["decode_calls"] for n, r in a.items()},
        "o10r_calls": {n: r["decode_calls"] for n, r in b.items()},
        "cross_variant_same_physical_files": True,
        "source_pinned_by_workflow": True,
        "release_credit": 0,
    }
    (artifacts / "decision.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"phase": "referee", **output}, sort_keys=True))
    assert decision == "O10R_DEPTH_LIMIT_KILLS_OLDER_COMMITTED_FALLBACK_ON_ORPHAN_TAIL"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("make", "assess", "referee"))
    parser.add_argument("--artifacts", default=RESULT_DIR)
    parser.add_argument("--variant", choices=("cache", "o10r"))
    args = parser.parse_args()
    artifacts = Path(args.artifacts).resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    if args.phase == "make":
        make(artifacts)
    elif args.phase == "assess":
        assert args.variant is not None
        assess(artifacts, args.variant)
    else:
        referee(artifacts)


if __name__ == "__main__":
    main()
