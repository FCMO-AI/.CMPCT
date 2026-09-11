from __future__ import annotations

"""Launch the CMPCT1 product worker from the sealed candidate checkout.

The certification authority belongs to the current harness, but the scientific runtime
must come from the frozen contender checkout.  The Genesis adapter executes this launcher
with cwd set to that contender checkout.  We therefore import the product worker from cwd,
prove that its module file is physically inside that checkout, point only its certification
authority at the harness-owned boundary, and delegate unchanged worker argument handling.

This layer performs no measurement itself and does not import ``experiments.one``.
"""

import importlib
import os
from pathlib import Path
import subprocess
import sys

HARNESS_ROOT = Path(__file__).resolve().parents[2]
HARNESS_BOUNDARY = HARNESS_ROOT / "benchmarks" / "one" / "genesis_one_candidate_boundary_v1.json"
WORKER_MODULE = "benchmarks.one.one_genesis_cmpct1_product_worker"
# Seal every repository-local Python surface that can participate in loading the worker
# and ONE runtime, not just the two leaf files certified separately in the boundary.
SEALED_RUNTIME_PATHS = (
    "experiments/one",
    "benchmarks/one",
)
FORBIDDEN_IGNORED_RUNTIME_SUFFIXES = frozenset((".so", ".dylib", ".dll", ".pyd"))


def _assert_runtime_worktree_sealed(root: Path) -> None:
    """Reject working-tree drift capable of changing the frozen scientific runtime.

    Commit/tree/blob identity alone is insufficient because Python executes working-tree
    bytes.  A checkout can remain at the authorized HEAD while a tracked runtime file is
    edited/deleted, or a new importable source file is added.  Ordinary tracked/untracked
    drift is rejected across both the ONE package and the worker package.

    Git-ignored bytecode/output caches are permitted because fresh-process phases can create
    them.  Ignored native-library artifacts are *not* permitted: Python/ctypes can load such
    files ahead of committed source while Git still reports the checkout as clean.
    """
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *SEALED_RUNTIME_PATHS,
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    if result.stdout.strip():
        raise RuntimeError("CMPCT1 frozen worker launcher runtime worktree differs from sealed Git state")

    ignored = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "--",
            *SEALED_RUNTIME_PATHS,
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    dangerous = [
        line
        for line in ignored.stdout.splitlines()
        if Path(line).suffix.lower() in FORBIDDEN_IGNORED_RUNTIME_SUFFIXES
    ]
    if dangerous:
        raise RuntimeError(
            "CMPCT1 frozen worker launcher found ignored native runtime artifacts: "
            + ", ".join(sorted(dangerous)[:8])
        )


def _sealed_candidate_root() -> Path:
    root = Path.cwd().resolve()
    if not (root / ".git").exists() and not subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
        text=True,
        capture_output=True,
    ).stdout.strip() == "true":
        raise RuntimeError("CMPCT1 frozen worker launcher cwd is not a Git checkout")
    expected = os.environ.get("CMPCT_GENESIS_SOURCE_SHA", "")
    observed = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if len(expected) != 40 or observed != expected:
        raise RuntimeError("CMPCT1 frozen worker launcher checkout differs from executor-sealed source")
    _assert_runtime_worktree_sealed(root)
    return root


def _load_candidate_worker():
    candidate = _sealed_candidate_root()
    # Remove any harness copy that may have been imported by surrounding orchestration.
    sys.modules.pop(WORKER_MODULE, None)
    candidate_text = str(candidate)
    if candidate_text in sys.path:
        sys.path.remove(candidate_text)
    sys.path.insert(0, candidate_text)
    importlib.invalidate_caches()
    worker = importlib.import_module(WORKER_MODULE)
    module_path = Path(worker.__file__).resolve()
    try:
        module_path.relative_to(candidate)
    except ValueError as exc:
        raise RuntimeError("CMPCT1 product worker was not imported from sealed candidate checkout") from exc
    worker.CANDIDATE_BOUNDARY_MANIFEST = HARNESS_BOUNDARY
    return worker


def main() -> None:
    if os.environ.get("CMPCT_GENESIS_REAL_GATE_AUTHORIZED") != "1":
        raise RuntimeError("CMPCT1 frozen worker launcher requires explicit real-gate authorization")
    worker = _load_candidate_worker()
    worker.main()


if __name__ == "__main__":
    main()
