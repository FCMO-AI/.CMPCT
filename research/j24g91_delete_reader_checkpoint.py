#!/usr/bin/env python3
"""J24G91 research-only physical r24 DELETE replay vs same-index checkpoint.

The private class is a narrow optimistic control, not the #823 shipping Reader.
It preserves the actual CMPCT footer decoder and delegates noneligible inputs.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

import msgpack

from cmpct.reader import CMPCT
from cmpct.transactions import append_rename
from j24g90_terminal_checkpoint import (
    FOOTER, make_court, check_semantics, digest, index_fingerprint, source_receipt
)

PREREG = "78d8ae137cb83ec1846c4a07b8cc7cda0c2bb6d2"
BASE_READER_SHA = "e716233403dabd0966863c45635e18fa5ac6afb8"
NUMBERS = (4096, 8192)
COLUMNS = ("reference_A", "owned_A", "reference_B", "owned_B", "reference_C", "owned_C")


def attest():
    root = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    subprocess.run(["git", "merge-base", "--is-ancestor", PREREG, head],
                   cwd=root, check=True)
    actual = subprocess.check_output(["git", "rev-parse", "HEAD:src/cmpct/reader.py"],
                                     cwd=root, text=True).strip()
    assert actual == BASE_READER_SHA, (actual, BASE_READER_SHA)
    inherited = source_receipt()
    own_blob = subprocess.check_output(
        ["git", "rev-parse", "HEAD:research/j24g91_delete_reader_checkpoint.py"],
        cwd=root, text=True).strip()
    return {"head": head, "prereg": PREREG, "reader_git_blob": actual,
            "instrument_git_blob": own_blob, "inherited": inherited}


class OwnedDeleteCMPCT(CMPCT):
    """Single freshly-decoded index owns its file rows; eligible DELETE chains only.

    A public caller or shared cache must never pass retained aliases to this method.
    This test subclass never mutates the public Reader's source implementation.
    """
    def _index_from_footer(self, footer_pos):
        chain = []
        pos, depth, seen = footer_pos, 0, set()
        while pos and pos not in seen:
            seen.add(pos)
            generation = self._decode_generation_payload(pos)
            if generation is None:
                return None
            kind, payload, prev = generation
            if kind == 0:
                index = msgpack.unpackb(payload, raw=False)
                if not chain:
                    self._research_route = "checkpoint"
                    return index, depth
                # Conservatively limit this oracle to exactly the J24G90 shape.
                # Anything requiring positional fsmeta rekeying or new physical
                # blobs executes inherited r24 semantics with no shortcut.
                fsmeta = index.get("fsmeta") or {}
                clean_meta = (isinstance(fsmeta, dict)
                              and not fsmeta.get("owner_overrides")
                              and not fsmeta.get("xattrs"))
                file_rows = index.get("files")
                if (not clean_meta or not isinstance(file_rows, list)
                        or any(not isinstance(row, list) or not row
                               or not isinstance(row[0], str) for row in file_rows)):
                    self._research_route = "inherited-fallback"
                    return super()._index_from_footer(footer_pos)
                deleted = set()
                eligible = True
                for delta in reversed(chain):
                    if (not isinstance(delta, dict) or delta.get("blobs")
                            or len(delta.get("ops", [])) != 1):
                        eligible = False
                        break
                    op = delta["ops"][0]
                    if (not isinstance(op, list) or len(op) != 2
                            or op[0] != "del" or not isinstance(op[1], str)):
                        eligible = False
                        break
                    deleted.add(op[1])
                if not eligible:
                    self._research_route = "inherited-fallback"
                    return super()._index_from_footer(footer_pos)
                index["files"] = [row for row in file_rows if row[0] not in deleted]
                self._research_route = "onepass-owned-delete"
                return index, depth
            if kind != 1:
                return None
            try:
                chain.append(msgpack.unpackb(payload, raw=False))
            except (ValueError, TypeError):
                return None
            depth += 1
            pos = prev
        return None


def make_reader(label):
    return OwnedDeleteCMPCT if label.startswith("owned_") else CMPCT


def assert_parity(case, n):
    names = sorted(case["expected"])
    expected_index_sha = case["index_sha256"]
    before = {key: digest(path.read_bytes()) for key, path in case["paths"].items()}
    proof = {}
    inherited = check_semantics(case)
    for label in COLUMNS:
        path = case["paths"][label[-1]]
        cls = make_reader(label)
        with cls(path) as reader:
            assert reader.delta_depth == (0 if label.endswith("B") else 63)
            assert index_fingerprint(reader.index) == expected_index_sha
            assert set(reader.by) == set(names)
            assert reader.verify() == len(names)
            # Independent expected payloads were generated from this formula in
            # source-identical J24G90, not from a second Reader.
            for path_name in names:
                ordinal = int(path_name[1:6])
                data = hashlib.sha256(f"j24g90-{n}-{ordinal}".encode()).digest()
                assert reader.read(path_name) == data, (label, path_name)
            route = getattr(reader, "_research_route", "public")
            if label == "owned_A" or label == "owned_C":
                assert route == "onepass-owned-delete", (label, route)
            if label == "owned_B":
                assert route == "checkpoint", (label, route)
            proof[label] = {"depth": reader.delta_depth,
                            "index_sha256": index_fingerprint(reader.index),
                            "latest_footer": reader.latest_footer_pos,
                            "verified": len(names), "research_route": route}
    assert before == {key: digest(path.read_bytes())
                      for key, path in case["paths"].items()}, "Reader mutated archive"
    # Exercise a genuine signed RENAME after the DELETE-only history. It must
    # delegate to the public Reader instead of treating mixed mutations as DELETE.
    with tempfile.TemporaryDirectory(prefix="j24g91-fallback-") as td:
        altered = Path(td) / "noneligible.cmpct"
        shutil.copyfile(case["paths"]["A"], altered)
        # At depth 63, public append_rename would AUTO-CHECKPOINT and fail
        # to exercise the mixed-delta fallback. Retain the genuine signed
        # generation-62 prefix, then append one real RENAME as generation 63.
        # This preserves the true public Writer semantic path.
        with altered.open("r+b") as stream:
            stream.seek(-FOOTER.size, os.SEEK_END)
            tail = FOOTER.unpack(stream.read(FOOTER.size))
            assert tail[0] == b"CMPTF24\x00"
            previous_pos = tail[7]
            assert 0 < previous_pos < stream.tell() - FOOTER.size
            stream.truncate(previous_pos + FOOTER.size)
        old = "f00100.dat"
        new = "j24g91-renamed.dat"
        append_rename(altered, old, new)
        with CMPCT(altered) as reference, OwnedDeleteCMPCT(altered) as private:
            assert private._research_route == "inherited-fallback"
            assert index_fingerprint(reference.index) == index_fingerprint(private.index)
            assert reference.read(new) == private.read(new)
            assert reference.verify() == private.verify() == len(names) + 1
            negative = {"route": private._research_route,
                        "semantic_hash": index_fingerprint(private.index),
                        "signed_rename": [old, new]}
    return {"public_inherited": inherited, "comparison": proof,
            "actual_fallback_negative": negative, "archives_sha256_unchanged": before}


def timed(label, case):
    cls = make_reader(label)
    path = case["paths"][label[-1]]
    batch = 64 if sys.platform == "win32" else 1
    begin_wall, begin_cpu = time.perf_counter_ns(), time.process_time_ns()
    routes = set()
    for _ in range(batch):
        with cls(path) as reader:
            assert len(reader.by) > 0
            routes.add(getattr(reader, "_research_route", "public"))
    assert len(routes) == 1, (label, routes)
    return {"wall_ns": (time.perf_counter_ns() - begin_wall) / batch,
            "cpu_ns": (time.process_time_ns() - begin_cpu) / batch,
            "batch": batch, "route": routes.pop()}


def measure(case):
    for label in COLUMNS:
        for _ in range(2):
            timed(label, case)
    samples = []
    for block in range(2):
        for shift in range(len(COLUMNS)):
            ordering = list(COLUMNS[shift:]) + list(COLUMNS[:shift])
            if block == 1:
                ordering.reverse()
            for label in ordering:
                samples.append({"block": block, "shift": shift,
                                "sequence": ",".join(ordering),
                                "variant": label, **timed(label, case)})
    assert len(samples) == 72
    medians = {metric: {label: statistics.median(
        row[metric] for row in samples if row["variant"] == label)
        for label in COLUMNS} for metric in ("wall_ns", "cpu_ns")}
    allocations = {}
    for label in COLUMNS:
        peaks = []
        for _ in range(2):
            tracemalloc.start()
            tracemalloc.reset_peak()
            timed(label, case)
            peaks.append(tracemalloc.get_traced_memory()[1])
            tracemalloc.stop()
        allocations[label] = peaks
    wall, cpu = medians["wall_ns"], medians["cpu_ns"]
    return {"raw": samples, "medians": medians, "traced_python_alloc_peak": allocations,
            "public_A_over_owned_A_wall": wall["reference_A"] / wall["owned_A"],
            "checkpoint_B_over_owned_A_wall": wall["owned_A"] / wall["reference_B"],
            "checkpoint_B_over_owned_A_cpu": cpu["owned_A"] / cpu["reference_B"],
            "recovered_owned_C_over_owned_A_wall": wall["owned_C"] / wall["owned_A"]}


def main():
    output = Path(os.environ.get("J24G91_EVIDENCE", "evidence/j24g91"))
    output.mkdir(parents=True, exist_ok=True)
    evidence = {"schema": "cmpct-j24g91-physical-discriminator-v1",
                "source": attest(), "status": "RUNNING",
                "host": platform.platform(), "python": platform.python_version(),
                "platform": sys.platform, "product_credit": 0, "cases": {}}
    try:
        with tempfile.TemporaryDirectory(prefix="cmpct-j24g91-") as td:
            for n in NUMBERS:
                case = make_court(Path(td), n)
                parity = assert_parity(case, n)
                measured = measure(case)
                evidence["cases"][str(n)] = {
                    "physics": case["physical"], "checkpoint_extra_bytes": case["checkpoint_extra_bytes"],
                    "checkpoint_overhead_ratio": case["checkpoint_overhead_ratio"],
                    "semantic_proof": parity, "timing": measured}
                for label, path in case["paths"].items():
                    saved = output / f"{n}-{label}.cmpct"
                    shutil.copyfile(path, saved)
                    assert digest(saved.read_bytes()) == case["physical"][label]["sha256"]
        evidence["H_integrity"] = True
        evidence["H_replay"] = all(
            x["timing"]["public_A_over_owned_A_wall"] >= 2.0
            for x in evidence["cases"].values())
        evidence["H_checkpoint_marginality"] = all(
            x["timing"]["checkpoint_B_over_owned_A_wall"] <= 1.50
            for x in evidence["cases"].values())
        evidence["H_checkpoint_survives"] = all(
            x["timing"]["checkpoint_B_over_owned_A_wall"] >= 2.0
            for x in evidence["cases"].values())
        evidence["status"] = "PASS"
    except BaseException as exc:
        evidence["status"] = "FAIL"
        evidence["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        (output / "receipt.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n")
        print("J24G91_REPORT", json.dumps({
            "status": evidence["status"],
            "H_replay": evidence.get("H_replay"),
            "H_checkpoint_marginality": evidence.get("H_checkpoint_marginality"),
            "cases": {key: {
                "wall_ns": value["timing"]["medians"]["wall_ns"],
                "checkpoint_extra_bytes": value["checkpoint_extra_bytes"],
                "ratio": value["timing"]["checkpoint_B_over_owned_A_wall"],
            } for key, value in evidence["cases"].items()}
        }, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 1:
        raise SystemExit("No positional arguments")
    main()
