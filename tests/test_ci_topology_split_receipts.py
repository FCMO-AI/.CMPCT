from __future__ import annotations

from pathlib import Path

from tools import check_ci_topology as C


ROOT = Path(__file__).resolve().parents[1]

# These are the highest-cost normative product/release authorities on the long-lived v0.30 integration PR. They
# must not regress to workflow-level exact-SHA concurrency: doing so preserves every otherwise-useless classifier
# invocation and recreates the runner starvation that blocks current release receipts.
SPLIT_AUTHORITIES = (
    ".github/workflows/v030-native-authority.yml",
    ".github/workflows/v030-final-release-authority.yml",
    ".github/workflows/v030-canonical-authority.yml",
    ".github/workflows/v030-external-competitors.yml",
    ".github/workflows/v030-authoritative-v2-pr.yml",
    ".github/workflows/v030-r25-manifest-canonical-integration.yml",
    ".github/workflows/v030-r25-manifest-derived-identity.yml",
    ".github/workflows/v030-r25-manifest-canonical-candidate.yml",
    ".github/workflows/v030-r25-manifest-implicit-reader-productization.yml",
    ".github/workflows/v030-r25-manifest-writer-admission.yml",
    ".github/workflows/v030-federated-generalization-admission.yml",
    ".github/workflows/v030-federated-candidate-productization.yml",
    ".github/workflows/v030-logs-sidecar-content-policy.yml",
    ".github/workflows/v030-logs-inverse-profile-productization.yml",
)


def test_migrated_release_authorities_satisfy_split_receipt_policy() -> None:
    for relative in SPLIT_AUTHORITIES:
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        assert "# ci-cancel-policy: split-classifier-preserve-receipts" in text
        assert C.validate(path) == [], relative


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
