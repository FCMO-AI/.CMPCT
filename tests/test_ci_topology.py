from __future__ import annotations

from pathlib import Path

from tools.check_ci_topology import validate


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "workflow.yml"
    path.write_text(body, encoding="utf-8")
    return path


def test_ordinary_automatic_runner_still_requires_cancel_true(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
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
""")
    assert any("cancel-in-progress: true" in error for error in validate(path))


def test_deep_pr_path_scope_alone_is_not_enough_on_long_integration_pr(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
on:
  pull_request:
    paths:
      - 'benchmarks/**'
concurrency:
  group: expensive-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
jobs:
  proof:
    runs-on: ubuntu-24.04
""")
    assert any("accumulated PR paths are not sufficient" in error for error in validate(path))


def test_exact_head_deep_lane_may_preserve_running_and_queued_receipt(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
# ci-pr-scope: latest-head-commit-gate
on:
  pull_request:
    paths:
      - 'benchmarks/**'
concurrency:
  group: long-ab-${{ github.event.pull_request.head.sha || github.sha }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  classify:
    runs-on: ubuntu-24.04
    steps:
      - run: git diff-tree --no-commit-id --name-only -r HEAD
  proof:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
""")
    assert validate(path) == []


def test_exact_head_release_lane_may_preserve_running_and_queued_receipt(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: release
# ci-cancel-policy: preserve-running-exact-receipt
# ci-pr-scope: latest-head-commit-gate
on:
  pull_request:
    paths:
      - 'experiments/**'
concurrency:
  group: release-authority-${{ github.event.pull_request.head.sha || github.sha }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  classify:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
      - run: git diff-tree --no-commit-id --name-only -r HEAD
  authority:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
""")
    assert validate(path) == []


def test_branch_push_deep_lane_may_preserve_running_and_queued_receipt(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
on:
  push:
    branches:
      - agent/v030-authoritative-integration
    paths:
      - 'benchmarks/**'
concurrency:
  group: long-ab-${{ github.sha }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
""")
    assert validate(path) == []


def test_pr_preserved_receipt_rejects_pr_number_concurrency_key(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
# ci-pr-scope: latest-head-commit-gate
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
  classify:
    runs-on: ubuntu-24.04
    steps:
      - run: git diff-tree --no-commit-id --name-only -r HEAD
  proof:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
""")
    assert any("pending-run custody" in error for error in validate(path))


def test_push_preserved_receipt_rejects_ref_concurrency_key(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
on:
  push:
    branches:
      - agent/v030-authoritative-integration
    paths:
      - 'benchmarks/**'
concurrency:
  group: long-ab-${{ github.ref }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
""")
    assert any("pending-run custody" in error for error in validate(path))


def test_push_preserved_receipt_requires_branch_scope(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
on:
  push:
    paths:
      - 'benchmarks/**'
concurrency:
  group: long-ab-${{ github.sha }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
""")
    errors = validate(path)
    assert any("preserved-receipt policy" in error for error in errors)
    assert any("must scope branches" in error for error in errors)


def test_preserved_receipt_policy_fails_without_path_scope(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
on:
  pull_request:
concurrency:
  group: long-ab-${{ github.event.pull_request.head.sha || github.sha }}
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
    assert any("preserved-receipt policy" in error for error in errors)
    assert any("must use paths/paths-ignore" in error for error in errors)


def test_preserved_receipt_policy_fails_without_exact_head_binding(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
on:
  pull_request:
    paths:
      - 'benchmarks/**'
concurrency:
  group: long-ab-${{ github.event.pull_request.head.sha || github.sha }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ env.EVIDENCE_HEAD }}
""")
    assert any("preserved-receipt policy" in error for error in validate(path))


def test_preserved_receipt_policy_fails_without_exact_checkout(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-cancel-policy: preserve-running-exact-receipt
on:
  pull_request:
    paths:
      - 'benchmarks/**'
concurrency:
  group: long-ab-${{ github.event.pull_request.head.sha || github.sha }}
  cancel-in-progress: false
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  proof:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
""")
    assert any("preserved-receipt policy" in error for error in validate(path))


def test_fast_lane_cannot_use_preserved_receipt_escape(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: fast
# ci-cancel-policy: preserve-running-exact-receipt
on:
  pull_request:
    paths:
      - 'src/**'
concurrency:
  group: fast-${{ github.event.pull_request.head.sha || github.sha }}
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
    assert any("preserved-receipt policy" in error for error in validate(path))


def test_cancel_true_cannot_key_group_by_exact_head_sha(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
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
""")
    assert any("concurrency group is keyed by pull_request.head.sha" in error for error in validate(path))


def test_cancel_true_pr_group_keeps_exact_sha_as_evidence_only(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-pr-scope: latest-head-commit-gate
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
  classify:
    runs-on: ubuntu-24.04
    steps:
      - run: git diff-tree --no-commit-id --name-only -r HEAD
  proof:
    runs-on: ubuntu-24.04
""")
    assert validate(path) == []


def test_retired_manual_only_lane_accepts_workflow_dispatch(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-auto-policy: retired-manual-only
on:
  workflow_dispatch:
jobs:
  proof:
    runs-on: ubuntu-24.04
""")
    assert validate(path) == []


def test_retired_manual_only_lane_rejects_automatic_trigger(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: deep
# ci-auto-policy: retired-manual-only
on:
  pull_request:
    paths:
      - 'benchmarks/**'
  workflow_dispatch:
concurrency:
  group: stale-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
jobs:
  proof:
    runs-on: ubuntu-24.04
""")
    assert any("retired-manual-only workflow" in error for error in validate(path))


def test_canonical_r25_authority_keeps_independent_golden_in_trigger_and_exact_head_gate() -> None:
    workflow = Path('.github/workflows/v030-canonical-authority.yml').read_text(encoding='utf-8')
    assert "- 'tests/conformance/v030-r25-canonical.json'" in workflow
    assert 'tests/conformance/v030-r25-canonical\\.json' in workflow


def test_release_workflow_rejects_nonexistent_bare_cmpct_trigger(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: release
on:
  pull_request:
    paths:
      - 'cmpct/**'
concurrency:
  group: release-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
jobs:
  proof:
    runs-on: ubuntu-24.04
""")
    assert any("canonical Python package is 'src/cmpct/'" in error for error in validate(path))


def test_release_workflow_rejects_nonexistent_bare_cmpct_classifier(tmp_path: Path) -> None:
    path = _write(tmp_path, """# ci-lane: release
# ci-pr-scope: latest-head-commit-gate
on:
  pull_request:
    paths:
      - 'src/cmpct/**'
concurrency:
  group: release-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
env:
  EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}
jobs:
  classify:
    runs-on: ubuntu-24.04
    steps:
      - run: |
          git diff-tree --no-commit-id --name-only -r HEAD
          grep -Eq '^(cmpct/.*|tests/.*)' changed.txt
""")
    assert any("canonical Python package is 'src/cmpct/'" in error for error in validate(path))
