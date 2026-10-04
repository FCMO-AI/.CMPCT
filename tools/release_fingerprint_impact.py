from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def fingerprint_pathspecs(manifest: dict[str, Any]) -> list[str]:
    """Translate release-lock fingerprint globs into Git glob pathspecs."""
    rows: list[str] = []
    for pattern in manifest["fingerprint_globs"]:
        if not isinstance(pattern, str) or not pattern:
            raise ValueError("invalid fingerprint glob")
        rows.append(f":(glob){pattern}")
    return rows


def changed_fingerprint_paths(
    manifest: dict[str, Any],
    base_ref: str,
    head_ref: str = "HEAD",
    *,
    repo_root: Path,
) -> list[str]:
    """Return accumulated base->head changes intersecting release identity.

    The release lock remains the path authority; this helper deliberately does
    not maintain a second workflow regex. Git's tree diff catches additions,
    edits, deletions, and moves across the fingerprint boundary.
    """
    if not base_ref or not head_ref:
        raise ValueError("base/head refs must be non-empty")
    proc = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root.resolve()),
            "diff",
            "--name-only",
            "-z",
            base_ref,
            head_ref,
            "--",
            *fingerprint_pathspecs(manifest),
        ],
        check=False,
        capture_output=True,
    )
    if proc.returncode:
        detail = proc.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"cannot compare release fingerprint surface: {detail}")
    return sorted({row for row in proc.stdout.decode("utf-8").split("\0") if row})
