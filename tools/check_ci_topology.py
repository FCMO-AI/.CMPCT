from __future__ import annotations

import re
import sys
from pathlib import Path

# Footnote: this is intentionally a lightweight text-level ratchet rather than a full YAML parser.
# GitHub's workflow YAML uses expressions and the key `on`, both of which have surprising behavior
# under generic YAML 1.1 parsers. The checker only enforces topology invariants that are unambiguous
# in source text, leaving workflow semantics to GitHub's own parser.

ALLOWED_LANES = {"fast", "deep", "release", "scheduled", "publisher"}
LANE_RE = re.compile(r"(?m)^# ci-lane: ([a-z-]+)\s*$")
AUTO_EVENT_RE = re.compile(r"(?m)^  (pull_request|push|schedule):(?:\s|$)")
PULL_REQUEST_RE = re.compile(r"(?m)^  pull_request:(?:\s|$)")
PUSH_RE = re.compile(r"(?m)^  push:(?:\s|$)")
RUNNER_RE = re.compile(r"(?m)^\s+runs-on:")
CONCURRENCY_RE = re.compile(r"(?m)^concurrency:\s*$")
CONCURRENCY_HEAD_SHA_RE = re.compile(r"(?m)^\s+group:.*github\.event\.pull_request\.head\.sha")
CONCURRENCY_GITHUB_SHA_RE = re.compile(r"(?m)^\s+group:.*github\.sha")
CANCEL_RE = re.compile(r"(?m)^\s+cancel-in-progress:\s*true\s*$")
CANCEL_FALSE_RE = re.compile(r"(?m)^\s+cancel-in-progress:\s*false\s*$")
PRESERVE_EXACT_RECEIPT_RE = re.compile(r"(?m)^# ci-cancel-policy: preserve-running-exact-receipt\s*$")
SPLIT_RECEIPT_RE = re.compile(r"(?m)^# ci-cancel-policy: split-classifier-preserve-receipts\s*$")
HEAD_CHANGE_GATE_RE = re.compile(r"(?m)^# ci-pr-scope: latest-head-commit-gate\s*$")
HEAD_CHANGE_DIFF_RE = re.compile(r"git diff-tree --no-commit-id --name-only -r HEAD")
RETIRED_MANUAL_ONLY_RE = re.compile(r"(?m)^# ci-auto-policy: retired-manual-only\s*$")
PR_EXACT_HEAD_BINDING_RE = re.compile(
    r"(?m)^\s+EVIDENCE_HEAD:\s*\$\{\{\s*github\.event\.pull_request\.head\.sha\s*\|\|\s*github\.sha\s*\}\}\s*$"
)
PUSH_EXACT_HEAD_BINDING_RE = re.compile(
    r"(?m)^\s+EVIDENCE_HEAD:\s*\$\{\{\s*github\.sha\s*\}\}\s*$"
)
EXACT_HEAD_CHECKOUT_RE = re.compile(r"(?m)^\s+ref:\s*\$\{\{\s*env\.EVIDENCE_HEAD\s*\}\}\s*$")
PATH_SCOPE_RE = re.compile(r"(?m)^\s+(paths|paths-ignore):\s*$")
BRANCH_SCOPE_RE = re.compile(r"(?m)^\s+branches(?:-ignore)?:\s*")
LEGACY_PYTHON_SOURCE_TRIGGER_RE = re.compile(r"(?m)^\s+-\s*['\"]cmpct/\*\*['\"]\s*$")
LEGACY_PYTHON_SOURCE_CLASSIFIER_RE = re.compile(r"(?:\^|[|(])cmpct/(?:\.\*)?")
JOB_CONCURRENCY_RE = re.compile(r"(?m)^    concurrency:\s*$")
JOB_PR_GROUP_RE = re.compile(
    r"(?m)^\s+group:.*github\.event\.pull_request\.number(?:\s*\|\|\s*github\.ref)?"
)
JOB_EXACT_GROUP_RE = re.compile(
    r"(?m)^\s+group:.*(?:github\.event\.pull_request\.head\.sha|github\.sha)"
)


def _has_exact_head_commit_scope(text: str) -> bool:
    return bool(HEAD_CHANGE_DIFF_RE.search(text))


def _preserved_receipt_is_exact(text: str, lane: str | None) -> bool:
    # Deep research A/Bs and release authorities can both be multi-hour exact-head receipts. GitHub concurrency
    # permits only one pending run per group, so preserving a running receipt is not enough: the scheduling group
    # must also contain the exact evidence SHA or a newer run can evict the queued receipt before it starts.
    if not PRESERVE_EXACT_RECEIPT_RE.search(text) or lane not in {"deep", "release"}:
        return False
    scoped = bool(PATH_SCOPE_RE.search(text) or _has_exact_head_commit_scope(text))
    if not scoped or not CONCURRENCY_RE.search(text) or not EXACT_HEAD_CHECKOUT_RE.search(text):
        return False
    if PULL_REQUEST_RE.search(text):
        if not PR_EXACT_HEAD_BINDING_RE.search(text) or not CONCURRENCY_HEAD_SHA_RE.search(text):
            return False
    if PUSH_RE.search(text):
        if not BRANCH_SCOPE_RE.search(text):
            return False
        # A workflow supporting both PR and push may use `pull_request.head.sha || github.sha`; pure push lanes
        # normally use github.sha directly. In either case the concurrency group must include github.sha.
        if not CONCURRENCY_GITHUB_SHA_RE.search(text):
            return False
        if not (PUSH_EXACT_HEAD_BINDING_RE.search(text) or PR_EXACT_HEAD_BINDING_RE.search(text)):
            return False
    return bool(PULL_REQUEST_RE.search(text) or PUSH_RE.search(text))


def _split_receipt_custody_is_exact(text: str, lane: str | None) -> bool:
    """Validate the queue-safe two-level exact-receipt model.

    A long-lived PR makes GitHub evaluate ``pull_request.paths`` against the accumulated PR diff. With workflow-
    level exact-SHA concurrency that means every unrelated commit still reserves a distinct queued classifier run.
    The split model cancels only obsolete classifier *jobs* by PR/ref while keeping each expensive receipt job in an
    exact-SHA, non-cancelling group. A newer classifier therefore cannot kill a useful old receipt, but dozens of
    obsolete five-second classifiers no longer consume pending-run capacity.
    """
    if not SPLIT_RECEIPT_RE.search(text) or lane not in {"deep", "release"}:
        return False
    if not PULL_REQUEST_RE.search(text) or not HEAD_CHANGE_GATE_RE.search(text) or not _has_exact_head_commit_scope(text):
        return False
    if not PR_EXACT_HEAD_BINDING_RE.search(text) or not EXACT_HEAD_CHECKOUT_RE.search(text):
        return False
    if not JOB_CONCURRENCY_RE.search(text):
        return False
    if not JOB_PR_GROUP_RE.search(text) or not JOB_EXACT_GROUP_RE.search(text):
        return False
    if not CANCEL_RE.search(text) or not CANCEL_FALSE_RE.search(text):
        return False
    # A workflow-level group would defeat the split: exact SHA recreates the classifier backlog, while a PR-level
    # cancelling group would kill the very receipt this policy exists to preserve.
    return not CONCURRENCY_RE.search(text)


def validate(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    lane_match = LANE_RE.search(text)
    if not lane_match:
        errors.append("missing '# ci-lane: fast|deep|release|scheduled|publisher' declaration")
        lane = None
    else:
        lane = lane_match.group(1)
        if lane not in ALLOWED_LANES:
            errors.append(f"unknown CI lane {lane!r}")

    consumes_runner = bool(RUNNER_RE.search(text))
    auto_events = AUTO_EVENT_RE.findall(text)
    split_receipt = SPLIT_RECEIPT_RE.search(text) is not None

    # The installed package is rooted at src/cmpct/. A historical bare cmpct/** trigger/classifier silently watches
    # a non-existent tree, allowing shipping Python changes to bypass evidence lanes. Keep this as a text-level typo
    # ratchet rather than forcing every workflow to watch src/cmpct: only workflows that claim the package dependency
    # must spell the canonical source root correctly.
    if LEGACY_PYTHON_SOURCE_TRIGGER_RE.search(text) or LEGACY_PYTHON_SOURCE_CLASSIFIER_RE.search(text):
        errors.append("workflow scopes non-existent 'cmpct/' source root; canonical Python package is 'src/cmpct/'")

    if HEAD_CHANGE_GATE_RE.search(text) and not HEAD_CHANGE_DIFF_RE.search(text):
        errors.append("latest-head-commit gate directive requires an exact HEAD diff-tree classifier")

    if RETIRED_MANUAL_ONLY_RE.search(text) and auto_events:
        errors.append(
            "retired-manual-only workflow must not declare pull_request, push, or schedule triggers; "
            "preserve it for workflow_dispatch replay only"
        )

    if consumes_runner and auto_events:
        if split_receipt:
            if not _split_receipt_custody_is_exact(text, lane):
                errors.append(
                    "split exact-receipt policy requires job-level PR/ref cancelling classifier concurrency plus "
                    "job-level exact-SHA non-cancelling receipt concurrency, exact checkout and newest-head scope"
                )
        else:
            if not CONCURRENCY_RE.search(text):
                errors.append("automatic runner workflow lacks a top-level concurrency group")
            if CANCEL_RE.search(text) and PULL_REQUEST_RE.search(text) and CONCURRENCY_HEAD_SHA_RE.search(text):
                errors.append(
                    "cancel-in-progress is ineffective because the concurrency group is keyed by pull_request.head.sha; "
                    "use a PR/ref scheduling key and keep exact SHA custody in checkout/evidence instead"
                )
            if not CANCEL_RE.search(text) and not _preserved_receipt_is_exact(text, lane):
                errors.append(
                    "automatic runner workflow lacks 'cancel-in-progress: true' or the narrow deep/release exact-head "
                    "preserved-receipt policy with exact-SHA pending-run custody"
                )

    if consumes_runner and PULL_REQUEST_RE.search(text):
        if lane in {"deep", "release", "publisher"} and not (
            PATH_SCOPE_RE.search(text) or _has_exact_head_commit_scope(text)
        ):
            errors.append(
                f"{lane} PR workflow must use paths/paths-ignore or an exact latest-head-commit gate"
            )
        if lane == "deep" and not _has_exact_head_commit_scope(text):
            errors.append(
                "deep PR workflow must use an exact latest-head-commit gate; accumulated PR paths are not "
                "sufficient scheduling scope for long-lived integration branches"
            )

    if consumes_runner and PUSH_RE.search(text) and not BRANCH_SCOPE_RE.search(text):
        errors.append("automatic push workflow must scope branches; bare feature-branch push duplicates PR work")

    return errors


def main(argv: list[str]) -> int:
    paths = [Path(arg) for arg in argv[1:] if arg.endswith((".yml", ".yaml"))]
    if not paths:
        print("CI topology: no changed workflow files")
        return 0

    failed = False
    for path in paths:
        if not path.exists():
            continue
        errors = validate(path)
        if errors:
            failed = True
            print(f"{path}:")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"{path}: topology OK")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
