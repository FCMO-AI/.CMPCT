from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools import check_v030_release_lock as lock


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict:
    return {
        "schema": "cmpct-v030-release-lock-manifest-v1",
        "release": "0.30.0",
        "target_format_revision": 25,
        "receipt_directory": "docs/v030-release-receipts",
        "fingerprint_globs": ["engine/**/*.py", "benchmarks/v030_*.py"],
        "required_receipts": [
            {
                "id": "compression-generalization",
                "owner_task": "T02",
                "assertions": [
                    {"path": "facts.saving", "min": 100},
                    {"path": "facts.regressions", "eq": 0},
                    {"path": "facts.max_amp", "max": 8.0},
                ],
            },
            {
                "id": "native-r25",
                "owner_task": "T01",
                "assertions": [{"path": "facts.parity", "eq": True}],
            },
        ],
    }


def _default_sources(receipt_id: str, facts: dict) -> dict:
    prefix = "compression" if receipt_id == "compression-generalization" else "native"
    return {
        f"facts.{key}": {"evidence_index": 0, "json_path": f"{prefix}.{key}"}
        for key in facts
    }


def _write_receipt(
    root: Path,
    manifest: dict,
    receipt_id: str,
    owner: str,
    fingerprint: str,
    evidence: Path,
    facts: dict,
    *,
    fact_sources: dict | None = None,
    evidence_path: str | None = None,
) -> Path:
    receipt_dir = root / manifest["receipt_directory"]
    receipt_dir.mkdir(parents=True, exist_ok=True)
    rel = evidence_path or evidence.relative_to(root).as_posix()
    payload = {
        "schema": lock.RECEIPT_SCHEMA,
        "id": receipt_id,
        "status": "pass",
        "owner_task": owner,
        "candidate_fingerprint": fingerprint,
        "evidence": [{"path": rel, "sha256": _sha(evidence)}],
        "facts": facts,
        "fact_sources": fact_sources if fact_sources is not None else _default_sources(receipt_id, facts),
    }
    path = receipt_dir / f"{receipt_id}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _fixture_root(tmp_path: Path) -> tuple[dict, str, Path]:
    (tmp_path / "engine").mkdir()
    (tmp_path / "engine" / "codec.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "benchmarks").mkdir()
    (tmp_path / "benchmarks" / "v030_gate.py").write_text("GATE = 1\n", encoding="utf-8")
    (tmp_path / "benchmarks" / "history").mkdir()
    evidence = tmp_path / "benchmarks" / "history" / "result.json"
    evidence.write_text(
        json.dumps(
            {
                "compression": {"saving": 150, "regressions": 0, "max_amp": 7.5},
                "native": {"parity": True},
            }
        ),
        encoding="utf-8",
    )
    manifest = _manifest()
    fingerprint, _ = lock.fingerprint(manifest)
    return manifest, fingerprint, evidence


def _write_passing_pair(tmp_path: Path, manifest: dict, fingerprint: str, evidence: Path) -> None:
    _write_receipt(
        tmp_path,
        manifest,
        "compression-generalization",
        "T02",
        fingerprint,
        evidence,
        {"saving": 150, "regressions": 0, "max_amp": 7.5},
    )
    _write_receipt(
        tmp_path,
        manifest,
        "native-r25",
        "T01",
        fingerprint,
        evidence,
        {"parity": True},
    )


def _write_task(root: Path, rel: str, state: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Task\n\n- **State:** {state}\n", encoding="utf-8")


def test_release_lock_fails_closed_when_receipts_are_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, _fingerprint, _evidence = _fixture_root(tmp_path)

    ok, report = lock.check(manifest)

    assert ok is False
    assert report["release_unlocked"] is False
    assert set(report["failures"]) == {"compression-generalization", "native-r25"}


def test_release_lock_accepts_only_complete_current_evidence_bound_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    _write_passing_pair(tmp_path, manifest, fingerprint, evidence)

    ok, report = lock.check(manifest)

    assert ok is True
    assert report["release_unlocked"] is True
    assert report["failures"] == {}
    assert report["task_state_failures"] == []


def test_release_lock_invalidates_receipts_after_critical_code_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    _write_passing_pair(tmp_path, manifest, fingerprint, evidence)

    # Footnote: evidence receipts deliberately live outside the fingerprint surface, but a change to the
    # tested engine must invalidate every receipt. This is the core anti-staleness property of the lock.
    (tmp_path / "engine" / "codec.py").write_text("VALUE = 2\n", encoding="utf-8")
    ok, report = lock.check(manifest)

    assert ok is False
    assert all(
        any("candidate fingerprint does not match" in error for error in errors)
        for errors in report["failures"].values()
    )


def test_release_lock_rejects_tampered_hashed_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    _write_passing_pair(tmp_path, manifest, fingerprint, evidence)
    evidence.write_text('{"compression":{"saving":999999},"native":{"parity":true}}\n', encoding="utf-8")

    ok, report = lock.check(manifest)

    assert ok is False
    assert any("SHA-256 mismatch" in error for error in report["failures"]["compression-generalization"])
    assert any("SHA-256 mismatch" in error for error in report["failures"]["native-r25"])


def test_release_lock_rejects_receipt_fact_that_disagrees_with_hashed_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    # 150 would pass the threshold, but the receipt is not allowed to invent it if the hashed evidence says 90.
    document = json.loads(evidence.read_text(encoding="utf-8"))
    document["compression"]["saving"] = 90
    evidence.write_text(json.dumps(document), encoding="utf-8")
    _write_receipt(
        tmp_path,
        manifest,
        "compression-generalization",
        "T02",
        fingerprint,
        evidence,
        {"saving": 150, "regressions": 0, "max_amp": 7.5},
    )

    ok, report = lock.check(manifest)

    assert ok is False
    errors = report["failures"]["compression-generalization"]
    assert any("disagrees with hashed evidence" in error for error in errors)


def test_release_lock_rejects_missing_or_invalid_fact_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    facts = {"saving": 150, "regressions": 0, "max_amp": 7.5}
    bindings = _default_sources("compression-generalization", facts)
    del bindings["facts.saving"]
    bindings["facts.max_amp"] = {"evidence_index": 99, "json_path": "compression.max_amp"}
    _write_receipt(
        tmp_path,
        manifest,
        "compression-generalization",
        "T02",
        fingerprint,
        evidence,
        facts,
        fact_sources=bindings,
    )

    ok, report = lock.check(manifest)

    assert ok is False
    errors = report["failures"]["compression-generalization"]
    assert any("missing fact source binding for facts.saving" in error for error in errors)
    assert any("evidence_index out of range for facts.max_amp" in error for error in errors)


def test_release_lock_rejects_missing_json_path_and_bool_integer_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    _write_receipt(
        tmp_path,
        manifest,
        "native-r25",
        "T01",
        fingerprint,
        evidence,
        {"parity": 1},
        fact_sources={"facts.parity": {"evidence_index": 0, "json_path": "native.missing"}},
    )

    ok, report = lock.check(manifest)

    assert ok is False
    errors = report["failures"]["native-r25"]
    assert any("does not exist" in error for error in errors)
    assert any("expected exactly True" in error for error in errors)


def test_release_lock_forbids_receipts_from_attesting_to_receipt_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    receipt_dir = tmp_path / manifest["receipt_directory"]
    receipt_dir.mkdir(parents=True, exist_ok=True)
    self_evidence = receipt_dir / "self-evidence.json"
    self_evidence.write_text('{"native":{"parity":true}}', encoding="utf-8")
    _write_receipt(
        tmp_path,
        manifest,
        "native-r25",
        "T01",
        fingerprint,
        self_evidence,
        {"parity": True},
        evidence_path=self_evidence.relative_to(tmp_path).as_posix(),
    )

    ok, report = lock.check(manifest)

    assert ok is False
    assert any("may not point into the release receipt directory" in error for error in report["failures"]["native-r25"])


def test_task_state_blocks_unlock_even_when_all_receipts_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    _write_passing_pair(tmp_path, manifest, fingerprint, evidence)
    task0 = "docs/v030-coordination/tasks/T00.md"
    task4 = "docs/v030-coordination/tasks/T04.md"
    manifest["required_task_states"] = [
        {"path": task0, "allowed": ["DONE"]},
        {"path": task4, "allowed": ["REVIEW"]},
    ]
    _write_task(tmp_path, task0, "CLAIMED")
    _write_task(tmp_path, task4, "REVIEW")

    ok, report = lock.check(manifest)

    assert ok is False
    assert report["failures"] == {}
    assert report["task_states"] == {task0: "CLAIMED", task4: "REVIEW"}
    assert any("expected one of ['DONE']" in error for error in report["task_state_failures"])

    _write_task(tmp_path, task0, "DONE")
    ok, report = lock.check(manifest)
    assert ok is True
    assert report["task_state_failures"] == []


def test_task_state_fails_closed_when_state_declaration_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    _write_passing_pair(tmp_path, manifest, fingerprint, evidence)
    task = "docs/v030-coordination/tasks/T03.md"
    manifest["required_task_states"] = [{"path": task, "allowed": ["DONE"]}]
    path = tmp_path / task
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Task without state\n", encoding="utf-8")

    ok, report = lock.check(manifest)

    assert ok is False
    assert any("no parseable" in error for error in report["task_state_failures"])


def test_template_uses_current_fingerprint_owner_and_fact_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, _evidence = _fixture_root(tmp_path)

    template = lock.template_for("compression-generalization", manifest, fingerprint)

    assert template["candidate_fingerprint"] == fingerprint
    assert template["owner_task"] == "T02"
    assert template["facts"]["regressions"] == 0
    assert template["facts"]["saving"].startswith("REPLACE_WITH_VALUE_>=_")
    assert template["fact_sources"]["facts.saving"]["evidence_index"] == 0
    assert "json_path" in template["fact_sources"]["facts.max_amp"]


def test_native_build_outputs_do_not_change_release_fingerprint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    source = tmp_path / "native" / "cmpct-portable" / "src"
    source.mkdir(parents=True)
    (source / "lib.rs").write_text("pub const REVISION: u8 = 25;\n", encoding="utf-8")
    target = tmp_path / "native" / "cmpct-portable" / "target" / "release"
    target.mkdir(parents=True)
    build_product = target / "cmpct-portable"
    build_product.write_bytes(b"first-build")
    manifest = {
        "fingerprint_globs": [
            "native/**/Cargo.toml",
            "native/**/Cargo.lock",
            "native/**/build.rs",
            "native/**/src/**/*",
            "native/**/tests/**/*",
            "native/**/benches/**/*",
            "native/**/vectors/**/*",
            "native/**/golden/**/*",
        ]
    }

    before, paths = lock.fingerprint(manifest)
    build_product.write_bytes(b"different-machine-build")
    after, paths_after = lock.fingerprint(manifest)

    # Footnote: Cargo target output is execution residue, not release source. If it participated in the
    # fingerprint, identical source could invalidate receipts merely because a different runner built it.
    assert before == after
    assert paths == paths_after == ["native/cmpct-portable/src/lib.rs"]
