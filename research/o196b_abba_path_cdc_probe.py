#!/usr/bin/env python3
"""O196b: reproduce the performance harness' exact source-path Python CDC admission.

No shipping source edits or benchmark timing modifications. Standalone read-only probe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=("base", "candidate"), required=True)
    ap.add_argument("--expected-src", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    from cmpct import codec
    expected_dir = (args.expected_src.resolve() / "cmpct")
    module = Path(codec.__file__).resolve()
    if module.parent != expected_dir:
        raise AssertionError(
            f"wrong imported engine for {args.arm}: {module} vs {expected_dir}"
        )

    data = b"".join(hashlib.sha256(i.to_bytes(4, "little")).digest()
                    for i in range(70000))
    if not len(data) > codec.CDC_MAX:
        raise AssertionError("non-discriminating input")
    parts = codec.cdc_chunks(data)
    lengths = tuple(map(len, parts))
    if not parts or b"".join(parts) != data:
        raise AssertionError("CDC reconstruction mismatch")
    fixed = tuple(min(codec.CHUNK, len(data) - i)
                  for i in range(0, len(data), codec.CHUNK))
    loaded = getattr(codec, "_cdc", None)
    native_name = str(getattr(loaded, "_name", "")) if loaded is not None else None
    helper_exists = (module.parent / "libcmpct_cdc.so").is_file()
    if loaded is None and lengths != fixed:
        raise AssertionError("helper absent but wrapper did not take fixed fallback")

    record = {
        "question": "O196b actual ABBA source-path native CDC admission",
        "arm": args.arm,
        "module": str(module),
        "source_sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
        "expected_src": str(args.expected_src.resolve()),
        "python_version": sys.version.split()[0],
        "python_executable": sys.executable,
        "native_cdc_loaded": loaded is not None,
        "native_cdc_path": native_name,
        "adjacent_native_file": helper_exists,
        "input_size": len(data),
        "input_sha256": hashlib.sha256(data).hexdigest(),
        "fixed_lengths": list(fixed),
        "observed_lengths": list(lengths),
        "exact_reassembly": True,
        "claim_scope": "source-path admission on one runner; not performance causality or release proof",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
