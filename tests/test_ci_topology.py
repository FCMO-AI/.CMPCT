from __future__ import annotations

from pathlib import Path

from tools.check_ci_topology import validate


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "workflow.yml"
    path.write_text(body, encoding="utf-8")
    return path


def test_ordinary_automatic_runner_still_requires_cancel_true(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# ci-lane: deep
on:
  pull_request:
    paths:
      - 'benchmarks/**'
concurrency:
  group: ordinary-${{ github.event.pull_request.number }}
  cancel-in-progress: false
jobs:
  proof:
    runs-on: ubuntu-24.04
""",
    )
    errors = validate(path)
    assert any("cancel-in-progress: true" in error for error in errors)


def test_exact_head_deep_lane_may_preserve_running_receipt(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
on:
  pull_request:
    paths:
      - 'benchmarks/**'
concurrency:
  group: long-ab-${{ github.event.pull_request.number }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
""",
    )
    assert validate(path) == []


def test_preserved_receipt_policy_fails_without_path_scope(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
on:
  pull_request:
concurrency:
  group: long-ab-${{ github.event.pull_request.number }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
""",
    )
    errors = validate(path)
    assert any("preserved-receipt policy" in error for error in errors)
    assert any("must use paths/paths-ignore" in error for error in errors)


def test_preserved_receipt_policy_fails_without_exact_head_binding(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
on:
  pull_request:
    paths:
      - 'benchmarks/**'
concurrency:
  group: long-ab-${{ github.event.pull_request.number }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
""",
    )
    errors = validate(path)
    assert any("preserved-receipt policy" in error for error in errors)


def test_fast_lane_cannot_use_preserved_receipt_escape(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# ci-lane: fast
# ci-cancel-policy: preserve-running-exact-receipt
on:
  pull_request:
    paths:
      - 'src/**'
concurrency:
  group: fast-${{ github.event.pull_request.number }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
""",
    )
    errors = validate(path)
    assert any("preserved-receipt policy" in error for error in errors)


def test_cancel_true_cannot_key_group_by_exact_head_sha(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# ci-lane: deep
on:
  pull_request:
    paths:
      - 'benchmarks/**'
concurrency:
  group: expensive-${{ github.event.pull_request.head.sha || github.sha }}
  cancel-in-progress: true
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
""",
    )
    errors = validate(path)
    assert any("concurrency group is keyed by pull_request.head.sha" in error for error in errors)


def test_cancel_true_pr_group_keeps_exact_sha_as_evidence_only(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """# ci-lane: deep
on:
  pull_request:
    paths:
      - 'benchmarks/**'
concurrency:
  group: expensive-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
""",
    )
    assert validate(path) == []
