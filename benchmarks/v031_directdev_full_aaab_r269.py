#!/usr/bin/env python3
"""Research-only source-identical full-harness sham vs true A/B, source-locked.

Does NOT change canonical benchmark, aggregator, comparator, timings, or thresholds.
Stores the original per-invocation JSON and the actual archive SHA-256s after each run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

CANONICAL = "4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b"
CANDIDATE_PARENT = "fb87f582918bd7ca0f16559eed2f782739977048"
NAMES = ("tiny", "source", "media", "binary", "dedup_links", "sparse", "nested", "combined")
LAYERS = ("library", "cli")


def check_git(root: Path, sha: str) -> None:
    actual = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if actual != sha:
        raise RuntimeError(f"source mismatch: {root}: {actual} != {sha}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while b := f.read(1024 * 1024):
            h.update(b)
    return h.hexdigest()


def run_court(name: str, labels: tuple[str, str, str, str], engines: dict, benchmarks: Path, corpus: Path, evidence: Path):
    outputs = []
    for idx, label in enumerate(labels):
        source = engines[label]
        tag = f"{name}-{idx + 1}-{label}"
        env = dict(os.environ)
        env["PYTHONPATH"] = str(source / "src")
        env["CMPCT_PARITY_CORPUS_ROOT"] = str(corpus)
        env["CMPCT_PARITY_REPS"] = "7"
        # Bind actual import resolution; the runner's installed candidate is not a substitute.
        imp = subprocess.check_output(
            [sys.executable, "-c",
             "import cmpct,cmpct.builder; print(cmpct.__file__); print(cmpct.builder.__file__)"],
            cwd=benchmarks, env=env, text=True).splitlines()
        expected = (source / "src" / "cmpct").resolve()
        if not all(Path(p).resolve().is_relative_to(expected) for p in imp):
            raise RuntimeError(f"{tag}: wrong imported package: {imp}, expected {expected}")
        logfile = evidence / f"{tag}.stdout.txt"
        with logfile.open("w") as f:
            subprocess.run([sys.executable, "zip_parity_bench.py"], cwd=benchmarks,
                           env=env, stdout=f, stderr=subprocess.STDOUT, check=True)
        output_dir = benchmarks / "_parity_work" / "out"
        artifact = evidence / f"{tag}.json"
        shutil.copyfile(output_dir / "zip-parity.json", artifact)
        parsed = json.loads(artifact.read_text())
        if parsed.get("schema") != "cmpct-zip-parity-v1" or parsed.get("repetitions") != 7:
            raise RuntimeError(f"{tag}: unexpected benchmark semantics")
        manifest = {}
        for corpus_name in NAMES:
            for layer in LAYERS:
                for ext in ("cmpct", "zip"):
                    filename = f"{corpus_name}.{layer}.{ext}"
                    path = output_dir / filename
                    field = parsed["corpora"][corpus_name][layer][ext]
                    if not isinstance(field["bytes"], int) or isinstance(field["bytes"], bool):
                        raise RuntimeError(f"{tag}: nonintegral archive bytes")
                    if path.stat().st_size != field["bytes"]:
                        raise RuntimeError(f"{tag}: completed archive size differs from benchmark JSON")
                    manifest[filename] = {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        (evidence / f"{tag}.archive-sha256.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        outputs.append((label, tag))
        print(f"COURT_RUN name={name} step={idx + 1} label={label} source={source}"
              f" binary_ms={parsed['corpora']['binary']['library']['cmpct']['create_s_median'] * 1000:.4f}", flush=True)

    a = [tag for label, tag in outputs if label == labels[0]]
    b = [tag for label, tag in outputs if label != labels[0]]
    if len(a) != 2 or len(b) != 2:
        raise RuntimeError(f"{name}: invalid ABBA control order")
    aggregator = evidence.parent / "tools" / "aggregate_parity_runs.py"
    checker = evidence.parent / "tools" / "check_performance_regression.py"
    ba = evidence / f"{name}.base.json"
    bb = evidence / f"{name}.candidate.json"
    subprocess.run([sys.executable, str(aggregator), "--out", str(ba),
                    *(str(evidence / (tag + ".json")) for tag in a)], check=True)
    subprocess.run([sys.executable, str(aggregator), "--out", str(bb),
                    *(str(evidence / (tag + ".json")) for tag in b)], check=True)
    comp = subprocess.run(
        [sys.executable, str(checker), "--base", str(ba), "--candidate", str(bb),
         "--max-time-regression", "0.05", "--max-size-regression", "0.01"],
        capture_output=True, text=True)
    (evidence / f"{name}.comparator.txt").write_text(comp.stdout + "\nSTDERR:\n" + comp.stderr)
    (evidence / f"{name}.comparator.exit").write_text(str(comp.returncode) + "\n")

    aggregate_a = json.loads(ba.read_text())
    aggregate_b = json.loads(bb.read_text())
    all_equal_size = all(
        aggregate_a["corpora"][corpus]["__".replace("__", layer)]["cmpct"]["bytes"]
        == aggregate_b["corpora"][corpus][layer]["cmpct"]["bytes"]
        for corpus in NAMES for layer in LAYERS)
    # Archive digest comparison is stronger than archive size but is only about the *produced*
    # archive, not a snapshot of every input inode/xattr or a Reader semantic guarantee.
    first = json.loads((evidence / f"{outputs[0][1]}.archive-sha256.json").read_text())
    mismatches = []
    for label, tag in outputs[1:]:
        d = json.loads((evidence / f"{tag}.archive-sha256.json").read_text())
        mismatches.extend([f"{tag}:{key}" for key in first if first[key] != d[key]])
    raw = {
        "court": name, "labels": list(labels),
        "source_heads": {key: str(value) for key, value in engines.items()},
        "run_tags": [t for _,t in outputs],
        "comparator_exit": comp.returncode,
        "all_16_cmpct_sizes_equal": all_equal_size,
        "archives_per_run": len(first),
        "archive_sha256_mismatches": mismatches,
        "binary_library_create_medians_ms": {
            "base": aggregate_a["corpora"]["binary"]["library"]["cmpct"]["create_s_median"] * 1000,
            "candidate": aggregate_b["corpora"]["binary"]["library"]["cmpct"]["create_s_median"] * 1000,
        },
        "negative_zip_control_medians_ms": {
            "base": aggregate_a["corpora"]["binary"]["library"]["zip"]["create_s_median"] * 1000,
            "candidate": aggregate_b["corpora"]["binary"]["library"]["zip"]["create_s_median"] * 1000,
        },
        "claim_boundary": "Research only; comparator red blocks promotion. Workflow SUCCESS is not release PASS.",
    }
    (evidence / f"{name}.decision.json").write_text(json.dumps(raw, sort_keys=True, indent=2) + "\n")
    print("COURT_DECISION " + json.dumps(raw, sort_keys=True), flush=True)
    # A real archive mismatch is material correctness truth, not something to waive as timing noise.
    if not all_equal_size or mismatches:
        raise RuntimeError(f"{name}: archive size/identity disagreement")
    return raw


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-root", type=Path, required=True)
    p.add_argument("--candidate-root", type=Path, required=True)
    p.add_argument("--corpus-root", type=Path, required=True)
    p.add_argument("--evidence-dir", type=Path, required=True)
    args = p.parse_args()
    a = args.base_root.resolve()
    b = args.candidate_root.resolve()
    check_git(a, CANONICAL)
    exact_parent = subprocess.run(["git", "-C", str(b), "merge-base", "--is-ancestor",
                                   CANDIDATE_PARENT, "HEAD"])
    if exact_parent.returncode:
        raise RuntimeError("research candidate is not derived from exact product parent")
    # No research change may alter code, native, release corpus, comparator or formatter.
    quiet = subprocess.run(["git", "-C", str(b), "diff", "--quiet", CANDIDATE_PARENT,
                            "HEAD", "--", "src/", "native/", "benchmarks/", "pyproject.toml",
                            "tools/check_performance_regression.py",
                            "tools/aggregate_parity_runs.py"])
    if quiet.returncode:
        raise RuntimeError("unauthorized candidate product/harness mutation")
    for path in ("src/cmpct/builder.py", "src/cmpct/codec.py",
                 "native/cmpct-core/src/lib.rs", "benchmarks/zip_parity_bench.py"):
        ha = sha256_file(a / path)
        hb = sha256_file(b / path)
        if ha != hb:
            raise RuntimeError(f"previously equal code diverged: {path} {ha} {hb}")
    root = args.evidence_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    candidate = b
    # Same source path for sham labels to exclude build/wheel import identity.
    sham = run_court("sham", ("A0", "A1", "A1", "A0"),
                     {"A0":a, "A1":a}, b / "benchmarks",
                     args.corpus_root.resolve(), root)
    actual = run_court("true-ab", ("A", "B", "B", "A"),
                       {"A":a, "B":candidate}, b / "benchmarks",
                       args.corpus_root.resolve(), root)
    (root / "outcome.json").write_text(json.dumps(
        {"schema":"cmpct-v031-source-matched-full-aaab-r269-v1",
         "canonical_source":CANONICAL,"candidate_product_source":CANDIDATE_PARENT,
         "research_source":subprocess.check_output(["git","-C",str(b),"rev-parse","HEAD"],text=True).strip(),
         "sham":sham,"true_ab":actual}, sort_keys=True, indent=2)+"\n")
    print("RESEARCH_COMPLETED_REDS_PRESERVED: canonical gate unchanged; no release credit")


if __name__ == "__main__":
    main()
