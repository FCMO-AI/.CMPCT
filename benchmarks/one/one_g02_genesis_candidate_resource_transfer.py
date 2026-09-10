from __future__ import annotations

"""Transfer-only resource observability falsifier for the ONE-G0.2 product boundary."""

import json
import math
from pathlib import Path
import random
import statistics
import sys
import tempfile
import zlib

from benchmarks.one.one_genesis_contender_workload_measurement import REPETITIONS, measure_workload


SCHEMA = "cmpct-one-g02-genesis-candidate-resource-transfer-v1"
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "one-g02-genesis-candidate-resource-transfer.json"
FORBIDDEN_MODULE_FRAGMENTS = (
    "one_genesis_gate_readiness",
    "neutral_hostile",
    "resemblance_hostile",
)


def _write_transfer_tree(root: Path) -> str:
    root.mkdir(parents=True, exist_ok=False)
    rng = random.Random(0x0A11CE)
    tiny = root / "tiny.txt"
    tiny.write_text("ONE transfer fixture\n", encoding="utf-8")
    tiny.chmod(0o640)
    structured = root / "structured"
    structured.mkdir()
    structured.chmod(0o750)
    rows = [
        {"id": index, "group": index % 7, "active": index % 3 != 0, "label": f"item-{index:04d}"}
        for index in range(512)
    ]
    (structured / "events.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )
    repeated = b"LAW-SURPRISE-TRANSFER|" * 2048
    (root / "repeated.bin").write_bytes(repeated)
    edited = bytearray(repeated)
    for offset in range(101, len(edited), 4093):
        edited[offset] ^= 0x5A
    (root / "local-edit.bin").write_bytes(bytes(edited))
    random_bytes = bytes(rng.randrange(256) for _ in range(65536))
    (root / "random.bin").write_bytes(random_bytes)
    (root / "already-compressed.z").write_bytes(zlib.compress(random_bytes, level=9))
    (root / "fill.bin").write_bytes(b"Z" * 65536)
    (root / "tiny-link").symlink_to("tiny.txt")
    return "structured/events.jsonl"


def _finite_nonnegative(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def _phase_summary(family: dict) -> dict:
    samples = family.get("samples")
    if not isinstance(samples, list) or len(samples) != REPETITIONS:
        raise RuntimeError("resource family does not retain exactly five samples")
    out: dict[str, object] = {"repetitions": REPETITIONS, "process_boundary": family.get("process_boundary")}
    for key in ("cpu_s", "wall_s", "peak_rss_bytes"):
        values = [row.get(key) for row in samples]
        if not all(_finite_nonnegative(value) for value in values):
            raise RuntimeError(f"invalid {key} sample")
        numeric = [float(value) for value in values]
        out[key] = {"median": statistics.median(numeric), "min": min(numeric), "max": max(numeric)}
    return out


def _assert_worker_attestation(samples: list[dict], phase: str) -> None:
    if len(samples) != REPETITIONS:
        raise RuntimeError(f"{phase} did not retain five fresh worker samples")
    for index, row in enumerate(samples):
        if row.get("genesis_workload_modules_imported") is not False:
            raise RuntimeError(f"{phase} worker {index} did not attest Genesis import isolation")
        observed = row.get("forbidden_module_fragments")
        if not isinstance(observed, list) or set(observed) != set(FORBIDDEN_MODULE_FRAGMENTS):
            raise RuntimeError(f"{phase} worker {index} used a different import-isolation boundary")


def run() -> dict:
    before_modules = set(sys.modules)
    with tempfile.TemporaryDirectory(prefix="one-g02-resource-transfer-") as td:
        root = Path(td) / "transfer-tree"
        member = _write_transfer_tree(root)
        result = measure_workload(
            contender="cmpct1",
            checkout=ROOT,
            root=root,
            member=member,
            transfer_fixture=True,
        )

    imported = sorted(set(sys.modules) - before_modules)
    forbidden = sorted(name for name in imported if any(fragment in name for fragment in FORBIDDEN_MODULE_FRAGMENTS))
    if forbidden:
        raise RuntimeError(f"Genesis workload module imported by transfer falsifier parent: {forbidden}")
    if result.get("synthetic") is not True or result.get("production_eligible") is not False:
        raise RuntimeError("transfer evidence was mislabeled as production")
    for flag in ("comparison_executed", "scoring_executed", "winner_selected"):
        if result.get(flag) is not False:
            raise RuntimeError(f"forbidden transfer operation flagged: {flag}")

    measurement = result["measurement"]
    creation = measurement["creation"]
    whole = measurement["whole_read"]
    selective = measurement["selective_access"]
    creation_samples = creation.get("samples", [])
    whole_samples = whole.get("samples", [])
    selective_samples = selective.get("samples", [])
    _assert_worker_attestation(creation_samples, "creation")
    _assert_worker_attestation(whole_samples, "whole_read")
    _assert_worker_attestation(selective_samples, "selective_access")

    wire_sizes = {row.get("stored_bytes") for row in creation_samples}
    wire_hashes = {row.get("wire_sha256") for row in creation_samples}
    if len(wire_sizes) != 1 or len(wire_hashes) != 1:
        raise RuntimeError("current ONE transfer wire is not deterministic across five builds")
    if not all(row.get("exact") is True and row.get("tree_semantics_checked") is True and row.get("integrity_checked_by_reader") is True for row in whole_samples):
        raise RuntimeError("whole-read transfer samples did not prove exact tree semantics")
    if not all(row.get("exact") is True and row.get("integrity_checked_by_reader") is True for row in selective_samples):
        raise RuntimeError("selective transfer samples are not exact/authenticated")

    return {
        "schema": SCHEMA,
        "experimental_version": "ONE-G0.2",
        "decision": "ADVANCE_RESOURCE_OBSERVABILITY_ONLY",
        "source_sha": result["source_sha"],
        "transfer_only": True,
        "production_eligible": False,
        "genesis_workload_modules_imported": False,
        "worker_import_isolation_attested_all_15_fresh_processes": True,
        "genesis_inputs_executed": False,
        "comparison_executed": False,
        "scoring_executed": False,
        "winner_selected": False,
        "repetitions": REPETITIONS,
        "stored_bytes": measurement["stored_bytes"],
        "artifact_sha256": result["artifact_sha256"],
        "wire_deterministic_across_samples": True,
        "whole_tree_semantics_exact_across_samples": True,
        "authenticated_selective_exact_across_samples": True,
        "resource_summary": {
            "creation": _phase_summary(creation),
            "whole_read": _phase_summary(whole),
            "selective_access": _phase_summary(selective),
        },
        "raw_measurement": measurement,
        "claim_boundary": "transfer-only repeatability and fresh-process CPU/wall/RSS observability for current ONE product surface; no Genesis workload, comparator, scoring, or candidate certification",
    }


def main() -> None:
    payload = run()
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "schema": payload["schema"],
        "decision": payload["decision"],
        "stored_bytes": payload["stored_bytes"],
        "artifact_sha256": payload["artifact_sha256"],
        "resource_summary": payload["resource_summary"],
        "scoring_executed": payload["scoring_executed"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
