#!/usr/bin/env python3
"""J24G66 independently tests *physical*, Builder-signed sparse xattrs.

Research-only independent replication of J24G64; no Reader/replay monkeypatch,
product mutation, decoder substitution, or release/performance claim.
"""
from __future__ import annotations

import copy
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time

import msgpack

from cmpct import _xattrs, transactions as tx
from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive
from j24g60_single_delta_chain_court import footer_chain, sha256_file, verify_source
from j24g62_crossgen_rename_oracle import read_wire
from j24g64_mixed_fsmeta_oracle import factored, fingerprint, reference

BASE = "41cd7f88d9fede55a495f36e78126b26eff85880"
PREREG = "2fbb61281d203e28a7bcc44ecaf2e7dfa6f3ddaf"
DEPTH = 63
KEY = ("com.fcmo.cmpct.j24g66" if sys.platform == "darwin"
       else "user.cmpct_j24g66")
KEY2 = KEY + ".second"
TAG_INDICES = (0, 2, 32, 33, 42, 64, 65, 100)
N = 128


def pin_source() -> dict:
    root = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    for parent in (BASE, PREREG):
        assert subprocess.run(
            ["git", "merge-base", "--is-ancestor", parent, head],
            cwd=root, stdout=subprocess.DEVNULL,
        ).returncode == 0, ("missing source/prereg ancestor", parent, head)
    return {"git_head": head, "parent": BASE, "prereg": PREREG,
            "original_product_sources": verify_source()}


def xset(path: Path, name: str, payload: bytes) -> None:
    _xattrs.setxattr(path, name, payload, follow_symlinks=False)
    actual = _xattrs.getxattr(path, name, follow_symlinks=False)
    assert actual == payload, ("source xattr write unreadable", path.name, name)


def xget_opt(path: Path, name: str):
    try:
        return _xattrs.getxattr(path, name, follow_symlinks=False)
    except OSError as exc:
        noattr = {errno.ENODATA, getattr(errno, "ENOATTR", errno.ENODATA)}
        if exc.errno in noattr:
            return None
        raise


def projection(index: dict) -> dict:
    rows = index["files"]
    result = {}
    records = index.get("fsmeta", {}).get("xattrs", [])
    for record in records:
        assert isinstance(record, list) and len(record) == 2
        pos, keys = record
        assert type(pos) is int and 0 <= pos < len(rows)
        name = rows[pos][0]
        assert name not in result, ("duplicate signed xattr ordinal", name)
        result[name] = {key: value for key, value in keys}
        assert len(result[name]) == len(keys)
    return result


def own_projection(index: dict) -> dict:
    rows = index["files"]
    return {
        rows[row[0]][0]: (row[1], row[2])
        for row in index.get("fsmeta", {}).get("owner_overrides", [])
    }


def main() -> None:
    source = pin_source()
    assert sys.platform in ("linux", "darwin"), "unsupported host: no xattr evidence"
    assert _xattrs.can_list() and _xattrs.can_set(), "xattr provider unavailable"
    w0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
    tracked = (KEY, KEY2)
    initial_tags = {}
    expected_data = {}
    with tempfile.TemporaryDirectory(prefix="cmpct-j24g66-") as td:
        root = Path(td)
        tree = root / "input"
        tree.mkdir()
        for i in range(N):
            name = f"f{i:04d}.dat"
            raw = hashlib.sha256(f"signed-xattr-court-{i}".encode()).digest() * 2
            path = tree / name
            path.write_bytes(raw)
            expected_data[name] = raw
            if i in TAG_INDICES:
                tags = {KEY: f"identity-{i:04d}".encode()}
                if i in (0, 42, 64):
                    tags[KEY2] = hashlib.sha256(f"second-{i}".encode()).digest()
                for key, payload in tags.items():
                    xset(path, key, payload)
                initial_tags[name] = tags

        archive = root / "authentic-signed.cmpct"
        Builder(tree, workers=1, reproducible=False).build(archive)
        with CMPCT(archive) as initial:
            signed_initial = projection(initial.index)
            assert initial.verify() == N
            assert initial.delta_depth == 0
            for path, attrs in initial_tags.items():
                assert all(signed_initial.get(path, {}).get(k) == v for k, v in attrs.items()), (
                    "source xattrs not captured by Builder", path)
        expected_tags = copy.deepcopy(initial_tags)
        assert len(footer_chain(archive)) == 1

        timeline = []
        for i in range(21):
            old, new = f"f{i:04d}.dat", f"r{i:04d}.dat"
            tx.append_rename(archive, old, new)
            expected_data[new] = expected_data.pop(old)
            if old in expected_tags:
                expected_tags[new] = expected_tags.pop(old)
            timeline.append(("ren", old, new))

            removed = f"f{32+i:04d}.dat"
            tx.append_delete(archive, removed)
            del expected_data[removed]
            expected_tags.pop(removed, None)
            timeline.append(("del", removed))

            replacement = hashlib.sha256(f"updated-signed-{i}".encode()).digest() * 2
            new_source = root / f"update-{i:04d}.dat"
            new_source.write_bytes(replacement)
            # At i=10, delete f0042 then reinsert the SAME name in the
            # following signed generation: the old xattr must not resurrect.
            target = (f"f{32+i:04d}.dat" if i == 10 else
                      f"f{64+i:04d}.dat" if i % 2 == 0 else
                      f"new{i:04d}.dat")
            tx.append_update(archive, target, new_source)
            expected_data[target] = replacement
            # Same-path PUT retains existing metadata; new name gets none.
            timeline.append(("put", target))
        assert len(timeline) == DEPTH
        archive_sha = sha256_file(archive)
        physical = footer_chain(archive)
        assert len(physical) == 64
        assert all(v["kind"] == 1 and v["op_width"] == 1 for v in physical[:-1])
        assert physical[-1]["kind"] == 0

        base, deltas = read_wire(archive)
        assert len(deltas) == DEPTH
        baseline = reference(base, deltas)
        candidate, route = factored(base, deltas)
        assert route == "factored", ("signed physical history not admitted", route)
        assert baseline == candidate
        assert msgpack.packb(baseline, use_bin_type=True) == msgpack.packb(
            candidate, use_bin_type=True), "logical index wire disagreement"
        initial_count = len(projection(base))
        final_xattrs = projection(candidate)
        assert initial_count >= len(TAG_INDICES), "sparse metadata not physically signed"

        with CMPCT(archive) as reader:
            assert reader.index == candidate == baseline
            assert reader.delta_depth == DEPTH
            assert reader.verify() == len(expected_data)
            assert set(reader.by) == set(expected_data)
            assert projection(reader.index) == final_xattrs
            for name, raw in expected_data.items():
                assert reader.read(name) == raw, ("payload", name)
            for name in expected_data:
                observed = final_xattrs.get(name, {})
                wanted = expected_tags.get(name, {})
                assert {k: observed.get(k) for k in tracked if k in observed} == wanted, (
                    "signed xattr identity mismatch", name, wanted, observed)
            assert "f0042.dat" in expected_data and "f0042.dat" not in expected_tags
            assert "f0042.dat" not in final_xattrs or KEY not in final_xattrs["f0042.dat"]
            assert "r0000.dat" in expected_tags and "f0064.dat" in expected_tags
            assert "f0032.dat" not in expected_data

            dest = root / "restored"
            reader.extractall(dest, require_xattrs=True)
            for name, raw in expected_data.items():
                restored = dest / name
                assert restored.is_file() and restored.read_bytes() == raw, ("extract bytes", name)
                wanted = expected_tags.get(name, {})
                for key in tracked:
                    got = xget_opt(restored, key)
                    assert got == wanted.get(key), (
                        "restored physical xattr transposed/lost/resurrected",
                        name, key, got, wanted.get(key))
        pf = preflight_archive(archive)
        assert pf["files"] == len(expected_data) and pf["delta_depth"] == DEPTH
        assert sha256_file(archive) == archive_sha

        # Independent evaluator-sensitivity control: a forged signed xattr
        # binding on a different existing row must not look like the correct
        # path->xattr projection. This does not represent a malformed archive.
        forged = copy.deepcopy(candidate)
        records = forged["fsmeta"]["xattrs"]
        assert records, "no signed metadata to challenge"
        taken = {r[0] for r in records}
        victim = next(i for i, row in enumerate(forged["files"])
                      if i not in taken and row[0] in expected_data)
        records[0][0] = victim
        assert projection(forged) != final_xattrs, "evaluator blind to ordinal swap"

        # Recovery control uses only a copied physical archive. The latest
        # signed footer digest is corrupted; the previous generation should
        # recover instead of accepting a forged latest index.
        damaged = root / "tail-digest-mutated.cmpct"
        shutil.copyfile(archive, damaged)
        with damaged.open("r+b") as f:
            f.seek(-1, os.SEEK_END)
            b = f.read(1)
            f.seek(-1, os.SEEK_END)
            f.write(bytes([b[0] ^ 0x01]))
        with CMPCT(damaged) as recovered:
            assert recovered.delta_depth == DEPTH - 1
            assert recovered.index != candidate
            assert recovered.verify() == len(expected_data) - 1 or (
                # For a same-name replacement, member count may stay the same.
                recovered.verify() == len(expected_data))
        assert sha256_file(archive) == archive_sha

        # Persist public-safe, generated physical sample, with no private paths.
        physical_out = Path(os.environ.get("J24G66_PHYSICAL", "evidence/j24g66-signed-physical.cmpct"))
        physical_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(archive, physical_out)
        assert sha256_file(physical_out) == archive_sha
        receipt = {
            "schema": "cmpct-j24g66-signed-fsmeta-physical-v1",
            "decision": "PHYSICAL_SIGNED_XATTR_IDENTITY_PASS",
            "source": source,
            "host": platform.platform(), "python": platform.python_version(),
            "xattr_keys": tracked,
            "initial_tagged_paths": sorted(initial_tags),
            "final_tagged_paths": sorted(expected_tags),
            "initial_xattr_records": initial_count,
            "final_xattr_records": len(final_xattrs),
            "base_members": len(base["files"]),
            "final_members": len(expected_data),
            "timeline": [list(x) for x in timeline],
            "depth": DEPTH, "footer_count": len(physical),
            "physical_archive_bytes": archive.stat().st_size,
            "logical_final_payload_bytes": sum(len(x) for x in expected_data.values()),
            "archive_sha256": archive_sha,
            "final_index_msgpack_sha256": fingerprint(candidate),
            "original_oracle_route": route,
            "original_reader_preflight_strict_restore": "pass",
            "hostile_swapped_ordinal_detected": True,
            "corrupt_footer_recovered": True,
            "wall_ns_total_including_builder_writer_extract": time.perf_counter_ns() - w0,
            "cpu_ns_total_including_builder_writer_extract": time.process_time_ns() - cpu0,
            "limitations": [
                "Research-only physical fidelity and index identity; no installed Reader optimization",
                "No multi-host result claimed until original CI artifacts verified",
                "No authentic signed owner_override variation (unprivileged runner)",
                "No hardlink xattr alias, 64th checkpoint, Windows xattr or full recovery matrix",
                "No same-runner ABBA Reader-open speed/RSS comparison",
                "No release, size-compression, create/extract benchmark or native parity credit"
            ],
        }
        path = Path(os.environ.get("J24G66_RESULT", "evidence/j24g66-result.json"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print("J24G66_DECISION", receipt["decision"])
        print("J24G66_HEAD", source["git_head"])
        print("J24G66_XATTR_RECORDS", initial_count, len(final_xattrs))
        print("J24G66_ARCHIVE_SHA256", archive_sha)
        print("J24G66_RESULT_SHA256", hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
