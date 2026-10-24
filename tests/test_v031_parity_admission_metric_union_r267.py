"""Joint non-production court for two independent parity fail-open boundaries.

Unlike individual owner tests, this exercises the real source-range admission
classifier *and* the actual release comparator on one continuous decision path.
No measured benchmark is simulated as a product result.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # Required by the real classifier's dataclass.
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=repo, stderr=subprocess.PIPE
    ).decode("utf-8").strip()


def _report() -> dict:
    metric = {"bytes": 1000, "create_s_median": 0.1, "extract_s_median": 0.07}
    return {
        "schema": "cmpct-zip-parity-v1",
        "corpora": {"shared": {
            "logical_bytes": 1000,
            "library": {"cmpct": copy.deepcopy(metric)},
            "cli": {"cmpct": copy.deepcopy(metric)},
        }},
    }


def test_documentation_last_cannot_skip_invalid_or_regressed_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    classifier = _load(
        "cmpct_r267_real_scope",
        ROOT / "tools" / "classify_zip_parity_scope.py",
    )
    comparator = _load(
        "cmpct_r267_real_parity",
        ROOT / "tools" / "check_performance_regression.py",
    )
    repo = tmp_path / "git"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "CMPCT Parity Union Court")
    _git(repo, "config", "user.email", "court@example.invalid")
    (repo / "README.md").write_text("baseline\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    base_sha = _git(repo, "rev-parse", "HEAD")

    # The legitimate regression is in the first commit; documentation is last.
    (repo / "src" / "cmpct").mkdir(parents=True)
    (repo / "src" / "cmpct" / "reader.py").write_text(
        "changed product source\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "material product change")
    (repo / "README.md").write_text("documentation-only final commit\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "docs last")
    head_sha = _git(repo, "rev-parse", "HEAD")
    decision = classifier.classify("pull_request", head_sha, base_sha, cwd=repo)
    assert decision.run is True
    assert decision.basis == "pr-merge-base"
    assert b"src/cmpct/reader.py" in decision.affected
    assert "src/cmpct/reader.py" not in _git(
        repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"
    )

    baseline = _report()
    candidate = _report()
    candidate["corpora"]["shared"]["library"]["cmpct"]["create_s_median"] = 0.107
    base_path = tmp_path / "base.json"
    candidate_path = tmp_path / "candidate.json"
    base_path.write_text(json.dumps(baseline), encoding="utf-8")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        "check_performance_regression.py", "--base", str(base_path),
        "--candidate", str(candidate_path),
    ])
    assert comparator.main() == 1  # True +7%/+7ms remains a block.
    assert "Result: **FAIL**" in capsys.readouterr().out

    candidate["corpora"]["shared"]["library"]["cmpct"]["create_s_median"] = float("nan")
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    with pytest.raises(ValueError, match="finite positive measured seconds"):
        comparator.main()  # Invalid evidence cannot turn a material PR green.

    candidate["corpora"]["shared"]["library"]["cmpct"]["create_s_median"] = 0.1
    candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
    assert comparator.main() == 0  # An honest no-regression remains admissible.
    assert "Result: **PASS**" in capsys.readouterr().out
