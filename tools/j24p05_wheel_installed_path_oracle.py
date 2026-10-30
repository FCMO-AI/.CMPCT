#!/usr/bin/env python3
"""J24P05 research-only necessary installed-path identity oracle.

This deliberately does NOT claim complete APFS equivalence, valid distribution
signature, secure installer behavior, or sufficiency for wheel publishing.
It compares raw ZIP identity with cross-platform candidate installed names.
"""
from __future__ import annotations

import json
import posixpath
import sys
import unicodedata
from pathlib import Path, PureWindowsPath
import zipfile


def inspect_names(names: list[str]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    posix_seen: dict[str, str] = {}
    portable_seen: dict[str, str] = {}
    for raw in names:
        if not isinstance(raw, str) or not raw or "\x00" in raw:
            errors.append({"member": str(raw), "kind": "invalid-member-name"})
            continue
        if raw.startswith("/") or "\\" in raw or PureWindowsPath(raw).drive:
            errors.append({"member": raw, "kind": "nonportable-absolute-or-separator"})
            continue
        parts = raw.split("/")
        if any(part in ("", ".", "..") for part in parts):
            errors.append({"member": raw, "kind": "noncanonical-path-component"})
        canonical = posixpath.normpath(raw)
        other = posix_seen.get(canonical)
        if other is not None:
            errors.append({"member": raw, "kind": "posix-installed-path-collision", "with": other})
        else:
            posix_seen[canonical] = raw
        # Necessary conservative approximation for commonly case-insensitive
        # macOS installations. Not a proof of APFS's complete comparison rules.
        portable = unicodedata.normalize("NFD", canonical).casefold()
        other = portable_seen.get(portable)
        if other is not None:
            errors.append({"member": raw, "kind": "nfd-casefold-collision", "with": other})
        else:
            portable_seen[portable] = raw
    return errors


def inspect_wheel(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as z:
        return inspect_names(z.namelist())


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: j24p05_wheel_installed_path_oracle.py WHEEL", file=sys.stderr)
        return 64
    path = Path(argv[1])
    errors = inspect_wheel(path)
    print(json.dumps({"wheel": path.name, "conservative_reject": bool(errors),
                      "errors": errors}, indent=2, sort_keys=True))
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
