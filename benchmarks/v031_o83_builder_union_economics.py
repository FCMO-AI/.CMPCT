#!/usr/bin/env python3
"""O83 source-exact real-Builder economic court: O64 versus O80.

One physical filesystem tree per case; separate installed distributions and
fresh child interpreters. Only Builder.build() is timed for creation.
Research evidence, never a substitute for the release parity gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import statistics
import subprocess
import sys
import tempfile
import time

REPS = 5
SHAPES = ("tiny", "xattr", "linked_symlinks")
PARENTS = {
    "base": "b02a30d4ad1b26ea8eea49e11159113caebd6006",
    "candidate": "37833f09dee4671b8ca6f3f3690a7fdebfbc4c70",
}


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bytes_for(i: int, length: int) -> bytes:
    seed = hashlib.sha256(("O83:payload:" + str(i)).encode()).digest()
    return (seed * (1 + length // len(seed)))[:length]


def shape(root: Path, name: str) -> dict:
    root.mkdir(parents=True)
    if name == "tiny":
        for i in range(192):
            (root / f"t{i:04d}.txt").write_bytes(bytes_for(i, 80))
        return {"regular_files": 192, "xattrs": 0, "selected_symlinks": 0}
    if name == "xattr":
        assert hasattr(os, "setxattr") and hasattr(os, "getxattr"), "xattr API absent"
        count = 0
        for i in range(64):
            f = root / f"x{i:04d}.bin"
            f.write_bytes(bytes_for(1000 + i, 640))
            value = bytes_for(5000 + i, 96)
            os.setxattr(f, "user.cmpct_o83", value, follow_symlinks=False)
            assert os.getxattr(f, "user.cmpct_o83", follow_symlinks=False) == value
            count += 1
        return {"regular_files": 64, "xattrs": count, "selected_symlinks": 0}
    if name == "linked_symlinks":
        external = root.parent / "external-hardlinks"
        external.mkdir()
        owner = root / "owner.bin"
        owner.write_bytes(bytes_for(7000, 1024))
        os.link(owner, root / "owner-alias.bin")
        for i in range(96):
            (root / f"f{i:04d}.bin").write_bytes(bytes_for(8000 + i, 640))
        for i in range(64):
            link = root / f"s{i:04d}.link"
            os.symlink("owner.bin", link)
            os.link(link, external / f"s{i:04d}.link", follow_symlinks=False)
            original = os.lstat(link)
            out = os.lstat(external / f"s{i:04d}.link")
            assert (original.st_dev, original.st_ino) == (out.st_dev, out.st_ino)
            assert original.st_nlink >= 2
        return {"regular_files": 98, "xattrs": 0, "selected_symlinks": 64,
                "out_of_tree_symlink_inode_aliases": 64}
    raise AssertionError(name)


def manifest(root: Path) -> str:
    entries = []
    for p in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        rel = p.relative_to(root).as_posix()
        st = p.lstat()
        rec = {"p": rel, "mode": st.st_mode, "mtime_ns": st.st_mtime_ns,
               "dev": st.st_dev, "ino": st.st_ino, "nlink": st.st_nlink}
        if stat.S_ISLNK(st.st_mode):
            rec["target"] = os.readlink(p)
        elif stat.S_ISREG(st.st_mode):
            rec["size"] = st.st_size
            rec["sha256"] = h(p.read_bytes())
        elif not stat.S_ISDIR(st.st_mode):
            raise AssertionError(f"unsupported source test type: {rel}")
        if hasattr(os, "listxattr"):
            keys = sorted(os.listxattr(p, follow_symlinks=False))
            rec["xattrs"] = [(k, h(os.getxattr(p, k, follow_symlinks=False))) for k in keys]
        entries.append(rec)
    return h(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode())


def prove_extraction(root: Path, extracted: Path) -> None:
    original = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
    restored = sorted(p.relative_to(extracted).as_posix() for p in extracted.rglob("*"))
    assert original == restored, ("member set drift", original[:5], restored[:5])
    for rel in original:
        a, b = root / rel, extracted / rel
        sa = a.lstat()
        sb = b.lstat()
        assert stat.S_IFMT(sa.st_mode) == stat.S_IFMT(sb.st_mode), rel
        if stat.S_ISLNK(sa.st_mode):
            assert os.readlink(a) == os.readlink(b), rel
        elif stat.S_ISREG(sa.st_mode):
            assert h(a.read_bytes()) == h(b.read_bytes()), rel
        if hasattr(os, "listxattr"):
            keys = sorted(os.listxattr(a, follow_symlinks=False))
            for key in keys:
                assert os.getxattr(a, key, follow_symlinks=False) == os.getxattr(
                    b, key, follow_symlinks=False), (rel, key)
    if (root / "owner-alias.bin").exists():
        assert os.stat(extracted / "owner.bin").st_ino == os.stat(
            extracted / "owner-alias.bin").st_ino


def worker(a: argparse.Namespace) -> None:
    import resource
    import cmpct.builder
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT

    pkg = Path(a.package).resolve()
    imported = Path(cmpct.builder.__file__).resolve()
    assert imported.is_relative_to(pkg), ("wrong package", imported, pkg)
    root, out = Path(a.root), Path(a.out)
    assert manifest(root) == a.source_sha, "source changed before build"
    wall_start, cpu_start = time.perf_counter_ns(), time.process_time_ns()
    info = Builder(root, workers=1, reproducible=False).build(out)
    create_cpu = time.process_time_ns() - cpu_start
    create_wall = time.perf_counter_ns() - wall_start
    assert manifest(root) == a.source_sha, "source changed after build"
    archive_bytes = out.read_bytes()
    extract_start = time.perf_counter_ns()
    with CMPCT(out) as reader:
        assert reader.verify() >= 1
        target = out.parent / (out.stem + "-extracted")
        reader.extractall(target)
    verify_extract_wall = time.perf_counter_ns() - extract_start
    prove_extraction(root, target)
    print(json.dumps({
        "arm": a.arm, "shape": a.shape, "repeat": a.repeat,
        "source_sha": a.source_sha, "builder_path": str(imported),
        "archive_bytes": len(archive_bytes), "archive_sha": h(archive_bytes),
        "builder_report_bytes": info["bytes"],
        "create_wall_ns": create_wall, "create_cpu_ns": create_cpu,
        "verify_extract_wall_ns": verify_extract_wall,
        "peak_process_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }, sort_keys=True), flush=True)


def court(a: argparse.Namespace) -> None:
    assert sys.platform.startswith("linux"), "O83 resource scope is Linux only"
    scratch = Path(tempfile.mkdtemp(prefix="cmpct-o83-"))
    report = {"experiment": "O83", "scope": "research-only installed source-exact",
              "source_commit": {"base": "9de342226bfbce3690ef1c8cabb1fdf229dbf003",
                                "candidate": "4d65f1bcbc68f1ad770e706197ece8355dd10637"},
              "builder_blobs": PARENTS, "cases": []}
    pkg = {"base": Path(a.base_package).resolve(),
           "candidate": Path(a.candidate_package).resolve()}
    for name in SHAPES:
        root = scratch / name / "source"
        shape_evidence = shape(root, name)
        digest = manifest(root)
        case = {"shape": name, "shape_evidence": shape_evidence,
                "source_sha": digest, "observations": []}
        # Prospective ABBA-like order. Same on-disk source shared by both arms.
        for rep in range(REPS):
            order = ("base", "candidate") if rep % 2 == 0 else ("candidate", "base")
            for arm in order:
                out = scratch / name / f"{rep}-{arm}.cmpct"
                env = os.environ.copy()
                env["PYTHONPATH"] = str(pkg[arm])
                cmd = [sys.executable, str(Path(__file__).resolve()),
                       "--worker", "--arm", arm, "--shape", name,
                       "--package", str(pkg[arm]), "--root", str(root),
                       "--out", str(out), "--source-sha", digest,
                       "--repeat", str(rep)]
                child = subprocess.run(cmd, env=env, cwd=scratch,
                                       capture_output=True, text=True, timeout=120)
                if child.returncode:
                    raise RuntimeError(f"{name}/{arm}/{rep} failed: "
                                       f"{child.returncode}\n{child.stdout[-1500:]}\n{child.stderr[-4000:]}")
                obj = json.loads(child.stdout.strip().splitlines()[-1])
                assert obj["arm"] == arm and obj["source_sha"] == digest
                case["observations"].append(obj)
        assert manifest(root) == digest, "shared physical source mutated"
        by_arm = {k: [r for r in case["observations"] if r["arm"] == k]
                  for k in ("base", "candidate")}
        assert all(len(rs) == REPS for rs in by_arm.values())
        med = lambda arm, metric: statistics.median(
            x[metric] for x in by_arm[arm])
        case["summary"] = {
            "base_bytes": by_arm["base"][0]["archive_bytes"],
            "candidate_bytes": by_arm["candidate"][0]["archive_bytes"],
            "byte_delta": by_arm["candidate"][0]["archive_bytes"] -
                          by_arm["base"][0]["archive_bytes"],
            "base_wall_ms": med("base", "create_wall_ns") / 1e6,
            "candidate_wall_ms": med("candidate", "create_wall_ns") / 1e6,
            "base_cpu_ms": med("base", "create_cpu_ns") / 1e6,
            "candidate_cpu_ms": med("candidate", "create_cpu_ns") / 1e6,
            "base_verify_extract_wall_ms": med("base", "verify_extract_wall_ns") / 1e6,
            "candidate_verify_extract_wall_ms": med("candidate", "verify_extract_wall_ns") / 1e6,
            "base_peak_rss_kib": med("base", "peak_process_rss_kib"),
            "candidate_peak_rss_kib": med("candidate", "peak_process_rss_kib"),
        }
        case["size_parity"] = (
            len({x["archive_sha"] for x in case["observations"]}) == 1
            and len({x["archive_bytes"] for x in case["observations"]}) == 1
        )
        report["cases"].append(case)
        print("O83_CASE=" + json.dumps({"shape": name, **case["summary"],
                                         "size_parity": case["size_parity"]},
                                        sort_keys=True), flush=True)
        # Keep raw observations even if actual full archive parity is red.
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("O83_REAL_OBSERVATIONS=" + str(sum(len(x["observations"]) for x in report["cases"])),
          flush=True)
    assert len(report["cases"]) == 3
    assert all(x["size_parity"] for x in report["cases"]), "complete stored bytes differ"
    print("O83_SAME_SOURCE_BYTES_PARITY=PASS; not a release gate", flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--arm", choices=("base", "candidate"))
    p.add_argument("--shape", choices=SHAPES)
    p.add_argument("--repeat", type=int)
    p.add_argument("--package")
    p.add_argument("--root")
    p.add_argument("--out")
    p.add_argument("--source-sha")
    p.add_argument("--base-package")
    p.add_argument("--candidate-package")
    p.add_argument("--report", default="o83-evidence/result.json")
    a = p.parse_args()
    if a.worker:
        worker(a)
    else:
        court(a)


if __name__ == "__main__":
    main()
