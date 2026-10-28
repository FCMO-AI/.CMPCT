#!/usr/bin/env python3
"""Source-locked J24C08 productization: no hidden original Reader or native C edits."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "reader": "b37b786966ac1506a0439567d4a58eea472d85f8",
    "validator": "fbcf6e9c108799dc8b6f5c19e95bcb0618cf41e8",
    "native": "50f29bb3539e01b25dd14c4701dcfb3622b2e97f",
}

OLD = """                storage=row[6]
                if row[1]==K_FILE and isinstance(storage,list) and storage and storage[0] in (S_SPARSE, S_CDC, S_CHUNKS):
                    if storage_validator is None:
                        from .validation import _validate_storage
                        storage_validator=_validate_storage
                    storage_validator(row[0],row[1],row[4],storage,self.index['blobs'],self.index['recipes'])
"""
NEW = """                storage=row[6]
                if row[1]==K_FILE and isinstance(storage,list) and storage and storage[0] in (S_SPARSE, S_CDC, S_CHUNKS):
                    # ABI3 is an optional positive-only proof for exact built-in S_CHUNKS.
                    # Invalid, unknown and unavailable cases ALWAYS run the inherited strict validator.
                    # This happens after canonical path admission and before mmap allocation.
                    if storage[0]==S_CHUNKS and native_chunk_ok(storage,self.index['blobs'],row[4]):
                        continue
                    if storage_validator is None:
                        from .validation import _validate_storage
                        storage_validator=_validate_storage
                    storage_validator(row[0],row[1],row[4],storage,self.index['blobs'],self.index['recipes'])
"""

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def one(text, before, after):
    if text.count(before) != 1:
        raise AssertionError("source drift: expected exactly one " + repr(before[:64]))
    return text.replace(before, after, 1)

def main():
    reader = (ROOT / "src/cmpct/reader.py").read_text(encoding="utf-8")
    reader = one(reader, "from ._chunk_admission import native_chunk_ok\n", "")
    reader = one(reader, NEW, OLD)
    c = (ROOT / "src/cmpct/_fastscan_abi3.c").read_text(encoding="utf-8")
    replacements = (
        ("Optional shipping stable-ABI exact built-in list path. False requires original validator",
         "Research-only stable-ABI exact built-in list path. False requires original validator"),
        ("Optional exact built-in list admission; False requires original validator.",
         "Research-only exact built-in list admission; False requires original validator."),
        ('"_fastscan_abi3", "CMPCT optional stable ABI fixed-chunk admission"',
         '"_o218_fastscan", "O218 CPython list native research oracle"'),
        ("PyInit__fastscan_abi3", "PyInit__o218_fastscan"),
    )
    for before, after in replacements:
        c = one(c, before, after)
    received = {
        "reader": blob(reader.encode("utf-8")),
        "validator": blob((ROOT / "src/cmpct/validation.py").read_bytes()),
        "native": blob(c.encode("utf-8")),
    }
    if received != EXPECTED:
        raise AssertionError({"expected": EXPECTED, "actual": received})
    assert blob((ROOT / "research/o218d_abi3_package/o218d_abi3_fastscan.c").read_bytes()) == EXPECTED["native"]
    print(json.dumps({"decision": "SOURCE_ISOLATION_PASS",
                      "original_blobs": received}, sort_keys=True))

if __name__ == "__main__":
    main()
