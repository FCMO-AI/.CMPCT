from __future__ import annotations

"""Test a content-native alternative after fixed 4 KiB dependency framing was falsified.

Why this experiment exists
==========================
The fixed-4KiB frame gate produced a 9,563,995-byte dependency sidecar versus a 1,681,984-byte
Analytics budget. Only five token records crossed page boundaries; the loss therefore came from
breaking descriptor redundancy into 938 tiny compression contexts, not from boundary duplication.
Sweeping page sizes would be threshold tuning after a structural negative.

Mission lock
============
Use the RFC-1951 stream's *existing DEFLATE block boundaries* as the only framing boundary. These are
content/encoder-native semantic units already required to reconstruct Huffman state, not a tuned CMPCT
page size. Serialize every token exactly once inside its owning block, include the exact block/Huffman
state in that block frame, independently zlib-9 compress each frame, and charge 32 bytes of digest plus
16 bytes of directory metadata per frame.

Hypothesis: natural-block framing preserves enough global descriptor redundancy that the complete
sidecar plus the 4,453,188-byte dual owner remains <= the accepted 6,135,172-byte v0.29 Analytics
artifact.

Disproof: any positive byte over v0.29 falsifies this natural-block sidecar as a density-compatible
productization path. A pass is only an economics/layout survival result: a real reader must still show
that dependency traversal touches <=8x total index+payload bytes, reconstructs exact output, verifies
frame authenticity from an archive-authenticated root, and obeys hostile resource bounds. No block
coalescing, block splitting, codec, threshold, or page-size sweep is permitted.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import zipfile
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP

SCHEMA = "cmpct-v030-r4-deflate-block-dependency-index-budget-v1"
DUAL_OWNER_BYTES = 4_453_188
ACCEPTED_V029_ANALYTICS = DUAL.ACCEPTED_V029_ANALYTICS
FRAME_AUTH_BYTES = 32
DIRECTORY_RECORD_BYTES = 16


def serialize_block(block: dict, tokens: list[tuple[int, int, int, int, int, int]]) -> tuple[bytes, dict]:
    out = bytearray(b"DBL1")
    out += DEP.uvarint(block["id"])
    out.append(block["type"])
    out += DEP.uvarint(block["header_bit"])
    out += DEP.uvarint(block["end_bit"] - block["header_bit"])
    out += DEP.uvarint(block["out_start"])
    out += DEP.uvarint(block["out_end"] - block["out_start"])
    if block["type"] == 2:
        llp = DEP.pack_nibbles(block["ll_lengths"])
        ddp = DEP.pack_nibbles(block["dd_lengths"])
        out += DEP.uvarint(len(block["ll_lengths"])) + DEP.uvarint(len(llp)) + llp
        out += DEP.uvarint(len(block["dd_lengths"])) + DEP.uvarint(len(ddp)) + ddp
    out += DEP.uvarint(len(tokens))

    prev_out = block["out_start"]
    prev_bit = block["header_bit"]
    token_bytes = 0
    for start, length, distance, bit0, bit1, bid in tokens:
        if bid != block["id"]:
            raise RuntimeError("token assigned to wrong DEFLATE block")
        before = len(out)
        out += DEP.uvarint(start - prev_out)
        out += DEP.uvarint(length)
        out += DEP.uvarint(distance)
        out += DEP.uvarint(bit0 - prev_bit)
        out += DEP.uvarint(bit1 - bit0)
        prev_out = start + length
        prev_bit = bit0
        token_bytes += len(out) - before
    return bytes(out), {"tokens": len(tokens), "token_descriptor_bytes": token_bytes}


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_depblock_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_depblock_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"
    rel = DUAL._npz_relation(source)["accepted"]
    npz = source.joinpath(*Path(rel["npz_path"]).parts)
    info, comp, expected, method = CONE._raw_zip_member(npz, rel["member"])
    if method != zipfile.ZIP_DEFLATED:
        raise RuntimeError("expected DEFLATE")
    parsed = DEP.parse_tokens(comp)
    actual = zlib.decompress(comp, -15)
    if actual != expected or parsed["output_bytes"] != len(actual):
        raise RuntimeError("token parser mismatch")

    by_block: list[list[tuple[int, int, int, int, int, int]]] = [[] for _ in parsed["blocks"]]
    for token in parsed["tokens"]:
        by_block[token[5]].append(token)

    total_raw = total_compressed = total_token_desc = total_refs = 0
    min_frame = max_frame = None
    frame_hash_accumulator = hashlib.sha256()
    frame_sizes = []
    for block, tokens in zip(parsed["blocks"], by_block, strict=True):
        raw, stats = serialize_block(block, tokens)
        enc = zlib.compress(raw, 9)
        total_raw += len(raw)
        total_compressed += len(enc)
        total_token_desc += stats["token_descriptor_bytes"]
        total_refs += stats["tokens"]
        frame_sizes.append(len(enc))
        min_frame = len(enc) if min_frame is None else min(min_frame, len(enc))
        max_frame = len(enc) if max_frame is None else max(max_frame, len(enc))
        frame_hash_accumulator.update(hashlib.sha256(enc).digest())

    frames = len(parsed["blocks"])
    auth_bytes = frames * FRAME_AUTH_BYTES
    directory_bytes = frames * DIRECTORY_RECORD_BYTES
    sidecar = total_compressed + auth_bytes + directory_bytes
    budget = ACCEPTED_V029_ANALYTICS - DUAL_OWNER_BYTES
    candidate = DUAL_OWNER_BYTES + sidecar
    global_reference = zlib.compress(DEP.serialize_index(parsed)[0], 9)
    survives = candidate <= ACCEPTED_V029_ANALYTICS
    return {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "workload": "04_analytics_and_database",
        "member": {
            "compressed_bytes": len(comp),
            "raw_bytes": len(actual),
            "compressed_sha256": hashlib.sha256(comp).hexdigest(),
            "raw_sha256": hashlib.sha256(actual).hexdigest(),
            "crc32": info.CRC,
        },
        "block_index": {
            "frames": frames,
            "unique_tokens": len(parsed["tokens"]),
            "token_refs": total_refs,
            "total_raw_frame_bytes": total_raw,
            "total_compressed_frame_bytes": total_compressed,
            "total_token_descriptor_bytes": total_token_desc,
            "auth_bytes": auth_bytes,
            "directory_bytes": directory_bytes,
            "stored_sidecar_bytes": sidecar,
            "min_compressed_frame_bytes": min_frame,
            "max_compressed_frame_bytes": max_frame,
            "median_compressed_frame_bytes": sorted(frame_sizes)[len(frame_sizes)//2],
            "frame_digest_accumulator_sha256": frame_hash_accumulator.hexdigest(),
            "whole_sidecar_zlib9_reference_bytes": len(global_reference),
            "addressability_tax_vs_global_zlib9_bytes": sidecar - len(global_reference),
        },
        "economics": {
            "dual_owner_bytes": DUAL_OWNER_BYTES,
            "accepted_v029_analytics_bytes": ACCEPTED_V029_ANALYTICS,
            "auxiliary_budget_bytes": budget,
            "owner_plus_block_sidecar_bytes": candidate,
            "margin_to_v029_bytes": ACCEPTED_V029_ANALYTICS - candidate,
        },
        "hypothesis": {
            "natural_deflate_block_dependency_information_fits_density_budget": survives,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "natural_boundary_only": True,
            "no_block_coalescing_or_splitting": True,
            "no_threshold_sweep": True,
            "no_codec_sweep": True,
            "frame_auth_bytes_charged": FRAME_AUTH_BYTES,
            "directory_record_bytes_charged": DIRECTORY_RECORD_BYTES,
            "important_limitation": "density/layout only; recursive selective reads, authenticated-root proofs, reconstruction CPU and hostile bounds are not yet product evidence",
        },
        "next_if_supported": "build a cold selective reader over block frames and charge directory/auth/index/payload bytes while reconstructing all fixed 4KiB requests exactly",
        "next_if_falsified": "preserve the negative; full per-token dependency persistence is not density-compatible under either fixed-page or natural-block framing, so move to a more compact dependency summary/representation rather than tuning frame size",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-depblock-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-depblock.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"block_index": d["block_index"], "economics": d["economics"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
