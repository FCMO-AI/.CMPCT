"""J24I14 independent source-exact #613 Reader verification donor / #723 compaction court.

Research-only runtime AST transplant; neither product file is edited. Every claim is
restricted to this installed Ubuntu experiment and the original immutable donor.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import json
import os
import resource
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from j24i12_sparse_compaction_cost import (
    MARK_HEAD, MARK_TAIL, PAGE, digest, io_snapshot, make_fixture,
)

DONOR_COMMIT = "3b2bf3c2e033fa27d77b2355821dc0087aa46873"
DONOR_BLOB = "b2b7774c13a5c8235ff89786d171b7ea3ff20710"
BASE_COMMIT = "52d51b9446dc8876319f7bd1e6ca2b7f54681de8"
METHODS = ("_blob", "_verify_sparse_streamed", "verify")
SIZES = (2 << 20, 128 << 20)
ORDER = ("A", "B", "B", "A")


def apply_exact_donor() -> dict:
    """Transfer method AST nodes, rather than inventing a second verifier.

    The donor Git blob identity is established independently by the checkout workflow.
    We install functions into the *original module globals*, so all codec/security
    dependencies and source-bound existing code remain the exact installed product.
    """
    import cmpct.reader as reader
    source = Path(os.environ["CMPCT_J24I14_DONOR_PATH"]).read_text()
    parsed = ast.parse(source)
    classes = [node for node in parsed.body
               if isinstance(node, ast.ClassDef) and node.name == "CMPCT"]
    assert len(classes) == 1
    functions = {node.name: node for node in classes[0].body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert all(name in functions for name in METHODS)
    hashes = {}
    for name in METHODS:
        node = functions[name]
        body = ast.Module(body=[node], type_ignores=[])
        namespace = {}
        exec(compile(body, DONOR_COMMIT + "/reader.py", "exec"),
             vars(reader), namespace)
        fn = namespace[name]
        setattr(reader.CMPCT, name, fn)
        hashes[name] = hashlib.sha256(
            ast.dump(node, include_attributes=False).encode()).hexdigest()
    assert reader.CMPCT is importlib.import_module("cmpct.transactions").CMPCT
    return {"donor_commit": DONOR_COMMIT, "donor_blob": DONOR_BLOB,
            "method_ast_sha256": hashes}


def child(mode: str, src: Path, dst: Path, receipt: Path) -> None:
    import cmpct.reader as reader
    from cmpct.transactions import compact_archive
    from cmpct.codec import S_SPARSE
    transplant = apply_exact_donor() if mode == "B" else None
    start_io = io_snapshot()
    start_wall, start_cpu = time.perf_counter_ns(), time.process_time_ns()
    result = compact_archive(src, dst)
    elapsed_wall, elapsed_cpu = (time.perf_counter_ns() - start_wall,
                                 time.process_time_ns() - start_cpu)
    end_io = io_snapshot()
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    with reader.CMPCT(dst) as ar:
        row = ar.by["sparse.bin"]
        assert row[6][0] == S_SPARSE
        assert ar.read_range("sparse.bin", 0, PAGE) == MARK_HEAD
        assert ar.read_range("sparse.bin", row[4] - PAGE, PAGE) == MARK_TAIL
        assert ar.read("small.bin") == b"J24I12 committed update" * 8
        assert ar.verify() == len([x for x in ar.files if x[1] != 1])
        rows = [(x[0], x[1], x[2], x[3], x[4]) for x in ar.files]
    record = {
        "mode": mode, "transplant": transplant,
        "source_sha256": digest(src), "output_sha256": digest(dst),
        "output_bytes": dst.stat().st_size, "logical_sparse_size": row[4],
        "rows": rows, "elapsed_wall_ns": elapsed_wall,
        "elapsed_cpu_ns": elapsed_cpu, "peak_rss_kib": peak,
        "io_delta": {k: end_io[k] - start_io[k] for k in
                     sorted(start_io.keys() & end_io.keys())},
        "builder_result": result, "verified": True,
    }
    receipt.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"mode": mode, "rss_kib": peak, "elapsed_ns": elapsed_wall,
                      "sha256": record["output_sha256"]}, sort_keys=True))


def negative_child(mode: str, src: Path, dst: Path, receipt: Path) -> None:
    if mode == "B":
        apply_exact_donor()
    from cmpct.transactions import compact_archive
    before = digest(dst)
    try:
        compact_archive(src, dst)
    except Exception as exc:
        record = {"mode": mode, "rejected": True, "exception": type(exc).__name__,
                  "destination_preserved": digest(dst) == before,
                  "source_preserved": True}
        assert record["destination_preserved"]
        receipt.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n")
        return
    raise AssertionError("corrupt source reached publication")


def corrupt_physical_blob(original: Path, target: Path) -> None:
    from cmpct.reader import CMPCT
    from cmpct.codec import BHDR, S_SPARSE
    shutil.copyfile(original, target)
    with CMPCT(target) as ar:
        row = ar.by["sparse.bin"]
        assert row[6][0] == S_SPARSE
        idx = row[6][1][0][2][0]
        offset, _, comp_size, _, meta_size = ar.blobs[idx]
        assert comp_size > 0
        payload_at = ar.record_base + offset + BHDR.size + meta_size
    contents = bytearray(target.read_bytes())
    assert payload_at < len(contents)
    contents[payload_at] ^= 0x01
    target.write_bytes(contents)
    assert digest(original) != digest(target)


def execute_child(argv: list[str], cwd: Path, out: Path, label: str):
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), *argv],
        cwd=cwd, text=True, capture_output=True, timeout=360, check=False,
        env={**os.environ, "CMPCT_ENCODE_WORKERS": "1"},
    )
    (out / (label + ".stdout.txt")).write_text(result.stdout)
    (out / (label + ".stderr.txt")).write_text(result.stderr)
    if result.returncode:
        raise AssertionError(
            f"{label} exit={result.returncode}; stderr={result.stderr[-4000:]}")
    return result


def main() -> dict:
    out = Path(os.environ["CMPCT_J24I14_ARTIFACT_DIR"])
    out.mkdir(parents=True, exist_ok=True)
    all_cases = []
    for size in SIZES:
        with tempfile.TemporaryDirectory(prefix="j24i14-") as temporary:
            work = Path(temporary)
            fixture = make_fixture(work, size)
            source = fixture["source"]
            before = fixture["input_archive_sha256"]
            pairs = []
            for index, mode in enumerate(ORDER):
                dst = work / f"compacted-{index}-{mode}.cmpct"
                receipt = work / f"child-{index}-{mode}.json"
                execute_child(["--child", mode, str(source), str(dst),
                               str(receipt)], work, out,
                              f"{size}-{index}-{mode}")
                obj = json.loads(receipt.read_text())
                assert obj["source_sha256"] == before
                assert obj["logical_sparse_size"] == size
                pairs.append(obj)
                shutil.copyfile(receipt, out / f"receipt-{size}-{index}-{mode}.json")
                shutil.copyfile(dst, out / f"output-{size}-{index}-{mode}.cmpct")
            assert digest(source) == before
            hashes = {p["output_sha256"] for p in pairs}
            bytes_set = {p["output_bytes"] for p in pairs}
            rows = {json.dumps(p["rows"], sort_keys=True) for p in pairs}
            exact = len(hashes) == len(bytes_set) == len(rows) == 1
            corrupt = work / "corrupt.cmpct"
            corrupt_physical_blob(source, corrupt)
            negatives = []
            for mode in ("A", "B"):
                destination = work / f"sentinel-{mode}.cmpct"
                destination.write_bytes(b"J24I14 keep destination unchanged")
                nrecord = work / f"negative-{mode}.json"
                execute_child(["--negative", mode, str(corrupt),
                               str(destination), str(nrecord)],
                              work, out, f"negative-{size}-{mode}")
                obj = json.loads(nrecord.read_text())
                assert obj["rejected"] and obj["destination_preserved"]
                negatives.append(obj)
            shutil.copyfile(source, out / f"source-{size}.cmpct")
            shutil.copyfile(corrupt, out / f"corrupt-{size}.cmpct")
            diffs_mib = [
                (pairs[0]["peak_rss_kib"] - pairs[1]["peak_rss_kib"]) / 1024,
                (pairs[3]["peak_rss_kib"] - pairs[2]["peak_rss_kib"]) / 1024,
            ]
            all_cases.append({
                "logical_sparse_bytes": size, "source_sha256": before,
                "source_archive_bytes": fixture["input_archive_bytes"],
                "exact_output_bytes": exact, "raw_repetitions": pairs,
                "paired_A_minus_B_rss_mib": diffs_mib,
                "corruption_controls": negatives,
            })
    large = next(c for c in all_cases if c["logical_sparse_bytes"] == 128 << 20)
    a = [p for p in large["raw_repetitions"] if p["mode"] == "A"]
    b = [p for p in large["raw_repetitions"] if p["mode"] == "B"]
    support = (all(c["exact_output_bytes"] for c in all_cases)
               and all(p["peak_rss_kib"] > 128 * 1024 for p in a)
               and all(p["peak_rss_kib"] < 128 * 1024 for p in b)
               and all(delta >= 128 for delta in large["paired_A_minus_B_rss_mib"]))
    result = {
        "schema": "j24i14-court-v1",
        "source_compaction_commit": BASE_COMMIT,
        "source_streaming_donor_commit": DONOR_COMMIT,
        "source_streaming_donor_blob": DONOR_BLOB,
        "platform": sys.platform, "python": sys.version,
        "cases": all_cases,
        "decision": "EXACT_DONOR_TRANSFER_SUPPORTED" if support else "TRANSFER_NOT_SUPPORTED_OR_AMBIGUOUS",
        "product_implementation_changed": False,
        "release_credit": False,
        "known_blocker": "PR #726 staged-name rebind; no security promotion",
    }
    (out / "court.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"decision": result["decision"],
                      "large_pair_rss_mib": large["paired_A_minus_B_rss_mib"],
                      "archive_byte_equal": large["exact_output_bytes"]}, sort_keys=True))
    return result


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "--child":
        child(sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5]))
    elif len(sys.argv) == 6 and sys.argv[1] == "--negative":
        negative_child(sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5]))
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("usage: no args or --child/--negative MODE SRC DST RECEIPT")
