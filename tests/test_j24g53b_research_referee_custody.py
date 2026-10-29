"""J24G53b: executable research referees must be covered by prospective source identity.

This guards the evidence-owner code used by hosted scientific courts; it does not
pretend a source fingerprint authenticates archives, release receipts or runtimes.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools import check_v031_candidate_fingerprint as C

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_REFEREES = {
    "research/j24g44/detached_zero_encoded_wire_audit.py",
    "research/j24g47/audit_signed_rekey.py",
    "research/j24g50/independent_audit.py",
}


def test_current_scientific_referees_belong_to_source_identity() -> None:
    manifest = C.load_manifest()
    _, rows = C.fingerprint(manifest)
    observed = set(rows)
    actual_referees = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "research").rglob("*.py")
        if path.is_file()
    }
    assert actual_referees, "no independent-referee source to protect"
    assert actual_referees <= observed, sorted(actual_referees - observed)
    assert REQUIRED_REFEREES <= observed
    assert REQUIRED_REFEREES <= set(manifest["required_paths"])


def test_scientific_referee_mutation_changes_source_identity(tmp_path: Path) -> None:
    referee = tmp_path / "research" / "j24g50" / "independent_audit.py"
    referee.parent.mkdir(parents=True)
    referee.write_bytes(b"def audit():\n    return True\n")
    manifest = {
        "fingerprint_globs": ["research/**/*.py"],
        "required_paths": ["research/j24g50/independent_audit.py"],
    }
    before, rows = C.fingerprint(manifest, root=tmp_path)
    assert rows == ["research/j24g50/independent_audit.py"]
    referee.write_bytes(b"def audit():\n    return False\n")
    after, _ = C.fingerprint(manifest, root=tmp_path)
    assert before != after, "scientific referee source modification must change identity"
    referee.unlink()
    with pytest.raises(ValueError, match="missing mandatory custody sources"):
        C.fingerprint(manifest, root=tmp_path)
