#!/usr/bin/env python3
"""O46 held-out, source-exact cross-host reproducible-mode transfer falsifier.

Scientific evidence only; no shipped mode normalization or performance claims.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import tempfile

import msgpack

from cmpct.builder import Builder
from cmpct.codec import HDR, K_DIR, K_FILE, K_HARDLINK
from cmpct.reader import CMPCT
from v031_crosshost_repro_modes_o14 import ModeOnlyOracle

SCHEMA = "cmpct-v031-crosshost-heldout-multitype-o46-v1"
EXPECTED_BLOBS = {
    "src/cmpct/builder.py": "663ef0922992b1fbb8f19e6eea88d55c10a56044",
    "src/cmpct/reader.py": "604f6a81bf03bd97a4defb4ad7a1393d01ed491f",
    "benchmarks/v031_crosshost_repro_modes_o14.py": "c439829f358ef92a4ae71a7aaa4d9bbe8d83718a",
}
REGULAR = {
    "README.md": b"CMPCT held-out multi-type semantics\n" * 64,
    "bin/runner.sh": b"#!/bin/sh\necho cmpct\n" * 128,
    "nested/sub/payload.bin": bytes((i * 73 + (i >> 5) * 19 + 11) & 255 for i in range(96 * 1024)),
    "empty.txt": b"",
    "shared/owner.bin": bytes((i * 41 + 7) & 255 for i in range(16 * 1024)),
}
REGULAR["aliases/ref.bin"] = REGULAR["shared/owner.bin"]
REGULAR["independent/copy.bin"] = REGULAR["shared/owner.bin"]
DIRECTORIES = ("aliases", "bin", "empty-dir", "independent", "nested", "nested/sub", "shared")
OWN = "shared/owner.bin"
ALIAS = "aliases/ref.bin"
COPY = "independent/copy.bin"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class AllKindModeOracle(ModeOnlyOracle):
    """Research-only stronger comparator: additionally canonicalize hardlink modes."""

    def scan(self):
        super().scan()
        for row in self.files:
            if row[1] == K_HARDLINK:
                row[2] = 0o644


def create_source(root: Path) -> Path:
    src = root / "source"
    src.mkdir()
    for rel in DIRECTORIES:
        (src / rel).mkdir(parents=True, exist_ok=True)
    for rel, payload in REGULAR.items():
        if rel == ALIAS:
            continue
        p = src / rel
        p.write_bytes(payload)
    os.link(src / OWN, src / ALIAS)
    os.chmod(src / "bin/runner.sh", 0o755)
    assert os.path.samefile(src / OWN, src / ALIAS)
    assert not os.path.samefile(src / OWN, src / COPY)
    return src


def source_receipt(src: Path) -> dict:
    items = []
    groups = {}
    for rel in sorted((*DIRECTORIES, *REGULAR)):
        p = src / rel
        st = p.lstat()
        typ = "directory" if stat.S_ISDIR(st.st_mode) else "regular"
        assert typ in ("directory", "regular")
        record = {"path": rel, "type": typ,
                  "size": st.st_size if typ == "regular" else 0,
                  "sha256": sha(p.read_bytes()) if typ == "regular" else None,
                  "mode": stat.S_IMODE(st.st_mode)}
        items.append(record)
        if typ == "regular":
            key = (st.st_dev, st.st_ino)
            groups.setdefault(key, []).append(rel)
    # In particular, Windows DirEntry.stat() can differ from os.stat() in
    # inode/link-count completeness. Builder.scan() consumes DirEntry.stat().
    # Preserve both observations instead of hypothesizing a codec error.
    stat_probe = {}
    for rel in (OWN, ALIAS, COPY):
        p = src / rel
        full = p.stat()
        with os.scandir(p.parent) as entries:
            fast = next(e.stat(follow_symlinks=False)
                        for e in entries if e.name == p.name)
        stat_probe[rel] = {
            "os_stat": {"nlink": int(full.st_nlink),
                        "dev": int(full.st_dev), "ino": int(full.st_ino)},
            "direntry_stat": {"nlink": int(fast.st_nlink),
                              "dev": int(fast.st_dev), "ino": int(fast.st_ino)}
        }
    parts = sorted(tuple(sorted(v)) for v in groups.values())
    assert (ALIAS, OWN) in parts or (OWN, ALIAS) in parts, parts
    assert all(COPY not in g or len(g) == 1 for g in parts)
    return {"entries": items, "file_equivalence_groups": parts,
            "source_stat_probe": stat_probe,
            "logical_digest": sha(json.dumps(
                [{k: v for k, v in x.items() if k != "mode"} for x in items],
                sort_keys=True).encode())}


def capture(arc: Path, destination: Path) -> dict:
    body = arc.read_bytes()
    _magic, version, _flags, packed_index_size, raw_index_size, physical_size, _digest = HDR.unpack(
        body[:HDR.size])
    assert version == 24
    physical = body[HDR.size + packed_index_size:
                    HDR.size + packed_index_size + physical_size]
    assert len(physical) == physical_size
    with CMPCT(arc) as reader:
        verified = reader.verify()
        assert verified >= 1, verified
        for rel, expected in REGULAR.items():
            assert reader.read(rel) == expected, rel
        reader.extractall(destination, metadata=False)
        idx = copy.deepcopy(reader.index)
        rows = [{"path": r[0], "kind": r[1], "mode": r[2], "size": r[4]}
                for r in idx["files"]]
        hardlink_rows = [
            {"alias": r[0], "target": r[6][0]}
            for r in idx["files"] if r[1] == K_HARDLINK
        ]
        for row in idx["files"]:
            row[2] = 0
        nonmode_hash = sha(msgpack.packb(idx, use_bin_type=True))
    for rel, expected in REGULAR.items():
        assert (destination / rel).read_bytes() == expected, rel
    for rel in DIRECTORIES:
        assert (destination / rel).is_dir(), rel
    alias_same = os.path.samefile(destination / OWN, destination / ALIAS)
    copy_distinct = not os.path.samefile(destination / OWN, destination / COPY)
    # Do not assert here: preserve an authenticated, exact-head red receipt
    # before failing the host, so other agents can attribute the actual cause.
    return {"archive_sha256": sha(body), "archive_bytes": len(body),
            "physical_sha256": sha(physical), "physical_bytes": len(physical),
            "index_digest_ignoring_modes": nonmode_hash,
            "index_uncompressed_bytes": raw_index_size, "index_rows": rows,
            "encoded_hardlink_rows": hardlink_rows,
            "verified_count": verified, "roundtrip": "PASS",
            "hardlink_alias_identity": alias_same,
            "equal_bytes_independent_identity": copy_distinct,
            "member_sha256": {p: sha(data) for p, data in sorted(REGULAR.items())}}


def main(out: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=repo).strip()
    for path, expected in EXPECTED_BLOBS.items():
        actual = subprocess.check_output(
            ["git", "hash-object", path], text=True, cwd=repo).strip()
        assert actual == expected, (path, expected, actual)
    from cmpct import builder as bm
    installed_builder = str(Path(bm.__file__).resolve())
    assert not Path(installed_builder).is_relative_to(repo), installed_builder
    with tempfile.TemporaryDirectory(prefix="cmpct-o46-") as td:
        root = Path(td)
        src = create_source(root)
        fixture = source_receipt(src)
        outcomes = {}
        for name, cls in (("baseline", Builder),
                          ("o14_mode_only", ModeOnlyOracle),
                          ("all_kind_mode", AllKindModeOracle)):
            repeated = []
            for trial in range(2):
                arc = root / (name + str(trial) + ".cmpct")
                dst = root / (name + str(trial) + "-extract")
                cls(src, workers=1, reproducible=True,
                    reproducible_epoch_ns=0).build(arc)
                repeated.append(capture(arc, dst))
            assert repeated[0] == repeated[1], (
                "same-host nondeterministic complete archive", name, repeated)
            outcomes[name] = repeated[0]

        reference = outcomes["baseline"]
        for name, sub in outcomes.items():
            assert sub["physical_sha256"] == reference["physical_sha256"], (
                "oracle altered the physical record", name)
            assert sub["index_digest_ignoring_modes"] == reference[
                "index_digest_ignoring_modes"], ("oracle altered non-mode index", name)
            assert sub["member_sha256"] == reference["member_sha256"]
        for name in ("o14_mode_only", "all_kind_mode"):
            for row in outcomes[name]["index_rows"]:
                if row["kind"] == K_DIR:
                    assert row["mode"] == 0o755
                elif row["kind"] == K_FILE:
                    assert row["mode"] == 0o644
                elif row["kind"] == K_HARDLINK and name == "all_kind_mode":
                    assert row["mode"] == 0o644

        verdict = {
            "schema": SCHEMA, "source_sha": head, "platform": platform.system(),
            "python": platform.python_version(), "installed_builder": installed_builder,
            "fixture": fixture, "outcomes": outcomes, "builds_per_arm": 2,
            "product_code_modified": False, "research_only": True,
            "inherited_o14_oracle_blob": EXPECTED_BLOBS[
                "benchmarks/v031_crosshost_repro_modes_o14.py"],
        }
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(verdict, sort_keys=True, indent=2) + "\n")
        if not all(
            result["hardlink_alias_identity"] and
            result["equal_bytes_independent_identity"]
            for result in outcomes.values()
        ):
            raise AssertionError(
                "O46_AUTHENTIC_PRODUCT_HARDLINK_PHYSICAL_IDENTITY_FAIL: "
                "fail-closed original criterion; diagnostic receipt saved "
                "to " + str(out) + "; index hardlink rows: " +
                json.dumps({arm: result["encoded_hardlink_rows"]
                            for arm, result in outcomes.items()}, sort_keys=True)
            )
        print(json.dumps({"source_sha": head, "platform": verdict["platform"],
                          "schema": SCHEMA, "original": reference["archive_sha256"],
                          "o14": outcomes["o14_mode_only"]["archive_sha256"],
                          "all_kind": outcomes["all_kind_mode"]["archive_sha256"],
                          "hardlink": "PASS", "roundtrip": "PASS"}, sort_keys=True))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    main(args.out)
