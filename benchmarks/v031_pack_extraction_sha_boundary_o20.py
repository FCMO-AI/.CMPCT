#!/usr/bin/env python3
"""O20 scientific court: whole-tree extraction vs physical PACK SHA (no product edit).

The inherited independent r24 fixture is intentionally reused unmodified.
A green court means the *predicted integrity-tier distinction was reproduced*,
not that a SHA-authenticated extraction path was implemented.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive

from v031_pack_physical_sha_court import archive_bytes


def sha_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def court() -> dict:
    left = (b"the quick brown fox " * 4)[:64]
    right = (b"PACK member two: exact " * 4)[:64]
    original = left + right
    altered = original[:-1] + bytes([original[-1] ^ 1])
    assert len(original) == len(altered) == 128
    assert sha_hex(original) != sha_hex(altered)
    results: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="cmpct-pack-extract-o20-") as td:
        root = Path(td)
        cases = (
            ("pack_control", True, original, True),
            ("pack_crc_repaired", True, altered, False),
            ("direct_crc_repaired", False, altered, False),
        )
        for label, packed, materialized, expected_verified in cases:
            archive = root / (label + ".cmpct")
            archive.write_bytes(archive_bytes(original, materialized, packed=packed))
            summary = preflight_archive(archive)
            assert summary["blobs"] == 1
            with CMPCT(archive) as reader:
                try:
                    reader.verify()
                except (OSError, ValueError) as exc:
                    verified = False
                    # An unrelated parse, I/O, resource or API error cannot be
                    # counted as the expected physical identity rejection.
                    expected_reason = (
                        "physical PACK SHA-256 verification failure"
                        if packed else "SHA-256 verification failure"
                    )
                    assert expected_reason in str(exc), (
                        f"{label}: rejection is not the registered SHA cause: {exc!r}"
                    )
                else:
                    verified = True
                assert verified is expected_verified, (
                    f"{label}: exact inherited #258 verify result drift; "
                    f"expected={expected_verified}, got={verified}"
                )
            dest = root / ("out-" + label)
            with CMPCT(archive) as reader:
                try:
                    reader.extractall(dest, metadata=False)
                except (OSError, ValueError) as error:
                    raise AssertionError(
                        f"{label}: ordinary extractall changed contract: {error}"
                    ) from error
            if packed:
                actual_left = (dest / "alpha.md").read_bytes()
                actual_right = (dest / "beta.md").read_bytes()
                assert actual_left == left
                observed = actual_left + actual_right
            else:
                actual_right = (dest / "direct.md").read_bytes()
                observed = actual_right
            assert observed == materialized, (label, sha_hex(observed), sha_hex(materialized))
            results[label] = {
                "archive_bytes": archive.stat().st_size,
                "archive_sha256": sha_hex(archive.read_bytes()),
                "index_and_structure": "PASS",
                "strong_verify": "ACCEPT" if verified else "REJECT",
                "ordinary_extractall": "ACCEPT",
                "output_sha256": sha_hex(observed),
                "original_physical_sha256": sha_hex(original),
                "output_matches_original": observed == original,
                "output_matches_crc_repaired_mutant": observed == altered,
                "physical_sha_consistent": sha_hex(materialized) == sha_hex(original),
            }
    assert results["pack_control"]["output_matches_original"]
    assert results["pack_control"]["strong_verify"] == "ACCEPT"
    assert results["pack_crc_repaired"]["strong_verify"] == "REJECT"
    assert results["pack_crc_repaired"]["ordinary_extractall"] == "ACCEPT"
    assert results["pack_crc_repaired"]["output_matches_crc_repaired_mutant"]
    assert not results["pack_crc_repaired"]["output_matches_original"]
    assert results["direct_crc_repaired"]["strong_verify"] == "REJECT"
    assert results["direct_crc_repaired"]["output_matches_crc_repaired_mutant"]
    return {
        "status": "PASS",
        "decision": "EXTRACT_CRC_TIER_CAN_PUBLISH_SHA_INCONSISTENT_BYTES",
        "classification": "RESEARCH_INTEGRITY_BOUNDARY_ONLY",
        "fixture_origin": "unchanged independent O1/#257 physical-r24 generator",
        "cases": results,
        "limitations": [
            "CRC-repaired synthetic corruption, not an observed storage fault",
            "normal read/extract contract intentionally cheaper than explicit verify",
            "stored physical SHA is not a trusted external signature",
            "no filesystem-concurrency, recovery, speed, memory or release claim",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    arguments = parser.parse_args()
    result = court()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if arguments.out is not None:
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(encoded, encoding="utf-8")
    print(encoded)
