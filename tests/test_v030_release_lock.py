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


def _write_receipt(
    root: Path,
    manifest: dict,
    receipt_id: str,
    owner: str,
    fingerprint: str,
    evidence: Path,
    facts: dict,
) -> None:
    receipt_dir = root / manifest["receipt_directory"]
    receipt_dir.mkdir(parents=True, exist_ok=True)
    rel = evidence.relative_to(root).as_posix()
    payload = {
        "schema": lock.RECEIPT_SCHEMA,
        "id": receipt_id,
        "status": "pass",
        "owner_task": owner,
        "candidate_fingerprint": fingerprint,
        "evidence": [{"path": rel, "sha256": _sha(evidence)}],
        "facts": facts,
    }
    (receipt_dir / f"{receipt_id}.json").write_text(json.dumps(payload), encoding="utf-8")


def _fixture_root(tmp_path: Path) -> tuple[dict, str, Path]:
    (tmp_path / "engine").mkdir()
    (tmp_path / "engine" / "codec.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "benchmarks").mkdir()
    (tmp_path / "benchmarks" / "v030_gate.py").write_text("GATE = 1\n", encoding="utf-8")
    (tmp_path / "benchmarks" / "history").mkdir()
    evidence = tmp_path / "benchmarks" / "history" / "result.json"
    evidence.write_text('{"gate": true}\n', encoding="utf-8")
    manifest = _manifest()
    fingerprint, _ = lock.fingerprint(manifest)
    return manifest, fingerprint, evidence


def test_release_lock_fails_closed_when_receipts_are_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, _fingerprint, _evidence = _fixture_root(tmp_path)

    ok, report = lock.check(manifest)

    assert ok is False
    assert report["release_unlocked"] is False
    assert set(report["failures"]) == {"compression-generalization", "native-r25"}


def test_release_lock_accepts_only_complete_current_receipts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    _write_receipt(
        tmp_path, manifest, "compression-generalization", "T02", fingerprint, evidence,
        {"saving": 150, "regressions": 0, "max_amp": 7.5},
    )
    _write_receipt(tmp_path, manifest, "native-r25", "T01", fingerprint, evidence, {"parity": True})

    ok, report = lock.check(manifest)

    assert ok is True
    assert report["release_unlocked"] is True
    assert report["failures"] == {}


def test_release_lock_invalidates_receipts_after_critical_code_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    _write_receipt(
        tmp_path, manifest, "compression-generalization", "T02", fingerprint, evidence,
        {"saving": 150, "regressions": 0, "max_amp": 7.5},
    )
    _write_receipt(tmp_path, manifest, "native-r25", "T01", fingerprint, evidence, {"parity": True})

    # Footnote: evidence receipts deliberately live outside the fingerprint surface, but a change to the
    # tested engine must invalidate every receipt. This is the core anti-staleness property of the lock.
    (tmp_path / "engine" / "codec.py").write_text("VALUE = 2\n", encoding="utf-8")
    ok, report = lock.check(manifest)

    assert ok is False
    assert all(
        "candidate fingerprint does not match" in errors
        for errors in report["failures"].values()
    )


def test_release_lock_rejects_tampered_evidence_and_threshold_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, evidence = _fixture_root(tmp_path)
    _write_receipt(
        tmp_path, manifest, "compression-generalization", "T02", fingerprint, evidence,
        {"saving": 99, "regressions": 0, "max_amp": 8.0},
    )
    _write_receipt(tmp_path, manifest, "native-r25", "T01", fingerprint, evidence, {"parity": True})
    evidence.write_text('{"gate": false}\n', encoding="utf-8")

    ok, report = lock.check(manifest)

    assert ok is False
    compression_errors = report["failures"]["compression-generalization"]
    assert any("SHA-256 mismatch" in error for error in compression_errors)
    assert any("expected >= 100" in error for error in compression_errors)
    assert any("SHA-256 mismatch" in error for error in report["failures"]["native-r25"])


def test_template_uses_current_fingerprint_and_manifest_owner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    manifest, fingerprint, _evidence = _fixture_root(tmp_path)

    template = lock.template_for("compression-generalization", manifest, fingerprint)

    assert template["candidate_fingerprint"] == fingerprint
    assert template["owner_task"] == "T02"
    assert template["facts"]["regressions"] == 0
    assert template["facts"]["saving"].startswith("REPLACE_WITH_VALUE_>=_")


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
