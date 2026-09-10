from __future__ import annotations

"""Transfer-only falsifier for the proposed ONE Genesis candidate product boundary.

Frozen by ONE_G02_GENESIS_CANDIDATE_ADAPTER_PROBE_PREREG_2026-09-10.md and repaired
under ONE_G02_SELECTIVE_SAFE_DISCOVERY_GATE_PREREG_2026-09-10.md after the original
hosted probe exposed a nested-Law selective incompatibility.
This module deliberately does not import or generate the frozen Genesis workload suites.
"""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

from experiments.one.general_law_archive import build_general_law_archive
from experiments.one.authenticated_archive_envelope import open_authenticated_archive

GENERIC_OPS = {"surprise", "concat", "repeat", "fill", "xor", "add8"}
FORBIDDEN_IMPORT_FRAGMENTS = (
    "one_genesis_gate_readiness",
    "neutral_hostile",
    "resemblance_hostile",
)


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _make_tree(root: Path) -> dict[str, bytes]:
    n = 64 * 1024
    base_a = _hash_stream(n, b"one-candidate-adapter-base-a")
    add_a = bytes(((b + 37) & 0xFF) for b in base_a)
    base_b = _hash_stream(n, b"one-candidate-adapter-base-b")
    xor_b = bytes((b ^ 0xA5) for b in base_b)
    files = {
        "00-base-a.bin": base_a,
        "01-add8-a.bin": add_a,
        "02-base-b.bin": base_b,
        "03-xor-b.bin": xor_b,
        "04-copy-xor.bin": xor_b,
        "05-fill.bin": b"Q" * n,
        "06-noise.bin": _hash_stream(n, b"one-candidate-adapter-noise"),
        "nested/tiny.txt": b"ONE transfer fixture\n",
        "empty.bin": b"",
    }
    for rel, payload in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return files


def _forbidden_imports() -> list[str]:
    return sorted(
        name for name in sys.modules
        if any(fragment in name.lower() for fragment in FORBIDDEN_IMPORT_FRAGMENTS)
    )


def run() -> dict:
    before_forbidden = _forbidden_imports()
    if before_forbidden:
        raise RuntimeError(f"Genesis workload module already imported: {before_forbidden}")

    with tempfile.TemporaryDirectory(prefix="cmpct-one-candidate-adapter-") as td:
        root = Path(td)
        expected = _make_tree(root)
        logical_bytes = sum(len(payload) for payload in expected.values())

        wire, stats = build_general_law_archive(root)
        wire2, stats2 = build_general_law_archive(root)
        if wire != wire2 or stats != stats2:
            raise AssertionError("ONE candidate archive is not deterministic on identical external input")

        opened = open_authenticated_archive(wire)
        ops = sorted({node.op for node in opened.program.nodes})
        if not set(ops) <= GENERIC_OPS:
            raise AssertionError(f"reader-visible ontology escaped generic ONE grammar: {ops}")

        selective_rows: list[dict] = []
        for rel, payload in sorted(expected.items()):
            whole = opened.read_file(rel)
            if whole != payload:
                raise AssertionError(f"whole reconstruction mismatch: {rel}")
            if payload:
                start = min(17, len(payload) - 1)
                length = min(4096, len(payload) - start)
                got, access = opened.read_range(rel, start, length)
                if got != payload[start : start + length]:
                    raise AssertionError(f"selective reconstruction mismatch: {rel}")
                if access.fallback:
                    raise AssertionError(f"selective read unexpectedly fell back: {rel}")
                selective_rows.append(
                    {
                        "path": rel,
                        "requested_bytes": length,
                        "cone_bytes": access.cone_bytes,
                        "source_read_bytes": access.source_read_bytes,
                        "proof_payload_bytes": access.proof_payload_bytes,
                        "proof_hash_bytes": access.proof_hash_bytes,
                        "auth_index_bytes": access.auth_index_bytes,
                        "fallback": access.fallback,
                    }
                )

        after_forbidden = _forbidden_imports()
        if after_forbidden:
            raise AssertionError(f"probe imported Genesis workload machinery: {after_forbidden}")

        stats_dict = asdict(stats)
        result = {
            "schema": "cmpct-one-g02-genesis-candidate-adapter-probe-v1",
            "experimental_version": "ONE-G0.2",
            "claim_boundary": "external transfer-tree product-boundary evidence only; no Genesis corpus; no timing/RSS or winner claim",
            "surface": {
                "builder": "experiments.one.general_law_archive.build_general_law_archive",
                "reader": "experiments.one.authenticated_archive_envelope.open_authenticated_archive",
            },
            "external_tree": {
                "files": len(expected),
                "logical_bytes": logical_bytes,
                "tree_sha256": sha256(
                    b"".join(
                        rel.encode("utf-8") + b"\0" + sha256(payload).digest()
                        for rel, payload in sorted(expected.items())
                    )
                ).hexdigest(),
            },
            "complete_stored_bytes": len(wire),
            "wire_sha256": sha256(wire).hexdigest(),
            "deterministic_wire": True,
            "stats": stats_dict,
            "reader_visible_ops": ops,
            "generic_reader_ontology_only": True,
            "whole_reconstruction_exact": True,
            "authenticated_selective_exact": True,
            "selective": selective_rows,
            "reader_burden": {"reader_discovery": False, "hidden_codec": False},
            "genesis_workload_modules_imported": False,
            "genesis_inputs_executed": False,
            "comparison_executed": False,
            "scoring_executed": False,
            "winner_selected": False,
        }

        required_classes = ("exact_reuse_roots", "fill_roots", "add8_roots", "xor_roots", "surprise_roots")
        missing_classes = [name for name in required_classes if int(stats_dict.get(name, 0)) < 1]
        if missing_classes:
            raise AssertionError(f"transfer fixture did not exercise required root classes: {missing_classes}")
        if len(wire) != int(stats_dict["wire_bytes"]):
            raise AssertionError("reported wire bytes differ from complete returned artifact")
        result["decision"] = "ADVANCE_ONE_ADAPTER_BOUNDARY"
        return result


def main() -> None:
    result = run()
    Path("one-g02-genesis-candidate-adapter-probe.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()