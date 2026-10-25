#!/usr/bin/env python3
"""O75: source-faithful old Builder vs staged-publication candidate. Research, not release."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import platform
import stat
import subprocess
import sys
import tempfile
import time
import types
from pathlib import Path
from unittest.mock import patch

BASE = "4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b"
BASE_BLOB = "663ef0922992b1fbb8f19e6eea88d55c10a56044"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def historical_builder():
    source = subprocess.check_output(
        ["git", "show", f"{BASE}:src/cmpct/builder.py"])
    git_blob = "blob " + str(len(source)) + "\0"
    real_blob = hashlib.sha1(git_blob.encode() + source).hexdigest()
    assert real_blob == BASE_BLOB, (real_blob, BASE_BLOB)
    name = "cmpct._o75_frozen_builder"
    module = types.ModuleType(name)
    module.__file__ = "<git-blob:" + BASE_BLOB + ">"
    module.__package__ = "cmpct"
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module.Builder


def court():
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    import cmpct.builder as builder_module

    assert "site-packages" in str(Path(builder_module.__file__).resolve()), builder_module.__file__
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() == os.environ["EXACT_HEAD"]
    Historical = historical_builder()
    results = {"head": os.environ["EXACT_HEAD"], "baseline_builder_blob": BASE_BLOB,
               "candidate_builder_blob": subprocess.check_output(
                   ["git", "hash-object", "src/cmpct/builder.py"], text=True).strip(),
               "platform": platform.platform(), "python": platform.python_version()}
    with tempfile.TemporaryDirectory(prefix="cmpct-o75-") as td:
        t = Path(td)
        root = t / "source"
        root.mkdir()
        (root / "main.txt").write_bytes(b"INITIAL_ARCHIVE_A\n" * 370)
        (root / "index.json").write_bytes(b'{"entries":[1,2,3],"tag":"A"}' * 4)
        out = t / "target.cmpct"
        Historical(root, reproducible=True, workers=1).build(out)
        old = out.read_bytes()
        old_sha = hashlib.sha256(old).hexdigest()
        with CMPCT(out) as ar:
            assert ar.verify() == 2
            assert ar.read("main.txt") == b"INITIAL_ARCHIVE_A\n" * 370
        (root / "main.txt").write_bytes(b"REPLACEMENT_ARCHIVE_B\n" * 400)
        (root / "index.json").write_bytes(b'{"entries":[4,5,6],"tag":"B"}' * 4)

        # Real historical Builder, injected short write after the old target was opened
        # with truncation, then an I/O error. This is the pre-repair negative.
        original_path_write = Path.write_bytes
        def torn_old_write(self, data):
            if Path(self) == out:
                with open(self, "wb") as f:
                    f.write(data[:41])
                raise OSError("O75 deliberate historical partial-write EIO")
            return original_path_write(self, data)
        try:
            with patch.object(Path, "write_bytes", torn_old_write):
                Historical(root, reproducible=True, workers=1).build(out)
        except OSError as exc:
            assert "O75 deliberate" in str(exc)
        else:
            raise AssertionError("historical build did not exercise injected torn-write")
        torn = out.read_bytes()
        assert len(torn) == 41 and hashlib.sha256(torn).hexdigest() != old_sha
        results["original_partial_write"] = {
            "prior_bytes": len(old), "post_error_bytes": len(torn),
            "prior_sha256": old_sha, "post_error_sha256": hashlib.sha256(torn).hexdigest(),
            "confirmed_data_loss": True}
        out.write_bytes(old)

        # New publication must never expose the partly staged bytes on failure.
        real_write = os.write
        calls = [0]
        def interrupted_write(fd, data):
            calls[0] += 1
            if calls[0] == 1:
                return real_write(fd, memoryview(data)[:min(41, len(data))])
            raise OSError("O75 deliberate staging EIO")
        try:
            with patch.object(os, "write", interrupted_write):
                Builder(root, reproducible=True, workers=1).build(out)
        except OSError as exc:
            assert "O75 deliberate" in str(exc)
        else:
            raise AssertionError("staging writer did not exercise injected EIO")
        assert calls[0] == 2
        assert out.read_bytes() == old
        assert not list(t.glob(".target.cmpct.cmpct-stage-*"))
        with CMPCT(out) as ar:
            assert ar.verify() == 2 and ar.read("main.txt") == b"INITIAL_ARCHIVE_A\n" * 370
        results["staging_partial_write"] = {"calls": calls[0],
                                             "old_archive_preserved": True,
                                             "temporary_files_left": 0}

        # A failed namespace commit must also retain the old exact archive.
        real_replace = os.replace
        def refused_replace(src, dst):
            assert Path(dst) == out
            assert Path(src).exists() and Path(src).stat().st_size > 41
            raise OSError("O75 deliberate replace EIO")
        try:
            with patch.object(os, "replace", refused_replace):
                Builder(root, reproducible=True, workers=1).build(out)
        except OSError as exc:
            assert "O75 deliberate" in str(exc)
        else:
            raise AssertionError("replace rejection did not fail")
        assert out.read_bytes() == old
        assert not list(t.glob(".target.cmpct.cmpct-stage-*"))
        results["failed_replace"] = {"old_archive_preserved": True,
                                      "temporary_files_left": 0}

        # Strong simpler control: unchanged historical source produces the same
        # complete r24 bytes as staged publication on identical B tree.
        control = t / "historical-b.cmpct"
        Historical(root, reproducible=True, workers=1).build(control)
        new_mode = stat.S_IMODE(control.stat().st_mode)
        complete = []
        staged_max = [0]
        def recording_replace(src, dst):
            staged_max[0] = max(staged_max[0], Path(src).stat().st_size)
            return real_replace(src, dst)
        with patch.object(os, "replace", recording_replace):
            Builder(root, reproducible=True, workers=1).build(out)
        assert out.read_bytes() == control.read_bytes()
        with CMPCT(out) as ar:
            assert ar.verify() == 2
            assert ar.read("main.txt") == b"REPLACEMENT_ARCHIVE_B\n" * 400
        assert not list(t.glob(".target.cmpct.cmpct-stage-*"))
        results["successful_replacement"] = {
            "identical_complete_r24_archive": True,
            "bytes": out.stat().st_size, "sha256": digest(out),
            "temporary_payload_peak_bytes": staged_max[0],
            "historical_fresh_mode": oct(new_mode),
            "candidate_overwrite_mode": oct(stat.S_IMODE(out.stat().st_mode))}
        # A fresh output must have the same caller-umask-derived mode.
        fresh = t / "fresh-b.cmpct"
        Builder(root, reproducible=True, workers=1).build(fresh)
        assert fresh.read_bytes() == control.read_bytes()
        fresh_mode = stat.S_IMODE(fresh.stat().st_mode)
        assert fresh_mode == new_mode, (oct(fresh_mode), oct(new_mode))
        results["fresh_path"] = {"identical_complete_r24_archive": True,
                                 "same_mode": True, "mode": oct(fresh_mode)}
        # Repeat source-identical materializations; report raw timing without
        # treating same-process/cached filesystem wall as release evidence.
        timings = {"historical_wall_ns": [], "staged_wall_ns": []}
        for i in range(5):
            for cls, key in [(Historical, "historical_wall_ns"), (Builder, "staged_wall_ns")]:
                tmp = t / f"{key}-{i}.cmpct"
                start = time.perf_counter_ns()
                cls(root, reproducible=True, workers=1).build(tmp)
                timings[key].append(time.perf_counter_ns() - start)
                assert tmp.read_bytes() == control.read_bytes()
        results["research_only_timings"] = timings
    return results


if __name__ == "__main__":
    result = court()
    path = Path(os.environ.get("O75_JSON", "o75-evidence/result.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
