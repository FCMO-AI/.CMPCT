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
CANCEL_RE = re.compile(r"(?m)^\s+cancel-in-progress:\s*true\s*$")
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
        if not CANCEL_RE.search(text):
            errors.append("automatic runner workflow lacks 'cancel-in-progress: true'")

    if consumes_runner and PULL_REQUEST_RE.search(text):
        if lane in {"deep", "release", "publisher"} and not PATH_SCOPE_RE.search(text):
            errors.append(f"{lane} PR workflow must use paths/paths-ignore or become manual/scheduled")

    if consumes_runner and PUSH_RE.search(text) and not BRANCH_SCOPE_RE.search(text):
        errors.append("automatic push workflow must scope branches; bare feature-branch push duplicates PR work")

    # Footnote: historical publishers that remain PR-triggered are particularly expensive because they
    # often discover at runtime that the durable target already exists. The lane rule makes that choice
    # explicit and forces path scoping at minimum; once one-shot publication is complete they should be
    # workflow_dispatch-only per docs/CI_ARCHITECTURE.md.

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
