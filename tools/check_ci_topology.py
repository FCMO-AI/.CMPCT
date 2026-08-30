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
CANCEL_RE = re.compile(r"(?m)^\s+cancel-in-progress:\s*true\s*$")
PRESERVE_EXACT_RECEIPT_RE = re.compile(r"(?m)^# ci-cancel-policy: preserve-running-exact-receipt\s*$")
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


def _has_exact_head_commit_scope(text: str) -> bool:
    return bool(HEAD_CHANGE_GATE_RE.search(text) and HEAD_CHANGE_DIFF_RE.search(text))


def _preserved_receipt_is_exact(text: str, lane: str | None) -> bool:
    if not PRESERVE_EXACT_RECEIPT_RE.search(text) or lane != "deep":
        return False
    scoped = bool(PATH_SCOPE_RE.search(text) or _has_exact_head_commit_scope(text))
    if not scoped or not CONCURRENCY_RE.search(text) or not EXACT_HEAD_CHECKOUT_RE.search(text):
        return False
    if PULL_REQUEST_RE.search(text) and PR_EXACT_HEAD_BINDING_RE.search(text):
        return True
    if PUSH_RE.search(text) and BRANCH_SCOPE_RE.search(text) and PUSH_EXACT_HEAD_BINDING_RE.search(text):
        return True
    return False


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

    if HEAD_CHANGE_GATE_RE.search(text) and not HEAD_CHANGE_DIFF_RE.search(text):
        errors.append("latest-head-commit gate directive requires an exact HEAD diff-tree classifier")

    if RETIRED_MANUAL_ONLY_RE.search(text) and auto_events:
        errors.append(
            "retired-manual-only workflow must not declare pull_request, push, or schedule triggers; "
            "preserve it for workflow_dispatch replay only"
        )

    if consumes_runner and auto_events:
        if not CONCURRENCY_RE.search(text):
            errors.append("automatic runner workflow lacks a top-level concurrency group")
        if CANCEL_RE.search(text) and PULL_REQUEST_RE.search(text) and CONCURRENCY_HEAD_SHA_RE.search(text):
            errors.append(
                "cancel-in-progress is ineffective because the concurrency group is keyed by pull_request.head.sha; "
                "use a PR/ref scheduling key and keep exact SHA custody in checkout/evidence instead"
            )
        if not CANCEL_RE.search(text) and not _preserved_receipt_is_exact(text, lane):
            errors.append(
                "automatic runner workflow lacks 'cancel-in-progress: true' or the narrow "
                "deep/exact-head preserved-receipt policy"
            )

    if consumes_runner and PULL_REQUEST_RE.search(text):
        if lane in {"deep", "release", "publisher"} and not (
            PATH_SCOPE_RE.search(text) or _has_exact_head_commit_scope(text)
        ):
            errors.append(
                f"{lane} PR workflow must use paths/paths-ignore or an exact latest-head-commit gate"
            )

    if consumes_runner and PUSH_RE.search(text) and not BRANCH_SCOPE_RE.search(text):
        errors.append("automatic push workflow must scope branches; bare feature-branch push duplicates PR work")

    # GitHub evaluates PR `paths:` against the whole accumulated PR diff. On a long-lived integration PR that can
    # cause a deep lane introduced hundreds of commits ago to rerun on every unrelated synchronization. A workflow
    # may instead declare `# ci-pr-scope: latest-head-commit-gate` and cheaply classify only the newest exact HEAD
    # commit with `git diff-tree ... HEAD`; the expensive job must then depend on that classifier output. This is a
    # scheduling optimization only: exact candidate SHA custody remains mandatory.
    #
    # Very long exact-head A/Bs may preserve a running receipt with the explicit directive above. PR-triggered
    # variants must bind EVIDENCE_HEAD to pull_request.head.sha; branch-push variants bind it to github.sha. Both
    # must check out that exact env value. A falsified or superseded lane may instead be retired-manual-only.

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
