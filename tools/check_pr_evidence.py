#!/usr/bin/env python3
from __future__ import annotations

"""Reject material pull requests whose evidence dossier is structurally incomplete."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

from check_version_discipline import MATERIAL_PREFIXES, MATERIAL_SINGLETONS

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SECTIONS = (
    "Problem and baseline",
    "Insight and hypothesis",
    "Alternatives considered",
    "Evidence",
    "Losses, ambiguity and negative evidence",
    "Safety, integrity and resource accounting",
    "Compatibility and portability",
    "Performance accounting",
    "Public-surface check",
    "Completion gates",
    "Future leverage",
)

# Footnote: these are structural/falsifiability markers, not a proxy score for intelligence. CI can
# prove that a contributor exposed a baseline and disproof surface; reviewers still judge whether the
# reasoning and evidence are technically good.
REQUIRED_MARKERS = (
    "disproof",
    "quality-ratchet",
)


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def material_paths(base: str) -> list[str]:
    changed = run("git", "diff", "--name-only", f"{base}...HEAD").splitlines()
    material = [p for p in changed if p in MATERIAL_SINGLETONS or p.startswith(MATERIAL_PREFIXES)]
    return [
        p
        for p in material
        if not p.startswith("docs/releases/") and not p.startswith("benchmarks/history/")
    ]


def normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def sections(body: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", body))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        result[normalize_heading(match.group(1))] = body[start:end].strip()
    return result


def visible_text(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"[-*]\s*\[[ xX]\]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def fail(message: str) -> int:
    print(f"engineering evidence: {message}", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-sha", required=True)
    ap.add_argument("--event", type=Path, required=True)
    args = ap.parse_args()

    try:
        material = material_paths(args.base_sha)
    except subprocess.CalledProcessError as exc:
        return fail(f"unable to inspect base {args.base_sha}: {exc}")

    if not material:
        print("engineering evidence: no material CMPCT paths changed")
        return 0

    try:
        event = json.loads(args.event.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail(f"cannot read pull-request event: {exc}")

    pr = event.get("pull_request") or {}
    body = str(pr.get("body") or "")
    draft = bool(pr.get("draft"))
    if not body.strip():
        return fail("material PR has no evidence dossier body")

    parsed = sections(body)
    missing: list[str] = []
    empty: list[str] = []
    for expected in REQUIRED_SECTIONS:
        key = normalize_heading(expected)
        if key not in parsed:
            missing.append(expected)
            continue
        # Footnote: a terse N/A is acceptable only when it explains why. Empty headings and untouched
        # template prompts are not evidence and should not make a material PR look complete.
        if len(visible_text(parsed[key])) < 24:
            empty.append(expected)

    if missing:
        print("engineering evidence: missing required section(s):", file=sys.stderr)
        for name in missing:
            print(f"  - {name}", file=sys.stderr)
        return 1
    if empty:
        print("engineering evidence: section(s) need concrete evidence or an explained N/A:", file=sys.stderr)
        for name in empty:
            print(f"  - {name}", file=sys.stderr)
        return 1

    lowered = body.lower()
    marker_missing = [marker for marker in REQUIRED_MARKERS if marker not in lowered]
    if marker_missing:
        return fail("missing falsifiability marker(s): " + ", ".join(marker_missing))

    if not draft:
        incomplete = re.findall(r"(?m)^\s*-\s*\[\s\]\s+.+$", parsed[normalize_heading("Completion gates")])
        if incomplete:
            print("engineering evidence: ready-for-review material PR has unchecked completion gates:", file=sys.stderr)
            for line in incomplete:
                print(f"  {line.strip()}", file=sys.stderr)
            return 1
        checked = re.findall(r"(?mi)^\s*-\s*\[[xX]\]\s+.+$", parsed[normalize_heading("Completion gates")])
        if len(checked) < 7:
            return fail("ready-for-review material PR must explicitly attest the completion gates")

    print(
        f"engineering evidence: complete dossier for {len(material)} material path(s); "
        f"draft={str(draft).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
