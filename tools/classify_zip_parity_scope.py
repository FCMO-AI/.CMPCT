"""Fail-closed source-impact admission for the canonical r24 ZIP parity gate.

This classifies *candidate-tree changes*, not benchmark evidence. The comparator,
same-input corpus, and exact-head performance receipt remain independently binding.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys

ZERO_SHA = "0" * 40
PREFIXES = (b"src/", b"native/", b"benchmarks/", b"tests/")
ROOT_FILES = {
    b"pyproject.toml",
    b"tools/check_performance_regression.py",
    b"tools/aggregate_parity_runs.py",
    b"tools/materialize_performance_base_native.py",
    b"tools/classify_zip_parity_scope.py",
    b"tools/check_ci_topology.py",
    b".github/workflows/zip-parity.yml",
}


@dataclass(frozen=True)
class Decision:
    run: bool
    basis: str
    affected: tuple[bytes, ...] = ()


def _git(*args: str, cwd: str | os.PathLike[str] = ".") -> bytes:
    return subprocess.run(
        ["git", *args], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=True,
    ).stdout


def is_performance_input(path: bytes) -> bool:
    """Byte-path matching avoids Git's quoting/newline and rename reporting traps."""
    return path.startswith(PREFIXES) or path in ROOT_FILES


def classify(
    event: str, head: str, base: str | None, *, cwd: str | os.PathLike[str] = ".",
) -> Decision:
    """Classify immutable event source; missing history **runs**, never silently skips.

    PR events: merge-base(base, head)..head. Push events: before..after.
    Git rename detection is deliberately disabled so deleting a source path
    via rename into docs cannot hide the source-side change.
    """
    # An incorrect checkout is not a valid comparison; running a benchmark on
    # different source is worse than an expensive fail-closed admission.
    actual = _git("rev-parse", "HEAD", cwd=cwd).decode("ascii").strip()
    if actual != head:
        raise ValueError(f"checkout HEAD mismatch: {actual} != {head}")
    if event == "workflow_dispatch":
        return Decision(True, "manual-dispatch")
    if event not in {"pull_request", "push"}:
        return Decision(True, "unknown-event-fail-closed")
    if not base or base == ZERO_SHA:
        return Decision(True, "missing-base-fail-closed")

    try:
        _git("cat-file", "-e", f"{base}^{{commit}}", cwd=cwd)
        if event == "pull_request":
            # Criss-cross merges can produce multiple incomparable merge bases.
            # Choosing whichever one Git returns first may hide a material
            # source delta. Such a history cannot safely authorize SKIP.
            merge_bases = _git("merge-base", "--all", base, head, cwd=cwd).decode("ascii").splitlines()
            if len(merge_bases) != 1:
                return Decision(True, "ambiguous-merge-base-fail-closed")
            origin = merge_bases[0]
            basis = "pr-merge-base"
        else:
            origin = base
            basis = "push-before-after"
        # --no-renames exposes both deleted and added sides of moves.
        changed = _git(
            "diff", "--no-renames", "--name-only", "-z", origin, head, cwd=cwd,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        print(f"scope history unavailable, RUN fail closed: {exc}", file=sys.stderr)
        return Decision(True, "history-unavailable-fail-closed")

    paths = tuple(part for part in changed.split(b"\0") if part)
    return Decision(any(is_performance_input(part) for part in paths), basis, paths)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--base")
    args = parser.parse_args(argv)
    decision = classify(args.event, args.head, args.base)
    print(f"run_performance={str(decision.run).lower()}")
    print(f"scope_basis={decision.basis}")
    impacted = [os.fsdecode(p) for p in decision.affected if is_performance_input(p)]
    print(
        f"ZIP-parity scope: head={args.head} basis={decision.basis} "
        f"run={decision.run} changed={len(decision.affected)} "
        f"relevant={impacted!r}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
