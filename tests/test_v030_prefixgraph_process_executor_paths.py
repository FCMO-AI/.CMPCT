from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from experiments import entropygraph_v030_prefixgraph_process_executor as E


def _canonical_build_placeholder(source, archive):
    raise AssertionError("the mocked child owns execution")


_canonical_build_placeholder.__module__ = E.EXPECTED_OWNER_MODULE
_canonical_build_placeholder.__name__ = E.EXPECTED_BUILD_NAME


def test_relative_paths_keep_caller_meaning_when_child_uses_repository_cwd(monkeypatch, tmp_path):
    caller = tmp_path / "caller"
    source = caller / "source"
    source.mkdir(parents=True)
    (source / "payload.bin").write_bytes(b"payload")
    caller.mkdir(exist_ok=True)
    monkeypatch.chdir(caller)

    observed = {}

    def fake_run(cmd, **kwargs):
        source_arg = Path(cmd[cmd.index("--source") + 1])
        archive_arg = Path(cmd[cmd.index("--archive") + 1])
        observed.update({"source": source_arg, "archive": archive_arg, "cwd": Path(kwargs["cwd"])})
        assert source_arg.is_absolute()
        assert archive_arg.is_absolute()
        assert source_arg == source
        assert archive_arg == caller / "out" / "candidate.cmpct"
        archive_arg.parent.mkdir(parents=True, exist_ok=True)
        archive_arg.write_bytes(b"candidate")
        digest = hashlib.sha256(b"candidate").hexdigest()
        receipt = {
            "schema": "cmpct-v030-prefixgraph-process-executor-v1",
            "semantic_owner": E.EXPECTED_OWNER_MODULE,
            "prefix_level": E.SUPPORTED_PREFIX_LEVEL,
            "archive_bytes": len(b"candidate"),
            "archive_sha256": digest,
            "stats": {"selected": "prefixgraph"},
        }
        return SimpleNamespace(returncode=0, stdout=json.dumps(receipt) + "\n", stderr="")

    monkeypatch.setattr(E.subprocess, "run", fake_run)
    result = E.PrefixGraphProcessExecutor().submit(
        _canonical_build_placeholder,
        Path("source"),
        Path("out/candidate.cmpct"),
    ).result()

    assert result == {"selected": "prefixgraph"}
    assert observed["cwd"] != caller
    assert observed["source"] == source
    assert observed["archive"].read_bytes() == b"candidate"
