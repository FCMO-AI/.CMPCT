#!/usr/bin/env python3
from __future__ import annotations

"""Fail CI when tracked CMPCT text contains forbidden private provenance.

Intentional legal attribution in the repository's dedicated copyright/licensing files is handled as a
narrow exact-line exception. This keeps the disclosure guard fail-closed for operational provenance
without making it contradict the canonical legal record merged from ``main``.
"""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

# Footnote: tokens are assembled so this guard does not contain the forbidden literal strings it is
# protecting against. The public repository-owner namespace is intentionally allowed; this rule
# targets unrelated private operational provenance, not CMPCT's public ownership metadata.
RESTRICTED = {
    "private project marker": "Her" + "mes",
    "private agent marker": "Jar" + "vis",
    "private person marker": "Jav" + "ier",
    "private person marker (ascii)": "Mat" + "ias",
    "private person marker (accented)": "Mat" + "ías",
    "private messaging-system marker": "Tele" + "gram",
    "private workspace marker": "Obsi" + "dian",
    "private analysis-system marker": "Levia" + "than",
    "private voice-system marker": "Voice" + "Script",
    "private vision-system marker": "Roz " + "Vision",
    "private model-plan marker": "Claude " + "Max",
    "private model marker": "Cor" + "ax",
    "private model marker 2": "Orn" + "ith",
    "private model-plan marker 2": "D" + "Spark",
    "private design-source provenance": "FCMO " + "identity",
    "private artifact-style prefix": "FCMO" + "_",
    "private benchmark scratch marker": "fcmo" + "_bench",
    "container scratch/private upload path": "/mnt/" + "data/",
}

# Legal attribution is not operational provenance. Keep this deliberately exact: adding a new personal
# reference anywhere, including elsewhere in these files, still fails the guard until reviewed.
_LEGAL_HOLDER = "Mat" + "ías Peña Szőke"
_LEGAL_FOUNDER = "Jav" + "ier Castellanos Peña"
LEGAL_PUBLIC_LINES = {
    Path("COPYRIGHT.md"): {
        f"`Copyright (c) 2026 {_LEGAL_HOLDER} and contributors`",
        (
            f"- Listing {_LEGAL_FOUNDER} as Founder of FCMO Group does not by itself make him an author "
            "or copyright holder of FCMO AI work."
        ),
    },
    Path("LICENSING.md"): {
        f"`Copyright (c) 2026 {_LEGAL_HOLDER} and contributors`",
    },
}

TEXT_SUFFIXES = {
    "",
    ".md",
    ".txt",
    ".json",
    ".py",
    ".rs",
    ".toml",
    ".lock",
    ".html",
    ".css",
    ".js",
    ".mjs",
    ".ts",
    ".yml",
    ".yaml",
    ".xml",
    ".sh",
    ".c",
    ".h",
    ".hpp",
}


def tracked_files():
    """Yield text-like files from Git's tracked tree rather than a hand-maintained allowlist."""
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    for item in raw.decode("utf-8").split("\0"):
        if not item:
            continue
        path = ROOT / item
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def _is_reviewed_legal_line(rel: Path, line: str) -> bool:
    """Return true only for an exact, deliberately reviewed public legal-attribution line."""
    return line.strip() in LEGAL_PUBLIC_LINES.get(rel, set())


def main() -> int:
    findings: list[str] = []
    checked = 0
    for path in tracked_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        checked += 1
        folded = text.casefold()
        rel = path.relative_to(ROOT)
        for label, token in RESTRICTED.items():
            if token.casefold() not in folded:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                if token.casefold() not in line.casefold():
                    continue
                if _is_reviewed_legal_line(rel, line):
                    continue
                findings.append(f"{rel}:{lineno}: {label}: {line.strip()}")

    if findings:
        print("CMPCT disclosure guard rejected private operational provenance:", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        print("Generalize/remove the provenance before publishing or merging.", file=sys.stderr)
        return 1

    print(f"CMPCT disclosure guard: clean ({checked} tracked text files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
