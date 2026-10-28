from __future__ import annotations

"""Research-only C25EG08 compression hot-path A/B using reusable per-worker Zstd contexts.

The exact feature-pruned Office executor spends ~272 ms compressing 21 final packs, 15 at
high effort. The inherited V25 ``zc`` helper calls the one-shot ``ZSTD_compress`` API for
every pack, which creates/resets a compression context internally on every call. This oracle
keeps the selected policy, levels and bytes fixed while testing one reusable ``ZSTD_CCtx`` per
ThreadPool worker through ``ZSTD_compressCCtx``.

Output must be byte-for-byte identical to the ordinary executor on every alternating round.
Timing covers only the already-isolated final-pack emission phase and therefore receives zero
release credit. A material result authorizes a separate complete-create productization A/B.
"""

import argparse
from contextlib import contextmanager
import ctypes
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import tempfile
import threading
import time

from benchmarks import v030_federated_compact_framing_v8_policy_distill as V1
from benchmarks import v030_federated_compact_framing_v8_policy_distill_v3 as V3
from benchmarks import v030_federated_compact_framing_v8_policy_distill_v5 as V5POL
from benchmarks import v030_federated_compact_framing_v8_direct_v4 as DV4
from benchmarks import v030_federated_compact_framing_v8_direct_v5 as DV5
from benchmarks import v030_federated_compact_framing_v8_policy_exec_v6 as V6
from experiments import entropygraph_v025 as V25

ROUNDS =  nine = 9
MIN_MEDIAN_SAVING_S = 0.015


# Bind the standard context API on the same libzstd already used by the product research engine.
V25.z.ZSTD_createCCtx.argtypes = []
V25.z.ZSTD_createCCtx.restype = ctypes.c_void_p
V25.z.ZSTD_freeCCtx.argtypes = [ctypes.c_void_p]
V25.z.ZSTD_freeCCtx.restype = V25.sz
V25.z.ZSTD_compressCCtx.argtypes = [ctypes.c_void_p, ctypes.c_void_p, V25.sz, ctypes.c_void_p, V25.sz, ctypes.c_int]
V25.z.ZSTD_compressCCtx.restype = V25.sz
V25.z.ZSTD_isError.argtypes = [V25.sz]
V25.z.ZSTD_isError.restype = ctypes.c_uint

_tls = threading.local()
_contexts: list[int] = []
_contexts_lock = threading.Lock()


def _reused_zc(raw: bytes, level: int = 19) -> bytes:
    if not raw:
        return b""
    ctx = getattr(_tls, "ctx", None)
    if not ctx:
        ctx = V25.z.ZSTD_createCCtx()
        if not ctx:
            raise RuntimeError("ZSTD_createCCtx failed")
        _tls.ctx = ctx
        with _contexts_lock:
            _contexts.append(int(ctx))
    src = ctypes.create_string_buffer(raw)
    cap = int(V25.z.ZSTD_compressBound(len(raw)))
    dst = ctypes.create_string_buffer(cap)
    n = int(V25.z.ZSTD_compressCCtx(ctx, dst, cap, src, len(raw), int(level)))
    if V25.z.ZSTD_isError(n):
        raise RuntimeError("ZSTD_compressCCtx failed")
    return dst.raw[:n]


def _free_contexts() -> None:
    # Worker threads may already be gone; libzstd contexts are process-owned handles and can be freed here.
    with _contexts_lock:
        handles = list(dict.fromkeys(_contexts))
        _contexts.clear()
    for handle in handles:
        V25.z.ZSTD_freeCCtx(ctypes.c_void_p(handle))


@contextmanager
def _zc(candidate: bool):
    old = V25.zc
    if candidate:
        V25.zc = _reused_zc
    try:
        yield
    finally:
        V25.zc = old
        if candidate:
            _free_contexts()


def _emit(raw_eg07: bytes, root: Path, rules: list[dict], tag: str, candidate: bool) -> tuple[dict, bytes, float]:
    out = root / f"{tag}.c25eg08"
    started = time.perf_counter()
    with _zc(candidate):
        stats = V6._emit_pruned(raw_eg07, out, rules)
    elapsed = time.perf_counter() - started
    return stats, out.read_bytes(), elapsed


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    source, accepted_v029 = V1._frozen_office(work_root)
    with tempfile.TemporaryDirectory(prefix="cmpct-eg08-reused-cctx-", dir=work_root) as td:
        root = Path(td)
        stage = V1.EXT._normalized_stage(source, root / "normalized")
        comparators = V1._comparators(stage, root / "comparators")
        raw_eg07, _graph_s = DV5._tmpfs_capture_raw_final_eg07(stage, root / "discovery")
        meta_comp, _meta_raw, _digest, raws = DV4._raw_eg07_parts(raw_eg07)
        features = V3._pack_features(raws)
        payload_table = V3._payload_table(raws)
        ceiling = min(int(accepted_v029), int(comparators["zip"]["archive_bytes"]), int(comparators["zstd19"]["archive_bytes"]))
        rules, vector, projected, _search = V5POL._search_full_frontier(features, meta_comp, payload_table, ceiling)
        if rules is None or vector is None or projected is None:
            raise RuntimeError("Office policy frontier unexpectedly missing")

        reference_path = root / "serial-reference.c25eg08"
        V1._emit(raw_eg07, reference_path, V3._selection_dict(vector))
        reference = reference_path.read_bytes()
        reference_sha = hashlib.sha256(reference).hexdigest()

        samples = {"baseline": [], "reused_cctx": []}
        compression = {"baseline": [], "reused_cctx": []}
        workers = set()
        for rep in range(ROUNDS):
            order = ("baseline", "reused_cctx") if rep % 2 == 0 else ("reused_cctx", "baseline")
            for kind in order:
                candidate = kind == "reused_cctx"
                stats, blob, elapsed = _emit(raw_eg07, root, rules, f"{kind}-{rep}", candidate)
                if blob != reference:
                    raise RuntimeError(f"{kind} changed exact EG08 archive bytes")
                if tuple(int(x) for x in stats["selected_levels"]) != tuple(int(x) for x in vector):
                    raise RuntimeError(f"{kind} changed selected compression levels")
                samples[kind].append(float(elapsed))
                compression[kind].append(float(stats["compression_s"]))
                workers.add(int(stats["workers"]))

    base = statistics.median(compression["baseline"])
    cand = statistics.median(compression["reused_cctx"])
    saving = base - cand
    valid = len(workers) == 1 and len(samples["baseline"]) == ROUNDS and len(samples["reused_cctx"]) == ROUNDS
    material = valid and saving >= MIN_MEDIAN_SAVING_S and cand < base
    return {
        "schema": "cmpct-v030-eg08-reused-zstd-context-oracle-v1",
        "contract": {
            "release_credit": False,
            "production_change": False,
            "archive_bytes_changed": False,
            "selected_levels_changed": False,
            "compression_backend": "same-libzstd-ZSTD_compressCCtx",
            "context_scope": "one reusable CCtx per bounded ThreadPool worker",
            "minimum_median_compression_saving_s": MIN_MEDIAN_SAVING_S,
            "timing_scope": "final-pack-emission-only",
        },
        "candidate": {
            "archive_bytes": len(reference),
            "archive_sha256": reference_sha,
            "selected_levels": list(vector),
            "workers": next(iter(workers)),
        },
        "timing": {
            "rounds": ROUNDS,
            "baseline_median_emit_s": float(statistics.median(samples["baseline"])),
            "candidate_median_emit_s": float(statistics.median(samples["reused_cctx"])),
            "baseline_median_compression_s": float(base),
            "candidate_median_compression_s": float(cand),
            "median_compression_saving_s": float(saving),
            "compression_speedup_fraction": float(1.0 - cand / max(base, 1e-12)),
            "raw_emit_s": samples,
            "raw_compression_s": compression,
        },
        "gate": {
            "experiment_valid": bool(valid),
            "materially_faster": bool(material),
            "passed": bool(valid),
        },
        "claim_boundary": "Research-only isolated compression A/B. Even a material exact-byte win requires complete verified-create timing, canonical implementation, all-15 no-regression, native/Android and final authority before promotion.",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-eg08-reused-zstd-context-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-eg08-reused-zstd-context.json"))
    a = p.parse_args()
    result = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": result["candidate"], "timing": result["timing"], "gate": result["gate"]}, indent=2), flush=True)
    if not result["gate"]["passed"]:
        raise SystemExit("reused Zstd context experiment invalid")


if __name__ == "__main__":
    main()
