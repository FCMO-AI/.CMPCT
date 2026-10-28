"""J24K07b: held-out signed canonical Deflate mode0 suffix-coordinate test.

Deliberately reuses the frozen J24K07 mutation/oracle, but substitutes the
third independently archived revision-24 representation. No test fixture,
original J24K07 accepted evidence, or product source is modified.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from test_j24k07_signed_nonmode2_suffix import (
    test_reauthenticated_nonmode2_skipped_stream_suffix_coordinates as oracle,
)

CANONICAL = ("canonical", "v24-virtual-zip-deflate-mode0.json", zipfile.ZIP_DEFLATED, 0)


@pytest.mark.parametrize("delta", (-1, 1), ids=("minus1", "plus1"))
def test_signed_canonical_deflate_skipped_stream_is_wrong_coordinate(
    tmp_path: Path, delta: int, capsys
):
    oracle(tmp_path, CANONICAL, delta)
    captured = capsys.readouterr().out
    rows = [
        json.loads(line.split("J24K07_RECEIPT=", 1)[1])
        for line in captured.splitlines()
        if "J24K07_RECEIPT=" in line
    ]
    assert len(rows) == 1
    receipt = rows[0]
    assert receipt["case"] == "canonical"
    assert receipt["delta"] == delta
    assert receipt["preflight"] == "REJECT"
    assert receipt["full_read"] == "REJECT" and receipt["verify"] == "REJECT"
    assert receipt["wrong_byte_count"] >= 1
    assert receipt["rejected_probes"] == 0 and receipt["truncated_probes"] == 0
    print("J24K07B_RECEIPT=" + json.dumps(receipt, sort_keys=True), flush=True)
