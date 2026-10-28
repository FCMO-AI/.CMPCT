#!/usr/bin/env python3
"""J24I04: same-source complete canonical ABBA research court; never a release waiver.

This executes, but does not modify, the current candidate's full zip_parity_bench.py,
aggregate_parity_runs.py, and check_performance_regression.py on one fixed corpus.
Both A and B checkouts MUST be the exact same #704 commit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import time

SOURCE = "293aa161a4a13b4c1f4fd0f5089aa62e4dbeedef"
NAMES = ("tiny", "source", "media", "binary", "dedup_links", "sparse", "nested", "combined")
ORDER = (("base-a", "A"), ("candidate-a", "B"), ("candidate-b", "B"), ("base-b", "A"))
FIXED_NS = 1767225600 * 1_000_000_000


def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def command(*args: str, cwd: Path | None = None, env: dict | None = None) -> str:
    return subprocess.check_output(list(args), cwd=cwd, env=env, text=True).strip()


def source_receipt(root: Path) -> dict:
    if command("git", "-C", str(root), "rev-parse", "HEAD") != SOURCE:
        raise RuntimeError("source SHA mismatch: " + str(root))
    src = root / "src" / "cmpct"
    paths = sorted(p for p in src.rglob("*.py") if p.is_file())
    native = sorted(p for p in src.glob("cmpct_core*") if p.is_file() and
                    p.suffix in (".so", ".pyd", ".dll", ".dylib"))
    if not native or len(native) != 1:
        raise RuntimeError("missing or ambiguous native payload: " + str(native))
    env = dict(os.environ, PYTHONPATH=str(root / "src"))
    probe = json.loads(command(sys.executable, "-c",
        "import json,cmpct; from cmpct import native_codec;"
        "print(json.dumps({'package':str(cmpct.__file__),"
        "'native':str(native_codec._library_path())}))", cwd=root, env=env))
    for k, v in probe.items():
        if not Path(v).resolve().is_relative_to(src.resolve()):
            raise RuntimeError(f"wrong {k} ownership: {v}")
    return {
        "source_commit": SOURCE, "engine_root": str(root.resolve()),
        "python_source_sha256": {str(p.relative_to(src)): sha_file(p) for p in paths},
        "native_sha256": sha_file(native[0]),
        "native_bytes": native[0].stat().st_size,
        "native_name": native[0].name, "imported_paths": probe,
    }


def create_corpus(harness: Path, corpus: Path) -> None:
    # Use the original canonical generator and identical timestamp normalization.
    sys.path.insert(0, str(harness / "benchmarks"))
    import universal_bench as universal
    corpus.mkdir(parents=True, exist_ok=False)
    universal.CORP = corpus
    universal.reset_rng()
    universal.make_corpora()
    if not set(NAMES) <= {p.name for p in corpus.iterdir() if p.is_dir()}:
        raise RuntimeError("canonical eight-corpus generation incomplete")
    paths = sorted(corpus.rglob("*"), key=lambda p: (len(p.parts), p.as_posix()), reverse=True)
    for p in paths:
        try:
            os.utime(p, ns=(FIXED_NS, FIXED_NS), follow_symlinks=False)
        except (NotImplementedError, OSError):
            if not p.is_symlink():
                raise
    os.utime(corpus, ns=(FIXED_NS, FIXED_NS))


def corpus_fingerprint(corpus: Path) -> dict:
    # The same hash fields and byte order used in the unmodified official gate.
    h = hashlib.sha256()
    count = logical = 0
    for p in sorted(corpus.rglob("*")):
        rel = p.relative_to(corpus).as_posix().encode()
        st = p.lstat()
        h.update(len(rel).to_bytes(4, "little"))
        h.update(rel)
        h.update((st.st_mode & 0o177777).to_bytes(4, "little"))
        h.update(st.st_mtime_ns.to_bytes(8, "little", signed=True))
        if p.is_symlink():
            target = os.readlink(p).encode()
            h.update(b"L")
            h.update(len(target).to_bytes(4, "little"))
            h.update(target)
        elif p.is_file():
            count += 1
            logical += st.st_size
            h.update(b"F")
            h.update(st.st_size.to_bytes(8, "little"))
            with p.open("rb") as f:
                for b in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(b)
        elif p.is_dir():
            h.update(b"D")
    return {"tree_sha256": h.hexdigest(), "files": count,
            "logical_bytes": logical, "fixed_mtime_ns": FIXED_NS}


def run_python(argv: list[str], *, cwd: Path, env: dict, stdout: Path,
               stderr: Path) -> tuple[int, float]:
    t = time.perf_counter()
    with stdout.open("w", encoding="utf8") as out, stderr.open("w", encoding="utf8") as err:
        p = subprocess.run([sys.executable, *argv], cwd=cwd, env=env,
                           stdout=out, stderr=err)
    return p.returncode, time.perf_counter() - t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", type=Path, required=True)
    ap.add_argument("--engine-a", type=Path, required=True)
    ap.add_argument("--engine-b", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ns = ap.parse_args()
    harness, a, b = (p.resolve() for p in (ns.harness, ns.engine_a, ns.engine_b))
    output = ns.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / "started_utc.txt").write_text(datetime.now(timezone.utc).isoformat() + "\n")
    corpus = output / "corpus"
    record = {"schema": "cmpct-v031-j24i04-full-matrix-aa-v1",
              "question": "can unmodified full canonical gate red on identical #704 code?",
              "expected_engine_sha": SOURCE,
              "research_only": True,
              "repetitions_per_sweep": 7,
              "order": list(ORDER),
              "harness_commit": command("git", "-C", str(harness), "rev-parse", "HEAD"),
              "platform": platform.platform(), "python": sys.version,
              "sweeps": [], "diagnostic_gate_return_code": None}
    try:
        ra, rb = source_receipt(a), source_receipt(b)
        for key in ("python_source_sha256", "native_sha256", "native_bytes", "native_name"):
            if ra[key] != rb[key]:
                raise RuntimeError("A/B source or native mismatch in " + key)
        record["engine_a"] = ra
        record["engine_b"] = rb
        for rel in ("benchmarks/zip_parity_bench.py", "benchmarks/universal_bench.py",
                    "tools/aggregate_parity_runs.py", "tools/check_performance_regression.py"):
            record.setdefault("harness_sha256", {})[rel] = sha_file(harness / rel)
        create_corpus(harness, corpus)
        before = corpus_fingerprint(corpus)
        record["corpus_before"] = before
        (output / "corpus-manifest.json").write_text(json.dumps(before, indent=2) + "\n")
        hashes = {}
        for label, side in ORDER:
            source = a if side == "A" else b
            env = dict(os.environ, PYTHONPATH=str(source / "src"),
                       CMPCT_PARITY_CORPUS_ROOT=str(corpus), CMPCT_PARITY_REPS="7")
            code, seconds = run_python(["zip_parity_bench.py"], cwd=harness / "benchmarks",
                env=env, stdout=output / f"{label}.stdout.txt",
                stderr=output / f"{label}.stderr.txt")
            row = {"label": label, "side": side, "engine_sha": SOURCE,
                   "engine_root": str(source), "return_code": code,
                   "process_wall_s": seconds, "timestamp_utc": datetime.now(timezone.utc).isoformat()}
            record["sweeps"].append(row)
            (output / "progress.json").write_text(json.dumps(record, indent=2) + "\n")
            if code:
                raise RuntimeError(f"original benchmark failed at {label} rc={code}")
            result_path = harness / "benchmarks" / "_parity_work" / "out"
            src_json = result_path / "zip-parity.json"
            if not src_json.is_file():
                raise RuntimeError("unmodified original benchmark produced no JSON")
            shutil.copy2(src_json, output / f"{label}.json")
            all_names = set(json.loads(src_json.read_text())["corpora"])
            if all_names != set(NAMES):
                raise RuntimeError(f"wrong canonical corpus names: {all_names}")
            observed = {}
            for name in NAMES:
                for layer in ("library", "cli"):
                    f = result_path / f"{name}.{layer}.cmpct"
                    observed[f"{name}/{layer}"] = (f.stat().st_size, sha_file(f))
                    if name == "binary" and layer == "library" and label in ("base-a", "candidate-a"):
                        shutil.copy2(f, output / f"{label}-binary-library.cmpct")
            hashes[label] = observed
            row["archive_sha256"] = observed
            if corpus_fingerprint(corpus) != before:
                raise RuntimeError("corpus mutated during " + label)
        if any(hashes[k] != hashes["base-a"] for k in hashes):
            raise RuntimeError("identical source did not produce identical complete archives")
        record["corpus_after"] = corpus_fingerprint(corpus)
        tools = harness / "tools"
        for label, components in (
            ("base", ("base-a.json", "base-b.json")),
            ("candidate", ("candidate-a.json", "candidate-b.json"))
        ):
            cmd = [str(tools / "aggregate_parity_runs.py"), "--out",
                   str(output / f"{label}.json"),
                   *(str(output / f) for f in components)]
            subprocess.run([sys.executable, *cmd], check=True, cwd=harness)
        chk = subprocess.run([sys.executable, str(tools / "check_performance_regression.py"),
            "--base", str(output / "base.json"), "--candidate",
            str(output / "candidate.json"), "--summary",
            str(output / "unchanged-release-checker.md")],
            cwd=harness, text=True, capture_output=True)
        (output / "unchanged-release-checker.stdout.txt").write_text(chk.stdout)
        (output / "unchanged-release-checker.stderr.txt").write_text(chk.stderr)
        if chk.returncode not in (0, 1):
            raise RuntimeError("unmodified release checker infrastructure failure")
        record["diagnostic_gate_return_code"] = chk.returncode
        record["decision"] = "AA_FALSE_RED_REPRODUCED" if chk.returncode else "AA_FULL_NEUTRAL"
        print(f"J24I04 {record['decision']} full-matrix same-source #704 A/A; NOT release credit")
    except Exception as exc:
        record["decision"] = "INVALID_OR_INFRASTRUCTURE"
        record["error"] = repr(exc)
        raise
    finally:
        record["ended_utc"] = datetime.now(timezone.utc).isoformat()
        (output / "j24i04-record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
