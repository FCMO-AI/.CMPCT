from __future__ import annotations

"""Transfer-only hostile falsifier for sampled Law nomination collisions.

Constructs ADD8/XOR near-misses that satisfy every frozen discovery sample but disagree at
one unsampled byte.  Genesis inputs are never used.
"""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from typing import Any

from experiments.one.authenticated_archive_envelope import open_authenticated_archive
from experiments.one.general_law_archive import (
    SAMPLE_POINTS,
    _sample_positions,
    build_general_law_archive,
    economically_admit_law,
)

OUT = Path("one-g02-economic-writer-sampler-collision.json")
LENGTHS = (17, 32, 256, 4096)
RELATIONS = ("add8", "xor")
ALLOWED_OPS = {"surprise", "concat", "repeat", "fill", "xor", "add8"}


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _oracle_sample_positions(length: int) -> tuple[int, ...]:
    """Independent transcription of the preregistered 16-point sampling geometry."""
    if length <= 0:
        return ()
    if length <= SAMPLE_POINTS:
        return tuple(range(length))
    return tuple(sorted({(i * (length - 1)) // (SAMPLE_POINTS - 1) for i in range(SAMPLE_POINTS)}))


def _relation_holds(relation: str, source: int, target: int) -> bool:
    if relation == "add8":
        return ((source + 37) & 0xFF) == target
    if relation == "xor":
        return (source ^ 0xA5) == target
    raise KeyError(relation)


def _write_near_miss(root: Path, relation: str, length: int) -> tuple[bytes, bytes, int, tuple[int, ...]]:
    root.mkdir(parents=True)
    source = _hash_stream(length, f"one-g02-sampler-collision-source-{relation}-{length}".encode())
    if relation == "add8":
        target = bytearray(((value + 37) & 0xFF) for value in source)
    elif relation == "xor":
        target = bytearray((value ^ 0xA5) for value in source)
    else:
        raise KeyError(relation)

    positions = _oracle_sample_positions(length)
    unsampled = [index for index in range(length) if index not in positions]
    if not unsampled:
        raise RuntimeError(f"hostile row has no unsampled poison position: {relation}-{length}")
    poison = unsampled[0]
    target[poison] ^= 0x01

    source_path = root / "00-source.bin"
    target_path = root / "01-target.bin"
    source_path.write_bytes(source)
    target_path.write_bytes(bytes(target))
    return source, bytes(target), poison, positions


def _snapshot(opened: Any) -> dict[str, str]:
    return {path: sha256(opened.read_file(path)).hexdigest() for path in opened.list_paths()}


def _expected_snapshot(root: Path) -> dict[str, str]:
    return {path.name: sha256(path.read_bytes()).hexdigest() for path in sorted(root.iterdir()) if path.is_file()}


def _target_structure(opened: Any) -> str:
    entry = opened.base.entries["01-target.bin"]
    root = opened.program.roots[entry["root"]]
    return opened.program.nodes[root.ref.node].op


def _row(parent: Path, relation: str, length: int) -> dict[str, Any]:
    root = parent / f"{relation}-{length}"
    source, target, poison, oracle_positions = _write_near_miss(root, relation, length)
    writer_positions = tuple(_sample_positions(length))

    sampled_relation_holds = all(_relation_holds(relation, source[index], target[index]) for index in oracle_positions)
    poison_breaks_relation = not _relation_holds(relation, source[poison], target[poison])

    current_wire, current_stats = build_general_law_archive(root, economic_admission=False)
    economic_wire, economic_stats = build_general_law_archive(root, economic_admission=True)
    economic_wire_2, economic_stats_2 = build_general_law_archive(root, economic_admission=True)
    current_opened = open_authenticated_archive(current_wire)
    economic_opened = open_authenticated_archive(economic_wire)
    expected = _expected_snapshot(root)

    current_structure = _target_structure(current_opened)
    economic_structure = _target_structure(economic_opened)
    current_ops = sorted({node.op for node in current_opened.program.nodes})
    economic_ops = sorted({node.op for node in economic_opened.program.nodes})

    return {
        "case": f"{relation}-{length}",
        "relation": relation,
        "length": length,
        "poison_index": poison,
        "oracle_sample_positions": list(oracle_positions),
        "writer_sample_positions": list(writer_positions),
        "sampler_matches_frozen_oracle": writer_positions == oracle_positions,
        "sampled_relation_holds": sampled_relation_holds,
        "poison_breaks_relation": poison_breaks_relation,
        "economic_model_admits": economically_admit_law(relation, length),
        "current_structure": current_structure,
        "economic_structure": economic_structure,
        "false_relation_rejected": current_structure == "surprise" and economic_structure == "surprise",
        "semantic_exact": _snapshot(current_opened) == expected and _snapshot(economic_opened) == expected,
        "economic_deterministic": economic_wire == economic_wire_2 and economic_stats == economic_stats_2,
        "generic_reader_ontology_only": set(current_ops) <= ALLOWED_OPS and set(economic_ops) <= ALLOWED_OPS,
        "current_wire_bytes": len(current_wire),
        "economic_wire_bytes": len(economic_wire),
        "economic_minus_current_bytes": len(economic_wire) - len(current_wire),
        "complete_bytes_non_regressing": len(economic_wire) <= len(current_wire),
        "current_exact_proof_bytes": current_stats.discovery_exact_proof_bytes,
        "economic_exact_proof_bytes": economic_stats.discovery_exact_proof_bytes,
        "proof_accounting_equal": current_stats.discovery_exact_proof_bytes == economic_stats.discovery_exact_proof_bytes,
        "proof_work_nonzero": economic_stats.discovery_exact_proof_bytes > 0,
        "current_stats": asdict(current_stats),
        "economic_stats": asdict(economic_stats),
        "current_reader_ops": current_ops,
        "economic_reader_ops": economic_ops,
    }


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="one-g02-sampler-collision-") as td:
        parent = Path(td)
        rows = [_row(parent, relation, length) for relation in RELATIONS for length in LENGTHS]

    h1 = all(
        row["sampler_matches_frozen_oracle"]
        and row["sampled_relation_holds"]
        and row["poison_breaks_relation"]
        for row in rows
    )
    h2 = all(row["false_relation_rejected"] for row in rows)
    h3 = all(
        row["semantic_exact"]
        and row["economic_deterministic"]
        and row["generic_reader_ontology_only"]
        and row["complete_bytes_non_regressing"]
        for row in rows
    )
    h4 = all(
        row["economic_model_admits"]
        and row["proof_work_nonzero"]
        and row["proof_accounting_equal"]
        for row in rows
    )

    if not h1 or not h3:
        decision = "RETIRE_OR_REPAIR_SAMPLER_COLLISION_SAFETY"
    elif not h2 or not h4:
        decision = "HOLD_SAMPLER_COLLISION_SAFETY"
    else:
        decision = "ADVANCE_SAMPLER_COLLISION_SAFETY_ONLY"

    result = {
        "schema": "cmpct-one-g02-economic-writer-sampler-collision-v1",
        "experimental_version": "ONE-G0.2",
        "sample_points": SAMPLE_POINTS,
        "relations": list(RELATIONS),
        "lengths": list(LENGTHS),
        "rows": rows,
        "hypotheses": {
            "H1_sampler_collision_real": h1,
            "H2_false_pattern_safety": h2,
            "H3_semantic_representation_safety": h3,
            "H4_proof_accounting_causality": h4,
        },
        "false_survivors": [row["case"] for row in rows if not row["false_relation_rejected"]],
        "decision": decision,
        "claim_boundary": "transfer-only adversarial sampler-collision safety; not density promotion, not product threshold, not Genesis",
        "genesis_inputs_executed": False,
        "genesis_comparison_executed": False,
        "genesis_scoring_executed": False,
        "genesis_winner_selected": False,
    }
    return result


def main() -> int:
    result = run()
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
