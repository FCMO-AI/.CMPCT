#!/usr/bin/env python3
"""Frozen falsifier for ONE-G0.2 authenticated Law archive composition."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import random
import tempfile

from experiments.one.authenticated_archive_envelope import AUTH_LEAF_BYTES, build_authenticated_archive, open_authenticated_archive
from experiments.one.authenticated_law_archive import CURRENT_PATH, PREVIOUS_PATH, build_authenticated_add8_pair_archive, build_surprise_pair_fixture

SIZES = (32 * 1024, 128 * 1024, 512 * 1024)
MIN_PRODUCTIVE_WIRE_SAVING = 0.25


def _pair(n: int) -> tuple[bytes, bytes]:
    rng = random.Random(0xA11C0000 ^ n)
    previous = bytes(rng.randrange(256) for _ in range(n))
    current = bytes(((b + 37) & 255) for b in previous)
    return previous, current


def _requests(n: int) -> tuple[tuple[int, int], ...]:
    return (
        (0, 0),
        (0, 64),
        (0, min(4096, n)),
        (max(0, n // 2 - 2048), min(4096, n - max(0, n // 2 - 2048))),
        (AUTH_LEAF_BYTES - 31, 127),
        (n - 257, 257),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="one_g02_authenticated_law_archive.json")
    parser.add_argument("--evidence-head", default=os.environ.get("EVIDENCE_HEAD", ""))
    args = parser.parse_args()

    rows = []
    for n in SIZES:
        previous, current = _pair(n)
        with tempfile.TemporaryDirectory(prefix="one-auth-law-") as td:
            source = Path(td) / "source"
            build_surprise_pair_fixture(source, previous, current)
            comparator_wire, comparator_stats = build_authenticated_archive(source)
        law_wire, law_stats = build_authenticated_add8_pair_archive(previous, current)
        comparator = open_authenticated_archive(comparator_wire)
        law = open_authenticated_archive(law_wire)

        if comparator.list_paths() != law.list_paths():
            raise AssertionError("archive path surfaces differ")
        if law.read_file(PREVIOUS_PATH) != previous or law.read_file(CURRENT_PATH) != current:
            raise AssertionError("Law archive full reconstruction mismatch")
        if comparator.read_file(PREVIOUS_PATH) != previous or comparator.read_file(CURRENT_PATH) != current:
            raise AssertionError("comparator full reconstruction mismatch")

        current_root = law.program.roots[law.base.entries[CURRENT_PATH]["root"]]
        if law.program.nodes[current_root.ref.node].op != "add8":
            raise AssertionError("current root is not ordinary add8 Law")

        request_rows = []
        for start, length in _requests(n):
            expected = current[start:start + length]
            cdata, cstats = comparator.read_range(CURRENT_PATH, start, length)
            ldata, lstats = law.read_range(CURRENT_PATH, start, length)
            if cdata != expected or ldata != expected:
                raise AssertionError("selective reconstruction mismatch")
            request_rows.append({
                "start": start,
                "length": length,
                "law_cone_bytes": lstats.cone_bytes,
                "law_source_read_bytes": lstats.source_read_bytes,
                "law_source_plan_write_bytes": lstats.source_plan_write_bytes,
                "law_proof_payload_bytes": lstats.proof_payload_bytes,
                "law_proof_hash_bytes": lstats.proof_hash_bytes,
                "law_plan_commands": lstats.plan_commands,
                "law_fallback": lstats.fallback,
                "law_fallback_reason": lstats.fallback_reason,
                "comparator_cone_bytes": cstats.cone_bytes,
            })

        saving = (len(comparator_wire) - len(law_wire)) / len(comparator_wire)
        rows.append({
            "file_bytes_each": n,
            "logical_bytes": 2 * n,
            "comparator_wire_bytes": len(comparator_wire),
            "law_wire_bytes": len(law_wire),
            "wire_saving_fraction": saving,
            "law_wire_sha256": sha256(law_wire).hexdigest(),
            "comparator_auth_index_bytes": comparator_stats.raw_auth_index_bytes,
            "law_auth_index_bytes": law_stats.auth_index_bytes,
            "law_bytes": law_stats.law_bytes,
            "law_surprise_bytes": law_stats.surprise_bytes,
            "request_rows": request_rows,
        })

    productive = [row for row in rows if row["file_bytes_each"] >= 128 * 1024]
    wire_pass = all(row["wire_saving_fraction"] >= MIN_PRODUCTIVE_WIRE_SAVING for row in productive)
    fixed_4k = []
    for row in rows:
        match = next(req for req in row["request_rows"] if req["start"] == 0 and req["length"] == 4096)
        fixed_4k.append(match["law_cone_bytes"])
    locality_pass = all(value <= AUTH_LEAF_BYTES for value in fixed_4k)
    auth_equal = all(row["comparator_auth_index_bytes"] == row["law_auth_index_bytes"] for row in rows)
    decision = "ADVANCE_AUTHENTICATED_LAW_ARCHIVE" if wire_pass and locality_pass and auth_equal else "HOLD_AUTHENTICATED_LAW_ARCHIVE"
    payload = {
        "experiment": "ONE-G0.2 authenticated Law archive",
        "evidence_head": args.evidence_head,
        "decision": decision,
        "gates": {"productive_wire_saving_min": MIN_PRODUCTIVE_WIRE_SAVING, "fixed_4k_cone_max": AUTH_LEAF_BYTES, "same_auth_index_bytes": True},
        "summary": {"wire_pass": wire_pass, "locality_pass": locality_pass, "auth_equal": auth_equal, "fixed_4k_cone_bytes": fixed_4k},
        "rows": rows,
    }
    Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, **payload["summary"]}, sort_keys=True))
    return 0 if decision == "ADVANCE_AUTHENTICATED_LAW_ARCHIVE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
