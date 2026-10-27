"""J24E01: original-source versus candidate JSON duplicate-key gate court.

Runs the unchanged historical comparator source from a real Git ancestor in a
separate file, then the current exact-head comparator. Never relaxes evaluator
policy or substitutes a copied algorithm for the actual product executable.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

BASE_COMMIT = "84bcd4144e3cf95bbc66a9cb3df8c7c101b89bb9"
SOURCE_PATH = "tools/check_performance_regression.py"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor", BASE_COMMIT, head],
                              cwd=repo, check=False)
    if ancestor.returncode:
        raise AssertionError("parent comparator source commit is not an ancestor of HEAD")
    baseline = subprocess.check_output(["git", "show", f"{BASE_COMMIT}:{SOURCE_PATH}"], cwd=repo)
    source = subprocess.check_output(["git", "show", f"HEAD:{SOURCE_PATH}"], cwd=repo)
    on_disk = (repo / SOURCE_PATH).read_bytes().replace(b"\r\n", b"\n")
    if source != on_disk:
        raise AssertionError("tested checker does not match exact HEAD Git blob")

    def metric(create=0.100):
        return {"bytes": 1000, "create_s_median": create, "extract_s_median": 0.07}

    def doc(create=0.100):
        return {"schema": "cmpct-zip-parity-v1", "corpora": {
            "demo": {"logical_bytes": 1000,
                     "library": {"cmpct": metric(create)},
                     "cli": {"cmpct": metric(create)}}}}

    clean = json.dumps(doc(), separators=(",", ":"))
    red = json.dumps(doc(0.107), separators=(",", ":"))
    dup_timing = red.replace('"create_s_median":0.107',
                             '"create_s_median":0.107,"create_s_median":0.100')
    dup_corpora = red[:-1] + ',"corpora":' + clean.split('"corpora":', 1)[1]
    dup_schema = clean.replace('"schema":"cmpct-zip-parity-v1"',
                             '"schema":"untrusted","schema":"cmpct-zip-parity-v1"')
    dup_archive_bytes = clean.replace('"bytes":1000', '"bytes":1100,"bytes":1000')
    dup_logical_length = clean.replace('"logical_bytes":1000', '"logical_bytes":1001,"logical_bytes":1000')
    cases = {"dup_timing": dup_timing, "dup_corpora": dup_corpora,
             "dup_schema": dup_schema, "dup_archive_bytes": dup_archive_bytes,
             "dup_logical_length": dup_logical_length,
             "unique_aa": clean, "unique_red": red}
    expected_old = {"dup_timing": 0, "dup_corpora": 0, "dup_schema": 0,
                    "dup_archive_bytes": 0, "dup_logical_length": 0,
                    "unique_aa": 0, "unique_red": 1}
    expected_new = {"dup_timing": 1, "dup_corpora": 1, "dup_schema": 1,
                    "dup_archive_bytes": 1, "dup_logical_length": 1,
                    "unique_aa": 0, "unique_red": 1}

    with TemporaryDirectory(prefix="j24e01-") as tmp:
        root = Path(tmp)
        orig = root / "original_comparator.py"
        orig.write_bytes(baseline)
        rows = []
        for label, raw in cases.items():
            # A permissive JSON parser accepts all these inputs; the attack is
            # duplicate member semantics, not invalid JSON syntax.
            json.loads(raw)
            b = root / "base.json"
            c = root / "candidate.json"
            b.write_text(clean, encoding="utf-8")
            c.write_text(raw, encoding="utf-8")
            observations = []
            for arm, checker, expected in (
                ("original", orig, expected_old[label]),
                ("candidate", repo / SOURCE_PATH, expected_new[label]),
            ):
                proc = subprocess.run([sys.executable, str(checker), "--base", str(b),
                                       "--candidate", str(c)],
                                      capture_output=True, text=True, check=False)
                if proc.returncode != expected:
                    raise AssertionError(
                        f"{arm}/{label} expected {expected}; got {proc.returncode}:"
                        f" stdout={proc.stdout!r} stderr={proc.stderr!r}"
                    )
                if label.startswith("dup_"):
                    if arm == "original" and "Result: **PASS**" not in proc.stdout:
                        raise AssertionError("original last-wins false green not reproduced")
                    if arm == "candidate" and "duplicate JSON object key" not in proc.stderr:
                        raise AssertionError("candidate did not reject duplicate members explicitly")
                elif label == "unique_aa" and "Result: **PASS**" not in proc.stdout:
                    raise AssertionError("valid A/A rejected")
                elif label == "unique_red" and "Result: **FAIL**" not in proc.stdout:
                    raise AssertionError("true regression not preserved")
                observations.append({"arm": arm, "exit_code": proc.returncode,
                                     "report_pass": "Result: **PASS**" in proc.stdout,
                                     "duplicate_rejected": "duplicate JSON object key" in proc.stderr})
            rows.append({"case": label, "json_sha256": sha(raw.encode()),
                         "observations": observations})

    evidence = {
        "decision": "DUPLICATE_JSON_FALSE_GREEN_REPRODUCED_AND_REJECTED",
        "source_head": head, "baseline_sha": BASE_COMMIT,
        "baseline_checker_sha256": sha(baseline),
        "candidate_checker_sha256": sha(source),
        "cases": rows,
        "format_mutated": False,
        "original_comparator_policy_changed": False,
        "release_credit": False,
    }
    print(json.dumps(evidence, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
