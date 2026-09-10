from __future__ import annotations

"""Preregistered transfer falsifier for represented ONE Law breadth.

This benchmark deliberately constructs only generator-distinct transfer data. It does not
import, generate, read, compare, or score any Genesis gate workload.
"""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import shutil
import stat
import tempfile
from typing import Any

from experiments.one.authenticated_archive_envelope import open_authenticated_archive
from experiments.one.general_law_archive import build_general_law_archive

OUT = Path("one-g02-general-law-breadth-transfer.json")
ALLOWED_OPS = {"surprise", "concat", "repeat", "fill", "xor", "add8"}


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _write_mode(path: Path, data: bytes, mode: int) -> None:
    path.write_bytes(data)
    path.chmod(mode)


def _build_transfer_tree(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)

    # Relation islands intentionally use distinct lengths. The current bounded policy only
    # examines the immediately preceding regular file, so length changes prevent a Law root
    # from accidentally becoming the predictor for the next relation family.
    add_base = _hash_stream(32 * 1024, b"breadth-add-base")
    add_target = bytes(((byte + 37) & 0xFF) for byte in add_base)
    xor_base = _hash_stream(32 * 1024 + 17, b"breadth-xor-base")
    xor_target = bytes((byte ^ 0xA5) for byte in xor_base)
    exact_base = _hash_stream(32 * 1024 + 41, b"breadth-exact-base")

    _write_mode(root / "00-add-base.bin", add_base, 0o640)
    _write_mode(root / "01-add-target.bin", add_target, 0o600)
    _write_mode(root / "02-xor-base.bin", xor_base, 0o644)
    _write_mode(root / "03-xor-target.bin", xor_target, 0o604)
    _write_mode(root / "04-exact-base.bin", exact_base, 0o660)
    _write_mode(root / "05-exact-copy.bin", exact_base, 0o640)
    _write_mode(root / "06-fill.bin", b"Q" * (32 * 1024 + 73), 0o644)
    _write_mode(root / "07-noise.bin", _hash_stream(32 * 1024 + 101, b"breadth-noise"), 0o600)
    _write_mode(root / "08-empty.bin", b"", 0o644)

    nested = root / "09-nested"
    nested.mkdir()
    nested.chmod(0o750)
    _write_mode(nested / "payload.txt", b"transfer-tree\n", 0o640)
    (root / "10-alias").symlink_to("09-nested/payload.txt")


def _filesystem_snapshot(root: Path) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if path.is_symlink():
            snapshot[rel] = {"kind": "symlink", "mode": mode, "target": path.readlink().as_posix()}
        elif path.is_dir():
            snapshot[rel] = {"kind": "dir", "mode": mode}
        elif path.is_file():
            data = path.read_bytes()
            snapshot[rel] = {"kind": "file", "mode": mode, "size": len(data), "sha256": sha256(data).hexdigest()}
        else:
            raise RuntimeError(f"unsupported transfer entry: {rel}")
    return snapshot


def _archive_snapshot(root: Path, wire: bytes) -> tuple[dict[str, dict[str, Any]], bool]:
    opened = open_authenticated_archive(wire)
    observed: dict[str, dict[str, Any]] = {}
    exact = True

    for rel, expected in _filesystem_snapshot(root).items():
        entry = opened.base.entries.get(rel)
        if entry is None:
            exact = False
            continue
        kind = expected["kind"]
        row: dict[str, Any] = {"kind": entry.get("kind"), "mode": entry.get("mode")}
        if kind == "file":
            data = opened.read_file(rel)
            row.update({"size": len(data), "sha256": sha256(data).hexdigest()})
        elif kind == "symlink":
            row["target"] = entry.get("target")
        observed[rel] = row
        if row != expected:
            exact = False

    if set(observed) != set(_filesystem_snapshot(root)):
        exact = False
    return observed, exact


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="one-g02-breadth-transfer-") as tmp:
        root = Path(tmp) / "tree"
        _build_transfer_tree(root)
        source_snapshot = _filesystem_snapshot(root)

        wire_a, stats_a = build_general_law_archive(root)
        wire_b, stats_b = build_general_law_archive(root)
        archive_snapshot, exact = _archive_snapshot(root, wire_a)
        opened = open_authenticated_archive(wire_a)
        ops = sorted({node.op for node in opened.program.nodes})

        gates = {
            "surprise_present": stats_a.surprise_roots > 0,
            "fill_present": stats_a.fill_roots > 0,
            "exact_reuse_present": stats_a.exact_reuse_roots > 0,
            "add8_present": stats_a.add8_roots > 0,
            "xor_present": stats_a.xor_roots > 0,
            "whole_tree_semantics_exact": exact and source_snapshot == archive_snapshot,
            "deterministic_wire": wire_a == wire_b and stats_a == stats_b,
            "generic_reader_ontology_only": set(ops) <= ALLOWED_OPS,
        }
        passed = all(gates.values())
        decision = "ADVANCE_GENERAL_LAW_BREADTH_ONLY" if passed else "HOLD_GENERAL_LAW_BREADTH"

        payload = {
            "schema": "cmpct-one-g02-general-law-breadth-transfer-v1",
            "experimental_version": "ONE-G0.2",
            "decision": decision,
            "claim_boundary": "transfer-only represented breadth; no Genesis corpus, comparator comparison, scoring, or winner selection",
            "gates": gates,
            "reader_ops": ops,
            "wire_sha256": sha256(wire_a).hexdigest(),
            "wire_bytes": len(wire_a),
            "stats": asdict(stats_a),
            "source_snapshot": source_snapshot,
            "archive_snapshot": archive_snapshot,
        }
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return payload


def main() -> int:
    payload = run()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["decision"] == "ADVANCE_GENERAL_LAW_BREADTH_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
