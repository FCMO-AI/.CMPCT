from __future__ import annotations

"""Density referee for the largest independent Office stream slab implied by the 8x locality law.

Mission Lock
------------
The 4 KiB slab candidate preserves physical locality but gives back most of frozen v0.25's
large-slab density. H-DICT8 showed that an 8 KiB shared dictionary recovers only 14,459 B,
so a small common statistical context is not the missing mechanism.

H-BMAX: if the remaining gap is primarily context *within* independently decodable frames,
then using the largest fixed slab that can still satisfy an arbitrary 4 KiB read spanning at
most two slabs should recover a material fraction of the deficit without a parameter sweep.

The slab size is derived, not tuned. The physical read budget is 8*4096 = 32768 B. Charging
the existing conservative 53-byte authenticated-frame tax for each of two worst-case slabs
leaves floor((32768 - 2*53)/2) = 16331 payload bytes per slab. Zstd level remains 3.

This is density evidence only. Even a density PASS receives no locality or release credit until
a cold reader charges directory/auth proof bytes, actual compressed frames touched, pread/seeks,
corruption/recovery, CPU/RSS and native parity. If density still cannot beat frozen v0.29 Office,
the independent-frame-context hypothesis is falsified and the 8x law must not be moved.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import time

import zstandard as zstd

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_office_page_seed_cold_reader as SEED
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD
from benchmarks import v030_r4_office_sfv4_all_member_skeleton as SFV4
from experiments import entropygraph_v030_release_product as PRODUCT

SCHEMA = "cmpct-v030-r4-office-budget-max-slab-density-v1"
REQUEST_BYTES = 4096
MAX_AMP = 8
READ_BUDGET = REQUEST_BYTES * MAX_AMP
FRAME_TAX = 53
WORST_CASE_SLABS = 2
SLAB_BYTES = (READ_BUDGET - WORST_CASE_SLABS * FRAME_TAX) // WORST_CASE_SLABS
ZSTD_LEVEL = 3

assert SLAB_BYTES == 16331
assert WORST_CASE_SLABS * (SLAB_BYTES + FRAME_TAX) <= READ_BUDGET


def _encode_stream(comp: bytes, enc: zstd.ZstdCompressor, dec: zstd.ZstdDecompressor) -> tuple[int, int, int]:
    stored = slabs = compressed = 0
    for off in range(0, len(comp), SLAB_BYTES):
        raw = comp[off:off + SLAB_BYTES]
        z = enc.compress(raw)
        if len(z) < len(raw):
            if dec.decompress(z, max_output_size=len(raw)) != raw:
                raise RuntimeError("budget-max slab roundtrip failed")
            payload = z
            compressed += 1
        else:
            payload = raw
        stored += len(payload) + FRAME_TAX
        slabs += 1
    return stored, slabs, compressed


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_office_bmax_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_office_bmax_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "02_office_workspace"
    built = SFV4.build_candidate(source, work / "sfv4", work / "sfv4-work")

    enc = zstd.ZstdCompressor(level=ZSTD_LEVEL)
    dec = zstd.ZstdDecompressor()
    raw_stream = wrapped = slabs = compressed_slabs = 0
    c0 = time.process_time(); t0 = time.perf_counter()
    for h in sorted(built["all_streams"]):
        comp = built["all_streams"][h]
        n, ns, nc = _encode_stream(comp, enc, dec)
        raw_stream += len(comp)
        wrapped += n
        slabs += ns
        compressed_slabs += nc
    cpu = time.process_time() - c0
    wall = time.perf_counter() - t0
    if raw_stream != int(built["all_member_stream_bytes"]):
        raise RuntimeError("all-member stream accounting mismatch")

    # Charge the same derived-stream sparse/seed metadata already required by the current
    # selective reconstruction line. This is deliberately conservative and keeps economics
    # directly comparable to the 4 KiB and H-DICT8 referees.
    sparse = seed = logical_seed = 0
    hashes = sorted({rec["stream_hash"] for rec in built["derived_inventory"].values()})
    for h in hashes:
        comp = built["all_streams"][h]
        raw = __import__("zlib").decompress(comp, -15)
        parsed = DEP.parse_tokens(comp)
        anchors, _blocks, sparse_stored = COLD._build_metadata(parsed)
        _seeds, seed_stored, seed_logical = SEED._build_seeds(parsed, anchors, raw)
        sparse += sparse_stored
        seed += seed_stored
        logical_seed += seed_logical

    sfv4 = int(built["stored_bytes"])
    nonstream = sfv4 - raw_stream
    candidate = nonstream + wrapped + sparse + seed
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "02_office_workspace",
        "tree_sha256": PRODUCT.treehash(source),
        "candidate": {
            "request_bytes": REQUEST_BYTES,
            "max_amplification": MAX_AMP,
            "read_budget_bytes": READ_BUDGET,
            "worst_case_slabs": WORST_CASE_SLABS,
            "frame_tax_bytes": FRAME_TAX,
            "slab_bytes": SLAB_BYTES,
            "zstd_level": ZSTD_LEVEL,
            "slabs": slabs,
            "compressed_slabs": compressed_slabs,
            "two_full_slab_upper_bound_bytes": WORST_CASE_SLABS * (SLAB_BYTES + FRAME_TAX),
        },
        "stream_store": {
            "raw_stream_bytes": raw_stream,
            "wrapped_stream_bytes": wrapped,
            "saving_bytes": raw_stream - wrapped,
            "encode_cpu_s": cpu,
            "encode_wall_s": wall,
        },
        "economics": {
            "sfv4_bytes": sfv4,
            "sfv4_nonstream_bytes": nonstream,
            "sparse_metadata_bytes": sparse,
            "seed_metadata_bytes": seed,
            "logical_seed_bytes": logical_seed,
            "candidate_with_locality_metadata_bytes": candidate,
            "accepted_v029_office_bytes": SFV4.ACCEPTED_V029_OFFICE,
            "margin_to_v029_bytes": SFV4.ACCEPTED_V029_OFFICE - candidate,
            "density_feasible": candidate < SFV4.ACCEPTED_V029_OFFICE,
        },
        "hypothesis": {
            "budget_max_independent_frames_recover_product_density": candidate < SFV4.ACCEPTED_V029_OFFICE,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "locality_credit": False,
            "slab_size_derived_from_existing_8x_contract": True,
            "no_parameter_sweep": True,
            "selector_changed": False,
            "production_format_changed": False,
            "all_frame_bytes_charged": True,
            "remaining_debt": "serialized directory/auth proof; actual cold-reader touched-frame accounting; pread/seeks; corruption/recovery; fresh CPU/RSS; native parity",
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-office-bmax-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-office-bmax.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"candidate": d["candidate"], "stream_store": d["stream_store"], "economics": d["economics"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
