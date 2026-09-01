from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tests" / "generate_v030_canonical_goldens.py"
GOLDEN = ROOT / "tests" / "conformance" / "v030-r25-canonical.json"


def test_independent_canonical_r25_golden_is_exactly_reproducible() -> None:
    """Keep the release-facing canonical authority anchored to its independent byte oracle.

    The generator deliberately does not import the CMPCT Builder or any v0.30 writer. Running its
    fail-closed ``--check`` mode here makes canonical authority itself reject a stale, malformed, or
    hand-edited fixed vector instead of relying on the separate native-authority lane to notice drift.
    """

    completed = subprocess.run(
        [sys.executable, str(GENERATOR), "--output", str(GOLDEN), "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, (
        "builder-independent canonical r25 golden drifted from its frozen generator:\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
