"""J24G48 installed-Reader physical journal rekey cost court.

Source-exact, identical r24 bytes for both implementations. Research only.
The older implementation is a known *incorrect* semantic negative, not a valid
release performance comparator. Never weaken the metadata identity oracle.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
import time


REPO = "FCMO-AI/.CMPCT"
BASE_SHA = "78b9dd2d148350898c95a0cdbeefe760de2e567e"
CAND_SHA = "893aac3f6b7b54e89d71af6970405ff5fc71aef7"
MARKER = "user.cmpct_j24g48"
CASES = [(256, 32), (2048, 0), (2048, 32), (2048, 2)]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_identity() -> dict:
    root = Path(os.environ["CMPCT_SOURCE_ROOT"]).resolve()
    expected = os.environ["CMPCT_EXPECTED_SHA"]
    git_sha = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if git_sha != expected:
        raise AssertionError("source HEAD mismatch: " + git_sha)
    mod = importlib.import_module("cmpct.reader")
    module_file = Path(mod.__file__).resolve()
    if not module_file.is_relative_to(root / "src"):
        raise AssertionError("imported Reader is not the pinned Git checkout: " + str(module_file))
    checkout_source = root / "src/cmpct/reader.py"
    if checkout_source.read_bytes() != module_file.read_bytes():
        raise AssertionError("installed Reader bytes differ")
    return {"git_sha": git_sha, "reader_sha256": digest(checkout_source),
            "reader_path": str(module_file)}


def fixture(case_dir: Path, count: int, divisor: int) -> dict:
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.transactions import append_update

    case_dir.mkdir(parents=True, exist_ok=False)
    source = case_dir / "source"
    source.mkdir()
    expected = {}
    for i in range(count):
        name = f"m{i:06d}.bin"
        target = source / name
        target.write_bytes(hashlib.sha256(name.encode()).digest() + b"\x00\xff")
        if divisor and i % divisor == 0:
            value = hashlib.sha256(("attribute:" + name).encode()).digest()[:16]
            os.setxattr(target, MARKER, value, follow_symlinks=False)
            if os.getxattr(target, MARKER, follow_symlinks=False) != value:
                raise AssertionError("physical source xattr precondition failed")
            expected[name] = value.hex()

    original = case_dir / "original.cmpct"
    start = time.perf_counter_ns()
    Builder(source, workers=1, reproducible=False).build(original)
    build_ns = time.perf_counter_ns() - start
    insert = case_dir / "insert.bin"
    insert.write_bytes(b"J24G48\x00source-exact-journal" * 7)
    shifted = case_dir / "shifted.cmpct"
    shifted.write_bytes(original.read_bytes())
    append_start = time.perf_counter_ns()
    append_update(shifted, "0000-inserted.bin", insert)
    append_ns = time.perf_counter_ns() - append_start
    with CMPCT(original) as ar:
        if ar.verify() != count:
            raise AssertionError("original contents failed verification")
    with CMPCT(shifted) as ar:
        if ar.verify() != count + 1:
            raise AssertionError("shifted contents failed verification")
    return {
        "case": f"n{count}-x{divisor}", "count": count, "xattr_divisor": divisor,
        "expected_xattrs": expected, "build_ns": build_ns, "append_ns": append_ns,
        "source_file_count": count,
        "original": {"path": str(original.resolve()), "bytes": original.stat().st_size,
                     "sha256": digest(original)},
        "shifted": {"path": str(shifted.resolve()), "bytes": shifted.stat().st_size,
                    "sha256": digest(shifted)},
    }


def read_once(archive: Path, expectation: dict, source_label: str,
              case: str, generation: str, round_index: int) -> dict:
    begin_import = time.perf_counter_ns()
    identity = source_identity()
    imported_ns = time.perf_counter_ns() - begin_import
    from cmpct.reader import CMPCT
    begin_wall = time.perf_counter_ns()
    begin_cpu = time.process_time_ns()
    with CMPCT(archive) as ar:
        names = [row[0] for row in ar.files]
        mapping = {
            names[ordinal]: value.hex()
            for ordinal, pairs in ar.fsmeta.get("xattrs", [])
            for key, value in pairs
            if key == MARKER
        }
        # The check is intentionally inside measured Reader lifecycle,
        # but cost is separately identified as map materialization below.
        member_count = len(names)
    cpu_ns = time.process_time_ns() - begin_cpu
    wall_ns = time.perf_counter_ns() - begin_wall
    expected = expectation["expected_xattrs"]
    all_matched = mapping == expected
    must_match = source_label == "correct" or generation == "original" or not expected
    if must_match and not all_matched:
        raise AssertionError(f"unexpected incorrect metadata association: {case} {source_label} {generation}")
    if source_label == "defective" and generation == "shifted" and expected and all_matched:
        raise AssertionError("pre-repair negative failed to reproduce")
    rss_bytes = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    return {
        "case": case, "generation": generation, "source": source_label,
        "round": round_index, "reader_open_plus_mapping_wall_ns": wall_ns,
        "reader_open_plus_mapping_cpu_ns": cpu_ns, "import_ns": imported_ns,
        "maxrss_bytes": rss_bytes,
        "members": member_count, "metadata_names": len(mapping),
        "metadata_matches_logical_names": all_matched, "archive_sha256": digest(archive),
        "source_identity": identity, "pid": os.getpid(),
    }


def launch(root: Path, sha: str, program: Path, arguments: list[str]) -> dict:
    env = dict(os.environ)
    env["CMPCT_SOURCE_ROOT"] = str(root.resolve())
    env["CMPCT_EXPECTED_SHA"] = sha
    env["PYTHONPATH"] = str((root / "src").resolve())
    completed = subprocess.run(
        [sys.executable, str(program), *arguments], env=env,
        text=True, capture_output=True, check=False, timeout=120,
    )
    if completed.returncode:
        raise RuntimeError(
            f"source {sha} failed:\nSTDOUT {completed.stdout[-3500:]}\nSTDERR {completed.stderr[-3500:]}"
        )
    return json.loads(completed.stdout.strip().splitlines()[-1])


def coordinator(args) -> None:
    if sys.platform != "linux":
        raise RuntimeError("physical J24G48 court is Linux-only")
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    program = Path(__file__).resolve()
    candidate = args.candidate.resolve()
    defective = args.defective.resolve()

    manifest = {
        "question": "J24G48 signed r24 journal metadata correction physical Reader economics",
        "scope": "research; semantically invalid baseline; not release parity",
        "candidate_sha": CAND_SHA, "defective_sha": BASE_SHA,
        "platform": sys.platform, "python": sys.version, "cases": [],
        "runs": [], "repetitions": 7, "source_order": "ABBA alternating",
    }
    # Generate exactly once on the candidate Reader+Builder; never rebuild per source.
    os.environ["CMPCT_SOURCE_ROOT"] = str(candidate)
    os.environ["CMPCT_EXPECTED_SHA"] = CAND_SHA
    identity = source_identity()
    manifest["builder_identity"] = identity
    for count, divisor in CASES:
        spec = fixture(root / f"n{count}-x{divisor}", count, divisor)
        manifest["cases"].append(spec)
        (root / "raw-results.json").write_text(json.dumps(manifest, indent=2))
        (root / f"{spec['case']}-manifest.json").write_text(json.dumps(spec, indent=2))
        for cycle in range(7):
            generation_order = ("original", "shifted") if cycle % 2 == 0 else ("shifted", "original")
            source_order = ("defective", "correct", "correct", "defective") \
                if cycle % 2 == 0 else ("correct", "defective", "defective", "correct")
            for generation in generation_order:
                archive = Path(spec[generation]["path"])
                for source_label in source_order:
                    source_root, sha = (candidate, CAND_SHA) if source_label == "correct" else (defective, BASE_SHA)
                    result = launch(source_root, sha, program, [
                        "read", "--archive", str(archive), "--case-json",
                        str(root / f"{spec['case']}-manifest.json"),
                        "--generation", generation, "--source", source_label,
                        "--round", str(cycle),
                    ])
                    if result["archive_sha256"] != spec[generation]["sha256"]:
                        raise AssertionError("non-identical benchmark artifact")
                    manifest["runs"].append(result)
                (root / "raw-results.json").write_text(json.dumps(manifest, indent=2))

    report = []
    for case in manifest["cases"]:
        for source in ("defective", "correct"):
            for generation in ("original", "shifted"):
                group = [r for r in manifest["runs"]
                         if r["case"] == case["case"] and r["source"] == source
                         and r["generation"] == generation]
                if len(group) != 14:
                    raise AssertionError("missing raw interleaved samples")
                report.append({
                    "case": case["case"], "source": source, "generation": generation,
                    "samples": len(group),
                    "median_open_wall_ms": statistics.median(
                        x["reader_open_plus_mapping_wall_ns"] for x in group) / 1e6,
                    "median_open_cpu_ms": statistics.median(
                        x["reader_open_plus_mapping_cpu_ns"] for x in group) / 1e6,
                    "max_rss_bytes": max(x["maxrss_bytes"] for x in group),
                    "metadata_correct": all(x["metadata_matches_logical_names"] for x in group),
                })
    manifest["summary"] = report
    (root / "raw-results.json").write_text(json.dumps(manifest, indent=2))
    (root / "summary.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"decision": "MEASURED_READER_OPEN_COST_NOT_RELEASE_CREDIT",
                      "summary": report}, sort_keys=True))


def cli() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="action", required=True)
    c = sub.add_parser("run")
    c.add_argument("--candidate", type=Path, required=True)
    c.add_argument("--defective", type=Path, required=True)
    c.add_argument("--output", type=Path, required=True)
    r = sub.add_parser("read")
    r.add_argument("--archive", type=Path, required=True)
    r.add_argument("--case-json", type=Path, required=True)
    r.add_argument("--generation", choices=["original", "shifted"], required=True)
    r.add_argument("--source", choices=["correct", "defective"], required=True)
    r.add_argument("--round", type=int, required=True)
    args = p.parse_args()
    if args.action == "run":
        coordinator(args)
    else:
        record = json.loads(args.case_json.read_text())
        print(json.dumps(read_once(args.archive, record, args.source,
                                   record["case"], args.generation, args.round)))


if __name__ == "__main__":
    cli()
