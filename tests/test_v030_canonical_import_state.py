from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest


@pytest.mark.xfail(
    strict=True,
    reason="T03 P1: canonical-final still rewrites the historical Geometry delimiter inverse at import time",
)
def test_canonical_import_does_not_mutate_historical_delimiter_owner() -> None:
    """Product import must not rewrite an already-imported research module's semantic owner.

    Run in a fresh interpreter so this test is independent of pytest collection/import order.  The current
    authority is expected to fail until T03 P1 removes the process-wide assignment.  strict=True makes an
    unreviewed XPASS fail rather than silently converting the debt into release credit.
    """
    script = textwrap.dedent(
        """
        from experiments import entropygraph_v030_geometry_overlay as overlay
        from experiments import entropygraph_v030_geometry_overlay_g04 as g04

        overlay_before = overlay.delimiter_inverse
        g04_before = g04.O.delimiter_inverse
        assert g04_before is overlay_before

        from experiments import entropygraph_v030_canonical_final as canonical  # noqa: F401

        assert overlay.delimiter_inverse is overlay_before
        assert g04.O.delimiter_inverse is g04_before
        """
    )
    proc = subprocess.run(
        [sys.executable, "-c", script],
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
