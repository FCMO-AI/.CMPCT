from __future__ import annotations

"""R4 Shifted CDC residual-relation oracle.

Exact CDC ownership and bounded packed CDC have representation floors far above solid Zstd-19. This family changes
what is stored: a unique content-defined chunk may be represented as a bounded XOR residual against a previously
authenticated unique chunk, rather than owning its raw bytes. Basis selection is generic and content-derived: among
a bounded recent window, compare a fixed set of byte samples and choose the best compatible predecessor. Chains are
strictly depth-bounded, so selective reconstruction and decoded context remain measurable and fail closed.

Research only. Candidate creation includes boundary scanning, source IO, hashing/dedup, basis search, residual
construction, compression, metadata/framing and publication. Native helper compilation is product-tool setup and is
outside the timed region. No workload name/hash/path affects selection.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import time

import msgpack
import zstandard as zstd

from benchmarks import resemblance_hostile_corpus_v1 as HOSTILE
from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_generalization as GENERAL
from experiments import entropygraph_v030_authoritative as CMPCT

MAGIC = b"C30CDR1\0"
HEADER = struct.Struct("<8sQ32s")
MIN_CHUNK = 16 * 1024
MAX_CHUNK = 256 * 1024
SAMPLE_POINTS = 64
MAX_DEPTH = 4
WORKERS = 4
# mean CDC bytes, recent-basis window, zstd level
ARMS = ((64 * 1024, 16, 1), (64 * 1024, 64, 1), (64 * 1024, 64, 3), (128 * 1024, 64, 1))


def _helper() -> Path:
    raw = os.environ.get("CMPCT_CDC_HELPER")
    if not raw:
        raise RuntimeError("CMPCT_CDC_HELPER must point to the prebuilt boundary scanner")
    p = Path(raw)
    if not p.is_file():
        raise RuntimeError("CDC helper unavailable")
    return p


def _boundaries(path: Path, average: int) -> list[int]:
    if average <= 0 or average & (average - 1):
        raise RuntimeError("CDC average must be a power of two")
    raw = subprocess.check_output([str(_helper()), str(path), str(MIN_CHUNK), str(average - 1), str(MAX_CHUNK)])
    if len(raw) % 8:
        raise RuntimeError("malformed CDC boundary stream")
    ends = [struct.unpack_from("<Q", raw, off)[0] for off in range(0, len(raw), 8)]
    size = path.stat().st_size
    if size == 0:
        if ends:
            raise RuntimeError("empty source emitted boundaries")
        return []
    starts = [0, *ends[:-1]]
    if not ends or ends[-1] != size or any(a >= b for a, b in zip(starts, ends, strict=True)):
        raise RuntimeError("invalid CDC boundaries")
    if any(b - a > MAX_CHUNK for a, b in zip(starts, ends, strict=True)):
        raise RuntimeError("CDC chunk exceeds bound")
    return ends


def _compress(raw: bytes, level: int) -> bytes:
    return zstd.ZstdCompressor(level=level, threads=0).compress(raw)


def _sample_distance(a: bytes, b: bytes) -> int:
    # Cheap deterministic proxy. Length mismatch is priced heavily; payload bytes decide the rest.
    if not a or not b:
        return abs(len(a) - len(b)) * 8
    n = max(len(a), len(b))
    distance = abs(len(a) - len(b)) * 8
    points = min(SAMPLE_POINTS, min(len(a), len(b)))
    for i in range(points):
        ia = (i * (len(a) - 1)) // max(1, points - 1)
        ib = (i * (len(b) - 1)) // max(1, points - 1)
        distance += (a[ia] ^ b[ib]).bit_count()
    return distance


def _xor_delta(target: bytes, base: bytes) -> bytes:
    # Prefix XOR plus literal target tail; target length is authenticated in the chunk row.
    common = min(len(target), len(base))
    return bytes(x ^ y for x, y in zip(target[:common], base[:common], strict=True)) + target[common:]


def _restore_delta(delta: bytes, base: bytes, target_len: int) -> bytes:
    common = min(target_len, len(base))
    if len(delta) != target_len:
        raise RuntimeError("residual length mismatch")
    return bytes(x ^ y for x, y in zip(delta[:common], base[:common], strict=True)) + delta[common:]


def build(root: Path, artifact: Path, *, average: int, window: int, level: int) -> dict:
    started = time.perf_counter()
    files = sorted(p for p in root.rglob("*") if p.is_file())
    if not files or any(p.is_symlink() for p in files):
        raise RuntimeError("residual oracle requires regular files")

    unique_raw: list[bytes] = []
    digest_to_ids: dict[bytes, list[int]] = {}
    file_rows: list[list] = []
    logical_bytes = 0
    duplicate_refs = 0
    for path in files:
        data = path.read_bytes(); logical_bytes += len(data)
        ends = _boundaries(path, average); starts = [0, *ends[:-1]]
        ids = []
        for start, end in zip(starts, ends, strict=True):
            chunk = data[start:end]; digest = hashlib.sha256(chunk).digest(); found = None
            for cid in digest_to_ids.get(digest, []):
                if unique_raw[cid] == chunk:
                    found = cid; break
            if found is None:
                found = len(unique_raw); unique_raw.append(chunk); digest_to_ids.setdefault(digest, []).append(found)
            else:
                duplicate_refs += 1
            ids.append(found)
        rel = path.relative_to(root).as_posix()
        file_rows.append([rel, len(data), hashlib.sha256(data).digest(), ids])

    # Decide a generic bounded predecessor for each unique chunk. Only candidates that keep chain depth <= MAX_DEPTH.
    depths = [0] * len(unique_raw)
    bases: list[int | None] = [None] * len(unique_raw)
    for cid, raw in enumerate(unique_raw):
        lo = max(0, cid - window)
        candidates = [bid for bid in range(lo, cid) if depths[bid] < MAX_DEPTH and abs(len(unique_raw[bid]) - len(raw)) <= 4096]
        if candidates:
            base = min(candidates, key=lambda bid: (_sample_distance(raw, unique_raw[bid]), cid - bid, bid))
            bases[cid] = base
            depths[cid] = depths[base] + 1

    def encode(cid: int) -> tuple[bytes, bytes | None]:
        raw = unique_raw[cid]
        direct = _compress(raw, level)
        base = bases[cid]
        if base is None:
            return direct, None
        delta = _xor_delta(raw, unique_raw[base])
        residual = _compress(delta, level)
        # Residual must pay its base-id field; require an actual byte win before using it.
        if len(residual) + 4 < len(direct):
            return residual, delta
        return direct, None

    with ThreadPoolExecutor(max_workers=min(WORKERS, max(1, len(unique_raw))), thread_name_prefix="cmpct-cdc-residual") as pool:
        encoded = list(pool.map(encode, range(len(unique_raw))))

    chunk_rows = []
    effective_bases: list[int | None] = []
    effective_depths = [0] * len(unique_raw)
    payload_bytes = 0
    residual_count = 0
    for cid, ((blob, delta), raw) in enumerate(zip(encoded, unique_raw, strict=True)):
        base = bases[cid] if delta is not None else None
        if base is not None:
            effective_depths[cid] = effective_depths[base] + 1
            if effective_depths[cid] > MAX_DEPTH:
                raise RuntimeError("effective residual depth exceeded bound")
            residual_count += 1
        effective_bases.append(base)
        chunk_rows.append([len(raw), hashlib.sha256(raw).digest(), -1 if base is None else base, blob])
        payload_bytes += len(blob)

    meta = msgpack.packb(["cmpct-cdc-residual-v1", MIN_CHUNK, average, MAX_CHUNK, window, level, MAX_DEPTH, file_rows, chunk_rows], use_bin_type=True)
    artifact.write_bytes(HEADER.pack(MAGIC, len(meta), hashlib.sha256(meta).digest()) + meta)
    create_s = time.perf_counter() - started

    # Conservative member decoded context: each referenced chunk plus all unique ancestors required for it.
    max_amp = 0.0
    max_decode = 0
    for _rel, fsize, _sha, ids in file_rows:
        touched: set[int] = set()
        for cid in ids:
            cur = int(cid)
            while cur not in touched:
                touched.add(cur)
                base = effective_bases[cur]
                if base is None:
                    break
                cur = base
        decoded = sum(len(unique_raw[cid]) for cid in touched)
        max_amp = max(max_amp, decoded / max(1, int(fsize)))
        max_decode = max(max_decode, max((sum(len(unique_raw[x]) for x in _chain(cid, effective_bases)) for cid in ids), default=0))

    return {
        "archive_bytes": artifact.stat().st_size,
        "create_s": create_s,
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "average_chunk_bytes": average,
        "basis_window": window,
        "level": level,
        "files": len(file_rows),
        "logical_bytes": logical_bytes,
        "unique_chunks": len(unique_raw),
        "duplicate_chunk_refs": duplicate_refs,
        "residual_chunks": residual_count,
        "direct_chunks": len(unique_raw) - residual_count,
        "payload_bytes": payload_bytes,
        "max_chain_depth": max(effective_depths, default=0),
        "max_decode_unit_bytes": max_decode,
        "max_member_read_amplification": max_amp,
    }


def _chain(cid: int, bases: list[int | None]) -> list[int]:
    out = []
    cur: int | None = int(cid)
    while cur is not None:
        if cur in out:
            raise RuntimeError("residual cycle")
        out.append(cur); cur = bases[cur]
    return out


def extract(artifact: Path, output: Path) -> None:
    raw = artifact.read_bytes()
    if len(raw) < HEADER.size:
        raise RuntimeError("short residual artifact")
    magic, size, digest = HEADER.unpack(raw[:HEADER.size]); body = raw[HEADER.size:]
    if magic != MAGIC or len(body) != int(size) or hashlib.sha256(body).digest() != digest:
        raise RuntimeError("residual artifact identity mismatch")
    row = msgpack.unpackb(body, raw=False, strict_map_key=False)
    if not isinstance(row, list) or len(row) != 9 or row[0] != "cmpct-cdc-residual-v1":
        raise RuntimeError("bad residual grammar")
    _, min_chunk, average, max_chunk, window, level, max_depth, files, chunks = row
    if int(min_chunk) != MIN_CHUNK or int(max_chunk) != MAX_CHUNK or int(max_depth) != MAX_DEPTH or int(window) <= 0 or int(level) <= 0 or int(average) <= 0:
        raise RuntimeError("bad residual profile")

    decoded: list[bytes] = []
    depths: list[int] = []
    dctx = zstd.ZstdDecompressor()
    for cid, chunk in enumerate(chunks):
        if not isinstance(chunk, list) or len(chunk) != 4:
            raise RuntimeError("bad residual chunk row")
        usize, sha, base, blob = chunk; usize = int(usize); base = int(base)
        if usize <= 0 or usize > MAX_CHUNK or not isinstance(sha, bytes) or len(sha) != 32 or not isinstance(blob, bytes):
            raise RuntimeError("bad residual chunk fields")
        coded = dctx.decompress(blob, max_output_size=usize)
        if len(coded) != usize:
            raise RuntimeError("bad residual coded length")
        if base == -1:
            value = coded; depth = 0
        else:
            if base < 0 or base >= cid:
                raise RuntimeError("unsafe residual basis")
            depth = depths[base] + 1
            if depth > MAX_DEPTH:
                raise RuntimeError("residual chain too deep")
            value = _restore_delta(coded, decoded[base], usize)
        if hashlib.sha256(value).digest() != sha:
            raise RuntimeError("residual chunk integrity mismatch")
        decoded.append(value); depths.append(depth)

    output.mkdir(parents=True, exist_ok=True); seen: set[str] = set()
    for f in files:
        if not isinstance(f, list) or len(f) != 4:
            raise RuntimeError("bad residual file row")
        rel, size, sha, ids = f
        if not isinstance(rel, str) or not rel or rel.startswith("/") or ".." in Path(rel).parts or rel in seen:
            raise RuntimeError("unsafe residual path")
        try:
            value = b"".join(decoded[int(cid)] for cid in ids)
        except (IndexError, ValueError, TypeError) as exc:
            raise RuntimeError("bad residual file reference") from exc
        if len(value) != int(size) or not isinstance(sha, bytes) or len(sha) != 32 or hashlib.sha256(value).digest() != sha:
            raise RuntimeError("residual file identity mismatch")
        dst = output.joinpath(*Path(rel).parts); dst.parent.mkdir(parents=True, exist_ok=True); dst.write_bytes(value); seen.add(rel)


def run(work_root: Path) -> dict:
    shutil.rmtree(work_root, ignore_errors=True); work_root.mkdir(parents=True)
    HOSTILE.shifted_versions(work_root); source = work_root / "01_shifted_versions"
    expected_tree = HOSTILE.tree_hash(source)
    accepted = GENERAL._accepted_v029_rows()[("resemblance_hostile_v1", "01_shifted_versions")]
    if expected_tree != accepted["tree_sha256"]:
        raise RuntimeError("Shifted corpus tree drift")
    normalized_parent = work_root / "normalized-parent"; normalized_parent.mkdir()
    stage = EXT._normalized_stage(source, normalized_parent)
    if CMPCT.treehash(stage) != expected_tree:
        raise RuntimeError("normalization changed Shifted tree")
    zip_result = EXT._zip(stage, work_root / "baseline.zip", work_root / "zip-out")
    zstd_work = work_root / "zstd-work"; zstd_work.mkdir()
    zstd_result = EXT._tar_zstd(stage, work_root / "baseline.tar.zst", work_root / "zstd-out", zstd_work)
    if not zstd_result.get("available"):
        raise RuntimeError("solid Zstd-19 unavailable")
    v029 = int(accepted["accepted_v029_bytes"]); zstd_bytes = int(zstd_result["archive_bytes"])

    arms = []
    for average, window, level in ARMS:
        artifact = work_root / f"residual-a{average}-w{window}-l{level}.bin"
        r = build(stage, artifact, average=average, window=window, level=level)
        out = work_root / f"out-a{average}-w{window}-l{level}"; extract(artifact, out)
        tree = CMPCT.treehash(out)
        strict = {
            "beats_v029_size": r["archive_bytes"] < v029,
            "beats_zip_size": r["archive_bytes"] < int(zip_result["archive_bytes"]),
            "beats_zstd19_size": r["archive_bytes"] < zstd_bytes,
            "beats_zip_create": r["create_s"] < float(zip_result["create_s"]),
            "beats_zstd19_create": r["create_s"] < float(zstd_result["create_s"]),
            "locality_le_8x": r["max_member_read_amplification"] <= 8.0,
            "decode_unit_le_8mib": r["max_decode_unit_bytes"] <= 8 * 1024 * 1024,
        }
        strict["seven_way_win"] = all(strict.values())
        arm = {**r, "tree_sha256": tree, "tree_verified": tree == expected_tree, "strict": strict}; arms.append(arm)
        print(json.dumps({"average":average,"window":window,"level":level,"bytes":r["archive_bytes"],"payload":r["payload_bytes"],"create_s":r["create_s"],"residual_chunks":r["residual_chunks"],"max_depth":r["max_chain_depth"],"amp":r["max_member_read_amplification"],"strict":strict}, separators=(",", ":")), flush=True)

    best = min(arms, key=lambda a:(a["archive_bytes"],a["create_s"],a["basis_window"],a["level"]))
    winners = [a for a in arms if a["tree_verified"] and a["strict"]["seven_way_win"]]
    return {
        "schema":"cmpct-v030-shifted-cdc-residual-oracle-v1",
        "source_commit":subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip(),
        "target":"resemblance_hostile_v1/01_shifted_versions",
        "diagnosis":"D4","radicality":"R4","saturation_inherited":["S1","S3","S4"],"rps":99,
        "referee":{"control":"retired packed CDC","hypothesis":"encode bounded relations among unique resynchronizing chunks instead of owning every unique raw chunk","strongest_failure":"cheap predecessor matching may miss nonlocal bases or XOR residuals may not express edit structure","retire_if":"payload floor remains above Zstd-19 or locality fails without a strict size win"},
        "contract":{"benchmark_identity_used_in_representation":False,"bounded_recent_basis_search":True,"max_chain_depth":MAX_DEPTH,"creation_prices_all_candidate_work":True,"research_only":True,"release_credit":False},
        "tree_sha256":expected_tree,"accepted_v029_bytes":v029,"comparators":{"zip_deflate9":zip_result,"tar_zstd19_solid":zstd_result},"arms":arms,
        "summary":{"strict_wins":len(winners),"best_size_bytes":best["archive_bytes"],"best_size_zstd_gap_bytes":best["archive_bytes"]-zstd_bytes,"best_payload_bytes":min(a["payload_bytes"] for a in arms),"best_payload_zstd_gap_bytes":min(a["payload_bytes"] for a in arms)-zstd_bytes,"promotion_signal":bool(winners),"decision_if_strict_win":"PROMOTE_NEXT_PREREQUISITE","decision_if_payload_below_zstd_but_complete_miss":"ITERATE_SAME_FAMILY","decision_if_payload_floor_above_zstd":"RETIRE_FAMILY","release_credit":False}
    }


def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--work-root",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args()
    r=run(a.work_root); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(r,indent=2)+"\n",encoding="utf-8"); print(json.dumps(r["summary"],indent=2),flush=True)


if __name__=="__main__":
    main()
