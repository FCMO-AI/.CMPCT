"""CMPCT v0.29 detached oracle — Shared Dictionary Record Context.

The closed residual experiments proved that recipe bytes and record framing are too small to explain the
remaining hostile structural gap. This oracle therefore measures a larger pool without changing record
boundaries: direct/root physical records keep their independent frames, but eligible zstd records may
reference one small archive-global trained dictionary.

No dictionary-coded CMPCT archive is emitted. The script builds the exact accepted attempt-5 portfolio,
reads its authenticated records, trains candidate dictionaries from those existing logical record bytes,
recompresses only direct/root records in memory, verifies every dictionary decode byte-for-byte, charges
the complete dictionary record plus conservative metadata cost, and reports the exact physical ceiling.

Footnote: Zstandard dictionaries are a real decoder dependency, not free compression context. A cold
single-target read therefore pays the dictionary once. The oracle preserves the established <=8x pack /
dependent-node materialization envelope and additionally caps dictionary-only overhead at <=2x per target.
Only a >=128 KiB net archive saving after all dictionary storage charges can authorize a reader-visible
implementation experiment.
"""
from __future__ import annotations

import argparse
import binascii
import ctypes
import ctypes.util
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time

HERE = Path(__file__).resolve().parent
STRICT_PATH = HERE / "entropygraph_v029_residual_strict.py"
PACK_PATH = HERE / "entropygraph_v029_residual_pack.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ENGINE = _load(STRICT_PATH, "cmpct_v029_dict_context_strict")
PACK = _load(PACK_PATH, "cmpct_v029_dict_context_pack")
PH = PACK.PH
H = PACK.H
CODEC_RAW = PACK.CODEC_RAW
CODEC_ZSTD = PACK.CODEC_ZSTD
CODEC_PREFLATE = PACK.CODEC_PREFLATE
MAX_READ_AMP = 8.0
MAX_ADDITIONAL_DICT_AMP = 2.0
DICT_SIZES = (8, 16, 32, 64, 96, 128)  # KiB; frozen before hostile execution.
TRAIN_SAMPLE_SLICE = 64 * 1024
DICT_METADATA_CHARGE = 512
MIN_NET_SAVING = 128 * 1024
MIN_IMPROVED_RECORDS = 8


class ZstdDictionaryAPI:
    """Minimal libzstd dictionary API wrapper used only by the detached oracle."""

    def __init__(self) -> None:
        libname = ctypes.util.find_library("zstd") or "libzstd.so"
        self.z = ctypes.CDLL(libname)
        sz = ctypes.c_size_t
        vp = ctypes.c_void_p

        self.z.ZDICT_trainFromBuffer.argtypes = [vp, sz, vp, ctypes.POINTER(sz), ctypes.c_uint]
        self.z.ZDICT_trainFromBuffer.restype = sz
        self.z.ZDICT_isError.argtypes = [sz]
        self.z.ZDICT_isError.restype = ctypes.c_uint
        self.z.ZDICT_getErrorName.argtypes = [sz]
        self.z.ZDICT_getErrorName.restype = ctypes.c_char_p

        self.z.ZSTD_compressBound.argtypes = [sz]
        self.z.ZSTD_compressBound.restype = sz
        self.z.ZSTD_createCCtx.argtypes = []
        self.z.ZSTD_createCCtx.restype = vp
        self.z.ZSTD_freeCCtx.argtypes = [vp]
        self.z.ZSTD_freeCCtx.restype = sz
        self.z.ZSTD_compress_usingDict.argtypes = [vp, vp, sz, vp, sz, vp, sz, ctypes.c_int]
        self.z.ZSTD_compress_usingDict.restype = sz
        self.z.ZSTD_createDCtx.argtypes = []
        self.z.ZSTD_createDCtx.restype = vp
        self.z.ZSTD_freeDCtx.argtypes = [vp]
        self.z.ZSTD_freeDCtx.restype = sz
        self.z.ZSTD_decompress_usingDict.argtypes = [vp, vp, sz, vp, sz, vp, sz]
        self.z.ZSTD_decompress_usingDict.restype = sz
        self.z.ZSTD_isError.argtypes = [sz]
        self.z.ZSTD_isError.restype = ctypes.c_uint
        self.z.ZSTD_getErrorName.argtypes = [sz]
        self.z.ZSTD_getErrorName.restype = ctypes.c_char_p

    def _zstd_error(self, code: int) -> str:
        return (self.z.ZSTD_getErrorName(code) or b"unknown zstd error").decode("utf-8", "replace")

    def train(self, samples: list[bytes], capacity: int) -> tuple[bytes | None, str | None]:
        if len(samples) < 8 or sum(map(len, samples)) < capacity * 8:
            return None, "insufficient-training-samples"
        blob = b"".join(samples)
        source = ctypes.create_string_buffer(blob)
        sizes = (ctypes.c_size_t * len(samples))(*(len(sample) for sample in samples))
        out = ctypes.create_string_buffer(capacity)
        written = int(self.z.ZDICT_trainFromBuffer(out, capacity, source, sizes, len(samples)))
        if self.z.ZDICT_isError(written):
            name = (self.z.ZDICT_getErrorName(written) or b"unknown zdict error").decode("utf-8", "replace")
            return None, name
        return out.raw[:written], None

    def compress_verify(self, raw: bytes, dictionary: bytes, level: int = 19) -> bytes:
        src = ctypes.create_string_buffer(raw)
        dct = ctypes.create_string_buffer(dictionary)
        bound = int(self.z.ZSTD_compressBound(len(raw)))
        dst = ctypes.create_string_buffer(bound)
        cctx = self.z.ZSTD_createCCtx()
        if not cctx:
            raise RuntimeError("ZSTD_createCCtx failed")
        try:
            written = int(self.z.ZSTD_compress_usingDict(
                cctx, dst, bound, src, len(raw), dct, len(dictionary), level
            ))
        finally:
            self.z.ZSTD_freeCCtx(cctx)
        if self.z.ZSTD_isError(written):
            raise RuntimeError(f"dictionary compression failed: {self._zstd_error(written)}")
        payload = dst.raw[:written]

        restored = ctypes.create_string_buffer(len(raw))
        compressed = ctypes.create_string_buffer(payload)
        dctx = self.z.ZSTD_createDCtx()
        if not dctx:
            raise RuntimeError("ZSTD_createDCtx failed")
        try:
            got = int(self.z.ZSTD_decompress_usingDict(
                dctx, restored, len(raw), compressed, len(payload), dct, len(dictionary)
            ))
        finally:
            self.z.ZSTD_freeDCtx(dctx)
        if self.z.ZSTD_isError(got):
            raise RuntimeError(f"dictionary decompression failed: {self._zstd_error(got)}")
        if got != len(raw) or restored.raw[:got] != raw:
            raise RuntimeError("dictionary round-trip changed physical logical record bytes")
        return payload


def _read_records(archive: Path) -> tuple[dict, list[dict]]:
    stream, meta, record_start, offsets, _ = ENGINE._open(archive)
    rows = []
    try:
        leaves = list(meta["record_leaf_sha256"])
        for record_id, rel in enumerate(offsets):
            stream.seek(record_start + rel)
            header = stream.read(PH.size)
            if len(header) != PH.size:
                raise RuntimeError("short shared-dictionary source record header")
            codec, usize, csize, crc, logical_sha = PH.unpack(header)
            payload = stream.read(csize)
            if len(payload) != csize or H(payload) != leaves[record_id]:
                raise RuntimeError("shared-dictionary source record leaf mismatch")
            if codec == CODEC_RAW:
                raw = payload
            elif codec == CODEC_ZSTD:
                raw = PACK.zd(payload, usize)
            elif codec == CODEC_PREFLATE:
                raw = PACK.V028._preflate_unpack(payload, usize)
            else:
                raise RuntimeError("unknown shared-dictionary source record codec")
            if len(raw) != usize or (binascii.crc32(raw) & 0xFFFFFFFF) != crc or H(raw) != logical_sha:
                raise RuntimeError("shared-dictionary source record integrity mismatch")
            rows.append({
                "record_id": record_id,
                "codec": int(codec),
                "logical_bytes": int(usize),
                "payload_bytes": int(csize),
                "raw": raw,
            })
    finally:
        stream.close()
    return meta, rows


def _direct_record_ids(meta: dict) -> set[int]:
    return {int(desc[1]) for desc in meta["nodes"] if desc[0] == "direct"}


def _node_target_len(desc: list) -> int:
    kind = desc[0]
    if kind == "direct":
        return int(desc[3])
    if kind in ("delta", "mosaic"):
        return int(desc[3])
    if kind in ("delta_pack", "pack_mosaic"):
        return int(desc[5])
    raise RuntimeError(f"unknown node kind for dictionary locality: {kind}")


def _node_record_dependencies(meta: dict, node_id: int) -> set[int]:
    nodes = meta["nodes"]
    desc = nodes[node_id]
    kind = desc[0]
    if kind == "direct":
        return {int(desc[1])}
    if kind == "delta":
        base_id, recipe_id = int(desc[1]), int(desc[2])
        return {int(nodes[base_id][1]), recipe_id}
    if kind == "delta_pack":
        base_id, recipe_id = int(desc[1]), int(desc[2])
        return {int(nodes[base_id][1]), recipe_id}
    if kind == "mosaic":
        base_ids, recipe_id = list(desc[1]), int(desc[2])
        return {int(nodes[int(base_id)][1]) for base_id in base_ids} | {recipe_id}
    if kind == "pack_mosaic":
        recipe_id, base_ids = int(desc[1]), list(desc[4])
        return {int(nodes[int(base_id)][1]) for base_id in base_ids} | {recipe_id}
    raise RuntimeError(f"unknown node kind for dictionary locality: {kind}")


def _training_samples(records: list[dict], direct_ids: set[int]) -> list[bytes]:
    samples = []
    for row in records:
        if row["record_id"] not in direct_ids or row["codec"] == CODEC_PREFLATE:
            continue
        raw = row["raw"]
        if len(raw) <= TRAIN_SAMPLE_SLICE:
            if len(raw) >= 64:
                samples.append(raw)
            continue
        samples.append(raw[:TRAIN_SAMPLE_SLICE])
        # Footnote: a second deterministic tail sample prevents the dictionary from learning only pack
        # prefixes while keeping each training sample bounded like zstd's own small-message guidance.
        samples.append(raw[-TRAIN_SAMPLE_SLICE:])
    return samples


def _locality_filter(meta: dict, records: list[dict], candidate_ids: set[int], dict_size: int) -> tuple[set[int], dict]:
    """Conservatively remove direct records whose shared dictionary would violate new locality debt."""
    raw_sizes = {row["record_id"]: row["logical_bytes"] for row in records}
    nodes = meta["nodes"]
    allowed = set(candidate_ids)

    usage = []
    for node_id, desc in enumerate(nodes):
        deps = _node_record_dependencies(meta, node_id)
        current = sum(raw_sizes[record_id] for record_id in deps)
        target_len = max(1, _node_target_len(desc))
        usage.append((node_id, deps, current, target_len))

    # Footnote: dictionary overhead is charged only to targets that actually touch a newly dictionary-
    # coded direct record. Existing attempt-5 targets that never consume the new context are not allowed
    # to fail this oracle merely because their inherited materialization policy differs from Mosaic's.
    for _, deps, _, target_len in usage:
        if deps & allowed and dict_size / target_len > MAX_ADDITIONAL_DICT_AMP:
            allowed.difference_update(deps & allowed)

    for _, deps, current, target_len in usage:
        if deps & allowed and (current + dict_size) / target_len > MAX_READ_AMP:
            # Conservative deterministic removal avoids a post-result combinatorial rescue optimizer.
            allowed.difference_update(deps & allowed)

    # Preserve the existing weighted direct-pack envelope while charging the dictionary once per cold
    # direct member request. This mirrors v0.28/attempt-5's direct-pack accounting contract.
    direct_members = [
        (int(desc[1]), max(1, int(desc[3])))
        for desc in nodes if desc[0] == "direct"
    ]
    weighted_logical = sum(length for _, length in direct_members)
    weighted_decoded = sum(
        raw_sizes[record_id] + (dict_size if record_id in allowed else 0)
        for record_id, _ in direct_members
    )
    weighted_pack_amp = weighted_decoded / max(1, weighted_logical)
    if weighted_pack_amp > MAX_READ_AMP:
        allowed.clear()
        weighted_decoded = sum(raw_sizes[record_id] for record_id, _ in direct_members)
        weighted_pack_amp = weighted_decoded / max(1, weighted_logical)

    # Final metrics intentionally cover only targets touched by the new dictionary dependency. This
    # isolates *added* locality debt from inherited attempt-5 behavior while the weighted pack metric
    # above still protects the whole direct-root population.
    max_touched_dep_amp = 0.0
    max_extra_amp = 0.0
    touched_nodes = 0
    for _, deps, current, target_len in usage:
        if not deps & allowed:
            continue
        touched_nodes += 1
        max_touched_dep_amp = max(max_touched_dep_amp, (current + dict_size) / target_len)
        max_extra_amp = max(max_extra_amp, dict_size / target_len)

    return allowed, {
        "weighted_direct_pack_read_amp": weighted_pack_amp,
        "max_dependent_node_read_amp": max_touched_dep_amp,
        "max_additional_dictionary_read_amp": max_extra_amp,
        "dictionary_touched_nodes": touched_nodes,
    }


def measure(root: Path, work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    archive = work_root / "attempt5.cmpct"
    started = time.perf_counter()
    built = ENGINE.build(root, archive)
    verified = ENGINE.strong_verify(archive)
    if not verified.get("ok") or verified.get("tree_sha256") != ENGINE.BASE.treehash(root):
        raise RuntimeError("attempt-5 source archive failed verification before dictionary oracle")

    meta, records = _read_records(archive)
    direct_ids = _direct_record_ids(meta)
    samples = _training_samples(records, direct_ids)
    api = ZstdDictionaryAPI()
    results = []

    candidate_pool = [
        row for row in records
        if row["record_id"] in direct_ids and row["codec"] != CODEC_PREFLATE
    ]
    baseline_direct_payload = sum(row["payload_bytes"] for row in candidate_pool)

    for kib in DICT_SIZES:
        capacity = kib * 1024
        train_started = time.perf_counter()
        dictionary, train_error = api.train(samples, capacity)
        train_s = time.perf_counter() - train_started
        if dictionary is None:
            results.append({
                "requested_dictionary_kib": kib,
                "available": False,
                "reason": train_error,
                "train_s": train_s,
            })
            continue

        compressed = {}
        recompress_started = time.perf_counter()
        for row in candidate_pool:
            payload = api.compress_verify(row["raw"], dictionary, 19)
            if len(payload) < row["payload_bytes"]:
                compressed[row["record_id"]] = {
                    "baseline_payload_bytes": row["payload_bytes"],
                    "dictionary_payload_bytes": len(payload),
                    "payload_saving_bytes": row["payload_bytes"] - len(payload),
                }
        recompress_s = time.perf_counter() - recompress_started

        allowed, locality = _locality_filter(meta, records, set(compressed), len(dictionary))
        payload_saving = sum(compressed[record_id]["payload_saving_bytes"] for record_id in allowed)
        dictionary_storage = PH.size + len(dictionary) + DICT_METADATA_CHARGE
        net = payload_saving - dictionary_storage
        results.append({
            "requested_dictionary_kib": kib,
            "available": True,
            "dictionary_bytes": len(dictionary),
            "dictionary_storage_charge_bytes": dictionary_storage,
            "training_samples": len(samples),
            "training_sample_bytes": sum(map(len, samples)),
            "train_s": train_s,
            "recompress_verify_s": recompress_s,
            "profitable_records_before_locality": len(compressed),
            "locality_admissible_profitable_records": len(allowed),
            "payload_saving_bytes": payload_saving,
            "net_saving_bytes": net,
            "baseline_direct_payload_bytes": baseline_direct_payload,
            "locality": locality,
            "top_record_savings": sorted(
                ({"record_id": record_id, **compressed[record_id]} for record_id in allowed),
                key=lambda row: (-row["payload_saving_bytes"], row["record_id"]),
            )[:20],
        })

    available = [row for row in results if row.get("available")]
    best = max(available, key=lambda row: (row["net_saving_bytes"], -row["dictionary_bytes"]), default=None)
    gate = bool(
        best
        and best["net_saving_bytes"] >= MIN_NET_SAVING
        and best["locality_admissible_profitable_records"] >= MIN_IMPROVED_RECORDS
        and best["locality"]["weighted_direct_pack_read_amp"] <= MAX_READ_AMP
        and best["locality"]["max_dependent_node_read_amp"] <= MAX_READ_AMP
        and best["locality"]["max_additional_dictionary_read_amp"] <= MAX_ADDITIONAL_DICT_AMP
    )
    return {
        "schema": "cmpct-v029-shared-dictionary-context-oracle-v1",
        "claim_boundary": "detached size/locality ceiling only; output archive remains exact attempt-5 bytes",
        "source_archive": {
            "bytes": archive.stat().st_size,
            "selected": built.get("selected"),
            "records": len(records),
            "direct_records": len(direct_ids),
            "dictionary_candidate_records": len(candidate_pool),
            "direct_candidate_payload_bytes": baseline_direct_payload,
        },
        "policy": {
            "dictionary_sizes_kib": list(DICT_SIZES),
            "dictionary_metadata_charge_bytes": DICT_METADATA_CHARGE,
            "max_read_amplification": MAX_READ_AMP,
            "max_additional_dictionary_read_amplification": MAX_ADDITIONAL_DICT_AMP,
            "min_net_saving_bytes": MIN_NET_SAVING,
            "min_improved_records": MIN_IMPROVED_RECORDS,
            "dictionary_storage_counted": True,
            "dictionary_roundtrip_verified_per_record": True,
        },
        "best": best,
        "research_gate_pass": gate,
        "results": results,
        "oracle_wall_s": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="CMPCT detached shared-dictionary record-context oracle")
    parser.add_argument("source", type=Path)
    parser.add_argument("--work-root", type=Path, default=Path("CMPCT_V029_Shared_Dictionary_Oracle"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = measure(args.source, args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"best": result["best"], "research_gate_pass": result["research_gate_pass"]}, indent=2))


if __name__ == "__main__":
    main()
