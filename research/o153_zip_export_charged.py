"""O153: exact-source same-runner charged ZIP-export court.

Research only. Three real CMPCT Readers; one original Builder; one archive per
family; seven rotating fresh-process observations per engine and destination.
No product source, frozen comparator, or release evaluator is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import resource
import statistics
import subprocess
import sys
import time
import zipfile


ENGINES = ("o140", "o149", "o150")
ORDERS = (
    ("o140", "o149", "o150"),
    ("o150", "o149", "o140"),
    ("o149", "o140", "o150"),
    ("o150", "o140", "o149"),
    ("o140", "o150", "o149"),
    ("o149", "o150", "o140"),
    ("o140", "o149", "o150"),
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while b := f.read(1024 * 1024):
            h.update(b)
    return h.hexdigest()


def dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def prepare(out: Path) -> None:
    # Invoked with a pinned O140 Builder; candidate Readers never generate inputs.
    from cmpct.builder import Builder
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    cases = {}
    for name in ("tiny-tree", "large-mixed"):
        src = out / ("src-" + name)
        src.mkdir(exist_ok=True)
        if name == "tiny-tree":
            for i in range(96):
                template = (f"setting_{i % 13:02d} = value_{i:04d}\n" * 120).encode()
                (src / f"config_{i:03d}.txt").write_bytes(template[:2048])
        else:
            rng = random.Random(153)
            (src / "random.bin").write_bytes(rng.randbytes(4 * 1024 * 1024))
            (src / "structured.bin").write_bytes(
                (b"v031-charged-zip-physical-payload" * 160000)[:4 * 1024 * 1024]
            )
        members = {
            f.name: {"sha256": file_sha(f), "bytes": f.stat().st_size}
            for f in sorted(src.iterdir())
        }
        archive = out / (name + ".cmpct")
        Builder(src, workers=1, reproducible=True).build(archive)
        cases[name] = {
            "archive": str(archive),
            "archive_sha256": file_sha(archive),
            "archive_bytes": archive.stat().st_size,
            "members": members,
        }
    dump(out / "inputs.json", {"schema": "o153-input-v1", "cases": cases})
    print("O153_INPUTS=" + json.dumps({
        k: {"archive_sha256": v["archive_sha256"], "archive_bytes": v["archive_bytes"],
            "members": len(v["members"])}
        for k, v in cases.items()
    }, sort_keys=True), flush=True)


def child(args) -> None:
    import cmpct.reader
    from cmpct.reader import CMPCT

    manifest = json.loads(Path(args.manifest).read_text())
    case = manifest["cases"][args.family]
    archive = Path(case["archive"])
    output = Path(args.output)
    assert archive.is_file() and file_sha(archive) == case["archive_sha256"]
    assert output.parent.is_dir()
    before_stat = output.stat() if output.exists() else None
    before_sha = file_sha(output) if before_stat else None

    module = Path(cmpct.reader.__file__).resolve()
    expected_install = Path(args.install).resolve()
    assert module.is_relative_to(expected_install), (module, expected_install)
    module_sha = file_sha(module)

    t_open = time.perf_counter_ns()
    with CMPCT(archive) as reader:
        open_ns = time.perf_counter_ns() - t_open
        ru0 = resource.getrusage(resource.RUSAGE_SELF)
        cpu0 = time.process_time_ns()
        t0 = time.perf_counter_ns()
        ret = reader.export_zip(output)
        export_ns = time.perf_counter_ns() - t0
        cpu_ns = time.process_time_ns() - cpu0
        ru1 = resource.getrusage(resource.RUSAGE_SELF)
    assert Path(ret) == output
    assert archive.is_file() and file_sha(archive) == case["archive_sha256"]
    assert output.is_file()
    with zipfile.ZipFile(output, "r") as zf:
        names = sorted(zf.namelist())
        assert names == sorted(case["members"]), (names, sorted(case["members"]))
        for member in names:
            got = zf.read(member)
            exp = case["members"][member]
            assert len(got) == exp["bytes"] and sha(got) == exp["sha256"], member
        assert zf.testzip() is None
    residual = [p.name for p in output.parent.iterdir() if p != output]
    assert not residual, f"unpublished staging residue: {residual}"

    st = output.stat()
    raw_rss = ru1.ru_maxrss
    rss_bytes = raw_rss if sys.platform == "darwin" else raw_rss * 1024
    result = {
        "schema": "o153-child-v1", "engine": args.engine,
        "family": args.family, "destination": args.destination,
        "block": args.block,
        "archive_sha256": case["archive_sha256"],
        "archive_bytes": case["archive_bytes"],
        "reader_sha256": module_sha,
        "zip_sha256": file_sha(output),
        "zip_bytes": st.st_size, "zip_mode": st.st_mode & 0o777,
        "old_zip_sha256": before_sha,
        "inode_changed": None if before_stat is None else st.st_ino != before_stat.st_ino,
        "reader_open_wall_ns": open_ns,
        "export_library_wall_ns": export_ns,
        "export_library_cpu_ns": cpu_ns,
        "process_peak_rss_bytes": rss_bytes,
        "export_ru_oublock": ru1.ru_oublock - ru0.ru_oublock,
        "stage_residue": residual,
        "member_count": len(case["members"]),
    }
    print("O153_CHILD=" + json.dumps(result, sort_keys=True), flush=True)


def make_old_zip(path: Path) -> None:
    info = zipfile.ZipInfo("previous/untouched.txt", date_time=(2020, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(info, b"old valid ZIP must be replaced on success")
    assert zipfile.is_zipfile(path)


def court(args) -> None:
    manifest = Path(args.manifest).resolve()
    evidence = Path(args.evidence).resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve()
    packages = {k: Path(getattr(args, "install_" + k)).resolve() for k in ENGINES}
    for p in packages.values():
        assert (p / "cmpct" / "reader.py").is_file(), p
    cases = json.loads(manifest.read_text())["cases"]
    raw = evidence / "raw.jsonl"
    errors = evidence / "errors.log"
    all_rows = []
    with raw.open("w") as log:
        for family in sorted(cases):
            for kind in ("absent", "existing"):
                for block, order in enumerate(ORDERS):
                    for engine in order:
                        target_dir = evidence / "outputs" / family / kind / str(block) / engine
                        target_dir.mkdir(parents=True, exist_ok=False)
                        output = target_dir / "output.zip"
                        if kind == "existing":
                            make_old_zip(output)
                        env = os.environ.copy()
                        env["PYTHONPATH"] = os.fspath(packages[engine])
                        command = [
                            sys.executable, os.fspath(script), "child",
                            "--manifest", os.fspath(manifest),
                            "--install", os.fspath(packages[engine]),
                            "--family", family, "--destination", kind,
                            "--output", os.fspath(output),
                            "--engine", engine, "--block", str(block),
                        ]
                        start = time.perf_counter_ns()
                        p = subprocess.run(command, cwd=target_dir, env=env, text=True,
                                           capture_output=True, timeout=120, check=False)
                        process_ns = time.perf_counter_ns() - start
                        if p.returncode:
                            with errors.open("a") as f:
                                f.write(f"{family} {kind} {block} {engine} RETURN {p.returncode}\n"
                                        + p.stdout + "\n" + p.stderr + "\n")
                            raise RuntimeError(f"engine {engine} failed; see {errors}")
                        lines = [line.split("O153_CHILD=", 1)[1]
                                 for line in p.stdout.splitlines() if "O153_CHILD=" in line]
                        assert len(lines) == 1, (command, p.stdout, p.stderr)
                        row = json.loads(lines[0])
                        assert row["engine"] == engine and row["family"] == family
                        assert row["destination"] == kind and row["block"] == block
                        row["child_process_wall_ns"] = process_ns
                        log.write(json.dumps(row, sort_keys=True) + "\n")
                        log.flush()
                        all_rows.append(row)
                        output.unlink()
    expected_count = len(cases) * 2 * len(ORDERS) * len(ENGINES)
    assert len(all_rows) == expected_count == 84, len(all_rows)
    summary = {"schema": "o153-court-v1", "observations": len(all_rows),
               "inputs": {k: {"archive_sha256": v["archive_sha256"],
                              "archive_bytes": v["archive_bytes"]}
                          for k, v in cases.items()},
               "groups": {}}
    for family in sorted(cases):
        for kind in ("absent", "existing"):
            group = [r for r in all_rows if r["family"] == family and
                     r["destination"] == kind]
            assert len(group) == 21
            assert len({r["zip_sha256"] for r in group}) == 1, (family, kind)
            assert len({r["zip_bytes"] for r in group}) == 1, (family, kind)
            datum = {}
            for engine in ENGINES:
                rows = [r for r in group if r["engine"] == engine]
                assert len(rows) == 7, (family, kind, engine)
                assert len({r["reader_sha256"] for r in rows}) == 1
                datum[engine] = {
                    "output_sha256": rows[0]["zip_sha256"],
                    "output_bytes": rows[0]["zip_bytes"],
                    "mode": sorted(set(r["zip_mode"] for r in rows)),
                    "inode_changed": sorted(set(str(r["inode_changed"]) for r in rows)),
                    **{field + "_median": statistics.median(r[field] for r in rows)
                       for field in ("reader_open_wall_ns", "export_library_wall_ns",
                                     "export_library_cpu_ns", "child_process_wall_ns",
                                     "process_peak_rss_bytes", "export_ru_oublock")},
                }
            base = datum["o140"]["export_library_wall_ns_median"]
            for engine in ("o149", "o150"):
                got = datum[engine]["export_library_wall_ns_median"]
                datum[engine]["relative_wall_delta_percent_vs_o140"] = (
                    100.0 * (got - base) / base if base else None
                )
                datum[engine]["release_threshold_exceeded_locally_not_promotion"] = (
                    got - base > 3_000_000 and got > base * 1.05
                )
            summary["groups"][family + "/" + kind] = datum
    dump(evidence / "summary.json", summary)
    print("O153_AUDIT=" + json.dumps({
        "observations": len(all_rows), "groups": summary["groups"]
    }, sort_keys=True), flush=True)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("prepare")
    a.add_argument("--output", required=True, type=Path)
    b = sub.add_parser("child")
    for key in ("manifest", "install", "family", "destination", "output", "engine"):
        b.add_argument("--" + key, required=True)
    b.add_argument("--block", required=True, type=int)
    c = sub.add_parser("court")
    c.add_argument("--manifest", required=True)
    c.add_argument("--evidence", required=True)
    for key in ENGINES:
        c.add_argument("--install-" + key, required=True)
    args = p.parse_args()
    if args.cmd == "prepare":
        prepare(args.output)
    elif args.cmd == "child":
        child(args)
    else:
        court(args)


if __name__ == "__main__":
    main()
