from __future__ import annotations

"""Transfer-only falsifier for the ONE-G0.2 general candidate product boundary.

This module intentionally does not import any Genesis corpus builder or comparator. A HOLD
is a scientific result, not a process failure, so main exits successfully after persisting
its receipt unless the harness itself raises.
"""

from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Callable

from experiments.one.authenticated_archive_envelope import (
    build_authenticated_archive,
    open_authenticated_archive,
)
from experiments.one.general_law_archive import build_general_law_archive

OUT = Path("one-g02-general-candidate-boundary-hostile-economics.json")
ALLOWED_OPS = {"surprise", "concat", "repeat", "fill", "xor", "add8"}
ADVANCE = "ADVANCE_GENERAL_CANDIDATE_BOUNDARY_ECONOMICS_PREFLIGHT"
HOLD = "HOLD_GENERAL_CANDIDATE_BOUNDARY_ECONOMICS"
EXPECTED_RELATION_FIELD: dict[str, str | None] = {
    "tiny_add8_2b": "add8_roots",
    "tiny_xor_2b": "xor_roots",
    "tiny_fill_1b": "fill_roots",
    "beneficial_add8_4k": "add8_roots",
    "beneficial_exact_reuse_4k": "exact_reuse_roots",
    "incompressible_pair_4k": None,
    "mixed_hostile_tree": "add8_roots",
}


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _write(path: Path, data: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(mode)


def _tiny_add8(root: Path) -> None:
    root.mkdir(parents=True)
    _write(root / "a.bin", bytes((7, 91)), 0o640)
    _write(root / "b.bin", bytes((8, 92)), 0o600)


def _tiny_xor(root: Path) -> None:
    root.mkdir(parents=True)
    _write(root / "a.bin", bytes((7, 91)), 0o640)
    _write(root / "b.bin", bytes((7 ^ 0xA5, 91 ^ 0xA5)), 0o600)


def _tiny_fill(root: Path) -> None:
    root.mkdir(parents=True)
    _write(root / "a.bin", b"Q", 0o644)


def _beneficial_add8(root: Path) -> None:
    root.mkdir(parents=True)
    base = _hash_stream(4096, b"candidate-boundary-add8")
    _write(root / "a.bin", base, 0o640)
    _write(root / "b.bin", bytes(((value + 37) & 0xFF) for value in base), 0o600)


def _beneficial_exact(root: Path) -> None:
    root.mkdir(parents=True)
    data = _hash_stream(4096, b"candidate-boundary-exact")
    _write(root / "a.bin", data, 0o640)
    _write(root / "b.bin", data, 0o600)


def _incompressible_pair(root: Path) -> None:
    root.mkdir(parents=True)
    _write(root / "a.bin", _hash_stream(4096, b"candidate-boundary-random-a"), 0o640)
    _write(root / "b.bin", _hash_stream(4096, b"candidate-boundary-random-b"), 0o600)


def _mixed_hostile(root: Path) -> None:
    root.mkdir(parents=True)
    _write(root / "00-small-base.bin", bytes((1, 19)), 0o640)
    _write(root / "01-small-add.bin", bytes((2, 20)), 0o600)
    _write(root / "02-noise.bin", _hash_stream(257, b"candidate-boundary-mixed-noise"), 0o755)
    _write(root / "03-empty.bin", b"", 0o644)
    nested = root / "04-dir"
    nested.mkdir()
    nested.chmod(0o750)
    _write(nested / "payload.txt", b"portable-transfer-only\n", 0o640)
    (root / "05-link").symlink_to("04-dir/payload.txt")


BUILDERS: tuple[tuple[str, Callable[[Path], None]], ...] = (
    ("tiny_add8_2b", _tiny_add8),
    ("tiny_xor_2b", _tiny_xor),
    ("tiny_fill_1b", _tiny_fill),
    ("beneficial_add8_4k", _beneficial_add8),
    ("beneficial_exact_reuse_4k", _beneficial_exact),
    ("incompressible_pair_4k", _incompressible_pair),
    ("mixed_hostile_tree", _mixed_hostile),
)


def _source_snapshot(root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISLNK(info.st_mode):
            rows[rel] = {"kind": "symlink", "mode": mode, "target": os.readlink(path)}
        elif stat.S_ISDIR(info.st_mode):
            rows[rel] = {"kind": "dir", "mode": mode}
        elif stat.S_ISREG(info.st_mode):
            data = path.read_bytes()
            rows[rel] = {
                "kind": "file",
                "mode": mode,
                "size": len(data),
                "sha256": sha256(data).hexdigest(),
            }
        else:
            raise RuntimeError(f"unsupported transfer entry: {rel}")
    return rows


def _archive_snapshot(wire: bytes) -> dict[str, dict[str, Any]]:
    opened = open_authenticated_archive(wire)
    rows: dict[str, dict[str, Any]] = {}
    for rel in opened.list_paths():
        entry = opened.base.entries[rel]
        kind = entry["kind"]
        row: dict[str, Any] = {"kind": kind, "mode": entry["mode"]}
        if kind == "file":
            data = opened.read_file(rel)
            row.update({"size": len(data), "sha256": sha256(data).hexdigest()})
        elif kind == "symlink":
            row["target"] = entry["target"]
        rows[rel] = row
    return rows


def _entry_root(opened: Any, path: str) -> Any:
    entry = opened.base.entries[path]
    return opened.program.roots[entry["root"]]


def _entry_root_op(opened: Any, path: str) -> str:
    root = _entry_root(opened, path)
    return opened.program.nodes[root.ref.node].op


def _reader_structure_evidence(name: str, opened: Any) -> dict[str, Any]:
    """Prove the preregistered structure from the reader graph, not writer counters."""
    if name == "tiny_add8_2b":
        actual = _entry_root_op(opened, "b.bin")
        return {"kind": "root_op", "path": "b.bin", "expected": "add8", "actual": actual, "ok": actual == "add8"}
    if name == "tiny_xor_2b":
        actual = _entry_root_op(opened, "b.bin")
        return {"kind": "root_op", "path": "b.bin", "expected": "xor", "actual": actual, "ok": actual == "xor"}
    if name == "tiny_fill_1b":
        actual = _entry_root_op(opened, "a.bin")
        return {"kind": "root_op", "path": "a.bin", "expected": "fill", "actual": actual, "ok": actual == "fill"}
    if name == "beneficial_add8_4k":
        actual = _entry_root_op(opened, "b.bin")
        return {"kind": "root_op", "path": "b.bin", "expected": "add8", "actual": actual, "ok": actual == "add8"}
    if name == "beneficial_exact_reuse_4k":
        left = _entry_root(opened, "a.bin").ref
        right = _entry_root(opened, "b.bin").ref
        return {"kind": "shared_root_ref", "left": "a.bin", "right": "b.bin", "ok": left == right}
    if name == "incompressible_pair_4k":
        left = _entry_root(opened, "a.bin").ref
        right = _entry_root(opened, "b.bin").ref
        left_op = _entry_root_op(opened, "a.bin")
        right_op = _entry_root_op(opened, "b.bin")
        ok = left_op == right_op == "surprise" and left != right
        return {
            "kind": "independent_surprise_roots",
            "left_op": left_op,
            "right_op": right_op,
            "distinct_refs": left != right,
            "ok": ok,
        }
    if name == "mixed_hostile_tree":
        actual = _entry_root_op(opened, "01-small-add.bin")
        return {
            "kind": "root_op",
            "path": "01-small-add.bin",
            "expected": "add8",
            "actual": actual,
            "ok": actual == "add8",
        }
    raise KeyError(name)


def _run_row(name: str, builder: Callable[[Path], None], parent: Path) -> dict[str, Any]:
    root = parent / name
    builder(root)
    expected = _source_snapshot(root)

    law_wire_a, law_stats_a = build_general_law_archive(root)
    law_wire_b, law_stats_b = build_general_law_archive(root)
    surprise_wire, surprise_stats = build_authenticated_archive(root)

    law_opened = open_authenticated_archive(law_wire_a)
    law_snapshot = _archive_snapshot(law_wire_a)
    surprise_snapshot = _archive_snapshot(surprise_wire)
    ops = sorted({node.op for node in law_opened.program.nodes})
    structure_evidence = _reader_structure_evidence(name, law_opened)

    law_bytes = len(law_wire_a)
    surprise_bytes = len(surprise_wire)
    delta = law_bytes - surprise_bytes
    gates = {
        "law_semantics_exact": law_snapshot == expected,
        "surprise_semantics_exact": surprise_snapshot == expected,
        "deterministic_law_wire": law_wire_a == law_wire_b and law_stats_a == law_stats_b,
        "generic_reader_ontology_only": set(ops) <= ALLOWED_OPS,
        "expected_structure_exercised": structure_evidence["ok"],
        "complete_bytes_non_regressing": law_bytes <= surprise_bytes,
    }
    return {
        "name": name,
        "expected_relation_field": EXPECTED_RELATION_FIELD[name],
        "reader_structure_evidence": structure_evidence,
        "decision": "PASS" if all(gates.values()) else "HOLD",
        "gates": gates,
        "law_wire_bytes": law_bytes,
        "surprise_wire_bytes": surprise_bytes,
        "law_minus_surprise_bytes": delta,
        "law_ratio": law_bytes / surprise_bytes if surprise_bytes else 1.0,
        "law_wire_sha256": sha256(law_wire_a).hexdigest(),
        "surprise_wire_sha256": sha256(surprise_wire).hexdigest(),
        "reader_ops": ops,
        "law_stats": asdict(law_stats_a),
        "surprise_stats": asdict(surprise_stats),
    }


def _aggregate_decision(rows: list[dict[str, Any]]) -> str:
    """Apply the preregistered per-row no-regression rule without averaging losses away."""
    return ADVANCE if rows and all(row["decision"] == "PASS" for row in rows) else HOLD


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="one-g02-candidate-hostile-") as tmp:
        parent = Path(tmp)
        rows = [_run_row(name, builder, parent) for name, builder in BUILDERS]

    losing_rows = [
        {
            "name": row["name"],
            "law_minus_surprise_bytes": row["law_minus_surprise_bytes"],
            "failed_gates": sorted(name for name, passed in row["gates"].items() if not passed),
        }
        for row in rows
        if row["decision"] != "PASS"
    ]
    payload = {
        "schema": "cmpct-one-g02-general-candidate-boundary-hostile-economics-v1",
        "experimental_version": "ONE-G0.2",
        "decision": _aggregate_decision(rows),
        "claim_boundary": (
            "transfer-only necessary-property falsifier; no Genesis inputs, comparator comparison, "
            "scoring, or winner selection"
        ),
        "rows": rows,
        "losing_rows": losing_rows,
        "genesis_inputs_executed": False,
        "genesis_comparison_executed": False,
        "genesis_scoring_executed": False,
        "genesis_winner_selected": False,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    payload = run()
    print(json.dumps(payload, indent=2, sort_keys=True))
    # Scientific HOLD is a valid completed experiment. Harness exceptions still fail CI.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
