"""Preregistered, source-faithful tree-evidence false-equivalence court (#312).

Runs actual old helper function bodies extracted via AST without importing their
surrounding benchmark engines. Reports failure modes; does not edit old oracles.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import struct
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fs_oracle", ROOT / "tools/v031_fs_semantics_oracle.py")
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def load_legacy(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(funcs) != 1:
        raise AssertionError(f"exact legacy function absent: {path.name}:{name}")
    code = ast.fix_missing_locations(ast.Module(body=funcs, type_ignores=[]))
    namespace = {"hashlib": hashlib, "Path": Path, "os": os, "struct": struct}
    exec(compile(code, str(path), "exec"), namespace)
    return namespace[name]


def make_pair(root: Path, kind: str):
    a, b = root / "a", root / "b"
    a.mkdir(); b.mkdir()
    if kind == "file_symlink":
        for side in (a, b):
            (side / "target").write_bytes(b"ABC")
        (a / "alias").symlink_to("target")
        (b / "alias").write_bytes(b"ABC")
    elif kind == "directory_symlink":
        for side in (a, b):
            (side / "adir").mkdir()
        (a / "dirlink").symlink_to("adir", target_is_directory=True)
        (b / "dirlink").mkdir()
    elif kind == "hardlink":
        for side in (a, b):
            (side / "original").write_bytes(b"ABC")
        os.link(a / "original", a / "alias")
        (b / "alias").write_bytes(b"ABC")
    else:
        raise ValueError(kind)
    return a, b


def main():
    old = {
        "transaction": load_legacy(ROOT / "src/cmpct/transactions.py", "tree_digest"),
        "direct_c25": load_legacy(ROOT / "benchmarks/v030_c25cc01_direct_extract_oracle.py", "_tree_digest"),
        "mmap_c25": load_legacy(ROOT / "benchmarks/v030_c25cc01_mmap_extract_oracle.py", "_tree_digest"),
    }
    result = {
        "schema": "cmpct-v031-fs-semantic-oracle-scientific-court-v1",
        "claim_scope": "type, relative raw name, regular file bytes, symlink payload, within-tree hardlink equivalence only",
        "reconstruction_product_credit": False,
        "archive_format_changed": False,
        "snapshot_or_concurrent_mutation_guarantee": False,
        "platform": platform.system(),
        "controls": {},
    }
    for kind in ("file_symlink", "directory_symlink", "hardlink"):
        with tempfile.TemporaryDirectory() as tmp:
            try:
                a, b = make_pair(Path(tmp), kind)
            except (OSError, NotImplementedError) as exc:
                if platform.system() == "Linux":
                    raise
                result["controls"][kind] = {"status": "UNSUPPORTED_PLATFORM", "error_type": type(exc).__name__}
                continue
            positive = MOD.semantic_tree_digest_v1(a)
            negative = MOD.semantic_tree_digest_v1(b)
            if positive == negative:
                raise AssertionError(f"new oracle false-equal for {kind}")
            equality = {name: (func(a) == func(b)) for name, func in old.items()}
            result["controls"][kind] = {
                "status": "NEW_ORACLE_DISTINGUISHES",
                "new_oracle_equal": False,
                "legacy_equal": equality,
                "new_a_sha256": positive,
                "new_b_sha256": negative,
            }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
