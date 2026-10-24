#!/usr/bin/env python3
"""O15 independently check public-C native byte and inode topology materialization.

This is a positive/negative research court for a deliberately flat, private
POSIX tree. C client sees only the documented Rust ABI, never Python's index.
The independent oracle uses actual source and extracted POSIX inode relations.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from cmpct.builder import Builder
from native_pack_batch_abi import source_bytes
from native_hardlink_owner_o14 import rebuild, wire_parts

ORIGIN_SHA = "611d0ea67a94f552f9ebca07ba747f191dee160e"
FIXED_TIME = 1_700_000_000_000_000_000
A = b"alpha independent inode O15|" * 30
B = b"bravo different source O15||" * 30
assert A != B and len(A) == len(B)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_tree(directory: Path, owner: str) -> None:
    directory.mkdir()
    assert owner in ("a.bin", "b.bin")
    for name, data in (("a.bin", A), ("b.bin", B), ("a_copy.bin", A)):
        (directory / name).write_bytes(data)
        (directory / name).chmod(0o600)
    for i in range(128):
        (directory / f"entry-{i:05d}.txt").write_bytes(source_bytes(i))
    os.link(directory / owner, directory / "y_alias.bin")
    os.link(directory / owner, directory / "z_alias.bin")
    (directory / "s_link").symlink_to(
        "b.bin" if owner == "a.bin" else "a.bin"
    )
    for leaf in directory.iterdir():
        if not leaf.is_symlink():
            os.utime(leaf, ns=(FIXED_TIME, FIXED_TIME))
    os.utime(directory, ns=(FIXED_TIME, FIXED_TIME))
    assert os.lstat(directory / owner).st_ino == os.lstat(
        directory / "y_alias.bin"
    ).st_ino
    assert os.lstat(directory / "a.bin").st_ino != os.lstat(
        directory / "a_copy.bin"
    ).st_ino, "equal bytes must not imply same inode"


def identity_partition(directory: Path) -> list[list[str]]:
    by_identity: dict[tuple[int, int], list[str]] = {}
    for p in directory.iterdir():
        if p.is_symlink():
            continue
        info = os.lstat(p)
        assert p.is_file(), p
        by_identity.setdefault((info.st_dev, info.st_ino), []).append(p.name)
    return sorted(sorted(v) for v in by_identity.values())


def tree_oracle(src: Path, dst: Path) -> dict:
    source_names = set(os.listdir(src))
    extracted_names = set(os.listdir(dst))
    assert source_names == extracted_names, (
        "directory names differ", source_names ^ extracted_names
    )
    expected_hashes = {}
    for name in sorted(source_names):
        source_leaf, dest_leaf = src / name, dst / name
        src_mode = os.lstat(source_leaf).st_mode
        dst_mode = os.lstat(dest_leaf).st_mode
        assert (src_mode & 0o170000) == (dst_mode & 0o170000), (
            "filesystem kind differs", name
        )
        if source_leaf.is_symlink():
            assert os.readlink(source_leaf) == os.readlink(dest_leaf), (
                "symlink payload differs", name
            )
            continue
        expected = digest(source_leaf.read_bytes())
        actual = digest(dest_leaf.read_bytes())
        assert expected == actual, ("source byte digest mismatch", name)
        expected_hashes[name] = expected
    src_groups = identity_partition(src)
    dst_groups = identity_partition(dst)
    assert src_groups == dst_groups, (
        "hardlink inode equivalence classes differ", src_groups, dst_groups
    )
    assert len([g for g in src_groups if len(g) > 1]) == 1
    return {
        "member_count": len(source_names),
        "sha256_by_member": expected_hashes,
        "inode_equivalence_classes": src_groups,
        "source_symlink_target": os.readlink(src / "s_link"),
        "extracted_symlink_target": os.readlink(dst / "s_link"),
    }


def invoke(binary: Path, archive: Path, dest: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(binary), str(archive), str(dest)],
        text=True, capture_output=True, timeout=90,
    )


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: native_inode_tree_o15.py C_BINARY RESULT.json")
    binary = Path(sys.argv[1]).resolve()
    result_path = Path(sys.argv[2]).resolve()
    assert binary.is_file()
    cases = {}
    with tempfile.TemporaryDirectory(prefix="cmpct-o15-") as temp:
        home = Path(temp)
        for owner in ("a.bin", "b.bin"):
            label = owner[0]
            source = home / f"source-{label}"
            source_tree(source, owner)
            archive = home / f"archive-{label}.cmpct"
            Builder(source, workers=1, reproducible=True).build(archive)
            dest = home / f"extracted-{label}"
            dest.mkdir(mode=0o700)
            p = invoke(binary, archive, dest)
            assert p.returncode == 0, (
                "native client failed", owner, p.returncode, p.stderr[:2000]
            )
            counts = json.loads(p.stdout.strip())
            actual = tree_oracle(source, dest)
            assert counts["regular"] == 131, counts
            assert counts["hardlinks"] == 2, counts
            assert counts["symlinks"] == 1, counts
            assert counts["batch_calls"] >= 1, (
                "preregistered Zstd PACK never executed", counts
            )
            assert counts["batch_members"] >= 2, counts
            assert counts["batch_members"] + counts["fallback"] == counts["regular"]
            assert counts["max_stage_bytes"] <= 1024 * 1024
            cases[label] = {
                "owner_name": owner,
                "archive_sha256": digest(archive.read_bytes()),
                "archive_bytes": archive.stat().st_size,
                "native_counts": counts,
                "oracle": actual,
            }
            # A pre-existing symlink to an external canary must fail before
            # ANY new member is materialized; private root is otherwise empty.
            if label == "a":
                bad = home / "unsafe-destination"
                bad.mkdir(mode=0o700)
                external = home / "canary.bin"
                canary = b"CMPCT-O15-EXTERNAL-CANARY-DO-NOT-OVERWRITE"
                external.write_bytes(canary)
                (bad / "a.bin").symlink_to(external)
                negative = invoke(binary, archive, bad)
                assert negative.returncode != 0, (
                    "preexisting symlink accepted", negative.stdout
                )
                assert external.read_bytes() == canary
                assert (bad / "a.bin").is_symlink()
                assert set(os.listdir(bad)) == {"a.bin"}, (
                    "partial materialization before destination admission"
                )
                hostile = {
                    "status": "REJECTED",
                    "returncode": negative.returncode,
                    "canary_sha256": digest(canary),
                    "destination_entries": sorted(os.listdir(bad)),
                }
        # O15b was preregistered after O15's first successful hosted result:
        # reorder only signed index *rows*, without rewriting physical payloads
        # or weakening the source-tree oracle. Here a hardlink alias precedes
        # its terminal regular-file owner in the public ABI enumeration.
        original_archive = (home / "archive-a.cmpct").read_bytes()
        original_index, original_records, original_flags = wire_parts(
            original_archive
        )
        positions = {
            row[0]: n for n, row in enumerate(original_index["files"])
        }
        assert positions["a.bin"] < positions["y_alias.bin"]
        def swap_owner_and_alias(index):
            rows = index["files"]
            rows[positions["a.bin"]], rows[positions["y_alias.bin"]] = (
                rows[positions["y_alias.bin"]], rows[positions["a.bin"]]
            )
        reordered = rebuild(original_archive, swap_owner_and_alias)
        new_index, new_records, new_flags = wire_parts(reordered)
        assert new_records == original_records and new_flags == original_flags
        assert sorted(repr(row) for row in original_index["files"]) == (
            sorted(repr(row) for row in new_index["files"])
        ), "reorder changed logical index rows, not merely enumeration"
        reordered_positions = {
            row[0]: n for n, row in enumerate(new_index["files"])
        }
        assert reordered_positions["y_alias.bin"] < reordered_positions["a.bin"]
        signed_path = home / "archive-a-reordered.cmpct"
        signed_path.write_bytes(reordered)
        reordered_dest = home / "extracted-a-reordered"
        reordered_dest.mkdir(mode=0o700)
        reordered_run = invoke(binary, signed_path, reordered_dest)
        assert reordered_run.returncode == 0, (
            "signed alias-before-owner extraction failed",
            reordered_run.returncode, reordered_run.stderr[:2000]
        )
        reorder_counts = json.loads(reordered_run.stdout.strip())
        reorder_oracle = tree_oracle(home / "source-a", reordered_dest)
        assert reorder_counts["batch_calls"] >= 1
        assert reorder_counts["batch_members"] >= 2
        assert reorder_counts["max_stage_bytes"] <= 1024 * 1024
        cases["a_reordered"] = {
            "owner_name": "a.bin",
            "archive_sha256": digest(reordered),
            "archive_bytes": len(reordered),
            "native_counts": reorder_counts,
            "signed_index_order": {
                "alias_ordinal": reordered_positions["y_alias.bin"],
                "owner_ordinal": reordered_positions["a.bin"],
            },
            "physical_records_sha256": digest(new_records),
            "original_records_sha256": digest(original_records),
            "oracle": reorder_oracle,
        }
        assert cases["a_reordered"]["archive_sha256"] != (
            cases["a"]["archive_sha256"]
        )
        assert cases["a"]["archive_sha256"] != cases["b"]["archive_sha256"]
        assert cases["a"]["oracle"]["inode_equivalence_classes"] != (
            cases["b"]["oracle"]["inode_equivalence_classes"]
        )
        assert cases["a"]["oracle"]["source_symlink_target"] == "b.bin"
        assert cases["b"]["oracle"]["source_symlink_target"] == "a.bin"
        result = {
            "schema": "cmpct-native-inode-tree-o15-v1",
            "source_base_sha": ORIGIN_SHA,
            "court": "PUBLIC_C_TREE_TOPOLOGY_COMPOSITION",
            "decision": "BOUNDED_POSIX_FLAT_TREE_TOPOLOGY_EXACT",
            "cases": cases,
            "hostile_existing_symlink": hostile,
            "claims_not_earned": [
                "arbitrary filesystem extraction", "atomic publication",
                "concurrent destination safety", "RAW source mutation identity",
                "metadata/xattr/ACL equivalence", "Windows/macOS portability",
                "whole-product performance", "release promotion",
            ],
        }
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps({
            "decision": result["decision"],
            "case_counts": {k: v["native_counts"] for k, v in cases.items()},
            "hostile": hostile["status"],
        }, sort_keys=True))


if __name__ == "__main__":
    main()
