from __future__ import annotations

"""Transfer-only complete-wire geometry for ONE-G0.2 Crystallization economics."""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from typing import Any

from experiments.one.authenticated_archive_envelope import build_authenticated_archive, open_authenticated_archive
from experiments.one.general_law_archive import build_general_law_archive

LENGTHS = (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 4096, 16384)
FAMILIES = ("exact_reuse", "add8", "xor", "fill")
ALLOWED_OPS = {"surprise", "concat", "repeat", "fill", "xor", "add8"}
OUT = Path("one-g02-crystallization-wire-economics-geometry.json")


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    i = 0
    while len(out) < n:
        out.extend(sha256(seed + i.to_bytes(8, "little")).digest())
        i += 1
    return bytes(out[:n])


def _build_tree(root: Path, family: str, length: int) -> None:
    root.mkdir(parents=True)
    if family == "fill":
        (root / "target.bin").write_bytes(b"Q" * length)
        return
    source = _hash_stream(length, f"wire-geometry-{family}-{length}".encode())
    if family == "exact_reuse":
        target = source
    elif family == "add8":
        target = bytes(((value + 37) & 0xFF) for value in source)
    elif family == "xor":
        target = bytes((value ^ 0xA5) for value in source)
    else:
        raise KeyError(family)
    (root / "00-source.bin").write_bytes(source)
    (root / "01-target.bin").write_bytes(target)


def _root(opened: Any, path: str) -> Any:
    entry = opened.base.entries[path]
    return opened.program.roots[entry["root"]]


def _root_op(opened: Any, path: str) -> str:
    root = _root(opened, path)
    return opened.program.nodes[root.ref.node].op


def _structure(opened: Any, family: str) -> dict[str, Any]:
    if family == "fill":
        actual = _root_op(opened, "target.bin")
        return {"expected": "fill", "actual": actual, "ok": actual == "fill"}
    if family == "exact_reuse":
        source = _root(opened, "00-source.bin").ref
        target = _root(opened, "01-target.bin").ref
        return {"expected": "shared_root_ref", "shared_root_ref": source == target, "ok": source == target}
    expected = family
    actual = _root_op(opened, "01-target.bin")
    return {"expected": expected, "actual": actual, "ok": actual == expected}


def _snapshot(opened: Any) -> dict[str, tuple[int, str]]:
    result: dict[str, tuple[int, str]] = {}
    for path in opened.list_paths():
        entry = opened.base.entries[path]
        if entry["kind"] == "file":
            data = opened.read_file(path)
            result[path] = (len(data), sha256(data).hexdigest())
    return result


def _row(parent: Path, family: str, length: int) -> dict[str, Any]:
    root = parent / f"{family}-{length}"
    _build_tree(root, family, length)
    candidate_a, stats_a = build_general_law_archive(root)
    candidate_b, stats_b = build_general_law_archive(root)
    control, control_stats = build_authenticated_archive(root)
    opened = open_authenticated_archive(candidate_a)
    opened_control = open_authenticated_archive(control)
    expected = {
        path.relative_to(root).as_posix(): (len(path.read_bytes()), sha256(path.read_bytes()).hexdigest())
        for path in sorted(root.rglob("*")) if path.is_file()
    }
    structure = _structure(opened, family)
    ops = sorted({node.op for node in opened.program.nodes})
    semantic_exact = _snapshot(opened) == expected and _snapshot(opened_control) == expected
    deterministic = candidate_a == candidate_b and stats_a == stats_b
    candidate_bytes = len(candidate_a)
    control_bytes = len(control)
    delta = candidate_bytes - control_bytes
    return {
        "family": family,
        "length": length,
        "candidate_wire_bytes": candidate_bytes,
        "control_wire_bytes": control_bytes,
        "candidate_minus_control_bytes": delta,
        "candidate_ratio": candidate_bytes / control_bytes,
        "candidate_wire_sha256": sha256(candidate_a).hexdigest(),
        "control_wire_sha256": sha256(control).hexdigest(),
        "semantic_exact": semantic_exact,
        "deterministic_wire": deterministic,
        "generic_reader_ontology_only": set(ops) <= ALLOWED_OPS,
        "reader_ops": ops,
        "reader_structure_evidence": structure,
        "non_regressing": delta <= 0,
        "candidate_stats": asdict(stats_a),
        "control_stats": asdict(control_stats),
    }


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="one-g02-wire-geometry-") as td:
        parent = Path(td)
        rows = [_row(parent, family, length) for family in FAMILIES for length in LENGTHS]

    structural_ok = all(
        row["semantic_exact"]
        and row["deterministic_wire"]
        and row["generic_reader_ontology_only"]
        and row["reader_structure_evidence"]["ok"]
        for row in rows
    )
    first_non_regressing: dict[str, int | None] = {}
    eventually_non_regressing = True
    for family in FAMILIES:
        family_rows = [row for row in rows if row["family"] == family]
        hits = [row["length"] for row in family_rows if row["non_regressing"]]
        first_non_regressing[family] = min(hits) if hits else None
        eventually_non_regressing &= bool(hits)

    tiny_regression_present = any(row["length"] <= 16 and row["candidate_minus_control_bytes"] > 0 for row in rows)
    if not structural_ok:
        decision = "RETIRE_OR_REPAIR_CRYSTALLIZATION_ECONOMICS_MODEL"
    elif eventually_non_regressing:
        decision = "ADVANCE_CRYSTALLIZATION_ECONOMICS_MODEL"
    else:
        decision = "HOLD_CRYSTALLIZATION_ECONOMICS_MODEL"

    payload = {
        "schema": "cmpct-one-g02-crystallization-wire-economics-geometry-v1",
        "experimental_version": "ONE-G0.2",
        "claim_boundary": "synthetic transfer complete-wire economics geometry only; descriptive crossover evidence, not a product threshold or Genesis result",
        "lengths": list(LENGTHS),
        "families": list(FAMILIES),
        "rows": rows,
        "first_non_regressing_length": first_non_regressing,
        "tiny_regression_present": tiny_regression_present,
        "all_structural_gates_exact": structural_ok,
        "every_family_eventually_non_regressing": eventually_non_regressing,
        "decision": decision,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
