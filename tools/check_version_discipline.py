#!/usr/bin/env python3
from __future__ import annotations

"""Enforce that material CMPCT work is represented by a new project version."""

import argparse
from pathlib import Path
import re
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[1]
MATERIAL_PREFIXES = (
    "src/", "native/", "integrations/", "benchmarks/", "experiments/", "site/", "tools/"
)
MATERIAL_SINGLETONS = {
    "pyproject.toml", "AGENTS.md", "README.md", "LICENSING.md",
    "docs/FORMAT.md", "docs/HARDENING.md", "docs/NATIVE_CORE.md", "docs/PORTABILITY.md",
}
RELEASE_RE = re.compile(r"^docs/releases/v(\d+\.\d+\.\d+)\.md$")


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-sha", required=True)
    args = ap.parse_args()
    base = args.base_sha
    if not base or set(base) == {"0"}:
        print("version discipline: no comparable base SHA; skipped")
        return 0
    try:
        base_pyproject = subprocess.check_output(
            ["git", "show", f"{base}:pyproject.toml"], cwd=ROOT
        )
        changed = run("git", "diff", "--name-only", f"{base}...HEAD").splitlines()
    except subprocess.CalledProcessError as exc:
        print(f"version discipline: unable to inspect base {base}: {exc}", file=sys.stderr)
        return 2

    material = [p for p in changed if p in MATERIAL_SINGLETONS or p.startswith(MATERIAL_PREFIXES)]
    # Footnote: a release note by itself is evidence of a version, not a reason to demand another
    # version.  Generated history records still count because benchmark/research output is material work.
    material = [p for p in material if not p.startswith("docs/releases/")]
    if not material:
        print("version discipline: no material CMPCT paths changed")
        return 0

    old = version_from_bytes(base_pyproject)
    new = current_version()
    if new <= old:
        print(
            f"material CMPCT change reuses project version {'.'.join(map(str, old))}; "
            "bump [project].version in pyproject.toml",
            file=sys.stderr,
        )
        for path in material:
            print(f"  - {path}", file=sys.stderr)
        return 1

    version_text = ".".join(map(str, new))
    expected_release = f"docs/releases/v{version_text}.md"
    if expected_release not in changed or not (ROOT / expected_release).is_file():
        print(f"material CMPCT change requires new release note {expected_release}", file=sys.stderr)
        return 1

    release_text = (ROOT / expected_release).read_text(encoding="utf-8")
    if f"Project version: **{version_text}**" not in release_text:
        print(f"{expected_release} must explicitly declare project version {version_text}", file=sys.stderr)
        return 1

    print(
        f"version discipline: {'.'.join(map(str, old))} -> {version_text}; "
        f"{len(material)} material path(s) accounted for"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
