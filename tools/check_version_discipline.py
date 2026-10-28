#!/usr/bin/env python3
from __future__ import annotations

"""Enforce scarce core versions plus lightweight x.x.a surface revisions.

Footnote: numeric project versions are deliberately expensive. A nicer site, clearer handoff, workflow
cleanup, or repository polish must not consume the same release namespace as a material improvement to
CMPCT's archive/engine behavior.
"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
SURFACE_FILE = ROOT / "SURFACE_REVISION"

# These paths can contain actual archive/engine capability. Changing one does not automatically force a
# release: development may land without a version. But a numeric version bump is invalid unless at least
# one of these paths participates in the candidate.
CORE_PREFIXES = ("src/", "native/", "integrations/")

# Presentation, handoff and repository-operability work uses the alphabetic surface track when no
# numeric core release is being cut in the same change. Multiple commits may belong to one coherent
# surface revision; the revision itself advances once per presentation milestone, not once per commit.
SURFACE_PREFIXES = ("site/", ".github/workflows/")
SURFACE_SINGLETONS = {
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
    "LICENSING.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    "docs/AGI_ENGINEERING_STANDARD.md",
    "docs/PERFORMANCE_RELEASE_GATE.md",
    "docs/CURRENT_STATE.md",
    "docs/HISTORY.md",
    "docs/RESEARCH_LOG.md",
    "docs/ENTROPYGRAPH.md",
    "docs/BENCHMARKS.md",
    "docs/PUBLIC_SURFACE.md",
    "docs/ROADMAP.md",
    "docs/releases/README.md",
    "site/README.md",
    "tools/check_version_discipline.py",
}
EVIDENCE_PREFIXES = ("docs/releases/v", "benchmarks/history/")


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def version_from_bytes(raw: bytes) -> tuple[int, int, int]:
    value = tomllib.loads(raw.decode("utf-8"))["project"]["version"]
    parts = value.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"project.version must be numeric MAJOR.MINOR.PATCH, got {value!r}")
    return tuple(map(int, parts))  # type: ignore[return-value]


def current_version() -> tuple[int, int, int]:
    return version_from_bytes((ROOT / "pyproject.toml").read_bytes())


def version_text(version: tuple[int, int, int]) -> str:
    return ".".join(map(str, version))


def parse_surface(raw: str) -> tuple[int, int, str]:
    value = raw.strip()
    match = re.fullmatch(r"(\d+)\.(\d+)\.([a-z]+)", value)
    if not match:
        raise ValueError(f"SURFACE_REVISION must use x.x.a lettering, got {value!r}")
    major, minor, suffix = match.groups()
    return int(major), int(minor), suffix


def alpha_value(value: str) -> int:
    total = 0
    for char in value:
        total = total * 26 + (ord(char) - ord("a") + 1)
    return total


def read_base_surface(base: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "show", f"{base}:SURFACE_REVISION"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return None


def matching_benchmark_records(changed: list[str], release_version: str) -> list[str]:
    matches: list[str] = []
    for rel in changed:
        if not (rel.startswith("benchmarks/history/") and rel.endswith(".json")):
            continue
        path = ROOT / rel
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(data.get("project_version") or "") == release_version:
            matches.append(rel)
    return matches


def is_surface_path(path: str) -> bool:
    if path == "SURFACE_REVISION" or path.startswith(EVIDENCE_PREFIXES):
        return False
    return path in SURFACE_SINGLETONS or path.startswith(SURFACE_PREFIXES)


def validate_surface_revision(
    *, base: str, old_version: tuple[int, int, int], new_version: tuple[int, int, int], changed: list[str],
    core_release: bool, surface_paths: list[str]
) -> tuple[bool, str]:
    if not SURFACE_FILE.is_file():
        return False, "SURFACE_REVISION is required"

    current_raw = SURFACE_FILE.read_text(encoding="utf-8").strip()
    try:
        current_major, current_minor, current_suffix = parse_surface(current_raw)
    except ValueError as exc:
        return False, str(exc)

    expected_line = new_version[:2]
    if (current_major, current_minor) != expected_line:
        return False, (
            f"surface revision {current_raw} must stay on current core line "
            f"{expected_line[0]}.{expected_line[1]}.x"
        )

    base_surface = read_base_surface(base)
    surface_file_changed = "SURFACE_REVISION" in changed

    if core_release:
        expected = f"{new_version[0]}.{new_version[1]}.a"
        if current_raw != expected:
            return False, f"new core line must reset surface revision to {expected}"
        if not surface_file_changed:
            return False, "new core line must update SURFACE_REVISION"
        return True, current_raw

    if not surface_paths:
        if surface_file_changed:
            return False, "SURFACE_REVISION changed without presentation/repository surface work"
        return True, current_raw

    if not surface_file_changed:
        # Footnote: direct-to-main maintenance can span several commits. Requiring one letter per commit
        # would recreate the version inflation this policy is meant to stop, so unchanged surface state
        # is valid inside the same coherent presentation milestone.
        return True, current_raw

    if base_surface is None:
        expected = f"{old_version[0]}.{old_version[1]}.a"
        if current_raw != expected:
            return False, f"first surface revision on this line must be {expected}"
        return True, current_raw

    try:
        base_major, base_minor, base_suffix = parse_surface(base_surface)
    except ValueError as exc:
        return False, f"base {exc}"
    if (base_major, base_minor) != (current_major, current_minor):
        return False, "surface revision line changed without a numeric core release"
    if alpha_value(current_suffix) != alpha_value(base_suffix) + 1:
        return False, f"surface revision must advance exactly once: {base_surface} -> next alphabetic revision"
    return True, current_raw


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-sha", required=True)
    args = ap.parse_args()
    base = args.base_sha
    if not base or set(base) == {"0"}:
        print("version discipline: no comparable base SHA; skipped")
        return 0

    try:
        base_pyproject = subprocess.check_output(["git", "show", f"{base}:pyproject.toml"], cwd=ROOT)
        changed = run("git", "diff", "--name-only", f"{base}...HEAD").splitlines()
    except subprocess.CalledProcessError as exc:
        print(f"version discipline: unable to inspect base {base}: {exc}", file=sys.stderr)
        return 2

    old = version_from_bytes(base_pyproject)
    new = current_version()
    if new < old:
        print(f"project version moved backwards: {version_text(old)} -> {version_text(new)}", file=sys.stderr)
        return 1

    core_paths = [path for path in changed if path.startswith(CORE_PREFIXES)]
    surface_paths = [path for path in changed if is_surface_path(path)]
    core_release = new != old

    if core_release:
        # Footnote: after the legacy 0.27.1 handoff patch, patch-number churn is retired. Material core
        # releases advance the MAJOR.MINOR line and reserve PATCH=0 for packaging compatibility.
        if new[2] != 0 or new[:2] <= old[:2]:
            print(
                f"numeric core release must advance the MAJOR.MINOR line with PATCH=0; got "
                f"{version_text(old)} -> {version_text(new)}",
                file=sys.stderr,
            )
            return 1
        if not core_paths:
            print(
                "numeric core version changed without an archive/engine path; site/docs/repo polish "
                "belongs on SURFACE_REVISION (x.x.a) instead",
                file=sys.stderr,
            )
            return 1

        release_version = version_text(new)
        expected_release = f"docs/releases/v{release_version}.md"
        if expected_release not in changed or not (ROOT / expected_release).is_file():
            print(f"core release requires new release note {expected_release}", file=sys.stderr)
            return 1
        release_text = (ROOT / expected_release).read_text(encoding="utf-8")
        if f"Project version: **{release_version}**" not in release_text:
            print(f"{expected_release} must explicitly declare project version {release_version}", file=sys.stderr)
            return 1
        benchmark_records = matching_benchmark_records(changed, release_version)
        if not benchmark_records:
            print(
                f"core release {release_version} requires a fresh JSON record under benchmarks/history/ "
                "with project_version set to this version",
                file=sys.stderr,
            )
            return 1
    else:
        benchmark_records = []

    surface_ok, surface = validate_surface_revision(
        base=base,
        old_version=old,
        new_version=new,
        changed=changed,
        core_release=core_release,
        surface_paths=surface_paths,
    )
    if not surface_ok:
        print(f"version discipline: {surface}", file=sys.stderr)
        if surface_paths:
            for path in surface_paths:
                print(f"  - {path}", file=sys.stderr)
        return 1

    if core_release:
        print(
            f"version discipline: core {version_text(old)} -> {version_text(new)}; "
            f"surface={surface}; benchmark={benchmark_records[0]}"
        )
    elif surface_paths:
        print(
            f"version discipline: core stays {version_text(new)}; surface={surface}; "
            f"{len(surface_paths)} presentation/repository path(s)"
        )
    else:
        print(f"version discipline: core stays {version_text(new)}; surface stays {surface}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
