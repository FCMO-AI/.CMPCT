#!/usr/bin/env python3
"""O41: independent fail-closed source/corpus witness for unmodified O33 raw receipts.

Keep original O33 measured timings and inherited header constants immutable.
A source label in old research JSON is not actual checked-out Git provenance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

O28_INSTRUMENT_BASE = "9c9cecc6c21dc741e57188076ea43dc0ede6425b"
O31_INSTRUMENT_CANDIDATE = "0edb7bc6e832deb1b403fea50c36e655da9844fd"
O31_READER_BLOB = "de9accf6607aca7cf70dfe71d7b299a02e298a2d"
O38_READER_BLOB = "4aee9e8ddf50ff3c3e0db20ebf7671e2ac477867"
O38_PRODUCT_SHA = "dffc6da03b588e209843f2fc6e219e5bce3a7800"
SHAPES = ("plain", "fanout", "chain")
SIZES = (512, 4096)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(
        ("git", "-C", str(repo), *args),
        capture_output=True, text=True, check=False
    )
    if p.returncode:
        raise ValueError(f"Git identity check failed ({args}): {p.stderr.strip()}")
    return p.stdout.strip()


def assert_contained(path: Any, root: Path, label: str) -> Path:
    p = Path(path)
    require(p.is_absolute(), f"{label}: non-absolute source path")
    r = p.resolve(strict=True)
    require(r.is_relative_to(root), f"{label}: outside verified source root: {r}")
    require(r.is_file() or r == root, f"{label}: not a file/source root: {r}")
    return r


def validate_rows(
    data: dict[str, Any],
    base_source: Path,
    candidate_source: Path,
) -> dict[str, Any]:
    """Validate original scientific bytes without trusting inherited O33 labels."""
    require(data["experiment"] == "O33", "wrong inherited instrument identity")
    require(data["status"] == "RESEARCH_NOT_RELEASE", "invalid evidence classification")
    require(data["source_base"] == O28_INSTRUMENT_BASE, "changed O33 base constant")
    require(
        data["source_candidate_product"] == O31_INSTRUMENT_CANDIDATE,
        "changed O33 candidate constant",
    )
    require(
        data["base_reader_blob"] == "c7850c08c7bb27563955c6e2294b8c17c140d0a2",
        "changed inherited O33 base blob constant",
    )
    require(
        data["candidate_reader_blob"] == O31_READER_BLOB,
        "changed inherited O33 candidate blob constant",
    )
    require(data["reps_per_source"] == 8, "repetition count mismatch")
    expected_cases = {(shape, size) for size in SIZES for shape in SHAPES}
    corpus = data["corpus"]
    require(len(corpus) == 6, "missing/duplicated corpus item")
    by_case: dict[tuple[str, int], dict[str, Any]] = {}
    for c in corpus:
        key = (c["shape"], c["size"])
        require(key in expected_cases and key not in by_case, "unexpected/duplicate corpus")
        path = Path(c["path"]).resolve(strict=True)
        require(path.is_file(), "missing archive")
        require(path.stat().st_size == c["bytes"], "archive byte size mismatch")
        require(
            hashlib.sha256(path.read_bytes()).hexdigest() == c["sha256"],
            "archive physical SHA-256 mismatch",
        )
        by_case[key] = c
    require(set(by_case) == expected_cases, "incomplete corpus")

    rows = data["raw"]
    require(len(rows) == 96, "not exactly 96 fresh-process observations")
    counts: dict[str, int] = {"base": 0, "candidate": 0}
    for key in sorted(expected_cases):
        section = [x for x in rows if (x["shape"], x["size"]) == key]
        require(len(section) == 16, f"{key}: missing/duplicate observations")
        case = by_case[key]
        for group in range(4):
            quartet = section[group * 4 : (group + 1) * 4]
            order = ("base", "candidate", "candidate", "base") if group % 2 == 0 else (
                "candidate", "base", "base", "candidate"
            )
            require(
                tuple(x["source_label"] for x in quartet) == order,
                f"{key}: non-ABBA/BAAB source order",
            )
            require(
                all(x["pair_group"] == group for x in quartet),
                f"{key}: group evidence mismatch",
            )
            for row in quartet:
                label = row["source_label"]
                counts[label] += 1
                src = base_source if label == "base" else candidate_source
                require(Path(row["source"]).resolve(strict=True) == src, "source directory swapped")
                require(
                    Path(row["module"]).resolve(strict=True) == src / "cmpct" / "reader.py",
                    "Reader code module swapped",
                )
                native = assert_contained(row["native_module"], src, "native module")
                require(native.parent == src / "cmpct", "native library outside package owner")
                require(native.name.startswith("cmpct_core") and native.suffix == ".so", "native module is not Linux cmpct_core cdylib")
                require(row["files"] == case["size"], "child Reader file count mismatch")
                require(
                    Path(row["archive"]).resolve(strict=True) ==
                    Path(case["path"]).resolve(strict=True),
                    "child archive path swapped",
                )
                for field in ("construct_ms", "wall_ms", "cpu_construct_ms"):
                    value = row[field]
                    require(
                        isinstance(value, (int, float)) and
                        math.isfinite(value) and value >= 0,
                        f"invalid timing {field}",
                    )
    require(counts == {"base": 48, "candidate": 48}, "wrong source observation counts")
    require(
        {(x["shape"], x["size"]) for x in data["results"]} == expected_cases
        and len(data["results"]) == 6,
        "summary cases do not match raw cases",
    )
    return {
        "cases": 6,
        "observations": 96,
        "observations_per_source": counts,
        "corpus_sha256": {f"{s}-{n}": by_case[(s, n)]["sha256"]
                          for s, n in sorted(expected_cases)},
    }


def negative_controls(raw: dict[str, Any], b: Path, c: Path) -> list[str]:
    """Falsifiers mutate copies only; original raw JSON remains untouched."""
    probes = {
        "wrong_source": lambda a: a["raw"][0].__setitem__("source", str(c)),
        "wrong_reader": lambda a: a["raw"][0].__setitem__("module", str(c / "cmpct" / "reader.py")),
        "wrong_native": lambda a: a["raw"][0].__setitem__("native_module", str(c / "cmpct" / "reader.py")),
        "wrong_native_same_source": lambda a: a["raw"][0].__setitem__("native_module", str(b / "cmpct" / "native_codec.py")),
        "wrong_sha": lambda a: a["corpus"][0].__setitem__("sha256", "0" * 64),
        "wrong_group": lambda a: a["raw"][0].__setitem__("pair_group", 99),
    }
    passed: list[str] = []
    for label, mutate in probes.items():
        suspect = copy.deepcopy(raw)
        mutate(suspect)
        try:
            validate_rows(suspect, b, c)
        except (ValueError, OSError, KeyError, TypeError):
            passed.append(label)
        else:
            raise ValueError(f"tampered receipt was falsely accepted: {label}")
    return passed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--base-source", required=True, type=Path)
    ap.add_argument("--candidate-source", required=True, type=Path)
    ap.add_argument("--evidence-head", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ns = ap.parse_args()

    base = ns.base_source.resolve(strict=True)
    candidate = ns.candidate_source.resolve(strict=True)
    require(base != candidate, "baseline and candidate source trees are the same")
    require(base.name == candidate.name == "src", "expected isolated source trees")
    base_repo, candidate_repo = base.parent, candidate.parent
    require(git(base_repo, "rev-parse", "HEAD") == O31_INSTRUMENT_CANDIDATE,
            "historical checked-out HEAD is not O31")
    require(git(candidate_repo, "rev-parse", "HEAD") == ns.evidence_head,
            "candidate checked-out HEAD does not match CI head")
    git(candidate_repo, "merge-base", "--is-ancestor", O38_PRODUCT_SHA, ns.evidence_head)
    git(candidate_repo, "diff", "--exit-code", O38_PRODUCT_SHA, ns.evidence_head,
        "--", "src", "native")
    require(git(base_repo, "hash-object", "src/cmpct/reader.py") == O31_READER_BLOB,
            "O31 historical Reader blob changed")
    require(git(candidate_repo, "hash-object", "src/cmpct/reader.py") == O38_READER_BLOB,
            "O38 actual Reader blob changed")
    require(
        git(candidate_repo, "rev-parse", f"{O38_PRODUCT_SHA}:src/cmpct/reader.py")
        == O38_READER_BLOB,
        "O38 product ancestor blob unexpected",
    )
    payload = ns.raw.read_bytes()
    raw = json.loads(payload)
    verified = validate_rows(raw, base, candidate)
    tampered = negative_controls(raw, base, candidate)
    # Hash native bytes after all timing children, outside measured CPU/wall intervals.
    native_loaded = {}
    for label, root in (("base", base), ("candidate", candidate)):
        paths = {row["native_module"] for row in raw["raw"] if row["source_label"] == label}
        require(len(paths) == 1, f"{label}: inconsistent loaded native artifact paths")
        module = assert_contained(next(iter(paths)), root, "loaded native binary")
        require(module.parent == root / "cmpct", "native binary not in package owner")
        require(module.name.startswith("cmpct_core") and module.suffix == ".so",
                "native binary is not Linux cmpct_core")
        native_data = module.read_bytes()
        native_loaded[label] = {
            "module_path": str(module),
            "sha256": hashlib.sha256(native_data).hexdigest(),
            "bytes": len(native_data),
        }
    # Independent historical native payload materialized from original O31 wheel.
    base_receipt = json.loads((ns.raw.parent / "base-native.json").read_text())
    require(base_receipt["source_commit"] == O31_INSTRUMENT_CANDIDATE,
            "historical native build source SHA mismatch")
    require(base_receipt["native_path"] == native_loaded["base"]["module_path"],
            "historical native artifact path mismatch")
    require(base_receipt["native_sha256"] == native_loaded["base"]["sha256"],
            "historical native artifact SHA mismatch")
    require(base_receipt["native_bytes"] == native_loaded["base"]["bytes"],
            "historical native artifact physical size mismatch")
    witness = {
        "schema": "cmpct-o41-o38-actual-sources-v1",
        "classification": "evidence-source-binding-not-product-benchmark",
        "actual_historical_source_head": O31_INSTRUMENT_CANDIDATE,
        "actual_candidate_evidence_head": ns.evidence_head,
        "candidate_product_ancestor": O38_PRODUCT_SHA,
        "historical_reader_blob": O31_READER_BLOB,
        "candidate_reader_blob": O38_READER_BLOB,
        "native_path_rule": "same source-owned cmpct_core Linux cdylib physically SHA-256-attested after timing",
        "native_loaded_artifacts": native_loaded,
        "historical_native_wheel_receipt_sha256": hashlib.sha256((ns.raw.parent / "base-native.json").read_bytes()).hexdigest(),
        "original_o33_json_sha256": hashlib.sha256(payload).hexdigest(),
        "inherited_o33_source_labels": {
            "source_base": raw["source_base"],
            "source_candidate_product": raw["source_candidate_product"],
            "semantic_status": "historical fixed O33 instrument headers, not actual O38 source identities",
        },
        "verified": verified,
        "negative_mutation_controls_rejected": tampered,
        "provenance_limits": [
            "Two exact checked-out source trees, not two independently installed wheels.",
            "Linux hosted source-bound fresh processes do not imply cold kernel cache.",
            "This witness does not remeasure timings or authorize promotion/release.",
            "Actual source/native library bytes and physical corpus SHA identities are bounded to this hosted evidence, not all platforms or ABI implementations.",
        ],
    }
    ns.out.parent.mkdir(parents=True, exist_ok=True)
    ns.out.write_text(json.dumps(witness, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": "O41_SOURCE_BINDING_PASS",
        "evidence_head": ns.evidence_head,
        "observations": verified["observations"],
        "negative_controls_rejected": tampered,
        "raw_sha256": witness["original_o33_json_sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
