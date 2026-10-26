#!/usr/bin/env python3
"""O162: genuine installed CMPCT r24 POSIX tree roundtrip against O155.

Research scope: a stable supported tree, not atomic snapshots, NTFS, special
files, concurrent mutation, or release certification. Preregistered separately.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "tools/research/o155_strict_tree_oracle.py"
TX = ROOT / "src/cmpct/transactions.py"
EXPECTED = {
    "src/cmpct/builder.py": "663ef0922992b1fbb8f19e6eea88d55c10a56044",
    "src/cmpct/reader.py": "e716233403dabd0966863c45635e18fa5ac6afb8",
    "src/cmpct/transactions.py": "964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c",
    "tools/research/o155_strict_tree_oracle.py": "0bef46e8d1944ff327063c66edc9bbc29fa58481",
}


def git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def identity_gate() -> dict:
    head = git(["rev-parse", "HEAD"])
    expected_head = os.environ.get("EVIDENCE_HEAD")
    if expected_head and head != expected_head:
        raise AssertionError(f"checkout head mismatch: {head} != {expected_head}")
    observed = {}
    for relative, expected in EXPECTED.items():
        actual = git(["hash-object", relative])
        if actual != expected:
            raise AssertionError(f"source identity drift {relative}: {actual} != {expected}")
        observed[relative] = actual
    # Executing outside the source tree must import a wheel installed elsewhere.
    import cmpct
    actual_package = Path(cmpct.__file__).resolve()
    if actual_package.is_relative_to((ROOT / "src").resolve()):
        raise AssertionError(f"editable/worktree import not an independent install: {actual_package}")
    return {"git_head": head, "source_blobs": observed,
            "installed_package_path": str(actual_package)}


def load_independent_witnesses():
    spec = importlib.util.spec_from_file_location("o155_strict_tree_oracle", ORACLE)
    if spec is None or spec.loader is None:
        raise RuntimeError("O155 oracle module unavailable")
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    # Original historical tree_digest executable source, not a paraphrase or copy.
    parsed = ast.parse(TX.read_text(encoding="utf-8"))
    fn = next(n for n in parsed.body
              if isinstance(n, ast.FunctionDef) and n.name == "tree_digest")
    ns = {"hashlib": hashlib, "os": os, "stat": stat, "Path": Path}
    import struct
    ns["struct"] = struct
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(TX), "exec"), ns)
    return oracle, ns["tree_digest"]


def build_fixture(root: Path) -> None:
    root.mkdir()
    (root / "nested").mkdir()
    (root / "empty").mkdir()
    (root / "a-base.bin").write_bytes(bytes(range(256)) * 17 + b"\x00\xff")
    (root / "nested" / "leaf.txt").write_text("exact bytes: \u03bb / caf\u00e9\n", encoding="utf-8")
    (root / "caf\u00e9.txt").write_bytes(b"\x80\x00CMPCT\xff")
    (root / "zero.dat").write_bytes(b"")
    os.link(root / "a-base.bin", root / "nested" / "hardcopy.bin")
    (root / "ln-file").symlink_to("a-base.bin")
    (root / "ln-dir").symlink_to("nested", target_is_directory=True)
    (root / "nested" / "ln-nested").symlink_to("leaf.txt")
    # chmod after all writes, and avoid root/user-specific ownership changes.
    (root / "a-base.bin").chmod(0o640)
    (root / "nested" / "leaf.txt").chmod(0o744)
    (root / "empty").chmod(0o750)
    root.chmod(0o755)


def call_cli(args: list[str], cwd: Path) -> dict:
    t0 = time.perf_counter_ns()
    proc = subprocess.run([sys.executable, "-m", "cmpct", *args],
                          cwd=cwd, capture_output=True, text=True, timeout=110)
    elapsed_ns = time.perf_counter_ns() - t0
    rec = {"args": [args[0], "<synthetic-paths>"], "returncode": proc.returncode,
           "wall_ms": round(elapsed_ns / 1e6, 3),
           "stdout_tail": proc.stdout[-2500:], "stderr_tail": proc.stderr[-2500:]}
    if proc.returncode:
        raise RuntimeError(f"CMPCT command failed: {json.dumps(rec)}")
    return rec


def run() -> dict:
    identity = identity_gate()
    oracle, old_tree_digest = load_independent_witnesses()
    import cmpct
    fixture = {}
    with tempfile.TemporaryDirectory(prefix="cmpct-o162-", dir=os.environ.get("RUNNER_TEMP")) as temporary:
        base = Path(temporary)
        source, output, archive = base / "source", base / "restore", base / "synthetic.cmpct"
        # Explicitly stabilize the fixture's ordinary POSIX mode profile.
        previous_umask = os.umask(0o022)
        try:
            build_fixture(source)
            source_digest, source_manifest = oracle.strict_digest(source)
            fixture["source_entries"] = len(source_manifest["entries"])
            fixture["source_hardlink_classes"] = source_manifest["hardlink_classes"]
            fixture["source_digest"] = source_digest
            create = call_cli(["create", str(source), str(archive), "--workers", "1"], base)
            verify = call_cli(["verify", str(archive)], base)
            extract = call_cli(["extract", str(archive), str(output)], base)
            output_digest, output_manifest = oracle.strict_digest(output)
            fixture["archive_bytes"] = archive.stat().st_size
            fixture["archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
            fixture["create"] = create
            fixture["verify"] = verify
            fixture["extract"] = extract
            fixture["output_digest"] = output_digest
            fixture["output_entries"] = len(output_manifest["entries"])
            fixture["output_hardlink_classes"] = output_manifest["hardlink_classes"]
            fixture["strict_manifest_equal"] = source_manifest == output_manifest
            fixture["direct_hardlink_samefile"] = os.path.samefile(
                output / "a-base.bin", output / "nested" / "hardcopy.bin")
            fixture["direct_symlink_targets"] = {
                "file": os.readlink(output / "ln-file"),
                "directory": os.readlink(output / "ln-dir"),
                "nested": os.readlink(output / "nested" / "ln-nested"),
            }
            fixture["source_modes"] = {
                "base": stat.S_IMODE(os.lstat(source / "a-base.bin").st_mode),
                "executable": stat.S_IMODE(os.lstat(source / "nested" / "leaf.txt").st_mode),
                "empty_directory": stat.S_IMODE(os.lstat(source / "empty").st_mode),
            }
            fixture["extracted_modes"] = {
                "base": stat.S_IMODE(os.lstat(output / "a-base.bin").st_mode),
                "executable": stat.S_IMODE(os.lstat(output / "nested" / "leaf.txt").st_mode),
                "empty_directory": stat.S_IMODE(os.lstat(output / "empty").st_mode),
            }
            fixture["readme_bytes_equal"] = (
                (source / "nested" / "leaf.txt").read_bytes()
                == (output / "nested" / "leaf.txt").read_bytes())
            fixture["archive_source_outside_tree"] = not archive.is_relative_to(source)
            if source_manifest != output_manifest:
                fixture["source_manifest"] = source_manifest
                fixture["output_manifest"] = output_manifest
                raise AssertionError("genuine CMPCT reconstruction differs under O155 strict tree witness")
            assert fixture["direct_hardlink_samefile"]
            assert fixture["direct_symlink_targets"] == {
                "file": "a-base.bin", "directory": "nested", "nested": "leaf.txt"
            }
            assert fixture["source_modes"] == fixture["extracted_modes"]
            assert fixture["readme_bytes_equal"]
            assert fixture["archive_source_outside_tree"]

            # Adversarial control on genuine extracted files: preserve the same
            # bytes/mode/name, only break the physical hardlink equivalence.
            legacy_before = old_tree_digest(output)
            duplicate = output / "nested" / "hardcopy.bin"
            raw = duplicate.read_bytes()
            old_mode = stat.S_IMODE(os.lstat(duplicate).st_mode)
            duplicate.unlink()
            duplicate.write_bytes(raw)
            duplicate.chmod(old_mode)
            legacy_after = old_tree_digest(output)
            perturbed, mutant_manifest = oracle.strict_digest(output)
            fixture["historical_digest_equal_after_severing"] = legacy_before == legacy_after
            fixture["strict_digest_changes_after_severing"] = output_digest != perturbed
            fixture["host_hardlink_severed"] = not os.path.samefile(
                output / "a-base.bin", duplicate)
            fixture["post_perturbation_hardlink_classes"] = mutant_manifest["hardlink_classes"]
            fixture["mutant_bytes_equal"] = raw == (output / "a-base.bin").read_bytes()
            assert fixture["host_hardlink_severed"] and fixture["mutant_bytes_equal"]
            assert fixture["historical_digest_equal_after_severing"], (
                "historical comparator unexpectedly observes topology; preserve this result"
            )
            assert fixture["strict_digest_changes_after_severing"], (
                "strict comparator failed to detect destroyed hardlink topology"
            )
        finally:
            os.umask(previous_umask)
    return {"schema": "cmpct-o162-real-posix-tree-roundtrip-v1", **identity,
            "fixture": fixture, "evidence_class": "installed-product-scope-limited",
            "result": "AUTHENTIC_TREE_FIDELITY_AND_LEGACY_TOPOLOGY_BLINDNESS_CONFIRMED"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    try:
        result = run()
        status = 0
    except Exception as exc:
        status = 1
        result = {
            "schema": "cmpct-o162-real-posix-tree-roundtrip-v1",
            "result": "FAILED_OR_INCONCLUSIVE",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc()[-6000:],
            "git_head": git(["rev-parse", "HEAD"]),
        }
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(status)


if __name__ == "__main__":
    main()
