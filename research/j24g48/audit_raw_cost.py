"""Independent J24G48 raw-run referee; imports no CMPCT Python modules.

Validates source/physical archive custody, complete interleaved observations,
correctness controls and recomputes medians from raw samples. Deliberately
does not purport to certify product release or cold OS-cache behavior.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import sys

PRIOR = "78b9dd2d148350898c95a0cdbeefe760de2e567e"
REPAIR = "893aac3f6b7b54e89d71af6970405ff5fc71aef7"
EXPECTED = {(256, 32), (2048, 0), (2048, 32), (2048, 2)}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(path: Path, out: Path) -> None:
    root = path.parent.resolve()
    data = json.loads(path.read_text())
    assert data["candidate_sha"] == REPAIR
    assert data["defective_sha"] == PRIOR
    assert data["repetitions"] == 7
    assert len(data["cases"]) == len(EXPECTED)
    assert len(data["runs"]) == 4 * 2 * 2 * 14
    assert {(x["count"], x["xattr_divisor"]) for x in data["cases"]} == EXPECTED
    assert {x["case"] for x in data["cases"]} == {x["case"] for x in data["runs"]}

    physical = {}
    for case in data["cases"]:
        count, div = case["count"], case["xattr_divisor"]
        assert len(case["expected_xattrs"]) == (
            ((count - 1) // div + 1) if div else 0
        )
        assert case["source_file_count"] == count
        physical[case["case"]] = {}
        for generation, expected_count in (("original", count), ("shifted", count + 1)):
            record = case[generation]
            artifact = Path(record["path"]).resolve()
            assert artifact.is_relative_to(root), f"unsafe path {artifact}"
            assert artifact.is_file()
            assert artifact.stat().st_size == record["bytes"]
            assert digest(artifact) == record["sha256"]
            physical[case["case"]][generation] = {
                "sha256": record["sha256"],
                "bytes": record["bytes"],
                "members": expected_count,
            }
        # The signed journal appends to the original immutable archive.
        assert case["shifted"]["bytes"] > case["original"]["bytes"]
        assert (
            Path(case["shifted"]["path"]).read_bytes()
            .startswith(Path(case["original"]["path"]).read_bytes())
        )

    groups = {}
    for row in data["runs"]:
        key = row["case"], row["generation"], row["source"]
        groups.setdefault(key, []).append(row)
        case = next(x for x in data["cases"] if x["case"] == row["case"])
        expected_sha = REPAIR if row["source"] == "correct" else PRIOR
        assert row["source_identity"]["git_sha"] == expected_sha
        assert row["archive_sha256"] == case[row["generation"]]["sha256"]
        assert row["members"] == case["count"] + (row["generation"] == "shifted")
        assert row["metadata_names"] == len(case["expected_xattrs"])
        assert row["metadata_matches_logical_names"] == (
            not (row["source"] == "defective"
                 and row["generation"] == "shifted"
                 and bool(case["expected_xattrs"]))
        )
        assert type(row["round"]) is int and 0 <= row["round"] < 7
        for field in ("reader_open_plus_mapping_wall_ns", "reader_open_plus_mapping_cpu_ns",
                      "maxrss_bytes", "import_ns"):
            assert type(row[field]) is int and row[field] > 0
        assert row["pid"] > 0

    # Each source appears twice per round and generation; preserve raw-repeat custody.
    assert len(groups) == 16
    for key, rows in groups.items():
        assert len(rows) == 14, key
        assert Counter(x["round"] for x in rows) == Counter({i: 2 for i in range(7)})
        reader_hashes = {r["source_identity"]["reader_sha256"] for r in rows}
        assert len(reader_hashes) == 1
        reader_path = Path(rows[0]["source_identity"]["reader_path"])
        assert reader_path.name == "reader.py"

    summary = []
    for case in data["cases"]:
        label = case["case"]
        for generation in ("original", "shifted"):
            for kind in ("defective", "correct"):
                rows = groups[label, generation, kind]
                med = lambda col: statistics.median(r[col] for r in rows)
                summary.append({
                    "case": label, "generation": generation, "source": kind,
                    "samples": len(rows),
                    "median_wall_ms": med("reader_open_plus_mapping_wall_ns") / 1e6,
                    "median_cpu_ms": med("reader_open_plus_mapping_cpu_ns") / 1e6,
                    "median_import_ms": med("import_ns") / 1e6,
                    "max_rss_bytes": max(r["maxrss_bytes"] for r in rows),
                    "correct": all(r["metadata_matches_logical_names"] for r in rows),
                })
    # Recompute source delta, then difference-in-differences for shifted vs original.
    by_key = {(s["case"], s["generation"], s["source"]): s for s in summary}
    comparisons = []
    for case in data["cases"]:
        label = case["case"]
        p = by_key[label, "shifted", "defective"]
        c = by_key[label, "shifted", "correct"]
        bp = by_key[label, "original", "defective"]
        bc = by_key[label, "original", "correct"]
        absolute = c["median_wall_ms"] - p["median_wall_ms"]
        ratio = c["median_wall_ms"] / p["median_wall_ms"]
        diffdiff = absolute - (bc["median_wall_ms"] - bp["median_wall_ms"])
        comparisons.append({
            "case": label, "source_invalid_on_shift": not p["correct"],
            "repaired_correct": c["correct"],
            "shift_correct_vs_prior_extra_wall_ms": absolute,
            "shift_correct_vs_prior_wall_ratio": ratio,
            "difference_in_differences_ms": diffdiff,
            "research_triage_20ms_and_10pct":
                absolute > 20 and ratio > 1.1,
            "rss_extra_bytes": c["max_rss_bytes"] - p["max_rss_bytes"],
        })
    assert all(x["repaired_correct"] for x in comparisons)
    assert all(not x["research_triage_20ms_and_10pct"] for x in comparisons)
    result = {
        "decision": "RESEARCH_TRIAGE_BELOW_ABSOLUTE_20MS_AT_TESTED_SCALES",
        "semantics_warning": "prior Reader fails actual metadata identity; not product performance parity",
        "not_measured": ["full extraction", "cold OS page cache", "release performance",
                         "large production trees", "macOS/Windows fidelity"],
        "receipt_sha256": digest(path), "physical": physical,
        "source_shas": {"defective": PRIOR, "correct": REPAIR},
        "summary": summary, "comparisons": comparisons,
    }
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"],
                      "comparisons": comparisons}, sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
