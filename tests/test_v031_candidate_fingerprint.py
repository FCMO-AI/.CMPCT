from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from tools import check_v031_candidate_fingerprint as C

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL_V030_LOCK_GIT_BLOB = "988a7b05ad4e0833fac0453de74133b38f890f87"


def _init_git_source(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)


def _stage(root: Path, *paths: str) -> None:
    subprocess.run(["git", "add", "--", *paths], cwd=root, check=True)


def test_historical_release_lock_is_unmodified() -> None:
    content = (ROOT / "docs/V030_RELEASE_LOCK.json").read_bytes()
    blob = b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    assert hashlib.sha1(blob).hexdigest() == HISTORICAL_V030_LOCK_GIT_BLOB


def test_prospective_identity_covers_original_four_red_custody_sources() -> None:
    manifest = C.load_manifest()
    digest, rows = C.fingerprint(manifest)
    assert len(digest) == 64
    assert set(manifest["required_paths"]).issubset(set(rows))
    assert "tools/materialize_performance_base_native.py" in rows
    assert "tests/conformance/v030-r25-canonical.json" in rows
    assert ".github/workflows/tests.yml" in rows
    assert all("/build/" not in row and "/jniLibs/" not in row for row in rows if row.startswith("integrations/android/"))


def test_source_mutation_add_remove_and_rename_alter_identity(tmp_path: Path) -> None:
    parent = tmp_path / "src"
    parent.mkdir()
    one = parent / "a.py"
    one.write_text("value = 1\n")
    _init_git_source(tmp_path)
    _stage(tmp_path, "src/a.py")
    manifest = {"fingerprint_globs": ["src/**/*.py"], "required_paths": []}
    before, rows = C.fingerprint(manifest, root=tmp_path)
    assert rows == ["src/a.py"]
    one.write_text("value = 2\n")
    mutated, _ = C.fingerprint(manifest, root=tmp_path)
    assert mutated != before
    one.rename(parent / "b.py")
    _stage(tmp_path, "src/a.py", "src/b.py")
    renamed, renamed_rows = C.fingerprint(manifest, root=tmp_path)
    assert renamed != mutated and renamed_rows == ["src/b.py"]
    (parent / "b.py").unlink()
    with pytest.raises(ValueError, match="empty candidate identity"):
        C.fingerprint(manifest, root=tmp_path)


def test_missing_required_or_unsafe_source_fails_closed(tmp_path: Path) -> None:
    source = tmp_path / "src"
    source.mkdir()
    (source / "real.py").write_text("safe = True\n")
    _init_git_source(tmp_path)
    _stage(tmp_path, "src/real.py")
    manifest = {"fingerprint_globs": ["src/**/*.py"], "required_paths": ["src/missing.py"]}
    with pytest.raises(ValueError, match="missing mandatory"):
        C.fingerprint(manifest, root=tmp_path)
    manifest["required_paths"] = []
    (source / "link.py").symlink_to(source / "real.py")
    _stage(tmp_path, "src/link.py")
    with pytest.raises(ValueError, match="symlink"):
        C.fingerprint(manifest, root=tmp_path)


def test_manifest_validation_rejects_traversal(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({
        "schema": C.SCHEMA,
        "status": "candidate-evidence-only-not-released",
        "fingerprint_globs": ["../**/*"],
        "required_paths": ["src/a.py"],
    }))
    with pytest.raises(ValueError, match="escapes"):
        C.load_manifest(path)
