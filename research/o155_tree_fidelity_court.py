#!/usr/bin/env python3
"""O155 falsification court. Original CMPCT tree_digest is compiled from *source*, not copied."""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/cmpct/transactions.py"
ORACLE = ROOT / "tools/research/o155_strict_tree_oracle.py"
EXPECTED_LEGACY_BLOB = "964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c"


def import_courts():
    observed = subprocess.check_output(
        ["git", "hash-object", str(SOURCE)], cwd=ROOT, text=True
    ).strip()
    if observed != EXPECTED_LEGACY_BLOB:
        raise AssertionError(f"legacy source mismatch {observed} != {EXPECTED_LEGACY_BLOB}")
    expected_head = os.environ.get("EVIDENCE_HEAD")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if expected_head and head != expected_head:
        raise AssertionError(f"wrong CI source {head} != {expected_head}")

    old_tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = next(node for node in old_tree.body
              if isinstance(node, ast.FunctionDef) and node.name == "tree_digest")
    ns = {"hashlib": hashlib, "os": os, "struct": struct, "Path": Path}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(SOURCE), "exec"), ns)

    spec = importlib.util.spec_from_file_location("o155_strict_oracle", ORACLE)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return head, observed, ns["tree_digest"], mod


def write(path, content=b"ABC"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def build_pair(parent: Path, case: str):
    left, right = parent / "left", parent / "right"
    left.mkdir(); right.mkdir()
    if case == "file_symlink_vs_copy":
        for root in (left, right):
            write(root / "target.txt")
        (left / "alias").symlink_to("target.txt")
        write(right / "alias")
    elif case == "dir_symlink_vs_real":
        for root in (left, right):
            (root / "adir").mkdir()
        (left / "dirlink").symlink_to("adir", target_is_directory=True)
        (right / "dirlink").mkdir()
    elif case == "hardlink_vs_copy":
        for root in (left, right):
            write(root / "original")
        os.link(left / "original", left / "alias")
        write(right / "alias")
    else:
        raise ValueError(case)
    return left, right


def run() -> dict:
    head, source_blob, old_digest, oracle = import_courts()
    observations = {}
    for case in ("file_symlink_vs_copy", "dir_symlink_vs_real", "hardlink_vs_copy"):
        with tempfile.TemporaryDirectory(prefix="cmpct-o155-") as td:
            left, right = build_pair(Path(td), case)
            inherited_l, inherited_r = old_digest(left), old_digest(right)
            strict_l, manifest_l = oracle.strict_digest(left)
            strict_r, manifest_r = oracle.strict_digest(right)
            assert inherited_l == inherited_r, (case, "legacy witness did not collide")
            assert strict_l != strict_r, (case, "new witness still conflates semantics")
            if case == "hardlink_vs_copy":
                assert os.path.samefile(left / "original", left / "alias")
                assert not os.path.samefile(right / "original", right / "alias")
                assert len(manifest_l["hardlink_classes"]) == 1
                assert not manifest_r["hardlink_classes"]
            if case == "file_symlink_vs_copy":
                assert stat.S_ISLNK(os.lstat(left / "alias").st_mode)
                assert stat.S_ISREG(os.lstat(right / "alias").st_mode)
                assert next(x for x in manifest_l["entries"] if x["path_hex"] == b"alias".hex())["type"] == "symlink"
            if case == "dir_symlink_vs_real":
                assert stat.S_ISLNK(os.lstat(left / "dirlink").st_mode)
                assert stat.S_ISDIR(os.lstat(right / "dirlink").st_mode)
                assert next(x for x in manifest_l["entries"] if x["path_hex"] == b"dirlink".hex())["type"] == "symlink"
            observations[case] = {
                "original_false_equivalence": inherited_l,
                "left_strict": strict_l, "right_strict": strict_r,
                "semantic_type_left": [r["type"] for r in manifest_l["entries"]],
                "semantic_type_right": [r["type"] for r in manifest_r["entries"]],
                "left_hardlink_classes": manifest_l["hardlink_classes"],
                "right_hardlink_classes": manifest_r["hardlink_classes"],
                "verdict": "LEGACY_COLLISION_STRICT_DISCRIMINATION_CONFIRMED",
            }

    with tempfile.TemporaryDirectory(prefix="cmpct-o155-controls-") as td:
        base = Path(td)
        a, b = base / "alpha", base / "beta"
        a.mkdir(); b.mkdir()
        for root in (a,b):
            (root / "sub").mkdir()
            write(root / "sub" / "original", b"\x00\xff\x7f" * 2048)
            os.link(root / "sub" / "original", root / "link")
            (root / "dangling").symlink_to("../outside-no-such-file")
            raw = os.fsencode(root) + b"/file-\xff"
            with open(raw, "wb") as f:
                f.write(b"raw-posix-name")
        expected, manifest_a = oracle.strict_digest(a)
        identical, manifest_b = oracle.strict_digest(b)
        assert expected == identical and manifest_a == manifest_b
        assert len(manifest_a["hardlink_classes"]) == 1
        assert any(x["path_hex"] == b"file-\xff".hex() for x in manifest_a["entries"])

        # A target suddenly materializing *outside* the selected root must not
        # alter an in-tree symlink's raw-target/type witness.
        write(base / "outside-no-such-file", b"fresh-external-bytes")
        link_target_created, _ = oracle.strict_digest(a)
        assert link_target_created == expected, "oracle followed external symlink"

        write(b / "sub" / "original", b"changed")
        mutated, _ = oracle.strict_digest(b)
        assert mutated != expected

        old_mode = stat.S_IMODE(os.lstat(a / "dangling").st_mode)
        # File-mode perturbation (symlink chmod is platform-dependent).
        file_path = a / "sub" / "original"
        prior = stat.S_IMODE(os.lstat(file_path).st_mode)
        os.chmod(file_path, prior ^ stat.S_IXUSR)
        mode_mutated, _ = oracle.strict_digest(a)
        assert mode_mutated != expected
        os.chmod(file_path, prior)

        fifo = a / "unsupported"
        os.mkfifo(fifo)
        try:
            oracle.strict_digest(a)
        except oracle.UnsupportedTreeEntry:
            refused_special = True
        else:
            refused_special = False
        assert refused_special, "special file was silently omitted"

        observations["controls"] = {
            "same_tree_recreated_inode_independence": expected == identical,
            "raw_surrogateescaped_filename": True,
            "dangling_symlink_no_follow": link_target_created == expected,
            "mutation_detection": mutated != expected,
            "permission_mode_detection": mode_mutated != expected,
            "fifo_refused": refused_special,
            "unchanged_digest": expected,
            "independent_clone_digest": identical,
            "changed_payload_digest": mutated,
            "changed_mode_digest": mode_mutated,
            "hardlink_partition": manifest_a["hardlink_classes"],
            "verdict": "ALL_POSITIVE_AND_NEGATIVE_CONTROLS_PASS",
        }
    return {
        "schema": "cmpct-o155-court-v1",
        "git_head": head, "legacy_source_git_blob": source_blob,
        "oracle_sha256": hashlib.sha256(ORACLE.read_bytes()).hexdigest(),
        "verdict": "THREE_LEGACY_FALSE_EQUALITIES_FALSIFIED_BY_STRICT_TOPOLOGY_ORACLE",
        "research_only": True,
        "scope_exclusions": ["ACL", "xattr", "uid/gid", "time", "sparse layout",
                             "streams", "racy source mutation", "Windows NTFS modes"],
        "observations": observations,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    encoded = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded)
