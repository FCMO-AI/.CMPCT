#!/usr/bin/env python3
"""J24G64: prospective MIXED + sparse-fsmeta cross-generation research oracle.

No product import monkeypatch, no archive emitted, no release claim.
Requires the exact inherited J24G57 journal_replay Git blob.
"""
from __future__ import annotations

import copy
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time
import tracemalloc

import msgpack
from cmpct.journal_replay import _apply_journal_ops, _validate_journal_ops

PARENT = "9dc765a902c0f5c424639caf9cdfd571cca2d6e6"
PREREG = "624eec80b90ec25bf22501f66b92b7a32e6b928b"
SOURCE_BLOB = "03743ca2a06c022c2ec64243a90fe373cf91e899"
SAMPLES = 8


def git_blob(data: bytes) -> str:
    data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def source_attestation() -> dict:
    root = Path(__file__).resolve().parents[1]
    import cmpct.journal_replay as mod
    expected = root / "src/cmpct/journal_replay.py"
    assert git_blob(expected.read_bytes()) == SOURCE_BLOB
    assert expected.read_bytes().replace(b"\r\n", b"\n") == (
        Path(mod.__file__).read_bytes().replace(b"\r\n", b"\n"))
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    for ancestor in (PARENT, PREREG):
        assert subprocess.run(["git", "merge-base", "--is-ancestor", ancestor, head],
                              cwd=root, stdout=subprocess.DEVNULL).returncode == 0
    git_id = subprocess.check_output(["git", "rev-parse", "HEAD:src/cmpct/journal_replay.py"],
                                     cwd=root, text=True).strip()
    assert git_id == SOURCE_BLOB
    return {"head": head, "baseline_source_blob": SOURCE_BLOB, "prereg": PREREG}


def reference(base: dict, deltas: list[dict], *, max_files=None) -> dict:
    """The exact inherited function, one call per physical generation.

    Deepcopy once per invocation to prevent aliasing the external research input.
    Physical Reader owns distinct decoded payloads for each signed generation.
    """
    state = copy.deepcopy(base)
    messages = copy.deepcopy(deltas)
    for delta in messages:
        state["blobs"].extend(delta.get("blobs", []))
        _apply_journal_ops(state, delta["ops"], max_files=max_files)
    return state


def admit(base, deltas, max_files):
    """Pure, conservative gate: every unsupported semantic shape uses baseline."""
    if (not isinstance(base, dict) or not isinstance(deltas, list) or not deltas
            or not isinstance(base.get("files"), list)
            or not isinstance(base.get("blobs"), list)):
        return False, "shape"
    rows = base["files"]
    if not all(isinstance(row, list) and row and isinstance(row[0], str) for row in rows):
        return False, "rows"
    names = [row[0] for row in rows]
    if names != sorted(names) or len(set(names)) != len(names):
        return False, "noncanonical-paths"
    fsmeta = base.get("fsmeta") or {}
    if not isinstance(fsmeta, dict):
        return False, "metadata-shape"
    for field in ("owner_overrides", "xattrs"):
        records = fsmeta.get(field, [])
        if not isinstance(records, list):
            return False, "metadata-shape"
        positions = []
        for entry in records:
            if (not isinstance(entry, list) or len(entry) < 2
                    or type(entry[0]) is not int or not (0 <= entry[0] < len(rows))):
                return False, "invalid-ordinal"
            positions.append(entry[0])
        if positions != sorted(set(positions)):
            return False, "noncanonical-ordinals"

    live = set(names)
    for delta in deltas:
        if not isinstance(delta, dict) or not isinstance(delta.get("blobs", []), list):
            return False, "delta-shape"
        ops = delta.get("ops")
        try:
            _validate_journal_ops(ops)
        except (ValueError, TypeError):
            return False, "grammar"
        if len(ops) != 1:
            return False, "not-one-operation"
        op = ops[0]
        kind = op[0]
        if kind == "ren":
            old, new = op[1:]
            if old not in live:
                return False, "rename-missing"
            if new != old and new in live:
                return False, "rename-collision"
            live.remove(old)
            live.add(new)
        elif kind == "del":
            if op[1] not in live:
                return False, "delete-missing"
            live.remove(op[1])
        elif kind == "put":
            path = op[1][0]
            live.add(path)
            if max_files is not None and len(live) > max_files:
                return False, "file-limit"
        else:
            return False, "opcode"
    return True, "mixed-one-op-sorted-sparse-metadata"


def factored(base, deltas, *, max_files=None):
    allowed, why = admit(base, deltas, max_files)
    if not allowed:
        return reference(base, deltas, max_files=max_files), "fallback:" + why
    state = copy.deepcopy(base)
    messages = copy.deepcopy(deltas)
    by_name = {row[0]: row for row in state["files"]}
    fsmeta = state.get("fsmeta") or {}
    fields = {}
    for field in ("owner_overrides", "xattrs"):
        fields[field] = {
            state["files"][entry[0]][0]: entry[1:]
            for entry in fsmeta.get(field, [])
        }
    for delta in messages:
        state["blobs"].extend(delta.get("blobs", []))
        op = delta["ops"][0]
        kind = op[0]
        if kind == "ren":
            old, new = op[1:]
            if old != new:
                row = by_name.pop(old)
                row[0] = new
                by_name[new] = row
                for identities in fields.values():
                    if old in identities:
                        identities[new] = identities.pop(old)
        elif kind == "del":
            path = op[1]
            del by_name[path]
            for identities in fields.values():
                identities.pop(path, None)
        else:
            row = op[1]
            by_name[row[0]] = row

    state["files"] = sorted(by_name.values(), key=lambda row: row[0])
    for field, identities in fields.items():
        if field in fsmeta:
            fsmeta[field] = [
                [i, *identities[row[0]]]
                for i, row in enumerate(state["files"]) if row[0] in identities
            ]
    return state, "factored"


def fingerprint(obj) -> str:
    return hashlib.sha256(msgpack.packb(obj, use_bin_type=True)).hexdigest()


def compare(base, deltas, max_files=None):
    before = fingerprint([base, deltas])
    try:
        expected = reference(base, deltas, max_files=max_files)
        err_original = None
    except Exception as exc:
        expected = None
        err_original = (type(exc).__name__, str(exc))
    try:
        got, route = factored(base, deltas, max_files=max_files)
        err_new = None
    except Exception as exc:
        got, route = None, "exception"
        err_new = (type(exc).__name__, str(exc))
    assert err_original == err_new, ("exception-parity", err_original, err_new, base, deltas)
    assert expected == got, ("index-parity", route, expected, got, base, deltas)
    if err_original is None:
        assert fingerprint(expected) == fingerprint(got), ("wire-parity", route)
    assert before == fingerprint([base, deltas]), ("input-mutation", route)
    return route if err_original is None else "matched-exception"


def make_case(seed: int, i: int):
    rng = random.Random(seed + i * 7919)
    n = rng.randint(2, 55)
    names = [f"p{j:03d}" for j in range(n)]
    rows = [[name, i, ["physical-id", j]] for j, name in enumerate(names)]
    mode = i % 17
    fsmeta = {"owner": [1000, 1000], "xattrs": [], "owner_overrides": []}
    if mode in (0, 1, 2, 3, 4, 8, 9, 12, 14, 15, 16):
        positions = sorted(rng.sample(range(n), min(n, 1 + n // 5)))
        fsmeta["xattrs"] = [[j, [[b"user.id", str(j).encode()]]] for j in positions]
        fsmeta["owner_overrides"] = [[j, 3000 + j, 4000 + j] for j in positions[::2]]
    if mode == 5:
        rows.append(copy.deepcopy(rows[-1]))
    if mode == 6:
        rows.reverse()
    if mode == 7:
        fsmeta["xattrs"] = [[n + 1, [[b"user.invalid", b"true"]]]]
    if mode == 10:
        fsmeta["owner_overrides"] = [[0, 1001, 1002], [0, 2001, 2002]]
    if mode == 11:
        fsmeta["xattrs"] = [[1, [[b"user.one", b"1"]]], [0, [[b"user.zero", b"0"]]]]
    if mode == 13:
        fsmeta["xattrs"] = [[True, [[b"user.bool", b"1"]]]]
    base = {"files": rows, "blobs": [], "fsmeta": fsmeta}
    live = list(names)
    deltas = []
    for step in range(rng.randint(1, 20)):
        opkind = rng.choice(("ren", "del", "put_existing", "put_new"))
        if not live:
            opkind = "put_new"
        if opkind == "ren":
            old = rng.choice(live)
            new = f"r{i:04d}_{step:02d}"
            op = ["ren", old, new]
            live.remove(old)
            live.append(new)
        elif opkind == "del":
            old = rng.choice(live)
            op = ["del", old]
            live.remove(old)
        elif opkind == "put_existing":
            old = rng.choice(live)
            op = ["put", [old, i, ["replaced", step], ["hardlink-opaque", old]]]
        else:
            new = f"a{i:04d}_{step:02d}"
            op = ["put", [new, i, ["created", step]]]
            live.append(new)
        if mode == 8 and step == 1:
            op = ["ren", "missing-source", "destination"]
        elif mode == 9 and step == 1:
            op = ["ren", live[0], live[-1]]
        elif mode == 12 and step == 1:
            op = ["del", "missing-delete"]
        elif mode == 14 and step == 1:
            op = ["future-op", "name"]
        elif mode == 15 and step == 1:
            op = ["put", ["fresh", 0]]
            deltas.append({"blobs": [], "ops": [op]})
        elif mode == 16 and step == 1:
            op = ["put", [f"overflow-{step}", 0]]
        deltas.append({"blobs": [["blob", step]] if step % 7 == 0 else [], "ops": [op]})
    limit = n + 2 if mode == 16 else None
    return base, deltas, limit


def differential():
    counts = {}
    for i in range(5000):
        base, deltas, limit = make_case(0xC0642026, i)
        route = compare(base, deltas, limit)
        counts[route] = counts.get(route, 0) + 1
    factored_count = counts.get("factored", 0)
    fallback_count = sum(n for key, n in counts.items() if key.startswith("fallback:"))
    assert factored_count > 500, counts
    assert fallback_count > 500, counts
    assert counts.get("matched-exception", 0) > 0, counts
    return counts


def targeted_semantic_edges():
    """Named adversaries against identity leakage and ordinal-rekey shortcuts."""
    initial = {
        "files": [["a", 1, ["opaque-hardlink", "b"]],
                  ["b", 2, ["opaque-hardlink", "a"]],
                  ["c", 3, ["regular", b"bytes"]]],
        "blobs": [["checkpoint-blob", 0]],
        "fsmeta": {
            "owner": [11, 12],
            "xattrs": [[0, [[b"user.a", b"first"]]],
                       [1, [[b"user.b", b"second"]]]],
            "owner_overrides": [[0, 111, 112], [2, 311, 312]],
        },
    }
    paths = {
        "delete-and-recreate-same-name": [
            ["del", "a"], ["put", ["a", 99, ["new-identity"]]]],
        "rename-then-reuse-old-name": [
            ["ren", "a", "z"], ["put", ["a", 99]], ["del", "c"]],
        "rename-return-cycle": [
            ["ren", "a", "z"], ["ren", "z", "a"], ["put", ["a", 99]]],
        "rename-transfer-metadata": [
            ["ren", "a", "z"], ["del", "b"], ["put", ["fresh", 99]]],
        "retain-metadata-on-replace": [
            ["put", ["a", 100]], ["ren", "a", "z"], ["put", ["z", 200]]],
        "delete-put-rename-recreate": [
            ["del", "a"], ["put", ["a", 100]], ["ren", "a", "z"],
            ["put", ["a", 101]]],
        "self-rename-no-rekey": [
            ["ren", "a", "a"], ["put", ["b", 100]], ["ren", "c", "c"]],
        "replace-only-retains-original-order": [
            ["put", ["a", 100]], ["put", ["c", 101]]],
        "collision-fallback": [
            ["ren", "a", "b"], ["put", ["b", 100]]],
        "missing-source-fallback": [
            ["ren", "absent", "z"], ["put", ["a", 100]]],
        "missing-delete-fallback": [
            ["del", "absent"], ["ren", "b", "z"]],
        "future-op-exact-failure": [
            ["put", ["a", 100]], ["future", "a"]],
        "file-limit-exact-failure": [
            ["put", ["new1", 100]], ["put", ["new2", 200]]],
        "multi-op-generation-fallback": [
            ["ren", "a", "z"], ["del", "b"]],
    }
    out = {}
    for title, operations in paths.items():
        if title == "multi-op-generation-fallback":
            deltas = [{"ops": operations, "blobs": []}]
        else:
            deltas = [{"ops": [op], "blobs": []} for op in operations]
        limit = 4 if title == "file-limit-exact-failure" else None
        route = compare(initial, deltas, limit)
        if title.endswith("-fallback"):
            assert route.startswith("fallback:"), (title, route)
        elif title.endswith("-exact-failure"):
            assert route == "matched-exception", (title, route)
        else:
            assert route == "factored", (title, route)
        out[title] = route
    assert len(out) == 14
    return out


def large_case():
    n, depth = 2048, 63
    rows = [[f"p{i:04d}", i, ["immutable-physical-record", i]] for i in range(n)]
    positions = list(range(0, n, 29))
    base = {"files": rows, "blobs": [],
            "fsmeta": {"owner": [1000, 1000],
                       "xattrs": [[i, [[b"user.bound", str(i).encode()]]] for i in positions],
                       "owner_overrides": [[i, 1000 + i, 2000 + i] for i in positions[::2]]}}
    deltas = []
    for step in range(depth):
        group, which = divmod(step, 4)
        if which == 0:
            op = ["ren", f"p{group:04d}", f"r{group:04d}"]
        elif which == 1:
            op = ["del", f"p{64 + group:04d}"]
        elif which == 2:
            op = ["put", [f"new{group:04d}", step, ["new-physical-record", group]]]
        else:
            op = ["put", [f"p{128 + group:04d}", step, ["replacement", group]]]
        deltas.append({"ops": [op], "blobs": [["delta-blob", step]]})
    assert len(deltas) == depth
    assert compare(base, deltas) == "factored"
    return base, deltas


def measure(base, deltas, variant):
    gc.collect()
    w0, c0 = time.perf_counter_ns(), time.process_time_ns()
    if variant == "reference":
        result = reference(base, deltas)
    else:
        result, route = factored(base, deltas)
        assert route == "factored"
    wall = time.perf_counter_ns() - w0
    cpu = time.process_time_ns() - c0
    return result, {"variant": variant, "wall_ns": wall, "cpu_ns": cpu}


def physical_mixed_writer_check():
    """J24G64b: actual Builder/public Writer 63x mixed signed-archive oracle.

    Run after replay microtiming: archive generation must not affect A/B cache
    state or get mistaken for an end-to-end measured speedup.
    """
    import shutil
    import tempfile
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.validation import preflight_archive
    from cmpct import transactions as tx
    from j24g60_single_delta_chain_court import footer_chain, sha256_file, verify_source
    from j24g62_crossgen_rename_oracle import read_wire

    physical_sources = verify_source()
    expected = {
        f"f{i:04d}.dat": hashlib.sha256(f"mixed-physical-{i}".encode()).digest() * 2
        for i in range(128)
    }
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g64b-") as temp:
        root = Path(temp)
        tree = root / "tree"
        tree.mkdir()
        for name, content in expected.items():
            (tree / name).write_bytes(content)
        archive = root / "mixed-public-writer.cmpct"
        Builder(tree, workers=1, reproducible=True).build(archive)
        assert len(footer_chain(archive)) == 1
        for i in range(21):
            old, new = f"f{i:04d}.dat", f"r{i:04d}.dat"
            tx.append_rename(archive, old, new)
            expected[new] = expected.pop(old)

            removed = f"f{32+i:04d}.dat"
            tx.append_delete(archive, removed)
            del expected[removed]

            replacement = hashlib.sha256(f"changed-physical-{i}".encode()).digest() * 2
            source = root / f"update-source-{i:04d}.dat"
            source.write_bytes(replacement)
            target = (f"f{64+i:04d}.dat" if i % 2 == 0
                      else f"new{i:04d}.dat")
            tx.append_update(archive, target, source)
            expected[target] = replacement

        before_sha = sha256_file(archive)
        wire = footer_chain(archive)
        assert len(wire) == 64
        assert all(entry["kind"] == 1 and entry["op_width"] == 1
                   for entry in wire[:-1])
        assert wire[-1]["kind"] == 0
        base, deltas = read_wire(archive)
        assert len(deltas) == 63
        names = [delta["ops"][0][0] for delta in deltas]
        assert names.count("ren") == names.count("del") == names.count("put") == 21
        baseline = reference(base, deltas)
        candidate, route = factored(base, deltas)
        assert route == "factored", ("physical mixed candidate not admitted", route)
        assert candidate == baseline
        assert fingerprint(candidate) == fingerprint(baseline)
        with CMPCT(archive) as reader:
            assert reader.delta_depth == 63
            assert reader.index == candidate
            assert reader.verify() == len(expected)
            assert set(reader.by) == set(expected)
            for name, payload in expected.items():
                assert reader.read(name) == payload, name
        preflight = preflight_archive(archive)
        assert preflight["files"] == len(expected)
        assert preflight["delta_depth"] == 63
        assert sha256_file(archive) == before_sha, "physical archive was mutated"

        dest = Path(os.environ.get("J24G64_PHYSICAL", "evidence/j24g64b-physical.cmpct"))
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(archive, dest)
        assert sha256_file(dest) == before_sha
        return {
            "prereg_commit": "bce038172d6d1c0c68945512bb354b6f25ddef6e",
            "source": physical_sources,
            "initial_members": 128, "final_members": len(expected),
            "delta_depth": 63,
            "operation_counts": {"ren": 21, "del": 21, "put": 21},
            "physical_footer_count": len(wire),
            "physical_archive_bytes": archive.stat().st_size,
            "physical_archive_sha256": before_sha,
            "source_index_msgpack_sha256": fingerprint(candidate),
            "admission_route": route,
            "reader_and_preflight_verified": True,
            "retained_archive": str(dest),
            "scope": "research-only authentic single-op mixed Writer corpus; no physical sparse xattrs",
        }


def main():
    source = source_attestation()
    outcomes = differential()
    edges = targeted_semantic_edges()
    base, deltas = large_case()
    expected = reference(base, deltas)
    observations = []
    for block in range(SAMPLES):
        order = ("reference", "factored", "factored", "reference") if block % 2 == 0 else (
            "factored", "reference", "reference", "factored")
        for phase, variant in enumerate(order):
            result, sample = measure(base, deltas, variant)
            assert result == expected
            observations.append({"block": block, "phase": phase, **sample})
    memory = {}
    for variant in ("reference", "factored"):
        gc.collect()
        tracemalloc.start()
        result = reference(base, deltas) if variant == "reference" else factored(base, deltas)[0]
        now, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert result == expected
        memory[variant] = {"retained_traced_bytes": now, "peak_traced_bytes": peak}
    a = statistics.median(v["wall_ns"] for v in observations if v["variant"] == "reference")
    b = statistics.median(v["wall_ns"] for v in observations if v["variant"] == "factored")
    extra = memory["factored"]["peak_traced_bytes"] - memory["reference"]["peak_traced_bytes"]
    decision = ("MIXED_FSMETA_REPLAY_SEED" if a / b >= 2 and extra <= 2 * 1024 * 1024
                else "NO_BOUNDED_MIXED_FSMETA_WIN")
    physical = physical_mixed_writer_check()
    report = {
        "schema": "cmpct-j24g64-mixed-fsmeta-research-v1",
        "decision": decision, "source": source, "platform": platform.platform(),
        "python": platform.python_version(), "differential": outcomes, "targeted_semantic_edges": edges, "physical_mixed_public_writer": physical,
        "members": len(base["files"]), "generations": len(deltas),
        "sparse_xattr_records": len(base["fsmeta"]["xattrs"]),
        "sparse_owner_records": len(base["fsmeta"]["owner_overrides"]),
        "raw_samples": observations,
        "wall_median_ns": {"reference": a, "factored": b},
        "wall_speedup": a / b, "tracemalloc": memory, "extra_peak_traced_bytes": extra,
        "final_index_msgpack_sha256": fingerprint(expected),
        "archive_bytes_added": 0,
        "limitations": [
            "Research-only Python helper oracle; not installed into Reader/Writer",
            "Synthetic performance workload is not a physically signed public archive",\n            "Separate physical Writer mixed check lacks deliberately signed sparse xattrs",
            "No end-to-end Reader open, read, extract, recovery or 64th checkpoint evidence",
            "No actual archive bytes changed; physical storage savings not measured",
            "Tracemalloc is not RSS; no external codec/ZIP/Zstd benchmark",
            "Conservative fallback covers ambiguous/collision/malformed/noncanonical histories",
            "Result is host-local until independently replicated across platforms"
        ]
    }
    dest = Path(os.environ.get("J24G64_RESULT", "evidence/j24g64-result.json"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("J24G64_HEAD", source["head"])
    print("J24G64_DECISION", decision)
    print("J24G64_SPEEDUP", round(a / b, 4))
    print("J24G64_EXTRA_PEAK", extra)
    print("J24G64_DIFFERENTIAL", json.dumps(outcomes, sort_keys=True))
    print("J24G64_RESULT_SHA256", hashlib.sha256(dest.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
