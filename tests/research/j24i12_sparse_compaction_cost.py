"""J24I12: source-bound sparse compaction memory/physical-cost experiment.

A research-only instrument. Exact product is installed by the external Actions workflow;
this module imports CMPCT only after the code has been authenticated outside checkout.
"""
from __future__ import annotations

import hashlib
import json
import os
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SIZES = (2 << 20, 32 << 20, 128 << 20)
PAGE = 4096
MARK_HEAD = bytes((i * 17 + 5) % 256 for i in range(PAGE))
MARK_TAIL = bytes((i * 29 + 11) % 256 for i in range(PAGE))


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def io_snapshot() -> dict:
    path = Path("/proc/self/io")
    if not path.exists():
        return {}
    return {k.rstrip(":"): int(v) for k, v in
            (ln.split() for ln in path.read_text().splitlines())}


def child(src: Path, dst: Path, receipt: Path) -> None:
    from cmpct.reader import CMPCT
    from cmpct.transactions import compact_archive
    pre = io_snapshot()
    started = time.perf_counter_ns()
    cpu = time.process_time_ns()
    result = compact_archive(src, dst)
    elapsed = time.perf_counter_ns() - started
    cpu_elapsed = time.process_time_ns() - cpu
    post = io_snapshot()
    with CMPCT(dst) as reader:
        sparse = reader.by["sparse.bin"]
        from cmpct.codec import S_SPARSE
        assert sparse[6][0] == S_SPARSE, "compaction no longer preserves S_SPARSE storage"
        assert reader.read_range("sparse.bin", 0, PAGE) == MARK_HEAD
        assert reader.read_range("sparse.bin", sparse[4] - PAGE, PAGE) == MARK_TAIL
        assert reader.read("small.bin") == b"J24I12 committed update" * 8
        rows = [(row[0], row[1], row[2], row[3], row[4],
                 row[6][0] if row[6] else None) for row in reader.files]
    record = {
        "schema": "j24i12-child-v1",
        "elapsed_wall_ns": elapsed,
        "elapsed_cpu_ns": cpu_elapsed,
        "peak_rss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "io_delta": {k: post[k] - pre[k] for k in sorted(pre.keys() & post.keys())},
        "output_bytes": dst.stat().st_size,
        "output_sha256": digest(dst),
        "rows": rows,
        "build_result": result,
        "sparse_data_fidelity": True,
    }
    receipt.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"child_ok": True, "rss_kib": record["peak_rss_kib_linux"],
                      "wall_ns": elapsed, "size": sparse[4]}, sort_keys=True))


def make_fixture(work: Path, logical_size: int) -> dict:
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.transactions import append_update
    from cmpct.codec import S_SPARSE
    root = work / "source-tree"
    root.mkdir()
    sparse = root / "sparse.bin"
    with sparse.open("wb") as stream:
        stream.write(MARK_HEAD)
        stream.seek(logical_size - PAGE)
        stream.write(MARK_TAIL)
    allocated = sparse.stat().st_blocks * 512
    assert allocated < logical_size // 4, (
        "filesystem lacks sparse allocation for this comparison", allocated, logical_size)
    (root / "small.bin").write_bytes(b"J24I12 old content")
    source = work / "source.cmpct"
    Builder(root, reproducible=True, workers=1).build(source)
    replacement = work / "replacement.bin"
    replacement.write_bytes(b"J24I12 committed update" * 8)
    append_update(source, "small.bin", replacement)
    with CMPCT(source) as reader:
        row = reader.by["sparse.bin"]
        assert row[6][0] == S_SPARSE, "Builder did not produce a sparse archive"
        assert row[4] == logical_size
        assert reader.read_range("sparse.bin", 0, PAGE) == MARK_HEAD
        assert reader.read_range("sparse.bin", logical_size - PAGE, PAGE) == MARK_TAIL
        assert reader.read("small.bin") == replacement.read_bytes()
        source_rows = [(x[0], x[1], x[2], x[3], x[4]) for x in reader.files]
    return {
        "source": source,
        "allocated_source_bytes": allocated,
        "logical_sparse_bytes": logical_size,
        "input_archive_bytes": source.stat().st_size,
        "input_archive_sha256": digest(source),
        "source_rows": source_rows,
        "sparse_extents_written_bytes": PAGE * 2,
    }


def run() -> dict:
    cases = []
    artifact_dir = Path(os.environ["CMPCT_J24I12_ARTIFACT_DIR"])
    artifact_dir.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        with tempfile.TemporaryDirectory(prefix="j24i12-") as temporary:
            work = Path(temporary)
            control = make_fixture(work, size)
            source = control["source"]
            dst = work / "compacted.cmpct"
            # This is an I/O lower bound only, not equivalent generation compaction:
            # original journal generations remain in the copied archive.
            copy_dest = work / "journal-preserving-copy.cmpct"
            t0 = time.perf_counter_ns()
            shutil.copyfile(source, copy_dest)
            copy_ns = time.perf_counter_ns() - t0
            assert digest(copy_dest) == control["input_archive_sha256"]
            proc_receipt = work / "child.json"
            attempt = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--child",
                 str(source), str(dst), str(proc_receipt)],
                cwd=work, text=True, capture_output=True, timeout=360, check=False,
                env={**os.environ, "CMPCT_ENCODE_WORKERS": "1"})
            (artifact_dir / f"child_{size}.stdout.txt").write_text(attempt.stdout)
            (artifact_dir / f"child_{size}.stderr.txt").write_text(attempt.stderr)
            if attempt.returncode != 0:
                raise AssertionError(
                    f"compaction child failed length {size}, exit={attempt.returncode}: "
                    + attempt.stderr[-4000:])
            child_result = json.loads(proc_receipt.read_text())
            assert digest(source) == control["input_archive_sha256"], "source was mutated"
            assert child_result["sparse_data_fidelity"]
            assert child_result["rows"] == [
                [x[0], x[1], x[2], x[3], x[4],
                 next((y[6][0] for y in _archive_rows(dst) if y[0] == x[0]), None)]
                for x in control["source_rows"]
            ]
            output_saved = artifact_dir / f"compacted_{size}.cmpct"
            source_saved = artifact_dir / f"source_{size}.cmpct"
            shutil.copyfile(src=dst, dst=output_saved)
            shutil.copyfile(src=source, dst=source_saved)
            cases.append({**{k: v for k, v in control.items() if k != "source"},
                          "copy_lower_bound_wall_ns": copy_ns,
                          "compaction": child_result})
    case_by_size = {x["logical_sparse_bytes"]: x for x in cases}
    small = case_by_size[SIZES[0]]["compaction"]["peak_rss_kib_linux"]
    large = case_by_size[SIZES[-1]]["compaction"]["peak_rss_kib_linux"]
    delta_mib = (large - small) / 1024
    if delta_mib >= 64:
        decision = "SPARSE_LOGICAL_RSS_COST_SUPPORTED"
    elif delta_mib <= 16:
        decision = "SPARSE_LOGICAL_RSS_COST_FALSIFIED"
    else:
        decision = "SPARSE_LOGICAL_RSS_COST_AMBIGUOUS"
    result = {
        "schema": "j24i12-court-v1",
        "platform": sys.platform,
        "python": sys.version,
        "sizes": list(SIZES),
        "cases": cases,
        "large_minus_small_peak_rss_mib": delta_mib,
        "decision": decision,
        "claim_scope": "Linux installed original #723 compaction candidate, resource economics only",
        "release_credit": False,
    }
    (artifact_dir / "court.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def _archive_rows(path: Path):
    from cmpct.reader import CMPCT
    with CMPCT(path) as archive:
        return list(archive.files)


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--child":
        child(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
    elif len(sys.argv) == 1:
        result = run()
        print(json.dumps({"decision": result["decision"],
                          "rss_delta_mib": result["large_minus_small_peak_rss_mib"],
                          "cases": len(result["cases"])}, sort_keys=True))
    else:
        raise SystemExit("usage: run without args or --child source dest receipt")
