from __future__ import annotations

"""Result-bearing transfer falsifier for the ONE-G0.2 general Law archive boundary.

Frozen by docs/one/prereg/ONE_G02_GENERAL_LAW_ARCHIVE_BOUNDARY_PREREG_2026-09-10.md.
This script uses synthetic/transfer fixtures only. It never imports or generates the
15-workload Genesis corpus and makes no timing/RSS claim.
"""

from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile

from experiments.one.authenticated_archive_envelope import build_authenticated_archive, open_authenticated_archive
from experiments.one.general_law_archive import SAMPLE_POINTS, _sample_positions, build_general_law_archive

GENERIC_OPS = {"surprise", "concat", "repeat", "fill", "xor", "add8"}


def _hash_stream(n: int, seed: bytes) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < n:
        out.extend(sha256(seed + counter.to_bytes(8, "little")).digest())
        counter += 1
    return bytes(out[:n])


def _pattern(n: int, seed: int) -> bytes:
    return bytes(((i * 73 + (i >> 3) * 19 + seed) & 0xFF) for i in range(n))


def _verify(root: Path, wire: bytes) -> dict:
    opened = open_authenticated_archive(wire)
    selective = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()):
        rel = path.relative_to(root).as_posix()
        expected = path.read_bytes()
        actual = opened.read_file(rel)
        if actual != expected:
            raise AssertionError(f"whole reconstruction mismatch: {rel}")
        if expected:
            start = min(17, len(expected) - 1)
            length = min(4096, len(expected) - start)
            got, stats = opened.read_range(rel, start, length)
            if got != expected[start : start + length]:
                raise AssertionError(f"selective reconstruction mismatch: {rel}")
            if stats.fallback:
                raise AssertionError(f"authenticated selective path unexpectedly fell back: {rel}")
            selective.append(
                {
                    "path": rel,
                    "requested_bytes": length,
                    "cone_bytes": stats.cone_bytes,
                    "source_read_bytes": stats.source_read_bytes,
                    "proof_payload_bytes": stats.proof_payload_bytes,
                    "proof_hash_bytes": stats.proof_hash_bytes,
                    "auth_index_bytes": stats.auth_index_bytes,
                    "fallback": stats.fallback,
                }
            )
    return {
        "whole_exact": True,
        "selective_exact": True,
        "generic_ops_only": {node.op for node in opened.program.nodes} <= GENERIC_OPS,
        "ops": sorted({node.op for node in opened.program.nodes}),
        "selective": selective,
    }


def _case(root: Path, name: str, files: list[tuple[str, bytes]]) -> dict:
    case_root = root / name
    case_root.mkdir(parents=True)
    for filename, data in files:
        path = case_root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    candidate_wire, candidate_stats = build_general_law_archive(case_root)
    candidate_wire_2, candidate_stats_2 = build_general_law_archive(case_root)
    baseline_wire, baseline_stats = build_authenticated_archive(case_root)
    if candidate_wire != candidate_wire_2 or candidate_stats != candidate_stats_2:
        raise AssertionError(f"{name}: candidate build is non-deterministic")

    verify = _verify(case_root, candidate_wire)
    if not verify["generic_ops_only"]:
        raise AssertionError(f"{name}: reader-visible operation escaped generic grammar")

    return {
        "name": name,
        "logical_bytes": candidate_stats.logical_file_bytes,
        "candidate": asdict(candidate_stats),
        "authenticated_surprise_control": {
            "wire_bytes": baseline_stats.wire_bytes,
            "raw_auth_index_bytes": baseline_stats.raw_auth_index_bytes,
            "source_reread_bytes": baseline_stats.source_reread_bytes,
        },
        "wire_delta_bytes": len(candidate_wire) - len(baseline_wire),
        "wire_ratio": len(candidate_wire) / len(baseline_wire) if baseline_wire else 1.0,
        "wire_byte_identical_to_control": candidate_wire == baseline_wire,
        "deterministic_wire": True,
        "verify": verify,
    }


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="cmpct-one-g02-general-law-archive-") as td:
        root = Path(td)
        n = 64 * 1024
        base = _pattern(n, 11)
        add = bytes(((b + 37) & 0xFF) for b in base)
        xor = bytes((b ^ 0xA5) for b in add)

        mixed = _case(
            root,
            "mixed_law_tree",
            [
                ("00-base.bin", base),
                ("01-copy.bin", base),
                ("02-add8.bin", add),
                ("03-xor.bin", xor),
                ("04-fill.bin", b"Z" * n),
                ("05-noise.bin", _hash_stream(n, b"noise")),
                ("nested/tiny.txt", b"tiny"),
                ("empty.bin", b""),
            ],
        )
        classes = mixed["candidate"]
        if not all(classes[key] >= 1 for key in (
            "exact_reuse_roots", "fill_roots", "add8_roots", "xor_roots", "surprise_roots"
        )):
            raise AssertionError("mixed tree did not exercise every required root class")
        if mixed["wire_delta_bytes"] >= 0:
            raise AssertionError("Law-bearing mixed archive did not beat authenticated Surprise control")

        random_control = _case(
            root,
            "unrelated_hash_streams",
            [("a.bin", _hash_stream(n, b"a")), ("b.bin", _hash_stream(n, b"b"))],
        )
        rc = random_control["candidate"]
        if any(rc[key] != 0 for key in ("exact_reuse_roots", "fill_roots", "add8_roots", "xor_roots")):
            raise AssertionError("unrelated control produced a false Law")
        if rc["discovery_exact_proof_bytes"] != 0:
            raise AssertionError("unrelated control paid a full exact relation proof after negative samples")
        if rc["discovery_sample_bytes"] != SAMPLE_POINTS * 6:
            raise AssertionError("unrelated control exceeded fixed nomination sample budget")
        if not random_control["wire_byte_identical_to_control"]:
            raise AssertionError("Surprise-only fallback exported wire overhead")

        false_root = root / "false_pattern"
        false_root.mkdir()
        source = _pattern(4097, 17)
        target = bytearray(((b + 7) & 0xFF) for b in source)
        sample_set = set(_sample_positions(len(source)))
        adversary = next(i for i in range(len(source)) if i not in sample_set)
        target[adversary] ^= 1
        (false_root / "a.bin").write_bytes(source)
        (false_root / "b.bin").write_bytes(bytes(target))
        false_wire, false_stats = build_general_law_archive(false_root)
        false_verify = _verify(false_root, false_wire)
        if false_stats.add8_roots != 0:
            raise AssertionError("sample false positive escaped exact ADD8 proof")
        if false_stats.discovery_exact_proof_bytes < len(source) * 2:
            raise AssertionError("false-positive fixture did not actually consume exact proof")

        result = {
            "schema": "cmpct-one-g02-general-law-archive-boundary-v1",
            "experimental_version": "ONE-G0.2",
            "claim_boundary": "synthetic/transfer boundary completeness and causal wire evidence only; no Genesis corpus; no timing/RSS claim",
            "cases": [mixed, random_control],
            "false_pattern": {
                "logical_bytes": false_stats.logical_file_bytes,
                "candidate": asdict(false_stats),
                "verify": false_verify,
                "adversarial_byte_index": adversary,
            },
            "gates": {
                "whole_reconstruction_exact": True,
                "authenticated_selective_exact": True,
                "deterministic_wire": True,
                "generic_reader_ontology_only": True,
                "unrelated_false_laws": 0,
                "unrelated_exact_relation_proof_bytes": rc["discovery_exact_proof_bytes"],
                "unrelated_nomination_sample_bytes": rc["discovery_sample_bytes"],
                "unrelated_fallback_wire_byte_identical": random_control["wire_byte_identical_to_control"],
                "false_pattern_add8_roots": false_stats.add8_roots,
                "false_pattern_exact_proof_exercised": false_stats.discovery_exact_proof_bytes >= len(source) * 2,
                "auth_source_reread_bytes": mixed["candidate"]["authentication_source_reread_bytes"],
            },
        }
        result["decision"] = "ADVANCE_BOUNDARY_SEED"
        return result


def main() -> None:
    result = run()
    output = Path("one-g02-general-law-archive-boundary.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
