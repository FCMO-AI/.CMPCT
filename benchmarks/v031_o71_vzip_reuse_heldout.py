#!/usr/bin/env python3
"""O71 research-only held-out VZIP cross-object ownership / admission oracle.

Not a product implementation. The opaque control replaces only the imported
virtual ZIP recipe function in a separately launched installed interpreter.
The accepted CMPCT revision-24 format, Reader and codec are unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import random
import resource
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

MIB = 1024 * 1024
REPS = 3
# case, payload-family, levels, owner-relationship, ZIP-member-name-policy
CASES = (
    ("singleton_repeat", "repeat", (6,), "shared", "different"),
    ("shared_repeat_levels", "repeat", (1, 6, 9), "shared", "different"),
    ("shared_text_levels", "text", (1, 6, 9), "shared", "different"),
    ("shared_mixed_levels", "mixed", (1, 6, 9), "shared", "different"),
    ("independent_mixed_levels", "mixed", (1, 6, 9), "independent", "different"),
    ("unrelated_repeat_levels", "repeat", (1, 6, 9), "independent", "different"),
    ("shared_repeat_names", "repeat", (6, 6, 6), "shared", "different"),
    ("shared_random_levels", "random", (1, 6, 9), "shared", "different"),
)


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def payload(family: str, index: int, ownership: str) -> bytes:
    idx = index if ownership == "independent" else 0
    if family == "repeat":
        return bytes([65 + idx]) * MIB
    if family == "text":
        seed = (
            "Record status=accepted and exact reconstructability matters. "
            "Content address and replay are different operations.\n"
        ).encode()
        return (seed * ((MIB // len(seed)) + 1))[:MIB]
    if family == "mixed":
        # Realistic mixed entropy: long structured runs plus incompressible data.
        r = random.Random(7100 + idx)
        # O71b preregistered causal contrast: same entropy class and file sizes,
        # but distinct long-range repeated patterns and distinct small random tails.
        pattern = (f"tenant=cohort-{idx}; event=complete; status=ok\n".encode()
                   if ownership == "independent" else
                   b"tenant=neutral; event=complete; status=ok\n")
        prefix = (pattern * 30000)[: MIB - 16384]
        return prefix.ljust(MIB - 16384, b"X") + r.randbytes(16384)
    if family == "random":
        return random.Random(7100 + idx).randbytes(MIB)
    raise AssertionError(family)


def fixtures(root: Path, family: str, levels: tuple[int, ...],
             ownership: str, names: str) -> list[dict]:
    root.mkdir(parents=True, exist_ok=True)
    result = []
    for i, level in enumerate(levels):
        expanded = payload(family, i, ownership)
        # Distinct container names, and metadata/entry names independent of
        # expanded-content identity. All timestamps and fields are fixed.
        inner = f"member-{i:02d}.bin" if names == "different" else "payload.bin"
        info = zipfile.ZipInfo(inner, (1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        path = root / f"source-{i:02d}.zip"
        with zipfile.ZipFile(path, "w") as z:
            z.writestr(info, expanded, compress_type=zipfile.ZIP_DEFLATED,
                       compresslevel=level)
        physical = path.read_bytes()
        with zipfile.ZipFile(io.BytesIO(physical), "r") as z:
            assert z.namelist() == [inner]
            assert z.read(inner) == expanded
            zi = z.getinfo(inner)
            assert zi.file_size == len(expanded)
            assert zi.compress_type == zipfile.ZIP_DEFLATED
        result.append({
            "name": path.name, "member": inner,
            "level": level, "physical_bytes": len(physical),
            "inflated_bytes": len(expanded),
            "inflation_ratio": len(expanded) / len(physical),
            "zip_sha256": digest(physical),
            "expanded_sha256": digest(expanded),
        })
    return result


def worker(opts: argparse.Namespace) -> None:
    import cmpct.builder as builder_module
    from cmpct.builder import Builder
    from cmpct.codec import K_FILE, S_VZIP, S_BLOB, S_PACK
    from cmpct.reader import CMPCT

    root = Path(opts.root)
    manifest = json.loads(Path(opts.manifest).read_text())
    assert len(manifest) < 8  # exclude independently owned O70 cohort branch
    paths = {x["name"]: root / x["name"] for x in manifest}
    assert {name: digest(p.read_bytes()) for name, p in paths.items()} == {
        x["name"]: x["zip_sha256"] for x in manifest}
    if opts.mode == "opaque":
        # Gifted scientific control: use product's existing BLOB fallback.
        builder_module.make_vzip_recipe = lambda *_a, **_kw: None

    out = Path(opts.output)
    b = Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0)
    begin = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    b.build(out)
    create_cpu = time.process_time_ns() - cpu_start
    create_wall = time.perf_counter_ns() - begin

    kinds = {row[0]: row[6][0] for row in b.files if row[1] == K_FILE}
    assert set(kinds) == set(paths), kinds
    if opts.mode == "opaque":
        assert set(kinds.values()) == {S_BLOB}, kinds
    else:
        assert set(kinds.values()).issubset({S_VZIP, S_BLOB}), kinds
    assert S_PACK not in kinds.values()
    read_begin = time.perf_counter_ns()
    read_cpu_begin = time.process_time_ns()
    with CMPCT(out) as reader:
        # Physical content can be deduplicated across multiple logical ZIPs.
        # Authentication is still required; completeness is proven per-member.
        assert reader.verify() >= 1
        for name, p in paths.items():
            assert reader.read(name) == p.read_bytes(), f"read mismatch: {name}"
        dest = out.with_suffix(".extracted")
        reader.extractall(dest)
        for name, p in paths.items():
            assert (dest / name).read_bytes() == p.read_bytes()
    read_cpu = time.process_time_ns() - read_cpu_begin
    read_wall = time.perf_counter_ns() - read_begin

    assert {name: digest(p.read_bytes()) for name, p in paths.items()} == {
        x["name"]: x["zip_sha256"] for x in manifest}, "source changed"
    print(json.dumps({
        "mode": opts.mode, "storage_kinds": kinds,
        "archive_bytes": out.stat().st_size,
        "archive_sha256": digest(out.read_bytes()),
        "create_cpu_ns": create_cpu, "create_wall_ns": create_wall,
        "verify_read_extract_cpu_ns": read_cpu,
        "verify_read_extract_wall_ns": read_wall,
        "maxrss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "source_sha256": {x["name"]: x["zip_sha256"] for x in manifest},
        "python": sys.version.split()[0],
    }, sort_keys=True))


def court() -> None:
    from importlib.metadata import version
    import cmpct.builder as builder_module
    import cmpct.codec as codec_module

    assert "/src/cmpct/" not in str(Path(builder_module.__file__).resolve()), (
        "expected installed CMPCT, not repository checkout"
    )
    base = Path(tempfile.mkdtemp(prefix="cmpct-o71-"))
    report = {"experiment": "O71",
              "source_parent": "18e32cae012f5dca9fc47f10d194f8b81005c85c",
              "source_builder_blob": "382e60983bf1e8e7595ea7112f3a5553dc33dcc0",
              "source_codec_blob": "dc3446b0eed82edfba9380e3885a20aa45577899",
              "installed_version": version("cmpct"),
              "installed_builder": str(Path(builder_module.__file__).resolve()),
              "installed_codec": str(Path(codec_module.__file__).resolve()),
              "cases": []}
    for case_name, family, levels, owner, names in CASES:
        root = base / case_name / "input"
        manifest = fixtures(root, family, levels, owner, names)
        manifest_path = base / case_name / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
        cases = {"name": case_name, "family": family,
                 "ownership": owner, "members": manifest, "observations": []}
        for rep in range(REPS):
            # Opposite arm first on successive repeats: guard ordering noise.
            order = ("virtual", "opaque") if rep % 2 == 0 else ("opaque", "virtual")
            for mode in order:
                out = base / case_name / f"{mode}-{rep}.cmpct"
                cmd = [sys.executable, str(Path(__file__).resolve()),
                       "--worker", "--root", str(root), "--manifest",
                       str(manifest_path), "--output", str(out), "--mode", mode]
                child = subprocess.run(cmd, text=True, capture_output=True,
                                       timeout=95, check=False)
                if child.returncode:
                    raise RuntimeError(
                        f"O71 genuine installed worker {case_name}/{mode}/{rep} "
                        f"returned {child.returncode}\n"
                        f"STDOUT:{child.stdout[-1800:]}\nSTDERR:{child.stderr[-5000:]}")
                record = json.loads(child.stdout.strip().splitlines()[-1])
                assert record["source_sha256"] == {
                    m["name"]: m["zip_sha256"] for m in manifest}
                record["rep"] = rep
                cases["observations"].append(record)
        groups = {m: [r for r in cases["observations"] if r["mode"] == m]
                  for m in ("virtual", "opaque")}
        assert all(len(v) == REPS for v in groups.values())
        assert all(len({r["archive_sha256"] for r in v}) == 1
                   for v in groups.values()), "nondeterministic archive"
        med = lambda m, key: statistics.median(r[key] for r in groups[m])
        vbytes = groups["virtual"][0]["archive_bytes"]
        obytes = groups["opaque"][0]["archive_bytes"]
        actual_virtual_kinds = groups["virtual"][0]["storage_kinds"]
        assert all(x["storage_kinds"] == actual_virtual_kinds
                   for x in groups["virtual"])
        vzip_count = sum(k == 2 for k in actual_virtual_kinds.values())
        summary = {
            "virtual_archive_bytes": vbytes, "opaque_archive_bytes": obytes,
            "virtual_minus_opaque_bytes": vbytes - obytes,
            "vzip_admitted_members": vzip_count,
            "total_members": len(manifest),
            "all_virtual_admitted": vzip_count == len(manifest),
            "virtual_create_cpu_ms": med("virtual", "create_cpu_ns") / 1e6,
            "opaque_create_cpu_ms": med("opaque", "create_cpu_ns") / 1e6,
            "virtual_create_wall_ms": med("virtual", "create_wall_ns") / 1e6,
            "opaque_create_wall_ms": med("opaque", "create_wall_ns") / 1e6,
            "virtual_verify_read_extract_wall_ms":
                med("virtual", "verify_read_extract_wall_ns") / 1e6,
            "opaque_verify_read_extract_wall_ms":
                med("opaque", "verify_read_extract_wall_ns") / 1e6,
            "virtual_peak_rss_kib_median": med("virtual", "maxrss_kib_linux"),
            "opaque_peak_rss_kib_median": med("opaque", "maxrss_kib_linux"),
            "min_source_inflation_ratio":
                min(x["inflation_ratio"] for x in manifest),
        }
        summary["prospective_high_ratio_128B_counterexample"] = bool(
            vzip_count == len(manifest) and
            summary["min_source_inflation_ratio"] >= 32 and
            (vbytes - obytes) <= -128)
        cases["summary"] = summary
        report["cases"].append(cases)
        print(json.dumps({"case": case_name, **summary}, sort_keys=True),
              flush=True)

    outcome = [c["name"] for c in report["cases"]
               if c["summary"]["prospective_high_ratio_128B_counterexample"]]
    report["scientific_decision"] = (
        "COUNTEREXAMPLE_OBSERVED" if outcome else
        "NO_COUNTEREXAMPLE_IN_TESTED_FAMILIES")
    report["positive_cases"] = outcome
    report["scope"] = (
        "Installed source-bound O63 oracle only. No product-policy, release, "
        "externally benchmarked, cross-platform, or generic-heuristic credit.")
    output = Path(os.environ.get("CMPCT_O71_REPORT", "o71-raw.json"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    assert len(report["cases"]) == len(CASES)
    assert sum(len(c["observations"]) for c in report["cases"]) == 2 * REPS * len(CASES)
    print(f"O71_REAL_BUILD_OBSERVATIONS={2 * REPS * len(CASES)}")
    print(f"O71_SCIENTIFIC_DECISION={report['scientific_decision']}")
    print(f"O71_REPORT={output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--root")
    parser.add_argument("--manifest")
    parser.add_argument("--output")
    parser.add_argument("--mode", choices=["virtual", "opaque"])
    opt = parser.parse_args()
    worker(opt) if opt.worker else court()


if __name__ == "__main__":
    main()
