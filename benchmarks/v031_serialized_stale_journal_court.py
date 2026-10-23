"""Source-exact scientific falsifier: two successful serialized journal appends with stale snapshots.

Research-only. It deliberately serializes entire generation writes; it does NOT implement a
lock for the transaction's complete read-modify-commit lifetime. That distinction is the question.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier, Lock, current_thread
from unittest import mock
import hashlib
import json

from cmpct.core import Builder, CMPCT
import cmpct.transactions as tx

ORIGINAL_WRITER_GIT_BLOB = "964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c"


def make_archive(base: Path, tag: str) -> Path:
    root = base / (tag + "-src")
    root.mkdir()
    (root / "alpha.txt").write_bytes(b"alpha-original\n" * 30)
    (root / "beta.txt").write_bytes(b"beta-original\n" * 30)
    archive = base / (tag + ".cmpct")
    Builder(root).build(archive)
    return archive


def observe(archive: Path) -> dict:
    with CMPCT(archive) as reader:
        names = sorted(reader.by)
        assert reader.verify() >= 2
        payloads = {
            name: hashlib.sha256(reader.read(name)).hexdigest()
            for name in names if name.endswith(".txt")
        }
    return {
        "names": names,
        "payload_sha256": payloads,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "archive_bytes": archive.stat().st_size,
    }


def main() -> None:
    with TemporaryDirectory(prefix="cmpct-stale-journal-") as tmp:
        base = Path(tmp)
        sequential = make_archive(base, "sequential")
        tx.append_rename(sequential, "alpha.txt", "alpha-new.txt")
        tx.append_rename(sequential, "beta.txt", "beta-new.txt")
        seq_observation = observe(sequential)
        assert "alpha-new.txt" in seq_observation["names"]
        assert "beta-new.txt" in seq_observation["names"]
        assert "alpha.txt" not in seq_observation["names"]
        assert "beta.txt" not in seq_observation["names"]

        concurrent = make_archive(base, "controlled")
        gate = Barrier(2, timeout=45)
        writer_lock = Lock()
        commits = []
        original_generation = tx._append_generation

        class SnapshotGatedCMPCT(CMPCT):
            def __exit__(self, *args):
                try:
                    return super().__exit__(*args)
                finally:
                    # Both real public APIs finish their original index/footer snapshot
                    # before either is permitted to append even one byte.
                    gate.wait(timeout=45)

        def serialized_whole_generation(*args, **kwargs):
            # Remove physical write interleaving as an alternative explanation.
            with writer_lock:
                prev_footer = args[2]
                output = original_generation(*args, **kwargs)
                commits.append({
                    "thread": current_thread().name,
                    "prev_footer": int(prev_footer),
                    "new_footer": int(output[0]),
                    "generation_bytes": int(output[1]),
                })
                return output

        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(tx, "CMPCT", SnapshotGatedCMPCT))
            stack.enter_context(mock.patch.object(tx, "_append_generation", serialized_whole_generation))
            with ThreadPoolExecutor(max_workers=2, thread_name_prefix="rename") as pool:
                futures = [
                    pool.submit(tx.append_rename, concurrent, "alpha.txt", "alpha-new.txt"),
                    pool.submit(tx.append_rename, concurrent, "beta.txt", "beta-new.txt"),
                ]
                # Exceptions here are failures of the proposed lost-update hypothesis,
                # not a success disguised as a corruption result.
                successful_returns = [future.result(timeout=90) for future in futures]

        assert len(commits) == 2, commits
        assert commits[0]["prev_footer"] == commits[1]["prev_footer"], commits
        assert commits[0]["new_footer"] < commits[1]["new_footer"], commits
        assert successful_returns == [None, None], successful_returns
        controlled_observation = observe(concurrent)
        survived = [
            name for name in ("alpha-new.txt", "beta-new.txt")
            if name in controlled_observation["names"]
        ]
        missing = [
            name for name in ("alpha-new.txt", "beta-new.txt")
            if name not in controlled_observation["names"]
        ]
        # Exactly one successful public mutation disappeared even though all
        # physical generation appends were serialized and the final archive verifies.
        decision = (
            "SILENT_LOST_UPDATE_WITH_SERIALIZED_GENERATIONS"
            if len(survived) == 1 and len(missing) == 1
            else "HYPOTHESIS_NOT_CONFIRMED"
        )
        result = {
            "source_writer_git_blob": ORIGINAL_WRITER_GIT_BLOB,
            "scientific_tier": "source-exact hostile concurrency falsifier",
            "sequential_control": seq_observation,
            "concurrent_control": controlled_observation,
            "successful_public_returns": 2,
            "physical_append_interleaving_allowed": False,
            "commits": commits,
            "survived_renames": survived,
            "missing_renames": missing,
            "decision": decision,
            "contract_limitation": (
                "This proves a single-writer ownership assumption under forced concurrent "
                "calls, not an established promise that multiwriter transactions are supported."
            ),
        }
        print(json.dumps(result, sort_keys=True, indent=2))
        assert decision == "SILENT_LOST_UPDATE_WITH_SERIALIZED_GENERATIONS", decision


if __name__ == "__main__":
    main()
