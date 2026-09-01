from __future__ import annotations

from pathlib import Path

from tools import check_ci_topology as C


ROOT = Path(__file__).resolve().parents[1]


def test_migrated_native_authority_satisfies_split_receipt_policy() -> None:
    path = ROOT / ".github/workflows/v030-native-authority.yml"
    assert C.validate(path) == []


def test_split_receipt_policy_rejects_workflow_level_concurrency(tmp_path: Path) -> None:
    workflow = tmp_path / "bad.yml"
    workflow.write_text(
        """# ci-lane: release
# ci-cancel-policy: split-classifier-preserve-receipts
# ci-pr-scope: latest-head-commit-gate
on:
  pull_request:
    paths:
      - 'src/**'
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
concurrency:
  group: bad-${{ github.event.pull_request.head.sha || github.sha }}
  cancel-in-progress: false
jobs:
  scope:
    runs-on: ubuntu-latest
    concurrency:
      group: scope-${{ github.event.pull_request.number || github.ref }}
      cancel-in-progress: true
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
      - run: git diff-tree --no-commit-id --name-only -r HEAD
  receipt:
    runs-on: ubuntu-latest
    concurrency:
      group: receipt-${{ github.event.pull_request.head.sha || github.sha }}
      cancel-in-progress: false
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
""",
        encoding="utf-8",
    )
    errors = C.validate(workflow)
    assert any("split exact-receipt policy" in error for error in errors)


def test_split_receipt_policy_rejects_missing_pr_classifier_group(tmp_path: Path) -> None:
    workflow = tmp_path / "bad.yml"
    workflow.write_text(
        """# ci-lane: release
# ci-cancel-policy: split-classifier-preserve-receipts
# ci-pr-scope: latest-head-commit-gate
on:
  pull_request:
    paths:
      - 'src/**'
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  scope:
    runs-on: ubuntu-latest
    concurrency:
      group: scope-${{ github.event.pull_request.head.sha || github.sha }}
      cancel-in-progress: true
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
      - run: git diff-tree --no-commit-id --name-only -r HEAD
  receipt:
    runs-on: ubuntu-latest
    concurrency:
      group: receipt-${{ github.event.pull_request.head.sha || github.sha }}
      cancel-in-progress: false
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
""",
        encoding="utf-8",
    )
    errors = C.validate(workflow)
    assert any("split exact-receipt policy" in error for error in errors)
