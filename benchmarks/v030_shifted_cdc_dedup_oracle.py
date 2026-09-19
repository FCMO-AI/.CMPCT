from __future__ import annotations

"""R4 Shifted oracle: content-defined chunks with global exact deduplication.

This is a representation-capacity experiment, not a shipping selector.  It tests
whether a shift-resynchronizing physical layout can recover cross-member reuse
without the quadratic pairwise recompression search required by cluster-owner
tournaments.  Boundaries and admission are content-agnostic and deterministic.
Every unique chunk is compressed exactly once per arm; all construction work is
reported and grants zero product/release credit.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import time

import msgpack
import zstandard as zstd

from benchmarks import v030_external_competitors as EXT
from benchmarks import v030_release_performance as PERF
from benchmarks import v030_prefixgraph_two_anchor_representation_oracle as BASE
from experiments import entropygraph_v030_canonical_final_impl as CANON
from experiments import entropygraph_v030_prefixgraph as PG

TARGET = BASE.TARGET
MAGIC = b"CMPNXCD\0"
TAIL = b"CMPNXCDT"
WINDOW = 64
ROLL_BASE = 257
U64 = (1 << 64) - 1
AVG_ARMS = (16 * 1024, 32 * 1024, 64 * 1024, 128 * 1024)
MAX_DECODE_UNIT = 8 * 1024 * 1024
MAX_LOCALITY = 8.0


def _rolling_chunks(raw: bytes, avg: int) -> list[bytes]:
    """Deterministic rolling-polynomial CDC; state forgets prefix after WINDOW bytes."""
    if not raw:
        return [b""]
    minimum = max(WINDOW, avg // 4)
    maximum = min(MAX_DECODE_UNIT, avg * 4)
    boundary_mask = avg - 1
    if avg & boundary_mask:
        raise ValueError("avg chunk size must be a power of two")
    if len(raw) <= minimum:
        return [raw]

    power = pow(ROLL_BASE, WINDOW, 1 << 64)
    h = 0
    start = 0
    window = bytearray()
    out: list[bytes] = []
    for pos, byte in enumerate(raw):
        x = byte + 1
        if len(window) < WINDOW:
            window.append(byte)
            h = ((h * ROLL_BASE) + x) & U64
        else:
            slot = pos % WINDOW
            old = window[slot] + 1
            window[slot] = byte
            h = ((h * ROLL_BASE) + x - old * power) & U64
        size = pos + 1 - start
        if size >= minimum and ((len(window) == WINDOW and (h & boundary_mask) == 0) or size >= maximum):
            out.append(raw[start:pos + 1])
            start = pos + 1
    if start < len(raw):
        out.append(raw[start:])
    return out


def _arm(avg: int, raws: list[bytes], rels: list[str], expected_tree: str) -> dict:
    started = time.perf_counter()
    chunk_raws: list[bytes] = []
    chunk_index: dict[bytes, int] = {}
    recipes: list[list[int]] = []
    total_chunk_refs = 0
    dedup_ref_bytes = 0

    for raw in raws:
        recipe: list[int] = []
        for chunk in _rolling_chunks(raw, avg):
            digest = hashlib.sha256(chunk).digest()
            cid = chunk_index.get(digest)
            if cid is not None and chunk_raws[cid] != chunk:
                raise RuntimeError("SHA-256 collision in CDC oracle")
            if cid is None:
                cid = len(chunk_raws)
                chunk_index[digest] = cid
                chunk_raws.append(chunk)
            else:
                dedup_ref_bytes += len(chunk)
            recipe.append(cid)
            total_chunk_refs += 1
        recipes.append(recipe)

    compression_started = time.perf_counter()
    compressor = zstd.ZstdCompressor(level=19)
    payloads = [compressor.compress(chunk) for chunk in chunk_raws]
    compression_seconds = time.perf_counter() - compression_started
    payload_bytes = sum(map(len, payloads))
    source_bytes = sum(map(len, raws))
    unique_raw_bytes = sum(map(len, chunk_raws))
    max_chunk_raw = max((len(c) for c in chunk_raws), default=0)

    chunk_rows = [
        [len(raw), len(payload), hashlib.sha256(raw).digest()]
        for raw, payload in zip(chunk_raws, payloads, strict=True)
    ]
    meta = {
        "v": 1,
        "engine": "rolling-cdc-global-dedup-zstd19-v1",
        "avg": avg,
        "window": WINDOW,
        "tree_sha256": expected_tree,
        "files": rels,
        "chunks": chunk_rows,
        "recipes": recipes,
    }
    meta_raw = msgpack.packb(meta, use_bin_type=True)
    if len(meta_raw) > PG.MAX_META_BYTES:
        raise RuntimeError("CDC metadata exceeds bounded metadata ceiling")
    meta_comp = zstd.ZstdCompressor(level=PG.META_LEVEL).compress(meta_raw)
    header = PG.HEADER.pack(MAGIC, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    footer = PG.FOOTER.pack(TAIL, len(meta_comp), len(meta_raw), PG.H(meta_raw))
    blob = header + meta_comp + b"".join(payloads) + meta_comp + footer

    decoded = []
    for raw, payload in zip(chunk_raws, payloads, strict=True):
        candidate = zstd.ZstdDecompressor().decompress(payload, max_output_size=max(1, len(raw)))
        if candidate != raw:
            raise RuntimeError("CDC chunk round-trip mismatch")
        decoded.append(candidate)
    verified_raws = [b"".join(decoded[cid] for cid in recipe) for recipe in recipes]
    if verified_raws != raws or PG._treehash_parts(rels, verified_raws) != expected_tree:
        raise RuntimeError("CDC representation changed logical tree")

    member_decoded = [sum(len(decoded[cid]) for cid in recipe) for recipe in recipes]
    max_amp = max(
        (decoded_bytes / max(1, len(raw)) for decoded_bytes, raw in zip(member_decoded, raws, strict=True)),
        default=1.0,
    )
    if max_chunk_raw > MAX_DECODE_UNIT or max_amp > MAX_LOCALITY:
        raise RuntimeError("CDC oracle violated decode-unit/locality law")

    return {
        "avg_chunk_bytes": avg,
        "min_chunk_bytes": max(WINDOW, avg // 4),
        "max_chunk_bytes": avg * 4,
        "archive_bytes": len(blob),
        "archive_sha256": hashlib.sha256(blob).hexdigest(),
        "payload_bytes": payload_bytes,
        "meta_raw_bytes": len(meta_raw),
        "meta_comp_bytes": len(meta_comp),
        "source_bytes": source_bytes,
        "unique_raw_bytes": unique_raw_bytes,
        "deduplicated_reference_bytes": dedup_ref_bytes,
        "unique_chunks": len(chunk_raws),
        "chunk_references": total_chunk_refs,
        "dedup_ratio_unique_raw_vs_source": unique_raw_bytes / max(source_bytes, 1),
        "compression_input_bytes": unique_raw_bytes,
        "compression_work_amplification_vs_source": unique_raw_bytes / max(source_bytes, 1),
        "zstd19_compression_seconds": compression_seconds,
        "arm_elapsed_s": time.perf_counter() - started,
        "max_chunk_raw_bytes": max_chunk_raw,
        "max_decoded_context_amplification": max_amp,
        "within_decode_unit": max_chunk_raw <= MAX_DECODE_UNIT,
        "within_locality_amplification": max_amp <= MAX_LOCALITY,
        "verified_tree_sha256": PG._treehash_parts(rels, verified_raws),
    }


def run(work_root: Path) -> dict:
    started = time.perf_counter()
    shutil.rmtree(work_root, ignore_errors=True)
    work_root.mkdir(parents=True)
    roots = PERF._build_corpora(work_root / "corpora")
    source = roots[TARGET]

    staged = work_root / "r25-stage"
    CANON._prepare_profile_tree(source, staged)
    files = sorted(path for path in staged.rglob("*") if path.is_file())
    rels = [path.relative_to(staged).as_posix() for path in files]
    raws = [path.read_bytes() for path in files]
    expected_tree = PG._treehash_parts(rels, raws)
    source_bytes = sum(map(len, raws))

    arms = [_arm(avg, raws, rels, expected_tree) for avg in AVG_ARMS]
    best = min(arms, key=lambda row: (row["archive_bytes"], row["avg_chunk_bytes"]))

    shipping = work_root / "shipping-prefixgraph.cmpct"
    PG.build(staged, shipping)

    ext_parent = work_root / "external"
    ext_parent.mkdir()
    normalized = EXT._normalized_stage(source, ext_parent)
    zip_row = EXT._zip(normalized, work_root / "shifted.zip", work_root / "zip-extracted")
    zstd_work = work_root / "zstd-work"
    zstd_work.mkdir()
    zstd_row = EXT._tar_zstd(normalized, work_root / "shifted.tar.zst", work_root / "zstd-extracted", zstd_work)
    source_tree = EXT._tree(normalized)
    EXT._verify_extracted(work_root / "zip-extracted", source_tree, "ZIP")
    if not zstd_row.get("available"):
        raise RuntimeError("Zstd-19 comparator unavailable")
    EXT._verify_extracted(work_root / "zstd-extracted", source_tree, "Zstd-19")

    shipping_bytes = shipping.stat().st_size
    zstd_bytes = int(zstd_row["archive_bytes"])
    zip_bytes = int(zip_row["archive_bytes"])
    best_bytes = int(best["archive_bytes"])
    strict_size_win = best_bytes < zstd_bytes and best_bytes < zip_bytes
    saving_vs_shipping = shipping_bytes - best_bytes
    gap_before = shipping_bytes - zstd_bytes
    if strict_size_win:
        decision = "PROMOTE_NEXT_PREREQUISITE"
    elif gap_before > 0 and saving_vs_shipping > 0 and saving_vs_shipping / gap_before >= 0.25:
        decision = "ITERATE_SAME_FAMILY"
    else:
        decision = "ESCALATE_RADICALITY"

    total_compression_input = sum(int(a["compression_input_bytes"]) for a in arms)
    return {
        "schema": "cmpct-v030-shifted-cdc-dedup-oracle-v1",
        "target": f"{TARGET[0]}/{TARGET[1]}",
        "files": len(raws),
        "source_bytes": source_bytes,
        "tree_sha256": expected_tree,
        "verified_tree_sha256": best["verified_tree_sha256"],
        "arms": arms,
        "best_avg_chunk_bytes": best["avg_chunk_bytes"],
        "best_archive_bytes": best_bytes,
        "best_archive_sha256": best["archive_sha256"],
        "shipping_prefixgraph_bytes": shipping_bytes,
        "shipping_prefixgraph_sha256": hashlib.sha256(shipping.read_bytes()).hexdigest(),
        "zip_bytes": zip_bytes,
        "zstd19_bytes": zstd_bytes,
        "saving_vs_shipping_prefixgraph_bytes": saving_vs_shipping,
        "margin_vs_zstd19_bytes": zstd_bytes - best_bytes,
        "strict_size_win_vs_zip_and_zstd19": strict_size_win,
        "search_arms": len(arms),
        "total_trial_compression_input_bytes": total_compression_input,
        "search_compression_work_amplification_vs_source": total_compression_input / max(source_bytes, 1),
        "best_single_pass_compression_work_amplification_vs_source": best["compression_work_amplification_vs_source"],
        "max_chunk_raw_bytes": best["max_chunk_raw_bytes"],
        "max_decoded_context_amplification": best["max_decoded_context_amplification"],
        "within_decode_unit": best["within_decode_unit"],
        "within_locality_amplification": best["within_locality_amplification"],
        "oracle_elapsed_s": time.perf_counter() - started,
        "release_credit": False,
        "product_create_time_claim": False,
        "decision": decision,
        "domination_audit": {
            "strict_target": "15/15 strictly smaller and faster than ZIP/Deflate and solid Zstd-19",
            "diagnosis": "D4",
            "radicality": "R4",
            "active_saturation": ["S2", "S3", "S4"],
            "research_priority_score": 96,
            "measured_gap_change_bytes": saving_vs_shipping,
            "strongest_self_critique": "The four-arm sweep is a capacity search, not a shipping policy. Even a strict size win must survive one fixed generic boundary policy and complete creation-time accounting; chunk hashes/recipes may also erase payload reuse on small files.",
            "terminal_decision": decision,
            "next_decisive_test": (
                "freeze one content-agnostic CDC policy, implement canonical bounded reader semantics, and measure complete creation time"
                if strict_size_win
                else "retire global exact-chunk dedup if it fails to close a material fraction of the Shifted Zstd gap; move to delta/referential chunk ownership rather than another chunk-size sweep"
            ),
        },
        "claim_boundary": "R4 representation-capacity oracle only; content-defined boundaries are generic and deterministic, all unique chunk compression is priced, but arm selection grants zero product/release credit.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-shifted-cdc-dedup-work"))
    parser.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-shifted-cdc-dedup.json"))
    args = parser.parse_args()
    result = run(args.work_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
