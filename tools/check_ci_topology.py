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
EXACT_HEAD_RE = re.compile(r"github\.event\.pull_request\.head\.sha")
PATH_SCOPE_RE = re.compile(r"(?m)^\s+(paths|paths-ignore):\s*$")
BRANCH_SCOPE_RE = re.compile(r"(?m)^\s+branches(?:-ignore)?:\s*")


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

    if consumes_runner and auto_events:
        if not CONCURRENCY_RE.search(text):
            errors.append("automatic runner workflow lacks a top-level concurrency group")
        if CANCEL_RE.search(text) and PULL_REQUEST_RE.search(text) and CONCURRENCY_HEAD_SHA_RE.search(text):
            errors.append(
                "cancel-in-progress is ineffective because the concurrency group is keyed by pull_request.head.sha; "
                "use a PR/ref scheduling key and keep exact SHA custody in checkout/evidence instead"
            )
        if not CANCEL_RE.search(text):
            preserve_exact_receipt = bool(PRESERVE_EXACT_RECEIPT_RE.search(text))
            if not (
                preserve_exact_receipt
                and lane == "deep"
                and PULL_REQUEST_RE.search(text)
                and PATH_SCOPE_RE.search(text)
                and CONCURRENCY_RE.search(text)
                and EXACT_HEAD_RE.search(text)
            ):
                errors.append(
                    "automatic runner workflow lacks 'cancel-in-progress: true' or the narrow "
                    "deep/exact-head preserved-receipt policy"
                )

    if consumes_runner and PULL_REQUEST_RE.search(text):
        if lane in {"deep", "release", "publisher"} and not PATH_SCOPE_RE.search(text):
            errors.append(f"{lane} PR workflow must use paths/paths-ignore or become manual/scheduled")

    if consumes_runner and PUSH_RE.search(text) and not BRANCH_SCOPE_RE.search(text):
        errors.append("automatic push workflow must scope branches; bare feature-branch push duplicates PR work")

    # Footnote: historical publishers that remain PR-triggered are particularly expensive because they
    # often discover at runtime that the durable target already exists. The lane rule makes that choice
    # explicit and forces path scoping at minimum; once one-shot publication is complete they should be
    # workflow_dispatch-only per docs/CI_ARCHITECTURE.md.
    #
    # Very long exact-head A/Bs are a separate case: cancelling a 20+ minute measurement whenever an
    # unrelated PR commit lands can prevent any receipt from completing at all. A deep lane may preserve
    # its running receipt only with the explicit directive above, PR path scoping, a concurrency group,
    # and direct pull_request.head.sha custody. The completed predecessor remains research-only; this
    # exception changes runner scheduling, never release-evidence inheritance.
    #
    # Conversely, a normal cancel-on-new-head lane must not key its concurrency group by that same head SHA:
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
            # Deleted workflows cannot introduce new fan-out.
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
