"""O22: same policy limits, no heavy validator import for an actual signed checkpoint."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys

from cmpct.builder import Builder
from cmpct.transactions import _append_generation


def test_shared_policy_identity_and_environment(monkeypatch):
    from cmpct import validation, resource_limits
    assert validation.ParserLimits is resource_limits.ParserLimits
    assert validation.ValidationError is resource_limits.ValidationError
    assert validation.ResourceLimitError is resource_limits.ResourceLimitError
    assert issubclass(validation.ResourceLimitError, validation.ValidationError)
    monkeypatch.setenv("CMPCT_MAX_GENERATION_BYTES", "8192")
    monkeypatch.setenv("CMPCT_MAX_DELTA_DEPTH", "1")
    assert validation.ParserLimits.from_env() == resource_limits.ParserLimits.from_env()
    assert resource_limits.ParserLimits.from_env().max_generation_bytes == 8192
    assert resource_limits.ParserLimits.from_env().max_delta_depth == 1


def test_actual_signed_checkpoint_skips_strict_validator_but_journal_imports_it(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "payload.txt").write_bytes(b"O22-SHARED-LIMITS" * 128)
    archive = tmp_path / "signed-checkpoint.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)

    probe = """
import sys
from pathlib import Path
from cmpct.reader import CMPCT
assert 'cmpct.validation' not in sys.modules, 'early strict import'
with CMPCT(Path(sys.argv[1])) as reader:
    assert reader.read('payload.txt') == b'O22-SHARED-LIMITS' * 128
    assert reader.delta_depth == int(sys.argv[2])
assert ('cmpct.validation' in sys.modules) == (sys.argv[2] == '1'), 'wrong replay import boundary'
"""
    def run(expected_depth):
        env = os.environ.copy()
        env.pop("CMPCT_MAX_GENERATION_BYTES", None)
        env.pop("CMPCT_MAX_DELTA_DEPTH", None)
        child = subprocess.run([sys.executable, "-c", probe, str(archive), str(expected_depth)],
                               env=env, capture_output=True, text=True, timeout=45, check=False)
        assert child.returncode == 0, child.stdout + "\n" + child.stderr

    from cmpct.reader import CMPCT
    with CMPCT(archive) as reader:
        checkpoint_index = reader.index
        previous = reader.latest_footer_pos

    signed_checkpoint, _ = _append_generation(
        archive, {}, previous, checkpoint_index=checkpoint_index
    )
    with CMPCT(archive) as reader:
        assert reader.latest_footer_pos == signed_checkpoint
        assert reader.delta_depth == 0
    run(0)

    _append_generation(
        archive, {"blobs": [], "ops": [["ren", "absent", "unused"]]},
        signed_checkpoint,
    )
    run(1)
