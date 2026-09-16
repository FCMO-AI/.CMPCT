from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_GENERATOR = ROOT / "tests" / "generate_v030_canonical_goldens.py"
CANONICAL_GOLDEN = ROOT / "tests" / "conformance" / "v030-r25-canonical.json"
IMPLICIT_GENERATOR = ROOT / "tests" / "generate_v030_implicit_goldens.py"
IMPLICIT_GOLDEN = ROOT / "tests" / "conformance" / "v030-r25-implicit-v4.json"


def _assert_independent_golden_is_reproducible(generator: Path, golden: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(generator), "--output", str(golden), "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        f"builder-independent canonical r25 golden drifted: {golden}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )


def test_independent_canonical_r25_golden_is_exactly_reproducible() -> None:
    """Keep explicit-filesystem r25 authority anchored to its independent byte oracle."""

    _assert_independent_golden_is_reproducible(CANONICAL_GENERATOR, CANONICAL_GOLDEN)


def test_independent_implicit_v4_golden_is_exactly_reproducible() -> None:
    """Keep the publishable implicit-v4 filesystem control anchored independently too.

    Both generators deliberately avoid the CMPCT Builder and v0.30 writers. Canonical authority must
    therefore reject stale, malformed, or hand-edited acceptance bytes for every r25 filesystem-control
    shape the release-facing selector may publish, rather than delegating this custody invariant to
    side/native workflows.
    """

    _assert_independent_golden_is_reproducible(IMPLICIT_GENERATOR, IMPLICIT_GOLDEN)
