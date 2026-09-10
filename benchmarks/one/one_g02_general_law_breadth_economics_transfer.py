from __future__ import annotations

"""Transfer-only complete-byte economics for general Law versus Surprise-only ONE."""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from typing import Any

from benchmarks.one import one_g02_general_law_breadth_transfer as breadth
from experiments.one.archive_envelope import build_archive as build_surprise_archive
from experiments.one.archive_envelope import open_archive as open_surprise_archive
from experiments.one.authenticated_archive_envelope import open_authenticated_archive
from experiments.one.general_law_archive import build_general_law_archive

OUT = Path("one-g02-general-law-breadth-economics-transfer.json")


def _opened_snapshot(source: dict[str, dict[str, Any]], opened: Any) -> tuple[dict[str, dict[str, Any]], bool]:
    observed: dict[str, dict[str, Any]] = {}
    exact = True
    for rel, expected in source.items():
        entry = opened.entries.get(rel) if hasattr(opened, "entries") else opened.base.entries.get(rel)
        if entry is None:
            exact = False
            continue
        row: dict[str, Any] = {"kind": entry.get("kind"), "mode": entry.get("mode")}
        if expected["kind"] == "file":
            data = opened.read_file(rel)
            row.update({"size": len(data), "sha256": sha256(data).hexdigest()})
        elif expected["kind"] == "symlink":
            row["target"] = entry.get("target")
        observed[rel] = row
        if row != expected:
            exact = False
    return observed, exact and set(observed) == set(source)


def run() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="one-g02-breadth-economics-") as tmp:
        root = Path(tmp) / "tree"
        breadth._build_transfer_tree(root)
        source = breadth._filesystem_snapshot(root)
        logical_bytes = sum(int(row.get("size", 0)) for row in source.values() if row["kind"] == "file")

        law_wire_a, law_stats_a = build_general_law_archive(root)
        law_wire_b, law_stats_b = build_general_law_archive(root)
        surprise_wire_a, surprise_stats_a = build_surprise_archive(root)
        surprise_wire_b, surprise_stats_b = build_surprise_archive(root)

        law_opened = open_authenticated_archive(law_wire_a)
        surprise_opened = open_surprise_archive(surprise_wire_a)
        law_snapshot, law_exact = _opened_snapshot(source, law_opened)
        surprise_snapshot, surprise_exact = _opened_snapshot(source, surprise_opened)
        reader_structure, reader_structure_exact = breadth._reader_relation_structure(law_opened)
        law_ops = sorted({node.op for node in law_opened.program.nodes})
        surprise_ops = sorted({node.op for node in surprise_opened.program.nodes})

        law_bytes = len(law_wire_a)
        surprise_bytes = len(surprise_wire_a)
        gates = {
            "law_whole_tree_semantics_exact": law_exact and law_snapshot == source,
            "surprise_whole_tree_semantics_exact": surprise_exact and surprise_snapshot == source,
            "law_deterministic_wire": law_wire_a == law_wire_b and law_stats_a == law_stats_b,
            "surprise_deterministic_wire": surprise_wire_a == surprise_wire_b and surprise_stats_a == surprise_stats_b,
            "reader_relation_structure_exact": reader_structure_exact,
            "generic_reader_ontology_only": set(law_ops) <= breadth.ALLOWED_OPS and set(surprise_ops) <= breadth.ALLOWED_OPS,
            "complete_stored_bytes_nonregression": law_bytes <= surprise_bytes,
        }
        decision = (
            "ADVANCE_BREADTH_REPRESENTATION_ECONOMICS_ONLY"
            if all(gates.values())
            else "HOLD_BREADTH_REPRESENTATION_ECONOMICS"
        )
        payload = {
            "schema": "cmpct-one-g02-general-law-breadth-economics-transfer-v1",
            "experimental_version": "ONE-G0.2",
            "decision": decision,
            "claim_boundary": "transfer-only complete persistent-byte representation economics; no Genesis corpus, frozen comparator, timing/RSS promotion, scoring, or winner selection",
            "logical_source_bytes": logical_bytes,
            "gates": gates,
            "law": {
                "stored_bytes": law_bytes,
                "wire_sha256": sha256(law_wire_a).hexdigest(),
                "stats": asdict(law_stats_a),
                "reader_ops": law_ops,
                "reader_relation_structure": reader_structure,
            },
            "surprise_only": {
                "stored_bytes": surprise_bytes,
                "wire_sha256": sha256(surprise_wire_a).hexdigest(),
                "stats": asdict(surprise_stats_a),
                "reader_ops": surprise_ops,
            },
            "stored_byte_delta": law_bytes - surprise_bytes,
            "law_over_surprise_stored_ratio": law_bytes / surprise_bytes if surprise_bytes else None,
            "comparison_executed": False,
            "scoring_executed": False,
            "winner_selected": False,
        }
        OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return payload


def main() -> int:
    payload = run()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["decision"] == "ADVANCE_BREADTH_REPRESENTATION_ECONOMICS_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
