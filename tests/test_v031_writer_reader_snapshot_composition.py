"""Cross-plane Writer lease × Reader snapshot integration, source-exact PR #298.

A Reader opened before two durable append operations must retain the old logical
snapshot while a subsequently opened Reader sees *both* successful changes.
This is intentionally additional to the immutable PR #295 loss-update court;
the latter does not hold an unrelated Reader open across concurrent commits.
"""
from __future__ import annotations

import multiprocessing as mp
import os
from pathlib import Path
from queue import Empty

import pytest

from cmpct.core import Builder, CMPCT
from cmpct.transactions import append_rename

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX lease candidate only")


def _rename_on_archive(path: str, old: str, new: str, result_queue) -> None:
    try:
        append_rename(Path(path), old, new)
        result_queue.put(("ok", old, new))
    except BaseException as exc:
        result_queue.put(("error", old, type(exc).__name__, str(exc)))
        raise


def test_active_reader_snapshot_survives_two_successful_cooperative_writer_commits(tmp_path):
    """Old mmap/index remains exact, new index contains both reported updates."""
    source = tmp_path / "tree"
    source.mkdir()
    alpha = (b"old alpha verified payload\n" * 97)
    beta = (b"old beta verified payload\n" * 101)
    (source / "alpha.txt").write_bytes(alpha)
    (source / "beta.txt").write_bytes(beta)
    archive = tmp_path / "archive.cmpct"
    Builder(source).build(archive)

    ctx = mp.get_context("fork")
    results = ctx.Queue()
    with CMPCT(archive) as old_reader:
        assert old_reader.read("alpha.txt") == alpha
        assert old_reader.read("beta.txt") == beta
        jobs = [
            ctx.Process(target=_rename_on_archive,
                        args=(str(archive), "alpha.txt", "alpha-final.txt", results)),
            ctx.Process(target=_rename_on_archive,
                        args=(str(archive), "beta.txt", "beta-final.txt", results)),
        ]
        for job in jobs:
            job.start()
        try:
            for job in jobs:
                job.join(timeout=35)
            if any(job.is_alive() for job in jobs):
                pytest.fail("cooperative writers did not complete in bounded time")
            assert all(job.exitcode == 0 for job in jobs), [
                job.exitcode for job in jobs
            ]
            outcomes = []
            for _ in jobs:
                try:
                    outcomes.append(results.get(timeout=4))
                except Empty as exc:
                    raise AssertionError("successful writer lacked completion receipt") from exc
            assert all(x[0] == "ok" for x in outcomes), outcomes
            assert {x[1] for x in outcomes} == {"alpha.txt", "beta.txt"}

            # An already-open Reader must not follow a new footer silently.
            assert old_reader.read("alpha.txt") == alpha
            assert old_reader.read("beta.txt") == beta
            old_reader.verify()

            # A fresh Reader must see BOTH distinct successful transitions.
            with CMPCT(archive) as committed:
                assert committed.read("alpha-final.txt") == alpha
                assert committed.read("beta-final.txt") == beta
                for vanished in ("alpha.txt", "beta.txt"):
                    with pytest.raises(KeyError):
                        committed.read(vanished)
                committed.verify()
                extracted = tmp_path / "extracted"
                committed.extractall(extracted)
            assert (extracted / "alpha-final.txt").read_bytes() == alpha
            assert (extracted / "beta-final.txt").read_bytes() == beta
        finally:
            for job in jobs:
                if job.is_alive():
                    job.terminate()
                    job.join(timeout=5)
            results.close()
            results.join_thread()
