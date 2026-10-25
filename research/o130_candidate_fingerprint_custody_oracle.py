#!/usr/bin/env python3
"""O130: exact helper + real Git-tree fingerprint-custody falsifier.

This is a SCIENTIFIC negative oracle. It does not modify CMPCT, its checker,
the candidate manifest, workflow conditions, or release law. Passing here
means reproducing a *limited standalone digest blind spot*, not product safety.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from tools import check_v031_candidate_fingerprint as checker

REPO = Path(__file__).resolve().parents[1]


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def observed(root: Path, manifest: dict, label: str) -> dict:
    digest, paths = checker.fingerprint(manifest, root=root)
    source = root / "tools/sample.py"
    mode_row = git(root, "ls-files", "--stage", "--", "tools/sample.py")
    assert mode_row and "\ttools/sample.py" in mode_row
    return {
        "case": label,
        "git_head": git(root, "rev-parse", "HEAD"),
        "git_tree": git(root, "rev-parse", "HEAD^{tree}"),
        "candidate_fingerprint": digest,
        "covered_paths": len(paths),
        "mode_row": mode_row,
        "included_example": "tools/sample.py" in paths,
        "excluded_yaml_example": ".github/workflows/new-execution.yaml" not in paths,
        "included_content_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }


def run() -> dict:
    manifest = checker.load_manifest()
    manifest_bytes = checker.MANIFEST.read_bytes()
    script_bytes = Path(checker.__file__).read_bytes()
    assert ".github/workflows/*.yml" in manifest["fingerprint_globs"]
    assert ".github/workflows/*.yaml" not in manifest["fingerprint_globs"]
    with tempfile.TemporaryDirectory(prefix="cmpct-o130-git-custody-") as td:
        root = Path(td).resolve()
        # Preserve the *actual*, unmodified required-path contract.
        for relative in manifest["required_paths"]:
            f = root / relative
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(b"o130 source-custody required-path fixture\n")
        source = root / "tools/sample.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("#!/usr/bin/env python3\nprint('o130 baseline')\n", encoding="utf-8")
        included_wf = root / ".github/workflows/known.yml"
        included_wf.parent.mkdir(parents=True, exist_ok=True)
        included_wf.write_text("name: O130 baseline\non: push\njobs: {}\n", encoding="utf-8")

        git(root, "init", "-q")
        git(root, "config", "user.name", "CMPCT O130 science")
        git(root, "config", "user.email", "o130-science@example.invalid")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "o130 fixture initial candidate")

        cases = [observed(root, manifest, "baseline")]
        assert cases[0]["included_example"]
        assert cases[0]["excluded_yaml_example"]

        # A committed workflow whose .yaml extension is recognized by Actions.
        hidden = root / ".github/workflows/new-execution.yaml"
        hidden.write_text("name: O130 new execution\non: push\njobs: {}\n", encoding="utf-8")
        git(root, "add", "--", ".github/workflows/new-execution.yaml")
        git(root, "commit", "-qm", "o130 introduce a tracked GitHub Actions yaml workflow")
        assert git(root, "ls-files", "--error-unmatch", ".github/workflows/new-execution.yaml")
        cases.append(observed(root, manifest, "tracked_yaml_workflow"))

        # Index mode changes are actual Git-tree changes even if bytes do not change.
        git(root, "update-index", "--chmod=+x", "--", "tools/sample.py")
        git(root, "commit", "-qm", "o130 change included script Git mode only")
        cases.append(observed(root, manifest, "tracked_executable_mode"))

        # Independent, differently rooted included-content control.
        source.write_text("#!/usr/bin/env python3\nprint('o130 mutated content')\n", encoding="utf-8")
        git(root, "add", "--", "tools/sample.py")
        # Keep the previously committed executable Git mode after a content-stage;
        # the fixture worktree itself began as a non-executable file.
        git(root, "update-index", "--chmod=+x", "--", "tools/sample.py")
        git(root, "commit", "-qm", "o130 change included script contents")
        cases.append(observed(root, manifest, "included_content_mutation"))

        for a, b in zip(cases, cases[1:]):
            assert a["git_head"] != b["git_head"], "invalid control: identical commits"
            assert a["git_tree"] != b["git_tree"], "invalid control: identical trees"
        assert cases[0]["candidate_fingerprint"] == cases[1]["candidate_fingerprint"], (
            "P1 disproof: .yaml changed the fingerprint"
        )
        assert cases[1]["candidate_fingerprint"] == cases[2]["candidate_fingerprint"], (
            "P2 disproof: mode-only mutation changed the fingerprint"
        )
        assert cases[2]["candidate_fingerprint"] != cases[3]["candidate_fingerprint"], (
            "P3 instrument failure: included content did not change fingerprint"
        )
        assert cases[0]["mode_row"].startswith("100644 ")
        assert cases[1]["mode_row"].startswith("100644 ")
        assert cases[2]["mode_row"].startswith("100755 ")
        assert cases[3]["mode_row"].startswith("100755 ")
        assert cases[0]["included_content_sha256"] == cases[2]["included_content_sha256"]
        assert cases[2]["included_content_sha256"] != cases[3]["included_content_sha256"]

    head = git(REPO, "rev-parse", "HEAD")
    expected = os.environ.get("EVIDENCE_HEAD")
    if expected and head != expected:
        raise AssertionError(f"CI exact-head mismatch: {head} != {expected}")
    return {
        "schema": "cmpct-o130-candidate-custody-science-v1",
        "evidence_tier": "real-Git / exact-O129-helper isolated scientific oracle",
        "source_sha": head,
        "checker_sha256": hashlib.sha256(script_bytes).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "required_paths_materialized": len(manifest["required_paths"]),
        "cases": cases,
        "decision": {
            "P1_git_tracked_yaml_invisible_to_digest": True,
            "P2_git_executable_bit_invisible_to_digest": True,
            "P3_included_byte_mutation_changes_digest": True,
            "P4_exact_unmodified_checker_manifest": True,
            "standalone_digest_full_git_semantics": "FALSIFIED",
            "exact_git_HEAD_bound_receipt": "NOT FALSIFIED",
            "product_or_release_credit": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    data = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data, encoding="utf-8")
    print(json.dumps({
        "source_sha": result["source_sha"],
        "manifest_sha256": result["manifest_sha256"],
        "checkers_sha256": result["checker_sha256"],
        "outcomes": result["decision"],
        "git_trees": [x["git_tree"] for x in result["cases"]],
        "fingerprints": [x["candidate_fingerprint"] for x in result["cases"]],
    }))


if __name__ == "__main__":
    main()
