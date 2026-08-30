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


def _preserved_receipt_is_exact(text: str, lane: str | None) -> bool:
    if not PRESERVE_EXACT_RECEIPT_RE.search(text) or lane != "deep":
        return False
    if not PATH_SCOPE_RE.search(text) or not CONCURRENCY_RE.search(text) or not EXACT_HEAD_CHECKOUT_RE.search(text):
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
        if lane in {"deep", "release", "publisher"} and not PATH_SCOPE_RE.search(text):
            errors.append(f"{lane} PR workflow must use paths/paths-ignore or become manual/scheduled")

    if consumes_runner and PUSH_RE.search(text) and not BRANCH_SCOPE_RE.search(text):
        errors.append("automatic push workflow must scope branches; bare feature-branch push duplicates PR work")

    # Deep research receipts are allowed to run from a branch-scoped push instead of a long-lived PR synchronize
    # event. Push-path filters apply to the new push rather than the PR's entire accumulated diff, which prevents a
    # research lane introduced early in a large integration PR from retriggering on every unrelated commit. These
    # receipts remain research-only unless a separate exact-candidate release authority explicitly consumes them.
    #
    # Very long exact-head A/Bs may preserve a running receipt with the explicit directive above. PR-triggered
    # variants must bind EVIDENCE_HEAD to pull_request.head.sha; branch-push variants bind it to github.sha. Both
    # must check out that exact env value and be path scoped. This changes scheduling only, never evidence identity.
    #
    # A falsified or fully superseded research lane may instead declare `# ci-auto-policy: retired-manual-only`.
    # That declaration is a durable no-run ratchet: the workflow may remain available through workflow_dispatch for
    # reproducibility and historical evidence, but it may not silently resume consuming runners on PR/push/schedule.
    #
    # Conversely, a normal cancel-on-new-head PR lane must not key its concurrency group by that same head SHA:
    # different commits would then enter different groups and could never cancel one another. Scheduling identity
    # belongs to the PR/ref; evidence identity belongs to the checked-out candidate SHA.

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
