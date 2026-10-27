#!/usr/bin/env python3
"""O228c: authentic Builder, source-exact native CDC versus explicit fixed fallback.
Scientific index oracle only; never creates a run-tag CMPCT archive.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import statistics
import sys
import tempfile
import time
from pathlib import Path

import msgpack
import cmpct.codec as codec
from cmpct.core import CMPCT
from o228b_builder_transfer_court import PROFILES, profile, SIZE

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(output):
    helper = codec._cdc
    if helper is None:
        raise RuntimeError("INSTRUMENT_INVALID: authentic native helper not loaded")
    helper_path = Path(codec.__file__).with_name("libcmpct_cdc.so")
    if not helper_path.is_file():
        raise RuntimeError("INSTRUMENT_INVALID: native helper path missing")
    baseline_lib_sha = sha(helper_path)
    native_c_src = Path(__file__).resolve().parents[1] / "native" / "cmpct_cdc.c"
    if not native_c_src.exists():
        raise RuntimeError("INSTRUMENT_INVALID: exact native source unavailable")
    results = []
    for name in PROFILES:
        case = {"name": name}
        for mode in ("fallback", "native"):
            codec._cdc = None if mode == "fallback" else helper
            assert (codec._cdc is None) == (mode == "fallback")
            with tempfile.TemporaryDirectory(prefix="o228c-"+name+"-"+mode+"-") as d:
                p = Path(d)
                row = profile(name, p)
                with CMPCT(p / "original.cmpct") as reader:
                    index = reader.index
                    st = index["files"][0][6]
                    assert st[0] == codec.S_CDC
                    lengths = [int(length) for length, _ in st[1]]
                    assert all(x > 0 for x in lengths)
                    assert sum(lengths) == SIZE
                    assert len(lengths) == row["cdc_ref_count"]
                    row["chunk_lengths_sha256"] = hashlib.sha256(
                        msgpack.packb(lengths, use_bin_type=True)).hexdigest()
                    row["chunk_min"] = min(lengths)
                    row["chunk_max"] = max(lengths)
                    row["chunk_nonuniform"] = len(set(lengths)) > 1
                    row["mode"] = mode
                    row["native_helper_present_during_build"] = codec._cdc is not None
                    row["native_helper_so_sha256"] = baseline_lib_sha
                    row["native_source_sha256"] = sha(native_c_src)
                    row["native_source_git_blob_sha"] = None  # workflow records git hash separately
                    assert row["file_integrity_pass"]
                case[mode] = row
            print(name, mode, row["cdc_ref_count"], row["run_count"],
                  row["full_archive_byte_delta"], round(row["unpack_heap_ratio"],3),
                  file=sys.stderr, flush=True)
        a, b = case["fallback"], case["native"]
        assert a["logical_sha256"] == b["logical_sha256"]
        assert a["builder_sha"] == b["builder_sha"]
        assert a["reader_sha"] == b["reader_sha"]
        results.append(case)
    codec._cdc = helper
    actual_differences = [p["name"] for p in results if p["name"] != "zero"
                          and p["native"]["chunk_lengths_sha256"] != p["fallback"]["chunk_lengths_sha256"]]
    valid = len(actual_differences) >= 2
    eligible = [p["name"] for p in results if p["name"] not in ("zero", "independent")
                and p["native"]["max_run"] >= 8
                and p["native"]["unpack_heap_ratio"] >= 2
                and p["native"]["full_archive_byte_delta"] <= 0]
    material = [p["name"] for p in results if p["native"]["full_archive_pct_delta"] <= -1.0]
    decision = ("INSTRUMENT_INVALID" if not valid else
                "NATIVE_TRANSFER_SEED" if len(eligible) >= 2 and material else
                "NO_NATIVE_BUILDER_TRANSFER_AT_16MIB")
    result = {
        "schema": "cmpct-o228c-native-cdc-transfer-v1",
        "status": "RESEARCH_ONLY_NO_PRODUCT_CREDIT",
        "source_sha256": sha(__file__),
        "native_source_sha256": sha(native_c_src),
        "native_helper_so_sha256": baseline_lib_sha,
        "python": sys.version,
        "input_bytes_per_profile": SIZE,
        "profiles": results,
        "mode_difference_profiles": actual_differences,
        "eligible_nontrivial": eligible,
        "material_whole_archive_profiles": material,
        "decision": decision,
    }
    Path(output).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"decision":decision, "profiles":len(results),
                      "isolated_unpack_observations":len(results)*2*2*3,
                      "differing_native_boundary_profiles":len(actual_differences)}))
    if not valid:
        raise RuntimeError("Native/fallback mode discriminator invalid")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    run(args.output)

if __name__=="__main__":
    main()
