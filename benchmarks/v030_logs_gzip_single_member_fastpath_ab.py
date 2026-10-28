from __future__ import annotations

"""Frozen R1 A/B for a semantic-preserving single-member gzip fast path."""

import argparse
import gc
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import statistics
import time
import zlib

from benchmarks import neutral_hostile_corpus_v1 as CORPUS
from experiments import entropygraph_v030_release_product_logs_candidate as PRODUCT
from experiments import entropygraph_v030_release_product_logs_runtime as RUNTIME
from experiments import entropygraph_v030_logs_fused_extract as FUSED

ROUNDS = 21
SUPPORT_REDUCTION = 0.04
RETIRE_REDUCTION = 0.01
PREREG = "docs/v030-rnd/R25_LOGS_GZIP_SINGLE_MEMBER_FASTPATH_AB_PREREG.md"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _clean(path: Path) -> None:
    if path.exists() or path.is_symlink():
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()


def _candidate_gzip(raw: bytes) -> tuple[bytes, bool]:
    """Return (decoded, fast_hit); fall back unless zlib proves exact one-member consumption."""
    try:
        decoder = zlib.decompressobj(wbits=31)
        out = decoder.decompress(raw)
        out += decoder.flush()
        if decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail:
            return out, True
    except zlib.error:
        pass
    return gzip.decompress(raw), False


def _outcome(fn, raw: bytes) -> tuple:
    try:
        return ("ok", fn(raw))
    except Exception as exc:  # semantic attack compares inherited acceptance/rejection, not exception prose.
        return ("err", type(exc).__name__)


def _named_member(payload: bytes) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(filename="named.log", mode="wb", fileobj=buf, mtime=0) as stream:
        stream.write(payload)
    return buf.getvalue()


def _semantic_parity() -> dict:
    a = b"alpha logs\n" * 128
    b = b"beta logs\n" * 97
    single = gzip.compress(a, mtime=0)
    second = gzip.compress(b, mtime=0)
    corrupt_crc = bytearray(single)
    corrupt_crc[-8] ^= 0x5A
    cases = {
        "single": single,
        "named_header": _named_member(a),
        "concatenated_members": single + second,
        "zero_padding": single + (b"\0" * 16),
        "corrupt_crc": bytes(corrupt_crc),
        "truncated": single[:-5],
        "malformed": b"not-a-gzip-stream",
        "trailing_garbage": single + b"garbage",
    }
    rows = {}
    all_equal = True
    expected_fallback = {"concatenated_members", "zero_padding", "corrupt_crc", "truncated", "malformed", "trailing_garbage"}
    for label, raw in cases.items():
        inherited = _outcome(gzip.decompress, raw)
        candidate = _outcome(lambda data: _candidate_gzip(data)[0], raw)
        try:
            _value, hit = _candidate_gzip(raw)
        except Exception:
            hit = False
        equal = inherited == candidate
        all_equal = all_equal and equal
        rows[label] = {
            "inherited": [inherited[0], inherited[1].hex() if inherited[0] == "ok" else inherited[1]],
            "candidate": [candidate[0], candidate[1].hex() if candidate[0] == "ok" else candidate[1]],
            "equal": equal,
            "fast_path_hit": bool(hit),
            "fallback_expected": label in expected_fallback,
        }
    fallback_shape_ok = all(not rows[label]["fast_path_hit"] for label in expected_fallback)
    return {"cases": rows, "all_equal": all_equal, "fallback_shape_ok": fallback_shape_ok}


def _extract(archive: Path, dst: Path, tree: str, *, candidate: bool) -> dict:
    _clean(dst)
    gc.collect()
    original = FUSED.LOGS.V2.BASE._decode
    fast_hits = 0
    fallback_calls = 0
    gzip_calls = 0

    def candidate_decode(codec: str, raw: bytes, *, max_output: int = FUSED.LOGS.V2.BASE.MAX_DECODE_UNIT) -> bytes:
        nonlocal fast_hits, fallback_calls, gzip_calls
        if codec != "gzip":
            return original(codec, raw, max_output=max_output)
        gzip_calls += 1
        value, hit = _candidate_gzip(raw)
        fast_hits += int(hit)
        fallback_calls += int(not hit)
        if len(value) > max_output:
            raise RuntimeError("inverse-edge decoded output exceeds policy")
        return value

    if candidate:
        FUSED.LOGS.V2.BASE._decode = candidate_decode
    try:
        started = time.perf_counter()
        RUNTIME.extract(archive, dst)
        elapsed = time.perf_counter() - started
    finally:
        if candidate:
            FUSED.LOGS.V2.BASE._decode = original
    if PRODUCT.treehash(dst) != tree:
        raise RuntimeError("Logs gzip fast-path extraction tree drift")
    return {
        "wall_s": elapsed,
        "gzip_calls": gzip_calls,
        "fast_hits": fast_hits,
        "fallback_calls": fallback_calls,
    }


def _median(rows: list[dict], key: str) -> float:
    return float(statistics.median(float(row[key]) for row in rows))


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    parity = _semantic_parity()

    corpus = work_root / "corpus"
    CORPUS.corpus_logs(corpus)
    source = corpus / "05_logs_and_telemetry"
    tree = PRODUCT.treehash(source)
    archive = work_root / "logs.cmpct"
    stats = dict(PRODUCT.build(source, archive))
    verified = dict(PRODUCT.strong_verify(archive))
    if not verified.get("ok") or verified.get("tree_sha256") != tree or stats.get("selected") != "logs-inverse":
        raise RuntimeError("frozen Logs archive/selection verification failed")

    _extract(archive, work_root / "warm-control", tree, candidate=False)
    _extract(archive, work_root / "warm-candidate", tree, candidate=True)

    controls: list[dict] = []
    candidates: list[dict] = []
    order: list[str] = []
    for i in range(ROUNDS):
        pair = ("control", "candidate") if i % 2 == 0 else ("candidate", "control")
        for label in pair:
            order.append(label)
            row = _extract(archive, work_root / f"round-{i:02d}-{label}", tree, candidate=label == "candidate")
            (candidates if label == "candidate" else controls).append(row)

    control_median = _median(controls, "wall_s")
    candidate_median = _median(candidates, "wall_s")
    ratio = candidate_median / control_median
    reduction = 1.0 - ratio
    gzip_call_sets = sorted({int(row["gzip_calls"]) for row in candidates})
    fast_hit_sets = sorted({int(row["fast_hits"]) for row in candidates})
    fallback_sets = sorted({int(row["fallback_calls"]) for row in candidates})
    geometry_ok = gzip_call_sets == [2] and min(fast_hit_sets or [0]) >= 1
    valid = bool(parity["all_equal"] and parity["fallback_shape_ok"] and geometry_ok and verified.get("ok"))

    if not valid:
        decision = "INVALID_GZIP_FASTPATH_PARITY"
    elif reduction >= SUPPORT_REDUCTION and ratio <= 0.96:
        decision = "LOGS_GZIP_SINGLE_MEMBER_FASTPATH_SUPPORTED"
    elif reduction < RETIRE_REDUCTION:
        decision = "LOGS_GZIP_SINGLE_MEMBER_FASTPATH_RETIRED"
    else:
        decision = "LOGS_GZIP_SINGLE_MEMBER_FASTPATH_AMBIGUOUS"

    return {
        "schema": "cmpct-v030-logs-gzip-single-member-fastpath-ab-v1",
        "preregistration": PREREG,
        "target": "neutral_hostile_v1/05_logs_and_telemetry",
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": _sha256(archive),
        "selected": stats.get("selected"),
        "tree_sha256": tree,
        "strong_verify": verified,
        "semantic_parity": parity,
        "rounds": ROUNDS,
        "order": order,
        "control_rows": controls,
        "candidate_rows": candidates,
        "control_median_s": control_median,
        "candidate_median_s": candidate_median,
        "candidate_wall_ratio": ratio,
        "candidate_total_reduction_fraction": reduction,
        "candidate_gzip_call_sets": gzip_call_sets,
        "candidate_fast_hit_sets": fast_hit_sets,
        "candidate_fallback_call_sets": fallback_sets,
        "candidate_geometry_ok": geometry_ok,
        "support_reduction_floor": SUPPORT_REDUCTION,
        "retire_reduction_ceiling": RETIRE_REDUCTION,
        "experiment_valid": valid,
        "decision": decision,
        "release_credit": False,
        "production_source_changed": False,
        "archive_semantics_changed": False,
        "multi_member_semantics_preserved_by_fallback": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-logs-gzip-fastpath-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-logs-gzip-fastpath.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in (
        "control_median_s", "candidate_median_s", "candidate_wall_ratio",
        "candidate_total_reduction_fraction", "candidate_gzip_call_sets",
        "candidate_fast_hit_sets", "candidate_fallback_call_sets",
        "experiment_valid", "decision",
    )}, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("Logs gzip single-member fast-path parity invalid")


if __name__ == "__main__":
    main()
