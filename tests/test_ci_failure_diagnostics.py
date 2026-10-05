"""Exercise diagnostic steps with a real failed gate and absent/invalid receipts."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/zip-parity.yml"


def _script(name: str) -> str:
    step = WORKFLOW.read_text().split(f"      - name: {name}\n", 1)[1]
    lines = step.split("        run: |\n", 1)[1].splitlines()
    body = []
    for line in lines:
        if line and not line.startswith("          "):
            break
        body.append(line)
    return textwrap.dedent("\n".join(body)).replace("python ", f"'{sys.executable}' ")


def _run(script: str, root: Path):
    return subprocess.run(
        ["bash", "-e", "-c", script], cwd=root, capture_output=True, text=True,
        env={**os.environ, "GITHUB_STEP_SUMMARY": str(root / "summary.md")},
    )


def test_failed_correctness_gate_retains_stream_and_failure(tmp_path):
    # Replace only the expensive workload. Bash, pipefail and the retained path are real.
    script = _script("Correctness gate").replace(
        "-m pytest -q", "-c 'import sys; print(\"intentional failure\", file=sys.stderr); sys.exit(23)'"
    )
    result = _run(script, tmp_path)
    assert result.returncode == 23
    assert (tmp_path / "benchmark-artifacts/correctness.txt").read_text() == "intentional failure\n"


def test_summary_without_benchmarks_does_not_add_a_failure_or_receipt(tmp_path):
    result = _run(_script("Publish performance summary"), tmp_path)
    assert result.returncode == 0, result.stderr
    assert "No performance claim" in (tmp_path / "summary.md").read_text()
    assert not (tmp_path / "benchmark-artifacts/PERFORMANCE_GATE.md").exists()


def _records(root: Path):
    directory = root / "benchmark-artifacts"
    directory.mkdir()
    for name, size in (("base", 100), ("candidate", 110)):
        data = {"corpora": {"sample": {"library": {"cmpct": {
            "bytes": size, "create_s_median": 1, "extract_s_median": 1,
        }}}}}
        (directory / f"{name}.json").write_text(json.dumps(data))
    return directory


def test_summary_keeps_real_comparison_when_measurements_exist(tmp_path):
    directory = _records(tmp_path)
    result = _run(_script("Publish performance summary"), tmp_path)
    assert result.returncode == 0, result.stderr
    assert "+10.00%" in (directory / "PERFORMANCE_GATE.md").read_text()


def test_summary_still_rejects_corrupt_available_evidence(tmp_path):
    directory = _records(tmp_path)
    (directory / "candidate.json").write_text("not JSON")
    result = _run(_script("Publish performance summary"), tmp_path)
    assert result.returncode != 0
    assert not (directory / "PERFORMANCE_GATE.md").exists()
