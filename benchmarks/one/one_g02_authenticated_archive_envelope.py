#!/usr/bin/env python3
"""Frozen system-composition falsifier for the ONE-G0.2 authenticated archive seam."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import tempfile

from experiments.one.archive_envelope import CHUNK_BYTES, build_program
from experiments.one.authenticated_archive_envelope import (
    AUTH_LEAF_BYTES,
    build_authenticated_archive,
    open_authenticated_archive,
)
from experiments.one.wire import encode_program


def _payload(size: int, salt: int) -> bytes:
    # Deterministic nonconstant content. This is a system-seam vector, not a compression corpus.
    return bytes(((i * 131 + (i >> 7) * 29 + salt * 17) ^ (i >> 13)) & 255 for i in range(size))


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="one-auth-archive-") as td:
        root = Path(td)
        large = _payload(CHUNK_BYTES + AUTH_LEAF_BYTES * 4 + 137, 3)
        medium = _payload(256 * 1024 + 73, 9)
        (root / "large.bin").write_bytes(large)
        (root / "medium.bin").write_bytes(medium)
        (root / "empty.bin").write_bytes(b"")

        base_program, base_build = build_program(root)
        base_wire, _ = encode_program(base_program)
        candidate_wire, build = build_authenticated_archive(root)
        archive = open_authenticated_archive(candidate_wire)

        requests = (
            ("large.bin", 0, 64, "first64"),
            ("large.bin", AUTH_LEAF_BYTES - 31, 127, "cross_auth_leaf"),
            ("large.bin", CHUNK_BYTES - 31, 127, "cross_one_chunk"),
            ("large.bin", len(large) // 2, 4096, "middle4k"),
            ("large.bin", len(large) - 257, 257, "final257"),
            ("medium.bin", 65517, 211, "medium_cross_leaf"),
            ("empty.bin", 0, 0, "empty_zero"),
        )
        rows = []
        for path, start, length, label in requests:
            value, stats = archive.read_range(path, start, length)
            original = (root / path).read_bytes()
            if value != original[start:start + length]:
                raise AssertionError(f"semantic mismatch: {label}")
            row = {"label": label, "path": path, "start": start, "length": length, **asdict(stats)}
            rows.append(row)

        logical = build.logical_file_bytes
        auth_delta_ratio = build.auth_manifest_delta_bytes / logical if logical else 0.0
        max_nonempty_cone = max(row["cone_bytes"] for row in rows if row["length"])
        full_reconstruct_violations = [
            row["label"] for row in rows
            if row["length"] and row["cone_bytes"] >= len((root / row["path"]).read_bytes())
            and len((root / row["path"]).read_bytes()) > AUTH_LEAF_BYTES
        ]
        decision = (
            "ADVANCE_AUTHENTICATED_ARCHIVE_ENVELOPE"
            if auth_delta_ratio <= 0.03 and not full_reconstruct_violations
            else "HOLD_AUTHENTICATED_ARCHIVE_ENVELOPE"
        )
        return {
            "schema": "one-g02-authenticated-archive-envelope-v1",
            "decision": decision,
            "gate": {
                "max_auth_manifest_delta_ratio": 0.03,
                "no_large_file_full_reconstruction": True,
            },
            "build": {
                **asdict(build),
                "base_wire_bytes": len(base_wire),
                "wire_delta_bytes": len(candidate_wire) - len(base_wire),
                "auth_manifest_delta_ratio": auth_delta_ratio,
                "base_logical_file_bytes": base_build["logical_file_bytes"],
            },
            "selective": {
                "request_count": len(rows),
                "max_nonempty_cone_bytes": max_nonempty_cone,
                "full_reconstruct_violations": full_reconstruct_violations,
                "rows": rows,
            },
            "known_regression_debt": {
                "authentication_build_source_reread_bytes": build.source_reread_bytes,
                "preferred_writer_requires_fused_auth_construction": True,
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    result = run()
    text = json.dumps(result, indent=2, sort_keys=True)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    return 0 if result["decision"] == "ADVANCE_AUTHENTICATED_ARCHIVE_ENVELOPE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
