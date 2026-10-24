"""Regress exact-head desktop-package custody without unlocking historical v0.30 evidence.

These tests deliberately exercise the real prospective candidate fingerprint CLI.
The 18-job hosted package matrix remains the authority for platform/wheel claims.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/installed-native-package.yml"
FINGERPRINT = ROOT / "tools/check_v031_candidate_fingerprint.py"


def _head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def test_desktop_evidence_routes_to_prospective_source_not_historical_release_lock() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'python tools/check_v031_candidate_fingerprint.py --output' in text
    assert 'experiments.entropygraph_v030_release_lock_strict --print-fingerprint' not in text
    assert "cmpct-v031-desktop-package-evidence-v1" in text
    assert "cmpct-v031-candidate-source-receipt-v1" in text
    assert 'EVIDENCE_HEAD: ${{ github.event.pull_request.head.sha || github.sha }}' in text
    assert "data.get('source_sha') == os.environ['EVIDENCE_HEAD']" in text
    assert "p.name==f'installed-native-{os_name}-{expected_head}'" in text
    # Never make aggregate evidence green by dropping the original smoke/ABI checks.
    for assertion in (
        "s['representative_archive_create_read_extract'] is True",
        "s['shipping_python_no_ambient_zstd'] is True",
        "s['python_zstandard_absent'] is True",
        "s['dict_vector_bytes']==104",
        "'-cp310.cp311.cp312.cp313.cp314-none-' in wheel.name",
    ):
        assert assertion in text


def test_prospective_receipt_from_authentic_source_and_exact_head(tmp_path: Path) -> None:
    head = _head()
    output = tmp_path / "candidate-source.json"
    env = dict(os.environ, EVIDENCE_HEAD=head)
    result = subprocess.run(
        [sys.executable, str(FINGERPRINT), "--output", str(output)],
        cwd=ROOT, env=env, text=True, capture_output=True, check=True,
    )
    result_json = json.loads(result.stdout)
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["schema"] == "cmpct-v031-candidate-source-receipt-v1"
    assert receipt["source_sha"] == head
    assert receipt["fingerprint"] == result_json["fingerprint"]
    assert len(receipt["fingerprint"]) == 64
    assert ".github/workflows/installed-native-package.yml" in receipt["paths"]
    assert "tools/check_v031_candidate_fingerprint.py" in receipt["paths"]
    assert "docs/V030_RELEASE_LOCK.json" in receipt["paths"]
    assert receipt["historical_lock_unchanged_by_this_tool"] is True


def test_foreign_head_must_not_receive_candidate_receipt(tmp_path: Path) -> None:
    wrong = "0" * 40 if _head() != "0" * 40 else "1" * 40
    output = tmp_path / "foreign-source.json"
    env = dict(os.environ, EVIDENCE_HEAD=wrong)
    result = subprocess.run(
        [sys.executable, str(FINGERPRINT), "--output", str(output)],
        cwd=ROOT, env=env, text=True, capture_output=True,
    )
    assert result.returncode != 0
    assert "candidate evidence SHA mismatch" in (result.stdout + result.stderr)
    assert not output.exists()
