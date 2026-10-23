"""Exact-source negative research court: release fingerprint versus admission scope.

This is NOT a release gate and never edits the published v0.30 lock.
"""
from __future__ import annotations

import fnmatch
import glob
import hashlib
import json
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LOCK_BLOB = "988a7b05ad4e0833fac0453de74133b38f890f87"
WORKFLOW_BLOB = "2f095ec3b5b1028bc1fa49dd730de8062876e0ee"


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def trigger_paths(workflow: str) -> list[str]:
    # Deliberately parse only the pinned, uncomplicated pull_request stanza.
    # It is not a generic YAML parser, and fails closed if the grammar changes.
    m = re.search(r"(?ms)^on:\n  pull_request:\n(?P<block>.*?)(?=^  workflow_dispatch:)", workflow)
    assert m, "workflow trigger shape changed: examine semantics"
    x = re.search(r"(?ms)^    paths:\n(?P<paths>(?:      - .+\n)+)", m.group("block"))
    assert x, "PR trigger paths missing"
    paths = re.findall(r"(?m)^      - ['\"]([^'\"]+)['\"]\s*$", x.group("paths"))
    assert paths and len(paths) == len(x.group("paths").splitlines()), "unknown paths grammar"
    return paths


def main() -> None:
    lock = (ROOT / "docs/V030_RELEASE_LOCK.json").read_bytes()
    wf = (ROOT / ".github/workflows/v030-authoritative-v2-pr.yml").read_bytes()
    assert git_blob_sha(lock) == LOCK_BLOB, "exact original lock changed"
    assert git_blob_sha(wf) == WORKFLOW_BLOB, "exact original workflow changed"
    manifest = json.loads(lock)
    globs = manifest["fingerprint_globs"]
    workflow = wf.decode()
    assert "fnmatch.fnmatchcase(p, pattern)" in workflow, "classifier semantics changed"
    assert "manifest['fingerprint_globs']" in workflow
    assert "git diff-tree --no-commit-id --name-only -r HEAD" in workflow
    event_paths = trigger_paths(workflow)

    # The real release fingerprint enumerator expands glob.glob(recursive=True).
    # Compare that exact file closure to BOTH GitHub event admission and
    # the subsequent exact-HEAD Python classifier.
    covered = set()
    for pat in globs:
        for matched in glob.glob(str(ROOT / pat), recursive=True):
            p = Path(matched)
            if p.is_file():
                covered.add(p.resolve().relative_to(ROOT.resolve()).as_posix())

    event_misses = sorted(p for p in covered if not any(
        fnmatch.fnmatchcase(p, x) for x in event_paths))
    classifier_misses = sorted(p for p in covered if not any(
        fnmatch.fnmatchcase(p, x) for x in globs))

    # Independent positive/negative controls are actual checked-in files.
    assert "docs/V030_RELEASE_LOCK.json" in covered
    assert "docs/V030_RELEASE_LOCK.json" in event_misses
    assert "src/cmpct/reader.py" in covered
    assert "src/cmpct/reader.py" not in event_misses
    assert "src/cmpct/reader.py" not in classifier_misses

    # Prospective zero-directory globstar case proves fnmatch/glob non-equivalence
    # independently, without contaminating the CMPCT source tree.
    with tempfile.TemporaryDirectory() as tmp:
        r = Path(tmp)
        (r / "src").mkdir()
        (r / "src/one.py").write_text("# zero-segment witness\n")
        hit = {Path(p).relative_to(r).as_posix()
               for p in glob.glob(str(r / "src/**/*.py"), recursive=True)}
        assert "src/one.py" in hit
        assert not fnmatch.fnmatchcase("src/one.py", "src/**/*.py")

    result = {
        "schema": "cmpct-v031-release-fingerprint-admission-scope-court-v1",
        "source_head_parent": "4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b",
        "original_lock_blob": LOCK_BLOB,
        "original_workflow_blob": WORKFLOW_BLOB,
        "fingerprinted_existing_paths": len(covered),
        "pr_event_excluded_fingerprinted_paths": len(event_misses),
        "inner_classifier_excluded_existing_fingerprinted_paths": len(classifier_misses),
        "event_exclusions": event_misses,
        "classifier_exclusions": classifier_misses,
        "current_witness": "docs/V030_RELEASE_LOCK.json",
        "prospective_globstar_witness": "src/one.py",
        "positive_control": "src/cmpct/reader.py",
        "classification": "NEGATIVE_EVIDENCE_ONLY_NO_RELEASE_OR_PRODUCT_CREDIT"
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    Path("fingerprint-scope-court.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
