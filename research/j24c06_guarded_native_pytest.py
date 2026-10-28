#!/usr/bin/env python3
"""J24C06: test actual ABI3 monkeypatch against inherited guarded-Reader tests.

The native scanner is research-only. False routes back to the unchanged strict
Python validator; native True is allowed only for exact integer S_CHUNKS geometry.
No product source is modified by this process-local exercise.
"""
from __future__ import annotations
import importlib
import json
from pathlib import Path

import pytest
import cmpct.validation as validation
from j24c06_o218b_native_reader import ORIGINAL, native_validator, source_identity

TARGETS = (
    "tests/test_reader_deflate_export_custody.py",
    "tests/test_reader_unsupported_blob_bits.py",
    "tests/test_o215_fixed_chunk_admission.py",
)

class ObservedScanner:
    def __init__(self, module):
        self.module = module
        self.calls = 0
        self.fallbacks = 0

    def scan_refs(self, refs, blobs, size):
        self.calls += 1
        result = self.module.scan_refs(refs, blobs, size)
        if result is not True:
            self.fallbacks += 1
        return result

def main():
    source = source_identity()  # installed Reader/validator/source C exact Git blobs
    extension = importlib.import_module("_o218_fastscan")
    observed = ObservedScanner(extension)
    blobs = [[0, 4, 4, 0, 0]]
    # Make the native eligible/noneligible split explicit before a pytest run.
    assert observed.scan_refs([0, 0], blobs, 8) is True
    assert observed.scan_refs([True], blobs, 4) is False
    assert observed.scan_refs([0], blobs, 5) is False
    validation._validate_storage = native_validator(observed)
    try:
        result = pytest.main(["--noconftest", "-q", *TARGETS])
    finally:
        validation._validate_storage = ORIGINAL
    if result != 0:
        raise SystemExit(f"guarded composed-Reader pytest failed: {result}")
    if observed.calls <= 3:
        raise AssertionError("O215 tests never exercised native list admission")
    if observed.fallbacks < 2:
        raise AssertionError("strict fallback was not observed")
    record = {"tier": "research_only_native_runtime_injection", "source": source,
              "scanner_calls_including_explicit_probes": observed.calls,
              "false_to_original_fallbacks": observed.fallbacks,
              "inherited_guarded_test_files": list(TARGETS),
              "result": "J24C06_NATIVE_GUARDED_READER_PASS"}
    print(json.dumps(record, sort_keys=True), flush=True)

if __name__ == "__main__":
    main()
