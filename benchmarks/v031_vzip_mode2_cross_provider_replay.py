#!/usr/bin/env python3
"""Replay independent O0 Python zlib streams on a *different* provider/version.

A research oracle, not a native Reader or cross-version portability guarantee.
Use `--reference-json` with the authentic full per-case JSON extracted from
PR #278 hosted O0 artifact 12528086507; hashes make the reference auditable.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import sys
import zlib

def h(b):
    return hashlib.sha256(b).hexdigest()

def run(reference):
    source = Path(__file__).resolve().with_name("v031_vzip_mode2_native_backend_probe.py")
    spec = importlib.util.spec_from_file_location("vzip_o0_reference", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    samples = module.fixed_samples()
    assert len(samples) == 7
    assert reference.get("comparisons") == 28 and len(reference["cases"]) == 28
    seen = set()
    rows = []
    for case in reference["cases"]:
        key = (case["family"], case["level"])
        if key in seen: raise AssertionError(("duplicate control", key))
        seen.add(key)
        raw = samples[case["family"]]
        if h(raw) != case["source_sha256"] or len(raw) != case["source_len"]:
            raise AssertionError(("input provenance mismatch", key))
        expected = case["python_stream_sha256"]
        encoded = module.zlib_raw(raw, case["level"])
        if zlib.decompress(encoded, -15) != raw:
            raise AssertionError(("new provider corrupt stream", key))
        rows.append({
            "family": case["family"], "level": case["level"], "source_sha256": h(raw),
            "reference_stream_sha256": expected, "local_stream_sha256": h(encoded),
            "reference_stream_len": case["python_stream_len"], "local_stream_len": len(encoded),
            "byte_identity_by_sha": h(encoded) == expected and len(encoded) == case["python_stream_len"]
        })
    if len(seen) != 28: raise AssertionError("reference not 7x4 cases")
    differences = [r for r in rows if not r["byte_identity_by_sha"]]
    return {
        "schema": "cmpct-vzip-o0-cross-provider-full-sha-replay-v1",
        "reference_source": reference.get("source"),
        "reference_runtime": reference.get("runtime"),
        "local_runtime": {
            "python": sys.version.split()[0], "zlib_compiled": zlib.ZLIB_VERSION,
            "zlib_runtime": zlib.ZLIB_RUNTIME_VERSION, "platform": platform.platform()
        },
        "comparisons": len(rows), "identical": len(rows)-len(differences),
        "different": len(differences), "cases": rows,
        "decision": "SCOPED_28_CASE_PARITY" if not differences else "SCOPED_CROSS_VERSION_MISMATCH",
        "no_product_credit": True
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reference-json", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args=p.parse_args()
    reference=json.loads(args.reference_json.read_text(encoding="utf-8"))
    result=run(reference)
    result["reference_file_sha256"]=h(args.reference_json.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("comparisons","identical","different","decision")},sort_keys=True))

if __name__ == "__main__": main()
