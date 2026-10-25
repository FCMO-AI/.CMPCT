#!/usr/bin/env python3
"""O124: independent child-process court for Reader archive/output inode aliases.

The source archive is copied separately for every alternative, and the archive SHA is
checked by the parent even when a faulty Reader crashes after truncating its own input.
Baseline/candidate share the identical fixture bytes and destination semantics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time


def sha_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def child(engine: Path, archive: Path, dest: Path, payload_sha: str) -> int:
    sys.path.insert(0, str(engine))
    from cmpct.reader import CMPCT
    import cmpct.reader
    print("O124_ENGINE=" + str(Path(cmpct.reader.__file__).resolve()), flush=True)
    try:
        with CMPCT(archive) as reader:
            payload = reader.read("payload.bin")
            if hashlib.sha256(payload).hexdigest() != payload_sha:
                raise AssertionError("source archive member SHA mismatch before extraction")
            print("O124_READER_OPENED", flush=True)
            reader.extractall(dest, metadata=False)
        print("O124_COMPLETED", flush=True)
        return 0
    except IOError as exc:
        if "extraction destination aliases open source archive:" in str(exc):
            print("O124_EXPLICIT_ALIAS_REFUSAL: " + str(exc), flush=True)
            return 47
        if "pre-existing destination hardlink alias:" in str(exc) or "pre-existing destination symlink:" in str(exc):
            print("O124_PARENT_STATIC_REFUSAL: " + str(exc), flush=True)
            return 48
        raise


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-src", type=Path, required=True)
    ap.add_argument("--parent-src", type=Path, required=True)
    ap.add_argument("--candidate-src", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.base_src = args.base_src.resolve()
    args.parent_src = args.parent_src.resolve()
    args.candidate_src = args.candidate_src.resolve()
    import cmpct.builder
    from cmpct.builder import Builder

    # Fixed bytes, no dependency on the generated archive's random filename or inode.
    payload = hashlib.shake_256(b"O124-v1-physical-archive-self-alias").digest(262144)
    payload_sha = hashlib.sha256(payload).hexdigest()
    observations = []
    with tempfile.TemporaryDirectory(prefix="cmpct-o118-") as tmp:
        root = Path(tmp)
        source_tree = root / "source-tree"
        source_tree.mkdir()
        (source_tree / "payload.bin").write_bytes(payload)
        seed = root / "immutable-seed.cmpct"
        Builder(source_tree, workers=1, reproducible=True).build(seed)
        original_sha = sha_file(seed)
        if not original_sha:
            raise AssertionError("fixture Builder failed")

        for engine_name, engine in (("baseline", args.base_src), ("parent", args.parent_src), ("candidate", args.candidate_src)):
            for case in ("clean", "same-path", "hardlink", "symlink"):
                case_root = root / (engine_name + "-" + case)
                case_root.mkdir()
                dest = case_root / "out"
                dest.mkdir()
                if case == "same-path":
                    archive = dest / "payload.bin"
                else:
                    archive = case_root / "source.cmpct"
                shutil.copy2(seed, archive)
                leaf = dest / "payload.bin"
                if case == "hardlink":
                    os.link(archive, leaf)
                elif case == "symlink":
                    os.symlink(archive, leaf)
                before = sha_file(archive)
                if before != original_sha:
                    raise AssertionError("fixture bytes differed before child")
                cmd = [sys.executable, __file__, "--child", str(engine),
                       str(archive), str(dest), payload_sha]
                t0 = time.monotonic()
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=12,
                                            env={**os.environ, "PYTHONPATH": str(engine)})
                    rc = result.returncode
                    stdout = result.stdout
                    stderr = result.stderr
                except subprocess.TimeoutExpired as exc:
                    rc = "TIMEOUT"
                    stdout = str(exc.stdout or "")
                    stderr = str(exc.stderr or "")
                after = sha_file(archive)
                unchanged = after == original_sha
                exact_output = leaf.is_file() and sha_file(leaf) == payload_sha
                opened = "O124_READER_OPENED" in stdout
                record = {"engine": engine_name, "case": case, "returncode": rc,
                          "source_unchanged": unchanged, "source_after_sha256": after,
                          "exact_member_output": exact_output, "child_opened": opened,
                          "elapsed_s": round(time.monotonic() - t0, 3),
                          "stdout": stdout[-1400:], "stderr": stderr[-1400:]}
                observations.append(record)
                print(json.dumps(record, sort_keys=True), flush=True)
                if not opened:
                    raise AssertionError(f"{engine_name}/{case}: child never reached Reader-open control")
                if case == "clean":
                    if rc != 0 or not unchanged or not exact_output:
                        raise AssertionError(f"{engine_name}: clean extraction or source integrity failed")
                elif engine_name == "baseline":
                    # Actual unmodified Reader must show real destructive source mutation.
                    if unchanged:
                        raise AssertionError(f"{case}: original Reader did not corrupt/delete its source")
                elif engine_name == "parent":
                    if case == "same-path":
                        if unchanged:
                            raise AssertionError("parent surprisingly protected single-link same-path source")
                    elif rc != 48 or not unchanged:
                        raise AssertionError(f"{case}: inherited #294 static guard did not reject and preserve archive")
                else:
                    if rc != 47 or not unchanged:
                        raise AssertionError(f"{case}: candidate did not refuse safely before mutation")

        receipt = {"schema": "cmpct-o118-source-inode-alias-v1",
                   "source_sha256": original_sha, "payload_sha256": payload_sha,
                   "baseline_src": str(args.base_src),
                   "parent_src": str(args.parent_src),
                   "candidate_src": str(args.candidate_src),
                   "observations": observations, "decision": "O124_STATIC_ALIAS_GUARD_PASS"}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(receipt, indent=2) + "\n")
        print("O124_STATIC_ALIAS_GUARD_PASS", flush=True)
    return 0


if __name__ == "__main__":
    if "--child" in sys.argv:
        p = sys.argv
        sys.exit(child(Path(p[p.index("--child")+1]), Path(p[p.index("--child")+2]),
                       Path(p[p.index("--child")+3]), p[p.index("--child")+4]))
    sys.exit(main())
