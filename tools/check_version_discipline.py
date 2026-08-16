#!/usr/bin/env python3
from __future__ import annotations

"""Enforce that material CMPCT work is versioned *and* leaves durable performance evidence."""

import argparse
import json
from pathlib import Path
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
    "docs/PERFORMANCE_RELEASE_GATE.md",
}


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


def matching_benchmark_records(changed: list[str], version_text: str) -> list[str]:
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
        if str(data.get("project_version") or "") == version_text:
            matches.append(rel)
    return matches


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
    # Footnote: release notes and benchmark records prove/describe a milestone; they do not themselves
    # recursively demand another version. The underlying code/site/tool change already triggered it.
    material = [
        p for p in material
        if not p.startswith("docs/releases/") and not p.startswith("benchmarks/history/")
    ]
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

    benchmark_records = matching_benchmark_records(changed, version_text)
    if not benchmark_records:
        print(
            f"material CMPCT version {version_text} requires a fresh changed JSON record under "
            "benchmarks/history/ with project_version set to this version",
            file=sys.stderr,
        )
        print("Run the release performance gate, validate it, then commit the accepted candidate record.", file=sys.stderr)
        return 1

    print(
        f"version discipline: {'.'.join(map(str, old))} -> {version_text}; "
        f"{len(material)} material path(s); benchmark={benchmark_records[0]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
