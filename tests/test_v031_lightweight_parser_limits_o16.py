"""O16: one resource policy, checkpoint-only Reader import, authentic hostile limits."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from cmpct.builder import Builder
from cmpct.resource_limits import ParserLimits, ResourceLimitError, ValidationError


def test_limit_types_reexport_identity_and_inheritance():
    from cmpct import validation
    assert validation.ParserLimits is ParserLimits
    assert validation.ValidationError is ValidationError
    assert validation.ResourceLimitError is ResourceLimitError
    assert issubclass(ResourceLimitError, ValidationError)
    assert ParserLimits.__module__ == "cmpct.validation"
    assert ValidationError.__module__ == "cmpct.validation"
    assert ResourceLimitError.__module__ == "cmpct.validation"


@pytest.mark.parametrize("environment_field, field", [
    ("CMPCT_MAX_INDEX_BYTES", "max_index_bytes"),
    ("CMPCT_MAX_GENERATION_BYTES", "max_generation_bytes"),
    ("CMPCT_MAX_BLOB_BYTES", "max_blob_bytes"),
    ("CMPCT_MAX_FILES", "max_files"),
    ("CMPCT_MAX_BLOBS", "max_blobs"),
    ("CMPCT_MAX_RECIPES", "max_recipes"),
    ("CMPCT_MAX_PATH_BYTES", "max_path_bytes"),
    ("CMPCT_MAX_DELTA_DEPTH", "max_delta_depth"),
])
def test_parser_limits_use_same_configured_environment(monkeypatch, environment_field, field):
    monkeypatch.setenv(environment_field, "17")
    assert getattr(ParserLimits.from_env(), field) == 17
    monkeypatch.setenv(environment_field, "0")
    with pytest.raises(ValueError, match="positive"):
        ParserLimits.from_env()
    monkeypatch.setenv(environment_field, "bad")
    with pytest.raises(ValueError, match="integer"):
        ParserLimits.from_env()


def test_authentic_checkpoint_reader_does_not_import_strict_validator(tmp_path: Path):
    source = tmp_path / "payload"
    source.mkdir()
    (source / "file.txt").write_bytes(b"lightweight-parser-policy" * 64)
    archive = tmp_path / "signed-checkpoint.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)

    # A genuinely fresh subprocess prevents this test's imports, fixtures and
    # pytest environment from preloading cmpct.validation on the test host.
    code = """
import sys
from pathlib import Path
from cmpct.reader import CMPCT
assert 'cmpct.validation' not in sys.modules, 'validator imported before Reader open'
with CMPCT(Path(sys.argv[1])) as reader:
    assert reader.read('file.txt') == b'lightweight-parser-policy' * 64
assert 'cmpct.validation' not in sys.modules, 'checkpoint-only Reader imported validator'
"""
    env = os.environ.copy()
    env.pop("CMPCT_MAX_GENERATION_BYTES", None)
    env.pop("CMPCT_MAX_DELTA_DEPTH", None)
    result = subprocess.run(
        [sys.executable, "-c", code, str(archive)],
        cwd=tmp_path, env=env, text=True, capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
