"""Independent two-OS-process serialization falsifier for unchanged CMPCT transactions.

Linux/fork-only research; the barrier and generation lock are test-only instrumentation.
Public APIs, physical archive bytes, predecessor links, and Reader semantics are genuine.
"""
from __future__ import annotations

from contextlib import ExitStack
from multiprocessing import get_context
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
import hashlib
import json
import os
import queue

from cmpct.core import Builder, CMPCT
import cmpct.transactions as tx


def archive_fixture(root: Path, name: str) -> Path:
    src = root / (name + "-input")
    src.mkdir()
    (src / "alpha.txt").write_bytes(b"alpha-original\n" * 30)
    (src / "beta.txt").write_bytes(b"beta-original\n" * 30)
    archive = root / (name + ".cmpct")
    Builder(src).build(archive)
    return archive


def snapshot(archive: Path) -> dict:
    with CMPCT(archive) as reader:
        n = sorted(reader.by)
        verified = reader.verify()
        data = {
            key: hashlib.sha256(reader.read(key)).hexdigest()
            for key in n if key.endswith(".txt")
        }
    assert verified >= 2
    return {
        "names": n,
        "payload_sha256": data,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "archive_bytes": archive.stat().st_size,
    }


def process_rename(archive: Path, old: str, new: str, gate, writer_lock, responses):
    """A genuine public transaction; instrumentation controls only thread/process scheduling."""
    original_generation = tx._append_generation

    class GatedCMPCT(CMPCT):
        def __exit__(self, *args):
            try:
                return super().__exit__(*args)
            finally:
                gate.wait(timeout=50)

    def whole_generation(*args, **kwargs):
        with writer_lock:
            result = original_generation(*args, **kwargs)
            responses.put({
                "kind": "generation",
                "pid": os.getpid(),
                "member": old,
                "prev_footer": int(args[2]),
                "new_footer": int(result[0]),
                "generation_bytes": int(result[1]),
            })
            return result

    try:
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(tx, "CMPCT", GatedCMPCT))
            stack.enter_context(mock.patch.object(tx, "_append_generation", whole_generation))
            result = tx.append_rename(archive, old, new)
        responses.put({"kind": "public_return", "pid": os.getpid(), "member": old, "success": result is None})
    except BaseException as exc:
        responses.put({"kind": "error", "pid": os.getpid(), "member": old, "exception": repr(exc)})
        raise


def main() -> None:
    if os.name != "posix":
        raise RuntimeError("This source-exact research court requires POSIX fork; no Windows claim.")
    ctx = get_context("fork")
    with TemporaryDirectory(prefix="cmpct-multiprocess-journal-") as scratch:
        base = Path(scratch)
        sequential = archive_fixture(base, "sequential")
        tx.append_rename(sequential, "alpha.txt", "alpha-new.txt")
        tx.append_rename(sequential, "beta.txt", "beta-new.txt")
        control = snapshot(sequential)
        assert set(control["names"]) == {"alpha-new.txt", "beta-new.txt"}

        concurrent = archive_fixture(base, "two-process")
        gate = ctx.Barrier(2, timeout=50)
        lock = ctx.Lock()
        responses = ctx.Queue()
        child_specs = [
            ("alpha.txt", "alpha-new.txt"),
            ("beta.txt", "beta-new.txt"),
        ]
        procs = [
            ctx.Process(
                target=process_rename,
                args=(concurrent, old, new, gate, lock, responses),
                name=f"cmpct-rename-{i}",
            )
            for i, (old, new) in enumerate(child_specs)
        ]
        for p in procs:
            p.start()
        for p in procs:
            p.join(timeout=80)
        for p in procs:
            if p.is_alive():
                p.terminate()
                p.join(timeout=5)
                raise RuntimeError(f"process timed out: {p.name}")
        exit_codes = [p.exitcode for p in procs]
        events = []
        try:
            for _ in range(4):
                events.append(responses.get(timeout=10))
        except queue.Empty as exc:
            raise AssertionError(f"missing child results: {events!r}, exit={exit_codes!r}") from exc
        if any(code != 0 for code in exit_codes) or any(e["kind"] == "error" for e in events):
            raise AssertionError(f"child error: exit={exit_codes!r}, events={events!r}")

        commits = [x for x in events if x["kind"] == "generation"]
        returns = [x for x in events if x["kind"] == "public_return"]
        assert len(commits) == 2 and len(returns) == 2, events
        assert all(x["success"] for x in returns), returns
        assert commits[0]["pid"] != commits[1]["pid"], commits
        assert commits[0]["prev_footer"] == commits[1]["prev_footer"], commits
        assert commits[0]["new_footer"] < commits[1]["new_footer"], commits

        actual = snapshot(concurrent)
        survived = [new for _, new in child_specs if new in actual["names"]]
        lost = [new for _, new in child_specs if new not in actual["names"]]
        decision = (
            "TWO_PROCESS_SILENT_LOST_UPDATE_WITH_SERIALIZED_GENERATIONS"
            if len(survived) == 1 and len(lost) == 1
            else "HYPOTHESIS_NOT_CONFIRMED"
        )
        receipt = {
            "source_writer_git_blob": "964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c",
            "evidence_tier": "Linux POSIX two-process installed-package scientific falsifier",
            "decision": decision,
            "source_snapshots_forced_equal": True,
            "physical_whole_generation_interleaving_allowed": False,
            "process_exit_codes": exit_codes,
            "sequential": control,
            "two_process": actual,
            "generation_events": commits,
            "successful_public_returns": len(returns),
            "survived_renames": survived,
            "lost_renames": lost,
            "scope_limit": (
                "Unpromised multiwriter support; no source edit; Windows/NFS/path replacement "
                "or independent archive-inode mutation beyond this controlled schedule not measured."
            ),
        }
        print(json.dumps(receipt, indent=2, sort_keys=True))
        assert decision == "TWO_PROCESS_SILENT_LOST_UPDATE_WITH_SERIALIZED_GENERATIONS", decision


if __name__ == "__main__":
    main()
