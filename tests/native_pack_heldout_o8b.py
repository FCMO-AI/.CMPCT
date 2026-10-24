#!/usr/bin/env python3
"""O8b prospective extension-only admission court; preserves executed O8 as-is."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
import tempfile
from pathlib import Path

from cmpct.builder import Builder

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
import native_pack_heldout_o8 as o8

FAMILIES = ("related_256", "independent_256", "duplicates_256", "mixed_256")
SUFFIXES = ("dat", "txt")
REPS = 4


def transformed(base: dict[str, bytes], suffix: str) -> dict[str, bytes]:
    assert suffix in SUFFIXES
    result: dict[str, bytes] = {}
    for name, data in base.items():
        new_name = name[:-3] + suffix if name.endswith(".dat") else name
        assert len(new_name) == len(name) and new_name not in result
        result[new_name] = data
    return result


def physical_content_manifest(files: dict[str, bytes]) -> list[tuple[str, int]]:
    # Multiset comparison keeps true duplicates distinct; no filenames in this identity.
    return sorted((hashlib.sha256(data).hexdigest(), len(data)) for data in files.values())


def run_cell(root: Path, binary: Path, label: str, files: dict[str, bytes]) -> dict:
    here = root / label
    source = here / "src"
    source.mkdir(parents=True)
    expected: dict[str, str] = {}
    for name, data in sorted(files.items()):
        (source / name).write_bytes(data)
        expected[name] = hashlib.sha256(data).hexdigest()
    total = sum(len(data) for data in files.values())
    archive = here / "src.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    original_sha = o8.hash_file(archive)
    observations: list[dict] = []
    for round_id in range(REPS):
        order = ("serial", "group", "group", "serial") if round_id % 2 == 0 else (
            "group", "serial", "serial", "group"
        )
        for trial_id, mode in enumerate(order):
            dest = here / f"out-{round_id}-{trial_id}-{mode}"
            observations.append(o8.run_trial(
                binary, archive, dest, mode, label, round_id,
                trial_id, expected, total,
            ))
            if o8.hash_file(archive) != original_sha:
                raise AssertionError((label, "archive bytes mutated"))
    def median(mode: str, key: str) -> float:
        return statistics.median(
            row[key] for row in observations if row["mode"] == mode
        )
    group = [r for r in observations if r["mode"] == "group"]
    scheduled = {(r["batched_members"], r["fallback"], r["batch_count"]) for r in group}
    assert len(scheduled) == 1, (label, "group admission not deterministic", scheduled)
    wall_a = median("serial", "wall_ms")
    wall_b = median("group", "wall_ms")
    rss_a = median("serial", "rss_kib")
    rss_b = median("group", "rss_kib")
    return {
        "source_archive_sha256": original_sha,
        "archive_bytes": archive.stat().st_size,
        "logical_bytes": total,
        "members": len(files),
        "content_multiset_sha256": hashlib.sha256(
            json.dumps(physical_content_manifest(files), separators=(",", ":")).encode()
        ).hexdigest(),
        "batched_members": group[0]["batched_members"],
        "batch_count": group[0]["batch_count"],
        "fallback_members": group[0]["fallback"],
        "serial_wall_median_ms": wall_a,
        "group_wall_median_ms": wall_b,
        "serial_cpu_median_ms": median("serial", "child_cpu_ms"),
        "group_cpu_median_ms": median("group", "child_cpu_ms"),
        "serial_rss_median_kib": rss_a,
        "group_rss_median_kib": rss_b,
        "wall_speedup": wall_a / wall_b if wall_b else None,
        "material_group_wall_regression": wall_b > wall_a * 1.10 and (wall_b - wall_a) > 5.0,
        "raw_abba": observations,
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python tests/native_pack_heldout_o8b.py C_BINARY RECEIPT")
    binary = Path(sys.argv[1]).resolve()
    receipt = Path(sys.argv[2]).resolve()
    assert binary.is_file()
    outcome = {
        "schema": "cmpct-native-public-c-extension-admission-o8b-v1",
        "prospective_prereg": "docs/v031-research/NATIVE_PACK_HELDOUT_O8B_PREREG.md",
        "o8_null_admission_run": 40066222077,
        "reps_per_cell": REPS,
        "families": {},
        "status": "EXECUTING",
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-native-o8b-") as tmp:
        root = Path(tmp)
        for family in FAMILIES:
            original = o8.population(family)
            controls = {suffix: transformed(original, suffix) for suffix in SUFFIXES}
            assert physical_content_manifest(controls["dat"]) == physical_content_manifest(controls["txt"])
            assert len(controls["dat"]) == len(controls["txt"])
            cells: dict[str, dict] = {}
            for suffix in SUFFIXES:
                cell_name = f"{family}.{suffix}"
                cells[suffix] = run_cell(root, binary, cell_name, controls[suffix])
                print(json.dumps({
                    "cell": cell_name,
                    "archive_bytes": cells[suffix]["archive_bytes"],
                    "members": cells[suffix]["members"],
                    "batch_count": cells[suffix]["batch_count"],
                    "batched_members": cells[suffix]["batched_members"],
                    "fallback_members": cells[suffix]["fallback_members"],
                    "wall_speedup": cells[suffix]["wall_speedup"],
                    "status": "BYTE_EXACT",
                    "observations": len(cells[suffix]["raw_abba"]),
                }, sort_keys=True), flush=True)
            if cells["dat"]["content_multiset_sha256"] != cells["txt"]["content_multiset_sha256"]:
                raise AssertionError((family, "different source bytes across suffix controls"))
            if cells["dat"]["logical_bytes"] != cells["txt"]["logical_bytes"]:
                raise AssertionError((family, "different logical lengths across suffix controls"))
            dat = cells["dat"]["archive_bytes"]
            txt = cells["txt"]["archive_bytes"]
            outcome["families"][family] = {
                "dat": cells["dat"],
                "txt": cells["txt"],
                "txt_archive_bytes_delta": txt - dat,
                "txt_archive_bytes_ratio": txt / dat,
                "txt_storage_loss_gt_1pct": txt > dat * 1.01,
                "txt_batch_admitted": cells["txt"]["batched_members"] > 0,
                "dat_batch_admitted": cells["dat"]["batched_members"] > 0,
            }
    outcome["status"] = "O8B_COMPLETE_WITH_ADMISSION_AND_COST_NEGATIVES_PRESERVED"
    outcome["summary"] = {
        "total_extractions": len(FAMILIES) * len(SUFFIXES) * REPS * 4,
        "families": len(FAMILIES),
        "txt_admission_families": [
            n for n, d in outcome["families"].items() if d["txt_batch_admitted"]
        ],
        "dat_admission_families": [
            n for n, d in outcome["families"].items() if d["dat_batch_admitted"]
        ],
        "txt_storage_loss_gt_1pct_families": [
            n for n, d in outcome["families"].items() if d["txt_storage_loss_gt_1pct"]
        ],
    }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n")
    print(json.dumps(outcome["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
