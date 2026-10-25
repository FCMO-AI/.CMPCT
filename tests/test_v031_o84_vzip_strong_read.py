"""Permanent mechanism-level VZIP SHA integrity regression.

Runs the independently source-bound O84 physical CRC32 collision instrument within
normal pytest as well as its stronger clean-installed three-host GitHub court.
The scientific fixture is not evidence of signature/origin authentication.
"""
from __future__ import annotations

import runpy
from pathlib import Path


def test_o84_optin_verified_vzip_rejects_physical_crc32_collision():
    instrument=Path(__file__).resolve().parents[1]/"benchmarks"/"v031_o84_vzip_strong_full_read.py"
    report=runpy.run_path(str(instrument))["main"]()
    assert report["crc32_equal"] is True
    assert report["physical_crc_preserving_tamper_rejected"] is True
    assert report["valid_source_control_retained"] is True
    assert report["decision"]=="OPTIN_SHA_REJECTS_O81_PHYSICAL_COLLISION; FAST_READ_UNCHANGED"
