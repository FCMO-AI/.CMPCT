from __future__ import annotations

"""Transfer-only falsifier for ONE-G0.2 marginal-cost writer admission."""

from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any

from experiments.one.authenticated_archive_envelope import open_authenticated_archive
from experiments.one.general_law_archive import (
    build_general_law_archive,
    economically_admit_law,
    predicted_law_complete_delta_bytes,
)

OUT = Path("one-g02-economic-writer-admission.json")
ALLOWED_OPS = {"surprise", "concat", "repeat", "fill", "xor", "add8"}
BINARY_LENGTHS = (2, 4, 8, 9, 10, 11, 12, 16, 32, 256, 4096)
SIMPLE_LENGTHS = (1, 2, 8, 32, 4096)
UNRELATED_LENGTHS = (8, 32, 4096)
REPEATS = 5
TIMING_RELATIVE_REGRESSION = 0.05
TIMING_ABSOLUTE_REGRESSION_S = 0.003


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _write_pair(root: Path, relation: str, length: int) -> None:
    root.mkdir(parents=True)
    if relation == "fill":
        (root / "target.bin").write_bytes(b"Q" * length)
        return
    source = _hash_stream(length, f"economic-admission-{relation}-{length}".encode())
    if relation == "exact_reuse":
        target = source
    elif relation == "add8":
        target = bytes(((value + 37) & 0xFF) for value in source)
    elif relation == "xor":
        target = bytes((value ^ 0xA5) for value in source)
    elif relation == "unrelated":
        target = _hash_stream(length, f"economic-admission-unrelated-target-{length}".encode())
    else:
        raise KeyError(relation)
    (root / "00-source.bin").write_bytes(source)
    (root / "01-target.bin").write_bytes(target)


def _write_mixed(root: Path) -> None:
    root.mkdir(parents=True)
    short = _hash_stream(8, b"economic-mixed-short")
    (root / "00-short-source.bin").write_bytes(short)
    (root / "01-short-add8.bin").write_bytes(bytes(((x + 37) & 0xFF) for x in short))

    long = _hash_stream(32, b"economic-mixed-long")
    (root / "02-long-source.bin").write_bytes(long)
    (root / "03-long-xor.bin").write_bytes(bytes((x ^ 0xA5) for x in long))
    (root / "04-fill.bin").write_bytes(b"Q" * 8)

    reuse = _hash_stream(64, b"economic-mixed-reuse")
    (root / "05-reuse-source.bin").write_bytes(reuse)
    (root / "06-reuse-target.bin").write_bytes(reuse)
    (root / "07-noise.bin").write_bytes(_hash_stream(37, b"economic-mixed-noise"))
    (root / "08-empty.bin").write_bytes(b"")
    executable = root / "09-executable.bin"
    executable.write_bytes(_hash_stream(19, b"economic-mixed-executable"))
    executable.chmod(0o755)
    (root / "10-dir").mkdir()
    os.symlink("09-executable.bin", root / "11-link")


def _expected_snapshot(root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISDIR(info.st_mode):
            out[rel] = {"kind": "dir", "mode": mode}
        elif stat.S_ISLNK(info.st_mode):
            out[rel] = {"kind": "symlink", "mode": mode, "target": os.readlink(path)}
        elif stat.S_ISREG(info.st_mode):
            data = path.read_bytes()
            out[rel] = {"kind": "file", "mode": mode, "size": len(data), "sha256": sha256(data).hexdigest()}
        else:
            raise RuntimeError(f"unexpected transfer entry: {rel}")
    return out


def _opened_snapshot(opened: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for path in opened.list_paths():
        entry = opened.base.entries[path]
        if entry["kind"] == "file":
            data = opened.read_file(path)
            out[path] = {
                "kind": "file",
                "mode": int(entry["mode"]),
                "size": len(data),
                "sha256": sha256(data).hexdigest(),
            }
        elif entry["kind"] == "dir":
            out[path] = {"kind": "dir", "mode": int(entry["mode"])}
        elif entry["kind"] == "symlink":
            out[path] = {"kind": "symlink", "mode": int(entry["mode"]), "target": entry["target"]}
        else:
            raise RuntimeError(f"unexpected reader entry: {path}")
    return out


def _target_structure(opened: Any, relation: str) -> str:
    if relation == "fill":
        entry = opened.base.entries["target.bin"]
        root = opened.program.roots[entry["root"]]
        return opened.program.nodes[root.ref.node].op
    source_entry = opened.base.entries["00-source.bin"]
    target_entry = opened.base.entries["01-target.bin"]
    source_root = opened.program.roots[source_entry["root"]]
    target_root = opened.program.roots[target_entry["root"]]
    if relation == "exact_reuse" and source_root.ref == target_root.ref:
        return "exact_reuse"
    return opened.program.nodes[target_root.ref.node].op


def _resource_measure(root: Path, economic: bool) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "-m",
        "benchmarks.one.one_g02_economic_writer_admission_worker",
        str(root),
        "--repeats",
        str(REPEATS),
    ]
    if economic:
        cmd.append("--economic-admission")
    proc = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return json.loads(proc.stdout)


def _build_once(root: Path, economic: bool) -> tuple[bytes, Any, Any]:
    wire, stats = build_general_law_archive(root, economic_admission=economic)
    return wire, stats, open_authenticated_archive(wire)


def _timing_regression(candidate_s: float, base_s: float) -> bool:
    return (
        candidate_s - base_s > TIMING_ABSOLUTE_REGRESSION_S
        and candidate_s > base_s * (1.0 + TIMING_RELATIVE_REGRESSION)
    )


def _isolated_row(parent: Path, relation: str, length: int) -> dict[str, Any]:
    root = parent / f"{relation}-{length}"
    _write_pair(root, relation, length)
    expected = _expected_snapshot(root)
    wire_a, stats_a, opened_a = _build_once(root, False)
    wire_b, stats_b, opened_b = _build_once(root, True)
    wire_b2, stats_b2, _opened_b2 = _build_once(root, True)
    structure_a = _target_structure(opened_a, relation)
    structure_b = _target_structure(opened_b, relation)
    ops_a = sorted({node.op for node in opened_a.program.nodes})
    ops_b = sorted({node.op for node in opened_b.program.nodes})

    if relation in {"add8", "xor", "fill", "exact_reuse"}:
        predicted_delta = predicted_law_complete_delta_bytes(relation, length)
        predicted_admit = economically_admit_law(relation, length)
    else:
        predicted_delta = None
        predicted_admit = False

    expected_b_structure = relation if predicted_admit and relation != "unrelated" else "surprise"
    if relation == "exact_reuse" and predicted_admit:
        expected_b_structure = "exact_reuse"

    resource_a = _resource_measure(root, False)
    resource_b = _resource_measure(root, True)
    cpu_regression = _timing_regression(resource_b["median_cpu_s"], resource_a["median_cpu_s"])
    wall_regression = _timing_regression(resource_b["median_wall_s"], resource_a["median_wall_s"])

    return {
        "case": f"{relation}-{length}",
        "relation": relation,
        "length": length,
        "predicted_delta_bytes": predicted_delta,
        "predicted_admit": predicted_admit,
        "current_wire_bytes": len(wire_a),
        "economic_wire_bytes": len(wire_b),
        "economic_minus_current_bytes": len(wire_b) - len(wire_a),
        "current_structure": structure_a,
        "economic_structure": structure_b,
        "expected_economic_structure": expected_b_structure,
        "economic_structure_matches_model": structure_b == expected_b_structure,
        "semantic_exact": _opened_snapshot(opened_a) == expected and _opened_snapshot(opened_b) == expected,
        "economic_deterministic": wire_b == wire_b2 and stats_b == stats_b2,
        "generic_reader_ontology_only": set(ops_a) <= ALLOWED_OPS and set(ops_b) <= ALLOWED_OPS,
        "current_reader_ops": ops_a,
        "economic_reader_ops": ops_b,
        "current_stats": asdict(stats_a),
        "economic_stats": asdict(stats_b),
        "current_resource": resource_a,
        "economic_resource": resource_b,
        "cpu_regression_gate": cpu_regression,
        "wall_regression_gate": wall_regression,
        "complete_bytes_non_regressing": len(wire_b) <= len(wire_a),
    }


def _mixed_row(parent: Path) -> dict[str, Any]:
    root = parent / "mixed"
    _write_mixed(root)
    expected = _expected_snapshot(root)
    wire_a, stats_a, opened_a = _build_once(root, False)
    wire_b, stats_b, opened_b = _build_once(root, True)
    wire_b2, stats_b2, _ = _build_once(root, True)
    resource_a = _resource_measure(root, False)
    resource_b = _resource_measure(root, True)
    ops_b = sorted({node.op for node in opened_b.program.nodes})

    def op(opened: Any, path: str) -> str:
        entry = opened.base.entries[path]
        root_obj = opened.program.roots[entry["root"]]
        return opened.program.nodes[root_obj.ref.node].op

    current_shapes = {
        "short_add8": op(opened_a, "01-short-add8.bin"),
        "long_xor": op(opened_a, "03-long-xor.bin"),
        "fill": op(opened_a, "04-fill.bin"),
    }
    economic_shapes = {
        "short_add8": op(opened_b, "01-short-add8.bin"),
        "long_xor": op(opened_b, "03-long-xor.bin"),
        "fill": op(opened_b, "04-fill.bin"),
    }
    reuse_source = opened_b.program.roots[opened_b.base.entries["05-reuse-source.bin"]["root"]].ref
    reuse_target = opened_b.program.roots[opened_b.base.entries["06-reuse-target.bin"]["root"]].ref
    economic_shapes["exact_reuse"] = "exact_reuse" if reuse_source == reuse_target else op(opened_b, "06-reuse-target.bin")

    cpu_regression = _timing_regression(resource_b["median_cpu_s"], resource_a["median_cpu_s"])
    wall_regression = _timing_regression(resource_b["median_wall_s"], resource_a["median_wall_s"])
    shapes_ok = economic_shapes == {
        "short_add8": "surprise",
        "long_xor": "xor",
        "fill": "fill",
        "exact_reuse": "exact_reuse",
    }

    return {
        "case": "mixed",
        "current_wire_bytes": len(wire_a),
        "economic_wire_bytes": len(wire_b),
        "economic_minus_current_bytes": len(wire_b) - len(wire_a),
        "current_shapes": current_shapes,
        "economic_shapes": economic_shapes,
        "mixed_shapes_ok": shapes_ok,
        "semantic_exact": _opened_snapshot(opened_a) == expected and _opened_snapshot(opened_b) == expected,
        "economic_deterministic": wire_b == wire_b2 and stats_b == stats_b2,
        "generic_reader_ontology_only": set(ops_b) <= ALLOWED_OPS,
        "current_stats": asdict(stats_a),
        "economic_stats": asdict(stats_b),
        "current_resource": resource_a,
        "economic_resource": resource_b,
        "cpu_regression_gate": cpu_regression,
        "wall_regression_gate": wall_regression,
        "complete_bytes_non_regressing": len(wire_b) <= len(wire_a),
    }


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="one-g02-economic-writer-") as td:
        parent = Path(td)
        rows = [
            _isolated_row(parent, relation, length)
            for relation, lengths in (
                ("add8", BINARY_LENGTHS),
                ("xor", BINARY_LENGTHS),
                ("fill", SIMPLE_LENGTHS),
                ("exact_reuse", SIMPLE_LENGTHS),
                ("unrelated", UNRELATED_LENGTHS),
            )
            for length in lengths
        ]
        mixed = _mixed_row(parent)

    tiny_binary = [row for row in rows if row["relation"] in {"add8", "xor"} and row["length"] <= 10]
    predicted_law_rows = [row for row in rows if row["relation"] != "unrelated" and row["predicted_admit"]]
    h1 = all(row["complete_bytes_non_regressing"] for row in rows) and mixed["complete_bytes_non_regressing"]
    # Fail closed over every frozen row, including unrelated false-pattern controls. The
    # independent oracle separately re-derives expected admission for proved Law rows.
    h2 = all(row["economic_structure_matches_model"] for row in rows)
    h3 = all(row["semantic_exact"] and row["economic_deterministic"] and row["generic_reader_ontology_only"] for row in rows)
    h3 = h3 and mixed["semantic_exact"] and mixed["economic_deterministic"] and mixed["generic_reader_ontology_only"] and mixed["mixed_shapes_ok"]
    proof_a = sum(row["current_stats"]["discovery_exact_proof_bytes"] for row in tiny_binary)
    proof_b = sum(row["economic_stats"]["discovery_exact_proof_bytes"] for row in tiny_binary)
    h4 = proof_b < proof_a
    timing_regressions = [row["case"] for row in rows if row["cpu_regression_gate"] or row["wall_regression_gate"]]
    if mixed["cpu_regression_gate"] or mixed["wall_regression_gate"]:
        timing_regressions.append("mixed")
    h5 = not timing_regressions
    resource_complete = all(row["current_resource"]["peak_rss_kib"] > 0 and row["economic_resource"]["peak_rss_kib"] > 0 for row in rows)
    resource_complete &= mixed["current_resource"]["peak_rss_kib"] > 0 and mixed["economic_resource"]["peak_rss_kib"] > 0

    false_admits = [row["case"] for row in rows if not row["complete_bytes_non_regressing"]]
    false_rejects = [row["case"] for row in predicted_law_rows if not row["economic_structure_matches_model"]]
    false_patterns = [row["case"] for row in rows if row["relation"] == "unrelated" and not row["economic_structure_matches_model"]]
    if not h1 or not h3:
        decision = "RETIRE_OR_REPAIR_ECONOMIC_WRITER_ADMISSION"
    elif h2 and h4 and h5 and resource_complete:
        decision = "ADVANCE_ECONOMIC_WRITER_ADMISSION"
    else:
        decision = "HOLD_ECONOMIC_WRITER_ADMISSION"

    payload = {
        "schema": "cmpct-one-g02-economic-writer-admission-v1",
        "experimental_version": "ONE-G0.2",
        "claim_boundary": "synthetic transfer writer-selection evidence only; no Genesis inputs, comparators, scoring, or product-default promotion",
        "frozen_model": {"exact_reuse": -3, "fill": 1, "add8": 11, "xor": 11},
        "timing_gate": {"relative": TIMING_RELATIVE_REGRESSION, "absolute_seconds": TIMING_ABSOLUTE_REGRESSION_S},
        "rows": rows,
        "mixed": mixed,
        "hypotheses": {"H1_economic_safety": h1, "H2_opportunity_and_false_pattern_selection": h2, "H3_semantic_representation_invariance": h3, "H4_proof_work_pruning": h4, "H5_creation_cost_sanity": h5},
        "tiny_binary_current_exact_proof_bytes": proof_a,
        "tiny_binary_economic_exact_proof_bytes": proof_b,
        "proof_work_reduction_bytes": proof_a - proof_b,
        "false_admits": false_admits,
        "false_rejects": false_rejects,
        "false_patterns": false_patterns,
        "timing_regressions": timing_regressions,
        "resource_evidence_complete": resource_complete,
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
