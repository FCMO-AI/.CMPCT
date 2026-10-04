from __future__ import annotations

"""Price a page-addressable version of the Analytics dependency sidecar.

The global dependency-index budget oracle showed a 22.96 MB raw token sidecar compressing to
1,373,118 B with whole-stream zlib-9, leaving only 308,866 B below accepted v0.29 Analytics. That
compression is not a selective-reader representation: one dependency lookup may require decoding the
whole sidecar.

Mission lock
============
Test the next unavoidable cost without implementing product framing. Partition dependency records by
the fixed 4 KiB decoded pages already used by the locality contract. Every page is independently
zlib-9 compressed, carries the exact token records intersecting that page, and carries the exact
Huffman-state descriptors for blocks referenced by those tokens. Charge a fixed 32-byte SHA-256 per
page and a conservative 16-byte directory record per page. Tokens crossing a page boundary are
intentionally duplicated into each intersected page.

Disproof: if the complete framed sidecar plus the 4,453,188-byte dual owner exceeds the accepted
6,135,172-byte v0.29 Analytics floor, reject this page-framed token-index path. There is no page-size,
codec or threshold sweep. A pass is still only an information/layout gate: dependency traversal,
selective sidecar reads, compressed-payload reads, reconstruction CPU, recovery and hostile-index
bounds remain to be implemented and charged.
"""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import zipfile
import zlib

from benchmarks import mosaic_v029_generalization_bench as V029
from benchmarks import v030_r4_analytics_dual_owner_oracle as DUAL
from benchmarks import v030_r4_deflate_dependency_cone_oracle as CONE
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP

SCHEMA = "cmpct-v030-r4-deflate-dependency-index-framed-budget-v1"
PAGE = 4096
DUAL_OWNER_BYTES = 4_453_188
ACCEPTED_V029_ANALYTICS = DUAL.ACCEPTED_V029_ANALYTICS
FRAME_AUTH_BYTES = 32
DIRECTORY_RECORD_BYTES = 16


def svarint(v: int) -> bytes:
    # Zig-zag to keep the only expected negative values (cross-page token starts) compact.
    return DEP.uvarint((v << 1) ^ (v >> 63))


def block_state_bytes(block: dict) -> bytes:
    out = bytearray()
    out.append(block["type"])
    out += DEP.uvarint(block["id"])
    out += DEP.uvarint(block["header_bit"])
    out += DEP.uvarint(block["end_bit"] - block["header_bit"])
    if block["type"] == 2:
        llp = DEP.pack_nibbles(block["ll_lengths"])
        ddp = DEP.pack_nibbles(block["dd_lengths"])
        out += DEP.uvarint(len(block["ll_lengths"])) + DEP.uvarint(len(llp)) + llp
        out += DEP.uvarint(len(block["dd_lengths"])) + DEP.uvarint(len(ddp)) + ddp
    return bytes(out)


def serialize_page(page: int, local: list[tuple[int, int, int, int, int, int]], blocks: list[dict]) -> tuple[bytes, dict]:
    base = page * PAGE
    bids = sorted({t[5] for t in local})
    out = bytearray(b"DPG1")
    out += DEP.uvarint(page)
    out += DEP.uvarint(len(local))
    out += DEP.uvarint(len(bids))
    state_bytes = 0
    for bid in bids:
        b = block_state_bytes(blocks[bid])
        out += DEP.uvarint(len(b)) + b
        state_bytes += len(b)

    prev_bit = 0
    token_bytes = 0
    for start, length, distance, bit0, bit1, bid in local:
        before = len(out)
        out += svarint(start - base)
        out += DEP.uvarint(length)
        out += DEP.uvarint(distance)
        out += DEP.uvarint(bit0 - prev_bit)
        out += DEP.uvarint(bit1 - bit0)
        out += DEP.uvarint(bid)
        prev_bit = bit0
        token_bytes += len(out) - before
    return bytes(out), {
        "tokens": len(local),
        "blocks": len(bids),
        "block_state_bytes": state_bytes,
        "token_descriptor_bytes": token_bytes,
    }


def group_tokens_by_page(tokens: list[tuple[int, int, int, int, int, int]], pages: int) -> list[list[tuple[int, int, int, int, int, int]]]:
    """One pass over tokens; preserve output order within every page.

    DEFLATE copy tokens are at most 258 output bytes, so a token normally touches one page and at
    most two at a 4 KiB boundary. This avoids an accidental pages*token_count benchmark cost while
    preserving exactly the same serialized representation and boundary-token duplication.
    """
    grouped: list[list[tuple[int, int, int, int, int, int]]] = [[] for _ in range(pages)]
    for token in tokens:
        start, length, *_ = token
        first = start // PAGE
        last = (start + length - 1) // PAGE
        if first < 0 or last >= pages:
            raise RuntimeError("token page outside decoded output")
        for page in range(first, last + 1):
            grouped[page].append(token)
    return grouped


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_depframe_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_depframe_repair")
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

    pages = math.ceil(len(actual) / PAGE)
    page_tokens = group_tokens_by_page(parsed["tokens"], pages)
    total_raw = total_compressed = total_token_desc = total_block_state = total_token_refs = 0
    max_frame = min_frame = None
    frame_hash_accumulator = hashlib.sha256()
    for page, local in enumerate(page_tokens):
        raw, stats = serialize_page(page, local, parsed["blocks"])
        enc = zlib.compress(raw, 9)
        frame_hash_accumulator.update(hashlib.sha256(enc).digest())
        total_raw += len(raw)
        total_compressed += len(enc)
        total_token_desc += stats["token_descriptor_bytes"]
        total_block_state += stats["block_state_bytes"]
        total_token_refs += stats["tokens"]
        max_frame = len(enc) if max_frame is None else max(max_frame, len(enc))
        min_frame = len(enc) if min_frame is None else min(min_frame, len(enc))

    auth_bytes = pages * FRAME_AUTH_BYTES
    directory_bytes = pages * DIRECTORY_RECORD_BYTES
    framed_sidecar = total_compressed + auth_bytes + directory_bytes
    budget = ACCEPTED_V029_ANALYTICS - DUAL_OWNER_BYTES
    candidate = DUAL_OWNER_BYTES + framed_sidecar
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
        "framed_index": {
            "page_bytes": PAGE,
            "pages": pages,
            "unique_tokens": len(parsed["tokens"]),
            "token_refs_after_boundary_duplication": total_token_refs,
            "duplicated_token_refs": total_token_refs - len(parsed["tokens"]),
            "total_raw_frame_bytes": total_raw,
            "total_compressed_frame_bytes": total_compressed,
            "total_token_descriptor_bytes": total_token_desc,
            "total_duplicated_block_state_bytes": total_block_state,
            "auth_bytes": auth_bytes,
            "directory_bytes": directory_bytes,
            "stored_sidecar_bytes": framed_sidecar,
            "min_compressed_frame_bytes": min_frame,
            "max_compressed_frame_bytes": max_frame,
            "frame_digest_accumulator_sha256": frame_hash_accumulator.hexdigest(),
            "whole_sidecar_zlib9_reference_bytes": len(global_reference),
            "addressability_tax_vs_global_zlib9_bytes": framed_sidecar - len(global_reference),
        },
        "economics": {
            "dual_owner_bytes": DUAL_OWNER_BYTES,
            "accepted_v029_analytics_bytes": ACCEPTED_V029_ANALYTICS,
            "auxiliary_budget_bytes": budget,
            "owner_plus_framed_sidecar_bytes": candidate,
            "margin_to_v029_bytes": ACCEPTED_V029_ANALYTICS - candidate,
        },
        "hypothesis": {
            "page_addressable_dependency_information_fits_density_budget": survives,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "no_threshold_sweep": True,
            "no_page_size_sweep": True,
            "no_codec_sweep": True,
            "frame_auth_bytes_charged": FRAME_AUTH_BYTES,
            "directory_record_bytes_charged": DIRECTORY_RECORD_BYTES,
            "important_limitation": "independent page compression is addressable, but this gate does not yet prove that recursive dependency traversal touches <=8x sidecar+payload bytes or reconstructs exact requested output without global state",
        },
        "next_if_supported": "deserialize dependency pages on demand and prove recursive token traversal from serialized frames matches the exact oracle closure; then charge frame I/O + payload I/O + auth under the 8x selective-read ceiling",
        "next_if_falsified": "preserve the negative and reject fixed-4KiB page framing for the token graph; seek a more compact hierarchical dependency representation rather than tuning page size",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-depframe-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-depframe.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"framed_index": d["framed_index"], "economics": d["economics"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
