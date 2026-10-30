#!/usr/bin/env python3
"""J24G59: reachability court for J24G58's >=16-op indexed replay.

Exact source identity, real Builder/Writer committed r24 footers, independent wire
decode, and a separate explicitly synthetic multi-op control. Not a product benchmark.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import time

import msgpack
import zstandard

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct import journal_replay as jr
from cmpct import transactions as tx
from cmpct.codec import FMAGIC, FTR

EXPECTED_INDEXED_BLOB = "ba5ac2d01be9757651576a6fb5d640c4d212a62a"
EXPECTED_WRITER_BLOB = "3eef7fdc3f6deca5ddd6d9edf1292c7e2c864f11"


def git_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def physical_footer(path: Path, offset: int) -> dict:
    """Separate zstandard/MessagePack wire inspection; do not call CMPCT decoder."""
    size = path.stat().st_size
    assert 0 < offset <= size - FTR.size, ("invalid footer offset", offset, size)
    with path.open("rb") as f:
        f.seek(offset)
        raw = f.read(FTR.size)
        assert len(raw) == FTR.size
        magic, kind, codec, flags, reserved, csize, usize, prev, digest = FTR.unpack(raw)
        assert (magic, flags, reserved) == (FMAGIC, 0, 0)
        assert kind in (0, 1) and codec in (0, 1)
        assert 0 < csize <= offset
        f.seek(offset - csize)
        encoded = f.read(csize)
        assert len(encoded) == csize
        payload = encoded if codec == 0 else zstandard.ZstdDecompressor().decompress(
            encoded, max_output_size=usize
        )
        assert len(payload) == usize and hashlib.sha256(payload).digest() == digest
        document = msgpack.unpackb(payload, raw=False)
        assert isinstance(document, dict)
        width = None if kind == 0 else len(document["ops"])
        if kind == 1:
            assert isinstance(document["ops"], list)
        return {
            "kind": int(kind),
            "codec": int(codec),
            "ops_width": width,
            "footer_position": int(offset),
            "previous_footer": int(prev),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "payload_bytes": len(payload),
        }


def state(path: Path, label: str) -> dict:
    with CMPCT(path) as ar:
        index_files = len(ar.files)
        footer = ar.latest_footer_pos
        depth = ar.delta_depth
    info = physical_footer(path, footer)
    return {
        "label": label, "archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "archive_bytes": path.stat().st_size,
        "files": index_files, "reader_delta_depth": depth, **info,
    }


@contextlib.contextmanager
def instrument_index_admission():
    """Count real Reader calls into the candidate's indexed dispatcher."""
    calls = []
    original = jr._try_indexed_row_mutations

    def observed(rows, ops, lineage, max_files):
        before = len(rows)
        used = original(rows, ops, lineage, max_files)
        calls.append({"row_count": before, "op_width": len(ops), "indexed": bool(used)})
        return used

    jr._try_indexed_row_mutations = observed
    try:
        yield calls
    finally:
        jr._try_indexed_row_mutations = original


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    assert git_blob(repo / "src/cmpct/journal_replay.py") == EXPECTED_INDEXED_BLOB
    assert git_blob(repo / "src/cmpct/transactions.py") == EXPECTED_WRITER_BLOB
    assert (repo / "src/cmpct/journal_replay.py").read_bytes() == Path(jr.__file__).read_bytes()
    assert (repo / "src/cmpct/transactions.py").read_bytes() == Path(tx.__file__).read_bytes()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()

    records = []
    observations = {}
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g59-") as temporary:
        root = Path(temporary)
        source = root / "source"
        source.mkdir()
        for i in range(80):
            (source / f"f{i:02d}.txt").write_bytes((f"record-{i:02d}-".encode()) * 4)
        archive = root / "ordinary.cmpct"
        Builder(source, workers=1, reproducible=True).build(archive)
        records.append(state(archive, "builder-checkpoint"))
        assert records[-1]["kind"] == 0

        replacement = root / "replacement.txt"
        replacement.write_bytes(b"replace existing generic file")
        tx.append_update(archive, "f00.txt", replacement)
        records.append(state(archive, "writer-replace-existing"))
        tx.append_update(archive, "new.txt", replacement)
        records.append(state(archive, "writer-insert-new"))
        tx.append_delete(archive, "f01.txt")
        records.append(state(archive, "writer-delete"))
        tx.append_rename(archive, "f02.txt", "r02.txt")
        records.append(state(archive, "writer-rename"))

        # The 64th operation must emit a complete checkpoint, never a 64-op delta.
        snapshot63 = root / "ordinary-63.cmpct"
        snapshot64 = root / "ordinary-64.cmpct"
        for i in range(3, 63):
            tx.append_rename(archive, f"f{i:02d}.txt", f"r{i:02d}.txt")
            step = i + 2  # Four initial ops, then i=3 is the fifth.
            record = state(archive, f"writer-rename-{step:02d}")
            records.append(record)
            if step == 63:
                shutil.copyfile(archive, snapshot63)
            if step == 64:
                shutil.copyfile(archive, snapshot64)
        assert snapshot63.is_file() and snapshot64.is_file()
        assert len(records) == 65  # Builder checkpoint plus exactly 64 mutations.

        tx.append_rename(archive, "f63.txt", "r63.txt")
        records.append(state(archive, "writer-post-checkpoint-65"))
        assert len(records) == 66
        assert all(r["ops_width"] == 1 for r in records if r["kind"] == 1)
        assert sum(r["kind"] == 0 for r in records) == 2
        assert records[63]["kind"] == 1 and records[63]["reader_delta_depth"] == 63
        assert records[64]["kind"] == 0 and records[64]["reader_delta_depth"] == 0
        assert records[65]["kind"] == 1 and records[65]["reader_delta_depth"] == 1

        # These real Readers replay one-op generations; 64th op checkpoints.
        for label, candidate, expected_depth in (
            ("63_delta_chain", snapshot63, 63),
            ("64_checkpoint", snapshot64, 0),
            ("post_checkpoint_single_delta", archive, 1),
        ):
            with instrument_index_admission() as calls:
                before = time.perf_counter_ns()
                with CMPCT(candidate) as ar:
                    assert ar.delta_depth == expected_depth
                    assert ar.verify() == 80
                wall_ns = time.perf_counter_ns() - before
            observations[label] = {"calls": calls, "reader_open_plus_verify_wall_ns": wall_ns}
            assert len(calls) == expected_depth, (label, calls)
            assert all(c["op_width"] == 1 and not c["indexed"] for c in calls), (label, calls)

        # Strong opposite-branch control: an explicitly synthetic, structurally valid
        # 20-op signed generation is reachable to the decoder but is NOT emitted by
        # any public Writer operation above. No release/product speed credit.
        synthetic = root / "synthetic-20op.cmpct"
        shutil.copyfile(snapshot64, synthetic)
        with CMPCT(synthetic) as ar:
            previous = ar.latest_footer_pos
        operations = [["ren", f"f{i:02d}.txt", f"s{i:02d}.txt"] for i in range(64, 84)
                      if i < 80]
        # Exactly 16 old f64..f79 rows, all still exist; additionally rename 4
        # untouched existing r02..r05 rows, totaling 20 noncolliding changes.
        operations += [["ren", f"r{i:02d}.txt", f"t{i:02d}.txt"] for i in range(2, 6)]
        assert len(operations) == 20
        tx._append_generation(synthetic, {"blobs": [], "ops": operations}, previous)
        physical = state(synthetic, "synthetic-multiop-positive-control")
        assert physical["kind"] == 1 and physical["ops_width"] == 20
        with instrument_index_admission() as calls:
            with CMPCT(synthetic) as ar:
                assert ar.verify() == 80
                assert "s64.txt" in ar.by and "t02.txt" in ar.by
        assert len(calls) == 1 and calls[0]["op_width"] == 20 and calls[0]["indexed"]
        observations["synthetic_multiop"] = {"calls": calls, "physical_footer": physical}

    report = {
        "decision": "ORDINARY_WRITER_FAST_PATH_NOT_REACHED",
        "source_head": head, "indexed_blob": EXPECTED_INDEXED_BLOB,
        "writer_blob": EXPECTED_WRITER_BLOB, "host": platform.platform(),
        "python": platform.python_version(),
        "public_mutation_apis": ["append_update replace", "append_update insert",
                                 "append_delete", "append_rename", "64th operation checkpoint"],
        "ordinary_footer_records": records,
        "reader_index_dispatch": observations,
        "limits": "Only current documented public mutation functions, Linux-like host run, 80-member deterministic tree; other future writers may batch."
    }
    output = Path(os.environ.get("J24G59_RESULT", "evidence/j24g59-result.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("J24G59_DECISION", report["decision"])
    print("J24G59_SOURCE_HEAD", head)
    print("J24G59_SHA256", hashlib.sha256(output.read_bytes()).hexdigest())
    print("J24G59_ORDINARY_DELTAS", sum(r["kind"] == 1 for r in records))
    print("J24G59_SYNTHETIC_CONTROL_INDEXED", observations["synthetic_multiop"]["calls"])
    print("J24G59_EVIDENCE", output)


if __name__ == "__main__":
    main()
