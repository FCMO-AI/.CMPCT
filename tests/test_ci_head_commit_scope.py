from __future__ import annotations

from pathlib import Path

from tools.check_ci_topology import validate


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "workflow.yml"
    path.write_text(body, encoding="utf-8")
    return path


def test_exact_head_commit_gate_is_valid_deep_pr_scope(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
# ci-pr-scope: latest-head-commit-gate
on:
  pull_request:
concurrency:
  group: deep-${{ github.event.pull_request.number }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  changes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
      - run: git diff-tree --no-commit-id --name-only -r HEAD
  proof:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
""")
    assert validate(path) == []


def test_head_commit_gate_marker_without_exact_classifier_fails(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
# ci-pr-scope: latest-head-commit-gate
on:
  pull_request:
concurrency:
  group: deep-${{ github.event.pull_request.number }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
""")
    errors = validate(path)
    assert any("requires an exact HEAD diff-tree classifier" in error for error in errors)
    assert any("preserved-receipt policy" in error for error in errors)


def test_unscoped_deep_pr_still_fails(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
on:
  pull_request:
concurrency:
  group: deep-${{ github.event.pull_request.number }}
  cancel-in-progress: true
jobs:
  proof:
    runs-on: ubuntu-24.04
""")
    assert any("must use paths/paths-ignore or an exact latest-head-commit gate" in error for error in validate(path))
