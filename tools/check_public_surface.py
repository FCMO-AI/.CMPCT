#!/usr/bin/env python3
from __future__ import annotations

"""Fail CI when release-facing CMPCT files contain known private-provenance markers."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

# Footnote: this intentionally scans the material a future visitor, agent, package consumer or
# website build is expected to read. It is a disclosure tripwire, not a claim that string matching can
# replace human privacy/security review.
PUBLIC_ROOTS = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "LICENSING.md",
    ROOT / "docs",
    ROOT / "site",
    ROOT / "benchmarks" / "history",
    ROOT / "benchmarks" / "universal_bench.py",
]

# Footnote: split a few internal names so this guard does not flag its own implementation if its scan
# scope expands later. The FCMO-AI repository/organization identifier and the provisional CMPCT MIME
# identifier are deliberately *not* banned; this gate targets unrelated/private provenance, not the
# project's public ownership namespace.
RESTRICTED = {
    "private regression corpus identifier": "Her" + "mes",
    "unrelated internal agent identifier": "Jar" + "vis",
    "private person identifier": "Jav" + "ier",
    "private person identifier (ascii)": "Mat" + "ias",
    "private person identifier (accented)": "Mat" + "ías",
    "private design-source provenance": "FCMO " + "identity",
    "container scratch/private upload path": "/mnt/" + "data/",
}

TEXT_SUFFIXES = {
    "",
    ".md",
    ".txt",
    ".json",
    ".py",
    ".html",
    ".css",
    ".js",
    ".mjs",
    ".yml",
    ".yaml",
    ".toml",
    ".xml",
}


def iter_files(path: Path):
    if path.is_file():
        yield path
        return
    if path.is_dir():
        for item in sorted(path.rglob("*")):
            if item.is_file() and item.suffix.lower() in TEXT_SUFFIXES:
                yield item


def main() -> int:
    findings: list[str] = []
    seen: set[Path] = set()
    for root in PUBLIC_ROOTS:
        if not root.exists():
            continue
        for path in iter_files(root):
            if path in seen:
                continue
            seen.add(path)
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for label, token in RESTRICTED.items():
                if token.casefold() not in text.casefold():
                    continue
                rel = path.relative_to(ROOT)
                for lineno, line in enumerate(text.splitlines(), 1):
                    if token.casefold() in line.casefold():
                        findings.append(f"{rel}:{lineno}: {label}: {line.strip()}")

    if findings:
        print("CMPCT public-surface guard rejected private/internal provenance:", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        print("Generalize/remove the provenance or explicitly revise docs/PUBLIC_SURFACE.md.", file=sys.stderr)
        return 1

    print(f"CMPCT public-surface guard: clean ({len(seen)} text files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
