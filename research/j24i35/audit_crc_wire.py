#!/usr/bin/env python3
"""J24I35: detached physical referee for authentic r24 and one-bit CRC-only variant.

This script imports neither CMPCT nor Rust. It reuses the separately frozen
J24I30 detached framing referee to avoid manufacturing a new interpretation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "j24i30"))
from audit_symlink_wire import parse  # noqa: E402

H = struct.Struct("<8sHHQQQ32s")
B = struct.Struct("<4sBBHQQII32s")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-dir", type=Path, required=True)
    base = ap.parse_args().case_dir
    original = (base / "original.cmpct").read_bytes()
    altered = (base / "crc-wrong.cmpct").read_bytes()
    assert len(original) == len(altered)
    _, _, _, index_csize, _, _, _ = H.unpack_from(original)
    start = H.size + index_csize
    crc_offset = start + 28
    assert [i for i, (a, b) in enumerate(zip(original, altered)) if a != b] == [crc_offset]
    assert (original[crc_offset] ^ altered[crc_offset]) == 1
    # The J24I30 referee validates both authenticated index copies, footer,
    # CMA4 schema, decoded bytes, and independent content SHA+CRC.
    control = parse(base / "original.cmpct")
    changed = parse(base / "crc-wrong.cmpct")
    assert control["physical_record_valid"] is True
    assert changed["physical_record_valid"] is False
    assert control["decoded_sha256"] == changed["decoded_sha256"]
    assert control["decoded_literal_hex"] == changed["decoded_literal_hex"]
    assert control["physical_sha256"] != changed["physical_sha256"]
    assert control["index_sha256"] == changed["index_sha256"]
    assert control["logical_row_sha"] == changed["logical_row_sha"]
    assert control["compressed_bytes"] == changed["compressed_bytes"]
    assert control["decoded_bytes"] == changed["decoded_bytes"]
    assert original[:crc_offset] == altered[:crc_offset]
    assert original[crc_offset+1:] == altered[crc_offset+1:]
    physical_prior = B.unpack_from(original, start)
    physical_changed = B.unpack_from(altered, start)
    assert physical_prior[:-2] == physical_changed[:-2]
    assert physical_prior[-1] == physical_changed[-1]  # SHA remains valid
    assert physical_prior[-2] != physical_changed[-2]  # CRC alone changed
    raw = bytes.fromhex(control["decoded_literal_hex"])
    assert zlib.crc32(raw) & 0xffffffff == physical_prior[-2]
    assert hashlib.sha256(raw).digest() == physical_prior[-1]

    outcome = {
        "schema": "cmpct-j24i35-detached-physical-referee-v1",
        "result": "PASS: only CMA4 CRC bit mutated; true decoded SHA remains correct; index+footer unchanged",
        "source_sha256": hashlib.sha256(original).hexdigest(),
        "crc_wrong_sha256": hashlib.sha256(altered).hexdigest(),
        "mutation_offset": crc_offset,
        "source": control,
        "crc_only": changed,
    }
    (base / "j24i35-detached-referee.json").write_text(
        json.dumps(outcome, sort_keys=True, indent=2) + "\n"
    )
    print(json.dumps(outcome, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
