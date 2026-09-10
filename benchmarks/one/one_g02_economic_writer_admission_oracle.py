from __future__ import annotations

"""Independent transfer oracle for ONE-G0.2 economic writer admission.

The oracle deliberately does not import the writer's marginal-cost helpers. Expected
admission is derived again from the frozen preregistration constants, then checked against
the reader-visible graph produced by the economic writer.
"""

from hashlib import sha256
import json
from pathlib import Path
import tempfile
from typing import Any

from experiments.one.authenticated_archive_envelope import open_authenticated_archive
from experiments.one.general_law_archive import build_general_law_archive

OUT = Path("one-g02-economic-writer-admission-oracle.json")
FROZEN_K = {"exact_reuse": -3, "fill": 1, "add8": 11, "xor": 11}
BINARY_LENGTHS = (2, 4, 8, 9, 10, 11, 12, 16, 32, 256, 4096)
SIMPLE_LENGTHS = (1, 2, 8, 32, 4096)


def _stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _oracle_admit(relation: str, length: int) -> bool:
    if relation not in FROZEN_K or length < 0:
        raise ValueError("oracle relation/length outside frozen contract")
    return FROZEN_K[relation] - length <= 0


def _write_case(root: Path, relation: str, length: int) -> None:
    root.mkdir(parents=True)
    if relation == "fill":
        (root / "target.bin").write_bytes(b"Q" * length)
        return
    source = _stream(length, f"oracle-{relation}-{length}".encode())
    if relation == "exact_reuse":
        target = source
    elif relation == "add8":
        target = bytes(((x + 37) & 0xFF) for x in source)
    elif relation == "xor":
        target = bytes((x ^ 0xA5) for x in source)
    else:
        raise KeyError(relation)
    (root / "00-source.bin").write_bytes(source)
    (root / "01-target.bin").write_bytes(target)


def _reader_relation(wire: bytes, relation: str) -> str:
    opened = open_authenticated_archive(wire)
    if relation == "fill":
        entry = opened.base.entries["target.bin"]
        ref = opened.program.roots[entry["root"]].ref
        return opened.program.nodes[ref.node].op
    source = opened.program.roots[opened.base.entries["00-source.bin"]["root"]].ref
    target = opened.program.roots[opened.base.entries["01-target.bin"]["root"]].ref
    if relation == "exact_reuse" and source == target:
        return "exact_reuse"
    return opened.program.nodes[target.node].op


def run() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="one-g02-admission-oracle-") as td:
        parent = Path(td)
        for relation, lengths in (
            ("add8", BINARY_LENGTHS),
            ("xor", BINARY_LENGTHS),
            ("fill", SIMPLE_LENGTHS),
            ("exact_reuse", SIMPLE_LENGTHS),
        ):
            for length in lengths:
                root = parent / f"{relation}-{length}"
                _write_case(root, relation, length)
                wire, _stats = build_general_law_archive(root, economic_admission=True)
                actual = _reader_relation(wire, relation)
                admit = _oracle_admit(relation, length)
                expected = relation if admit else "surprise"
                rows.append({
                    "case": f"{relation}-{length}",
                    "relation": relation,
                    "length": length,
                    "oracle_k": FROZEN_K[relation],
                    "oracle_predicted_delta": FROZEN_K[relation] - length,
                    "oracle_admit": admit,
                    "expected_reader_relation": expected,
                    "actual_reader_relation": actual,
                    "match": actual == expected,
                })

    mismatches = [row for row in rows if not row["match"]]
    payload = {
        "schema": "cmpct-one-g02-economic-writer-admission-oracle-v1",
        "experimental_version": "ONE-G0.2",
        "claim_boundary": "independent transfer admission oracle only; no Genesis input/comparator/scoring",
        "frozen_k": FROZEN_K,
        "rows": rows,
        "mismatches": mismatches,
        "decision": "ADVANCE_INDEPENDENT_ADMISSION_ORACLE" if not mismatches else "HOLD_INDEPENDENT_ADMISSION_ORACLE",
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
