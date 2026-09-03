from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import check_v030_release_lock as lock
from tools import mint_v030_release_receipt as mint


def _manifest() -> dict:
    return {
        "schema": "cmpct-v030-release-lock-manifest-v1",
        "release": "0.30.0",
        "target_format_revision": 25,
        "receipt_directory": "docs/v030-release-receipts",
        "fingerprint_globs": ["engine/**/*.py", "tests/test_v030_*.py"],
        "required_receipts": [
            {
                "id": "runtime-memory-selective",
                "owner_task": "T02",
                "assertions": [
                    {"path": "facts.median_create_ratio", "max": 1.10},
                    {"path": "facts.selective_read_measured", "eq": True},
                ],
            }
        ],
    }


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict, Path]:
    monkeypatch.setattr(lock, "ROOT", tmp_path)
    (tmp_path / "engine").mkdir()
    (tmp_path / "engine" / "codec.py").write_text("REVISION = 25\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_v030_fixture.py").write_text("# fingerprint witness\n", encoding="utf-8")
    manifest = _manifest()
    fingerprint, _ = lock.fingerprint(manifest)
    evidence = tmp_path / "benchmark-artifacts" / "runtime.json"
    evidence.parent.mkdir()
    evidence.write_text(
        json.dumps(
            {
                "candidate_fingerprint": fingerprint,
                "totals": {"median_create_ratio": 1.04},
                "gate": {"selective_read_measured": True},
            }
        ),
        encoding="utf-8",
    )
    return manifest, evidence


def test_mint_copies_normative_facts_from_hashed_json_and_validates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, evidence = _fixture(tmp_path, monkeypatch)
    bindings = {
        "facts.median_create_ratio": (0, "totals.median_create_ratio"),
        "facts.selective_read_measured": (0, "gate.selective_read_measured"),
    }

    receipt = mint.build_receipt("runtime-memory-selective", [evidence], bindings, manifest=manifest)
    output = tmp_path / manifest["receipt_directory"] / "runtime-memory-selective.json"
    mint.write_validated_receipt(receipt, output, manifest=manifest)

    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["facts"] == {"median_create_ratio": 1.04, "selective_read_measured": True}
    assert written["fact_sources"]["facts.median_create_ratio"] == {
        "evidence_index": 0,
        "json_path": "totals.median_create_ratio",
    }
    assert written["candidate_fingerprint_source"] == {
        "evidence_index": 0,
        "json_path": "candidate_fingerprint",
    }
    spec = manifest["required_receipts"][0]
    fingerprint, _ = lock.fingerprint(manifest)
    assert written["candidate_fingerprint"] == fingerprint
    assert lock.validate_receipt(output, spec, fingerprint, manifest["receipt_directory"]) == []


def test_mint_refuses_missing_or_extra_fact_bindings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, evidence = _fixture(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="must match manifest assertions exactly"):
        mint.build_receipt(
            "runtime-memory-selective",
            [evidence],
            {"facts.median_create_ratio": (0, "totals.median_create_ratio")},
            manifest=manifest,
        )

    with pytest.raises(ValueError, match="must match manifest assertions exactly"):
        mint.build_receipt(
            "runtime-memory-selective",
            [evidence],
            {
                "facts.median_create_ratio": (0, "totals.median_create_ratio"),
                "facts.selective_read_measured": (0, "gate.selective_read_measured"),
                "facts.unowned": (0, "totals.median_create_ratio"),
            },
            manifest=manifest,
        )


def test_mint_never_publishes_a_receipt_that_fails_canonical_thresholds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, evidence = _fixture(tmp_path, monkeypatch)
    fingerprint, _ = lock.fingerprint(manifest)
    evidence.write_text(
        json.dumps(
            {
                "candidate_fingerprint": fingerprint,
                "totals": {"median_create_ratio": 1.50},
                "gate": {"selective_read_measured": True},
            }
        ),
        encoding="utf-8",
    )
    receipt = mint.build_receipt(
        "runtime-memory-selective",
        [evidence],
        {
            "facts.median_create_ratio": (0, "totals.median_create_ratio"),
            "facts.selective_read_measured": (0, "gate.selective_read_measured"),
        },
        manifest=manifest,
    )
    output = tmp_path / manifest["receipt_directory"] / "runtime-memory-selective.json"

    with pytest.raises(ValueError, match="failed canonical validation"):
        mint.write_validated_receipt(receipt, output, manifest=manifest)
    assert not output.exists()


def test_mint_refuses_receipt_directory_as_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest, _evidence = _fixture(tmp_path, monkeypatch)
    fingerprint, _ = lock.fingerprint(manifest)
    self_evidence = tmp_path / manifest["receipt_directory"] / "self.json"
    self_evidence.parent.mkdir(parents=True)
    self_evidence.write_text(
        json.dumps(
            {
                "candidate_fingerprint": fingerprint,
                "totals": {"median_create_ratio": 1.0},
                "gate": {"selective_read_measured": True},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="may not be used as their own release evidence"):
        mint.build_receipt(
            "runtime-memory-selective",
            [self_evidence],
            {
                "facts.median_create_ratio": (0, "totals.median_create_ratio"),
                "facts.selective_read_measured": (0, "gate.selective_read_measured"),
            },
            manifest=manifest,
        )


def test_mint_refuses_missing_or_stale_strict_fingerprint_witness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest, evidence = _fixture(tmp_path, monkeypatch)
    bindings = {
        "facts.median_create_ratio": (0, "totals.median_create_ratio"),
        "facts.selective_read_measured": (0, "gate.selective_read_measured"),
    }
    document = json.loads(evidence.read_text(encoding="utf-8"))

    missing = dict(document)
    missing.pop("candidate_fingerprint")
    evidence.write_text(json.dumps(missing), encoding="utf-8")
    with pytest.raises(ValueError, match="must record candidate_fingerprint"):
        mint.build_receipt("runtime-memory-selective", [evidence], bindings, manifest=manifest)

    stale = dict(document)
    stale["candidate_fingerprint"] = "0" * 64
    evidence.write_text(json.dumps(stale), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match the current release-critical fingerprint"):
        mint.build_receipt("runtime-memory-selective", [evidence], bindings, manifest=manifest)
