#!/usr/bin/env python3
"""Local cold-tree comparison. Private paths/hashes stay in the work directory.

This is a fresh-process, warm/uncontrolled-cache experiment, not a release gate.
Both tar pipelines are checked for upstream failures (including late checksum errors).
Only aggregate results are exported; inspect them before publishing private-corpus data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def manifest(root):
    result = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(directory) / name
            st = path.lstat()
            rel = path.relative_to(root).as_posix()
            if stat.S_ISLNK(st.st_mode):
                result[rel] = ["l", os.readlink(path)]
            elif stat.S_ISDIR(st.st_mode):
                result[rel] = ["d"]
            elif stat.S_ISREG(st.st_mode):
                result[rel] = ["f", st.st_size, digest(path)]
            else:
                raise ValueError("unsupported source kind; no silent omission")
    return result


def timed_pipeline(commands, work, label, *, output=None, env=None):
    """Wall covers all children; RSS is max individual high-water mark, never a sum."""
    started = time.monotonic()
    children = []
    previous = None
    with (output.open("wb") if output else open(os.devnull, "wb")) as sink:
        with (work / (label + ".stderr")).open("wb") as errors:
            for i, command in enumerate(commands):
                last = i == len(commands) - 1
                rss = work / f"{label}-{i}.rss"
                child = subprocess.Popen(
                    ["/usr/bin/time", "-f", "%M", "-o", str(rss), *command],
                    stdin=previous if previous else subprocess.DEVNULL,
                    stdout=sink if last else subprocess.PIPE,
                    stderr=errors, env=env,
                )
                if previous:
                    previous.close()
                previous = None if last else child.stdout
                children.append((child, rss))
            codes = [child.wait() for child, _ in children]
    elapsed = time.monotonic() - started
    if any(codes):
        raise RuntimeError(f"{label}: child exit codes {codes}; private diagnostics in work directory")
    return {"wall_s": elapsed,
            "rss_max_child_kib": max(int(rss.read_text().strip()) for _, rss in children)}


def check_no_link_parents(entries):
    """Trusted-source link restoration still must not redirect any materialized member."""
    links = {name for name, row in entries.items() if row[0] == "l"}
    for name in entries:
        parts = name.split("/")
        if any("/".join(parts[:i]) in links for i in range(1, len(parts))):
            raise ValueError("a source link is a parent of another member")


def measure(source, work, engines, repetitions=1, cmpct_src=None, trusted_source_links=False,
            diagnostic_runtime=False):
    if source == work or source in work.parents or work in source.parents:
        raise ValueError("source and work must be disjoint")
    work.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, TMPDIR=str(work), PYTHONDONTWRITEBYTECODE="1")
    if cmpct_src:
        env["PYTHONPATH"] = str(cmpct_src)
        env["CMPCT_DIAGNOSTIC_SOURCE"] = str(cmpct_src)
    print("Calculando hashes del árbol completo…", flush=True)
    before = manifest(source)
    check_no_link_parents(before)
    # Names and hashes never appear in aggregate output or stdout.
    (work / "manifest.private.json").write_text(json.dumps(before))
    files = sorted((v[1], k) for k, v in before.items() if v[0] == "f")
    if not files:
        raise ValueError("no regular source files")
    size, member = files[len(files) // 2]
    results = {"schema": "cmpct-cold-tree-v1", "repetitions": repetitions,
               "logical_bytes": sum(n for n, _ in files), "regular_files": len(files),
               "directories": sum(v[0] == "d" for v in before.values()),
               "symlinks": sum(v[0] == "l" for v in before.values()),
               "selected_member_bytes": size, "results": {},
               "cmpct_runtime": ("DIAGNOSTIC_SUBSTITUTED_BACKEND_NOT_RELEASE_EVIDENCE"
                                 if diagnostic_runtime else "normal package entry point"),
               "semantics": {
                   "layer": "fresh processes, full CLI; uncontrolled/warm filesystem cache",
                   "rss": "maximum individual child high-water RSS, not simultaneous aggregate",
                   "exactness": "SHA-256 of every regular file; full path/kind set and symlink targets",
                   "metadata": "default encoder/extractor settings; ownership/xattrs/hardlink topology not adjudicated",
                   "integrity": "tar zstd checksums; CMPCT read validation; external SHA-256 after extraction",
                   "durability": "no fsync on either side", "tar": "GNU tar --sort=name, default format",
                   "cmpct_source_links": "explicit trusted-source restoration" if trusted_source_links else "default safe policy",
               }}
    for engine in engines:
        rows = []
        results["results"][engine] = rows
        for rep in range(repetitions):
            print(f"Midiendo {engine}, repetición {rep + 1}…", flush=True)
            archive = work / f"{engine}-{rep}.archive"
            dest = work / f"{engine}-{rep}.restored"
            dest.mkdir()
            selected = work / f"{engine}-{rep}.member"
            cli = ([sys.executable, str(Path(__file__).with_name("diagnostic_zstd_adapter.py"))]
                   if diagnostic_runtime else [sys.executable, "-m", "cmpct"])
            if engine == "cmpct":
                create = [cli + ["create", str(source), str(archive), "--workers", "4"]]
                extract = [cli + ["extract", str(archive), str(dest)]]
                if trusted_source_links:
                    extract[0].append("--unsafe-symlinks")
                single = [cli + ["cat", str(archive), member]]
            elif engine in ("zstd", "zstd-long"):
                flags = ["--long=31"] if engine == "zstd-long" else []
                create = [["tar", "--sort=name", "-cf", "-", "-C", str(source), "."],
                          ["zstd", "-q", "-19", "-T4", *flags, "-c"]]
                decode = ["zstd", "-q", "-d", "--long=31", "-c", str(archive)]
                extract = [decode, ["tar", "-xf", "-", "-C", str(dest)]]
                # Do not stop early: all bytes pass through the checksum decoder and tar.
                single = [decode, ["tar", "-xOf", "-", "--", "./" + member]]
            else:
                raise ValueError("unknown engine")
            row = {"create": timed_pipeline(create, work, f"{engine}-{rep}-create",
                                             output=archive if engine != "cmpct" else None, env=env),
                   "bytes": archive.stat().st_size}
            row["extract"] = timed_pipeline(extract, work, f"{engine}-{rep}-extract", env=env)
            row["roundtrip_exact"] = manifest(dest) == before
            if not row["roundtrip_exact"]:
                raise RuntimeError("restored tree does not match source manifest")
            row["single"] = timed_pipeline(single, work, f"{engine}-{rep}-single", output=selected, env=env)
            row["single_exact"] = selected.stat().st_size == size and digest(selected) == before[member][2]
            if not row["single_exact"]:
                raise RuntimeError("selected member does not match source")
            rows.append(row)
            (work / "aggregate.json").write_text(json.dumps(results, indent=2) + "\n")
            # Only our own newly created restore tree is removed. Archives/logs remain for audit.
            shutil.rmtree(dest)
            selected.unlink()
    results["source_stable"] = manifest(source) == before
    if not results["source_stable"]:
        raise RuntimeError("source changed during benchmark; comparison invalid")
    (work / "aggregate.json").write_text(json.dumps(results, indent=2) + "\n")
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path)
    ap.add_argument("work", type=Path, help="new directory, disjoint from source")
    ap.add_argument("--engines", nargs="+", choices=["cmpct", "zstd", "zstd-long"],
                    default=["cmpct", "zstd-long", "zstd"])
    ap.add_argument("--cmpct-src", type=Path)
    ap.add_argument("--repetitions", type=int, default=3)
    ap.add_argument("--trusted-source-links", action="store_true",
                    help="restore the original trusted source's link bytes; refuse link-parent pivots")
    ap.add_argument("--diagnostic-runtime", action="store_true",
                    help="explicit ambient Zstd/MessagePack substitution; never release evidence")
    args = ap.parse_args()
    if args.repetitions < 1:
        ap.error("repetitions must be positive")
    print(json.dumps(measure(args.source.resolve(), args.work.resolve(), args.engines,
                             args.repetitions, args.cmpct_src, args.trusted_source_links,
                             args.diagnostic_runtime), indent=2))
