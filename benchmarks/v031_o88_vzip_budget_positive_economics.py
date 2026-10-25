#!/usr/bin/env python3
"""O88: historical O63 versus O86 whole-product VZIP budget economics.

No monkeypatch, no product changes, no release credit. Both arms import actual
independently installed GitHub source into fresh Python processes on one host.
Raw same-tree observations survive even when the hypothesis is falsified.
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
BASE_SHA = "18e32cae012f5dca9fc47f10d194f8b81005c85c"
CAND_SHA = "6225e30f3e21c0783aa56726b52a3a3583540f99"
BLOBS = {
    "o63": {"builder": "382e60983bf1e8e7595ea7112f3a5553dc33dcc0",
            "codec": "dc3446b0eed82edfba9380e3885a20aa45577899"},
    "o86": {"builder": "e46c8670c11c386925f9ae228b25de44c8045f2e",
            "codec": "7d4c4a5a5f00c42561043611e5d4400dd8af38e6"},
}
CASES = (
    ("shared_low", 1 * MIB, "shared"),
    ("shared_over", 65 * MIB, "shared"),
    ("independent_over", 65 * MIB, "independent"),
)


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def expanded(size: int, owner: str, idx: int) -> bytes:
    token = idx if owner == "independent" else 0
    prefix = (f"record tenant={token}; object=payload; state=exact;\\n".encode()
              if owner == "independent" else
              b"record tenant=neutral; object=payload; state=exact;\n")
    # Fixed-seed bounded entropy tail, independent of the physical container.
    random_tail = random.Random(8800 + token).randbytes(16384)
    wanted = size - len(random_tail)
    return (prefix * (1 + wanted // len(prefix)))[:wanted] + random_tail


def fixture(root: Path, size: int, owner: str) -> list[dict]:
    root.mkdir(parents=True, exist_ok=True)
    result = []
    for idx, level in enumerate((1, 6, 9)):
        data = expanded(size, owner, idx)
        info = zipfile.ZipInfo(f"member-{idx:02d}.bin", (1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        path = root / f"source-{idx:02d}.zip"
        with zipfile.ZipFile(path, "w") as stream:
            stream.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED,
                            compresslevel=level)
        raw = path.read_bytes()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            got = z.read(info.filename)
            assert got == data and z.getinfo(info.filename).file_size == size
        result.append({
            "path": path.name, "level": level,
            "zip_sha256": digest(raw), "physical_zip_bytes": len(raw),
            "expanded_sha256": digest(data), "declared_inflated_bytes": size,
        })
    assert all(x["declared_inflated_bytes"] == size for x in result)
    assert len({x["zip_sha256"] for x in result}) == len(result)
    assert len({x["expanded_sha256"] for x in result}) == (
        1 if owner == "shared" else len(result))
    return result


def source_digest(root: Path) -> dict:
    return {p.name: digest(p.read_bytes()) for p in sorted(root.glob("*.zip"))}


def worker(a: argparse.Namespace) -> None:
    import cmpct.builder as builder_module
    import cmpct.codec as codec_module
    from cmpct.builder import Builder
    from cmpct.codec import K_FILE, S_VZIP, S_BLOB, S_PACK
    from cmpct.reader import CMPCT

    pkg = Path(a.package).resolve()
    imports = {
        "builder": Path(builder_module.__file__).resolve(),
        "codec": Path(codec_module.__file__).resolve(),
    }
    assert all(p.is_relative_to(pkg) for p in imports.values()), (
        "installed origin mismatch", imports, pkg)
    root = Path(a.root)
    expected = json.loads(Path(a.manifest).read_text())
    sha = {x["path"]: x["zip_sha256"] for x in expected}
    assert source_digest(root) == sha, "source drift before build"
    assert "CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES" not in os.environ, (
        "candidate must use its default 64 MiB budget")
    out = Path(a.output)
    t0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
    b = Builder(root, workers=1, reproducible=True, reproducible_epoch_ns=0)
    b.build(out)
    wall, cpu = time.perf_counter_ns() - t0, time.process_time_ns() - cpu0
    assert source_digest(root) == sha, "source drift after build"
    kinds = {row[0]: row[6][0] for row in b.files if row[1] == K_FILE}
    assert set(kinds) == set(sha) and S_PACK not in kinds.values()
    assert set(kinds.values()).issubset({S_VZIP, S_BLOB})
    t1, c1 = time.perf_counter_ns(), time.process_time_ns()
    with CMPCT(out) as reader:
        assert reader.verify() >= 1
        for rel in sha:
            assert digest(reader.read(rel)) == sha[rel], ("read", rel)
        dest = out.parent / (out.stem + "-extract")
        reader.extractall(dest, metadata=False)
        assert {p.name: digest(p.read_bytes()) for p in dest.glob("*.zip")} == sha
    read_wall, read_cpu = time.perf_counter_ns() - t1, time.process_time_ns() - c1
    print(json.dumps({
        "arm": a.arm, "rep": a.rep, "case": a.case,
        "source_digest": sha,
        "builder_origin": str(imports["builder"]),
        "codec_origin": str(imports["codec"]),
        "stored_bytes": out.stat().st_size,
        "archive_sha256": digest(out.read_bytes()),
        "kinds": kinds,
        "create_wall_ns": wall, "create_cpu_ns": cpu,
        "verify_read_extract_wall_ns": read_wall,
        "verify_read_extract_cpu_ns": read_cpu,
        "peak_rss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "python": sys.version.split()[0],
    }, sort_keys=True), flush=True)


def court(a: argparse.Namespace) -> None:
    assert sys.platform.startswith("linux")
    scratch = Path(tempfile.mkdtemp(prefix="cmpct-o88-"))
    pkg = {"o63": Path(a.o63_package).resolve(),
           "o86": Path(a.o86_package).resolve()}
    report = {
        "experiment": "O88", "status": "science-only",
        "source_commits": {"o63": BASE_SHA, "o86": CAND_SHA},
        "source_blobs": BLOBS, "cases": [], "reps": REPS,
    }
    destination = Path(a.report).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)

    def persist():
        destination.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")

    for name, expanded_len, ownership in CASES:
        src = scratch / name / "src"
        manifest = fixture(src, expanded_len, ownership)
        manifest_file = scratch / name / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, sort_keys=True, indent=2))
        sha = source_digest(src)
        case = {"name": name, "expanded_per_member": expanded_len,
                "ownership": ownership, "source": manifest,
                "observations": [], "summary": None}
        report["cases"].append(case)
        persist()
        for rep in range(REPS):
            order = ("o63", "o86") if rep % 2 == 0 else ("o86", "o63")
            for arm in order:
                out = scratch / name / f"{arm}-{rep}.cmpct"
                env = os.environ.copy()
                env.pop("CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES", None)
                env["PYTHONPATH"] = str(pkg[arm])
                cmd = [sys.executable, str(Path(__file__).resolve()), "--worker",
                       "--package", str(pkg[arm]), "--case", name,
                       "--arm", arm, "--rep", str(rep),
                       "--root", str(src), "--manifest", str(manifest_file),
                       "--output", str(out)]
                child = subprocess.run(cmd, env=env, cwd=scratch, text=True,
                                       capture_output=True, timeout=420)
                if child.returncode:
                    case.setdefault("failures", []).append({
                        "arm": arm, "rep": rep, "exit": child.returncode,
                        "stdout_tail": child.stdout[-1500:],
                        "stderr_tail": child.stderr[-3000:]})
                    persist()
                    raise RuntimeError(
                        f"O88 {name}/{arm}/{rep}: child returned {child.returncode}\n"
                        f"{child.stdout[-2000:]}\n{child.stderr[-3000:]}")
                row = json.loads(child.stdout.strip().splitlines()[-1])
                assert row["source_digest"] == sha, "independent source mutated"
                case["observations"].append(row)
                persist()
        arms = {k: [v for v in case["observations"] if v["arm"] == k]
                for k in ("o63", "o86")}
        assert all(len(v) == REPS for v in arms.values())
        assert all(len({v["archive_sha256"] for v in rows}) == 1
                   for rows in arms.values()), "nondeterminism within one engine"
        median = lambda arm, col: statistics.median(
            row[col] for row in arms[arm])
        b, c = arms["o63"][0], arms["o86"][0]
        summary = {
            "o63_complete_bytes": b["stored_bytes"],
            "o86_complete_bytes": c["stored_bytes"],
            "o86_minus_o63_bytes": c["stored_bytes"] - b["stored_bytes"],
            "o63_kinds": b["kinds"], "o86_kinds": c["kinds"],
            "o63_create_wall_ms": median("o63", "create_wall_ns") / 1e6,
            "o86_create_wall_ms": median("o86", "create_wall_ns") / 1e6,
            "o63_create_cpu_ms": median("o63", "create_cpu_ns") / 1e6,
            "o86_create_cpu_ms": median("o86", "create_cpu_ns") / 1e6,
            "o63_rss_kib": median("o63", "peak_rss_kib_linux"),
            "o86_rss_kib": median("o86", "peak_rss_kib_linux"),
            "o63_verify_read_extract_ms": median(
                "o63", "verify_read_extract_wall_ns") / 1e6,
            "o86_verify_read_extract_ms": median(
                "o86", "verify_read_extract_wall_ns") / 1e6,
        }
        case["summary"] = summary
        if expanded_len > 64 * MIB:
            assert all(k == 0 for k in c["kinds"].values()), (  # r24 S_BLOB = 0
                "O86 default budget did not reject all above-budget VZIP members", c)
        if expanded_len <= 64 * MIB:
            assert b["archive_sha256"] == c["archive_sha256"], (
                "under-budget default no longer equals historical O63 bytes")
        persist()
        print("O88_RESULT " + json.dumps({"case": name, **summary},
                                            sort_keys=True), flush=True)
    report["scientific_decision"] = (
        "ABOVE_BUDGET_SHARED_SIZE_DEBT_OBSERVED"
        if next(x for x in report["cases"] if x["name"] == "shared_over")
               ["summary"]["o86_minus_o63_bytes"] > 0
        else "NO_SHARED_SIZE_DEBT_ON_TESTED_FAMILY")
    persist()
    print("O88_REAL_INSTALLED_PROCESS_OBSERVATIONS=" +
          str(sum(len(x["observations"]) for x in report["cases"])))
    print("O88_DECISION=" + report["scientific_decision"])
    print("O88_RAW_REPORT=" + str(destination))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--arm", choices=("o63", "o86"))
    p.add_argument("--rep", type=int)
    p.add_argument("--case")
    p.add_argument("--root")
    p.add_argument("--manifest")
    p.add_argument("--output")
    p.add_argument("--package")
    p.add_argument("--o63-package")
    p.add_argument("--o86-package")
    p.add_argument("--report", default="o88-evidence/o88-raw.json")
    a = p.parse_args()
    worker(a) if a.worker else court(a)


if __name__ == "__main__":
    main()
