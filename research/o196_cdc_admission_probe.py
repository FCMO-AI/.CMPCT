#!/usr/bin/env python3
"""O196: falsifiable installed-wheel native CDC helper-admission witness.

Research experiment, not a modification of CMPCT's shipping loader or Builder.
Run from a fresh wheel-installed virtualenv with PYTHONPATH unset and cwd outside checkout.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def native_lengths(cdll, data: bytes, codec) -> tuple[int, ...]:
    function = cdll.cmpct_cdc_cut
    function.argtypes = [
        ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_uint64), ctypes.c_size_t,
    ]
    function.restype = ctypes.c_size_t
    cap = max(4, len(data) // max(1, codec.CDC_MIN) + 4)
    ends = (ctypes.c_uint64 * cap)()
    buffer = ctypes.create_string_buffer(data)
    n = int(function(buffer, len(data), codec.CDC_MIN, codec.CDC_AVG,
                     codec.CDC_MAX, ends, cap))
    if not 1 < n <= cap:
        raise AssertionError(f"invalid native cut count: {n}, cap={cap}")
    cuts = tuple(int(ends[i]) for i in range(n))
    if cuts[-1] != len(data):
        raise AssertionError(f"native final cut {cuts[-1]} != {len(data)}")
    prev = 0
    lengths = []
    for cut in cuts:
        if not prev < cut <= len(data):
            raise AssertionError(f"invalid native cut {cut} after {prev}")
        lengths.append(cut - prev)
        prev = cut
    return tuple(lengths)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["default", "injected"], required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    # A checkout/source import would not answer the wheel-packaging question.
    from cmpct import codec
    prefix = Path(sys.prefix).resolve()
    module = Path(codec.__file__).resolve()
    if sys.prefix == sys.base_prefix or not module.is_relative_to(prefix):
        raise AssertionError(f"not an independently installed venv package: {module}; prefix={prefix}")
    source = args.source.resolve()
    if not source.is_file():
        raise AssertionError(f"missing source: {source}")

    data = b"".join(hashlib.sha256(i.to_bytes(4, "little")).digest()
                    for i in range(70000))
    assert len(data) > max(codec.CDC_MAX, 4 * codec.CHUNK)
    fixed = tuple(min(codec.CHUNK, len(data) - i)
                  for i in range(0, len(data), codec.CHUNK))
    original_helper = getattr(codec, "_cdc", None)
    originally_present = original_helper is not None
    originally_loaded_name = str(getattr(original_helper, "_name", "")) if originally_present else None
    root = module.parent
    distributed_native = sorted(x.name for x in root.iterdir()
                                if x.is_file() and x.suffix.lower() in (".so", ".dylib", ".dll", ".pyd"))

    expected_direct = None
    if args.mode == "injected":
        with tempfile.TemporaryDirectory(prefix="o196-admission-") as d:
            native_path = Path(d) / "libcmpct_o196_exact.so"
            cmd = [
                "cc", "-O2", "-std=c11", "-shared", "-fPIC",
                str(source), "-o", str(native_path),
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=90)
            injected = ctypes.CDLL(str(native_path))
            expected_direct = native_lengths(injected, data, codec)
            if expected_direct == fixed:
                raise AssertionError("positive-control native cuts coincide with fixed fallback")
            # This is deliberate instrumentation, not a packaging/loader change.
            codec._cdc = injected
            parts = codec.cdc_chunks(data)
            observed = tuple(map(len, parts))
            if observed != expected_direct:
                raise AssertionError(
                    f"the Python wrapper did not execute direct checked-in C cuts: {observed} != {expected_direct}"
                )
    else:
        parts = codec.cdc_chunks(data)
        observed = tuple(map(len, parts))
        # Do NOT require absence in the default arm: its presence would falsify
        # the prediction and must survive as an honest positive observation.
        if not originally_present and observed != fixed:
            raise AssertionError("helper absent but default wrapper not using fixed fallback")

    if b"".join(parts) != data:
        raise AssertionError("CDC partitioning changed bytes")
    evidence = {
        "question": "O196 clean-wheel optional CDC helper admission",
        "mode": args.mode,
        "python_version": sys.version.split()[0],
        "venv_prefix": str(prefix),
        "import_file": str(module),
        "module_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
        "native_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "source_path": str(source),
        "originally_loaded": originally_present,
        "original_helper_path": originally_loaded_name,
        "distributed_native_files": distributed_native,
        "package_helper_exists": (root / "libcmpct_cdc.so").exists(),
        "input_size": len(data),
        "input_sha256": hashlib.sha256(data).hexdigest(),
        "fixed_lengths": list(fixed),
        "observed_lengths": list(observed),
        "direct_checked_in_c_lengths": list(expected_direct) if expected_direct else None,
        "bytes_exact": True,
        "claim_scope": "clean wheel admission + deterministic segmentation; not product compression/speed/release proof",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    print(json.dumps(evidence, sort_keys=True))


if __name__ == "__main__":
    main()
