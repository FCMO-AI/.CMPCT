#!/usr/bin/env python3
"""O65 detached exact-parent referee. Invoked only from source-bound hosted CI.

Load the *actual* immutable historical Builder from Git as a second implementation,
execute it against the same installed codec and physical source tree, and keep
its genuine false-success negative independent of the candidate's tests.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from unittest.mock import patch

import cmpct.builder as candidate
from cmpct.reader import CMPCT

PARENT = "4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b"
PARENT_BUILDER_BLOB = "663ef0922992b1fbb8f19e6eea88d55c10a56044"


def original_builder():
    original = subprocess.check_output(
        ["git", "show", f"{PARENT}:src/cmpct/builder.py"]
    )
    source_hash = subprocess.check_output(
        ["git", "hash-object", "--stdin"], input=original, text=False
    ).decode().strip()
    assert source_hash == PARENT_BUILDER_BLOB, source_hash
    name = "cmpct._o65_historical_original_builder"
    module = types.ModuleType(name)
    module.__package__ = "cmpct"
    module.__file__ = f"{PARENT}:src/cmpct/builder.py"
    sys.modules[name] = module
    exec(compile(original, module.__file__, "exec"), module.__dict__)
    return module.Builder


def root_tree(td):
    path = Path(td) / "source"
    path.mkdir()
    (path / "member.bin").write_bytes(b"O65 historical same-root source\n")
    return path


def main():
    old = original_builder()
    report = {"parent": PARENT, "historical_builder_blob": PARENT_BUILDER_BLOB,
              "case_results": []}
    with tempfile.TemporaryDirectory(prefix="o65-historical-") as td:
        root = root_tree(td)
        # Independent *full physical archive* comparison on one stable source.
        base_path = Path(td) / "original.cmpct"
        cand_path = Path(td) / "candidate.cmpct"
        old(root, workers=1, reproducible=True).build(base_path)
        candidate.Builder(root, workers=1, reproducible=True).build(cand_path)
        base_raw, cand_raw = base_path.read_bytes(), cand_path.read_bytes()
        assert base_raw == cand_raw, (len(base_raw),len(cand_raw))
        with CMPCT(cand_path) as r:
            assert r.verify() >= 1
            assert r.read("member.bin") == (root / "member.bin").read_bytes()
        report["case_results"].append({
            "case": "normal_reproducible_complete_archive_parity",
            "archive_bytes": len(base_raw),
            "archive_sha256": hashlib.sha256(base_raw).hexdigest(),
            "passed": True,
        })

        # Inject the same OS API on every host, even where Python lacks the
        # native interface (macOS/Windows), to prove the original-source branch.
        def enumerated(_path, *, follow_symlinks=False):
            return ["user.cmpct_o65"]

        def cannot_read(*_args, **_kw):
            raise PermissionError(13, "injected observed xattr denial")

        with patch.object(os, "listxattr", enumerated, create=True), patch.object(
            os, "getxattr", cannot_read, create=True
        ):
            before = old(root, workers=1)
            before.scan()
            assert before.meta_by_rel["member.bin"][2] == {}
            try:
                candidate.Builder(root, workers=1).scan()
            except OSError as exc:
                assert "refusing lossy archive" in str(exc), str(exc)
            else:
                raise AssertionError("candidate silently omitted observed unreadable xattr")
            report["case_results"].append({
                "case": "original_builder_incorrect_success_vs_candidate_refusal",
                "passed": True,
                "historical_silent_loss": True,
                "candidate_failure_closed": True,
            })
    print("O65_ORIGINAL_SOURCE_REFEREE", json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
