from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

from experiments import entropygraph_v030_release_lock_strict as strict
from tools import check_v030_release_lock as core


def _fingerprinted_manifest(root: Path, receipt_id: str = "runtime") -> tuple[dict, str]:
    engine = root / "engine"
    engine.mkdir(parents=True, exist_ok=True)
    (engine / "candidate.py").write_text("REVISION = 25\n", encoding="utf-8")
    manifest = {
        "fingerprint_globs": ["engine/**/*.py"],
        "required_task_states": [],
        "receipt_directory": "docs/v030-release-receipts",
        "required_receipts": [{"id": receipt_id, "owner_task": "T02", "assertions": []}],
    }
    fingerprint, _ = core.fingerprint(manifest)
    return manifest, fingerprint


def _write_receipt(
    root: Path,
    receipt_id: str,
    fingerprint: str,
    evidence_rel: str,
    evidence_sha: str,
    *,
    source_json_path: str = "candidate_fingerprint",
) -> Path:
    receipt_dir = root / "docs" / "v030-release-receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    path = receipt_dir / f"{receipt_id}.json"
    path.write_text(
        json.dumps(
            {
                "schema": "cmpct-v030-release-receipt-v1",
                "id": receipt_id,
                "status": "pass",
                "owner_task": "T02",
                "candidate_fingerprint": fingerprint,
                "candidate_fingerprint_source": {
                    "evidence_index": 0,
                    "json_path": source_json_path,
                },
                "evidence": [{"path": evidence_rel, "sha256": evidence_sha}],
                "facts": {},
                "fact_sources": {},
            }
        ),
        encoding="utf-8",
    )
    return path


def test_strict_json_rejects_nan_and_infinity() -> None:
    for token in ("NaN", "Infinity", "-Infinity"):
        with pytest.raises(strict.StrictReleaseInputError, match="non-standard JSON numeric constant"):
            strict.strict_json_loads(f'{{"value": {token}}}', label="hostile.json")


def test_strict_json_rejects_programmatic_non_finite_values() -> None:
    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(strict.StrictReleaseInputError, match="non-finite"):
            strict._require_finite({"facts": {"ratio": value}}, label="programmatic")


def test_strict_json_accepts_finite_release_numbers() -> None:
    value = strict.strict_json_loads(
        '{"saving":687783,"ratio":1.1,"passed":true}', label="evidence.json"
    )
    assert value == {"saving": 687783, "ratio": 1.1, "passed": True}


def test_strict_repo_file_rejects_symlink_component(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    evidence = outside / "evidence.json"
    evidence.write_text('{"passed":true}', encoding="utf-8")
    link = root / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("host platform cannot create symlinks")

    monkeypatch.setattr(strict, "ROOT", root)
    with pytest.raises(strict.StrictReleaseInputError, match="symlink component"):
        strict.strict_repo_file("linked/evidence.json")


def test_strict_preflight_rejects_nonfinite_receipt_before_core_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path
    monkeypatch.setattr(strict, "ROOT", root)
    monkeypatch.setattr(core, "ROOT", root)
    manifest, _fingerprint = _fingerprinted_manifest(root)
    task = root / "docs" / "v030-coordination" / "tasks" / "T02.md"
    task.parent.mkdir(parents=True)
    task.write_text("# T02\n- **State:** DONE\n", encoding="utf-8")
    manifest["required_task_states"] = [{"path": "docs/v030-coordination/tasks/T02.md", "allowed": ["DONE"]}]
    receipt_dir = root / "docs" / "v030-release-receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    (receipt_dir / "runtime.json").write_text(
        '{"schema":"cmpct-v030-release-receipt-v1","id":"runtime","status":"pass",'
        '"owner_task":"T02","candidate_fingerprint":"x","evidence":[],"facts":{"ratio":NaN}}',
        encoding="utf-8",
    )

    failures = strict.preflight(manifest)
    assert any("non-standard JSON numeric constant" in failure for failure in failures)


def test_strict_preflight_rejects_nonfinite_json_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path
    monkeypatch.setattr(strict, "ROOT", root)
    monkeypatch.setattr(core, "ROOT", root)
    manifest, fingerprint = _fingerprinted_manifest(root)
    evidence = root / "benchmarks" / "history" / "runtime.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text('{"candidate_fingerprint":"x","totals":{"ratio":Infinity}}', encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    _write_receipt(root, "runtime", fingerprint, "benchmarks/history/runtime.json", digest)

    failures = strict.preflight(manifest)
    assert any("non-standard JSON numeric constant" in failure for failure in failures)


def test_strict_preflight_accepts_evidence_bound_to_current_fingerprint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path
    monkeypatch.setattr(strict, "ROOT", root)
    monkeypatch.setattr(core, "ROOT", root)
    manifest, fingerprint = _fingerprinted_manifest(root)
    evidence = root / "benchmarks" / "history" / "runtime.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text(json.dumps({"candidate_fingerprint": fingerprint, "passed": True}), encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    _write_receipt(root, "runtime", fingerprint, "benchmarks/history/runtime.json", digest)

    assert strict.preflight(manifest) == []


def test_strict_preflight_rejects_old_green_evidence_with_new_receipt_fingerprint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path
    monkeypatch.setattr(strict, "ROOT", root)
    monkeypatch.setattr(core, "ROOT", root)
    manifest, fingerprint = _fingerprinted_manifest(root)
    stale = "1" * 64 if fingerprint != "1" * 64 else "2" * 64
    evidence = root / "benchmarks" / "history" / "runtime.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text(json.dumps({"candidate_fingerprint": stale, "passed": True}), encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    _write_receipt(root, "runtime", fingerprint, "benchmarks/history/runtime.json", digest)

    failures = strict.preflight(manifest)
    assert any("does not match current fingerprint" in failure for failure in failures)


def test_strict_preflight_rejects_missing_fingerprint_source_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path
    monkeypatch.setattr(strict, "ROOT", root)
    monkeypatch.setattr(core, "ROOT", root)
    manifest, fingerprint = _fingerprinted_manifest(root)
    evidence = root / "benchmarks" / "history" / "runtime.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text(json.dumps({"candidate_fingerprint": fingerprint}), encoding="utf-8")
    digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
    receipt = _write_receipt(root, "runtime", fingerprint, "benchmarks/history/runtime.json", digest)
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    del payload["candidate_fingerprint_source"]
    receipt.write_text(json.dumps(payload), encoding="utf-8")

    failures = strict.preflight(manifest)
    assert any("missing candidate_fingerprint_source" in failure for failure in failures)


def test_strict_check_cannot_unlock_when_preflight_is_red(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = {"required_task_states": [], "receipt_directory": "x", "required_receipts": []}
    monkeypatch.setattr(strict, "preflight", lambda _manifest: ["hostile evidence"])
    monkeypatch.setattr(
        core,
        "check",
        lambda _manifest: (
            True,
            {
                "candidate_fingerprint": "0" * 64,
                "passed_receipts": [],
                "required_receipts": 0,
                "failures": {},
                "task_state_failures": [],
                "release_unlocked": True,
            },
        ),
    )

    ok, report = strict.check(manifest)
    assert ok is False
    assert report["release_unlocked"] is False
    assert report["strict_input_failures"] == ["hostile evidence"]
