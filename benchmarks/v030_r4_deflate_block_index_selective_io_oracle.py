from __future__ import annotations

"""Charge natural-block dependency sidecar I/O together with sparse DEFLATE payload I/O.

Mission lock
============
The natural DEFLATE-block sidecar survived the Analytics density budget at 1,441,252 stored bytes,
leaving 240,732 bytes below accepted v0.29. That only prices storage. A selective reader must also read
the dependency metadata needed to discover the sparse LZ77 closure.

This oracle freezes the exact natural-block serialization from
v030_r4_deflate_block_dependency_index_budget.py. For every fixed 4 KiB request used by the prior
token-anchor oracle it:

1. computes the exact decoded dependency closure with the existing diagnostic parent graph;
2. charges the independently-compressed natural-block sidecar frame for every DEFLATE block that
   produces any byte in that closure, including the frozen 32-byte digest and 16-byte directory record;
3. charges the sparse compressed payload ranges from the existing token-anchor physical model; and
4. sums unique sidecar bytes + unique payload bytes against the unchanged 32,768-byte (8x) ceiling.

This intentionally still gifts the in-memory parent graph and therefore is a *lower bound* on a real
reader. It answers one narrow falsifier before implementing traversal: can the full-token block sidecar
even satisfy the physical selective-I/O budget when its own reads are no longer free?

Disproof
========
If any request exceeds 32,768 total sidecar+payload bytes, reject the full-token natural-block sidecar
as the locality solution even though it fits the stored-byte budget. Do not tune frame sizes, page sizes,
codecs or thresholds. If it passes, the next step must deserialize/traverse frames cold, remove the gifted
parent graph, authenticate from an archive-rooted commitment, and test arbitrary unaligned/hostile reads.
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
from benchmarks import v030_r4_deflate_physical_range_oracle as PHYS
from benchmarks import v030_r4_deflate_token_anchor_physical_oracle as TOKEN
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP
from benchmarks import v030_r4_deflate_block_dependency_index_budget as BLOCK

SCHEMA = "cmpct-v030-r4-deflate-block-index-selective-io-oracle-v1"
PAGE = 4096
LIMIT = 8 * PAGE
FRAME_TAX = BLOCK.FRAME_AUTH_BYTES + BLOCK.DIRECTORY_RECORD_BYTES


def parse_for_both(raw: bytes) -> tuple[dict, dict]:
    # Keep the physical byte-parent parser as the authority for closure/payload charging and the compact
    # token parser as the authority for the frozen sidecar serialization. Cross-check their block counts.
    phys = PHYS.parse_physical(raw)
    compact = DEP.parse_tokens(raw)
    if len(phys["blocks"]) != len(compact["blocks"]):
        raise RuntimeError("block parser disagreement")
    return phys, compact


def block_frame_sizes(compact: dict) -> list[int]:
    by_block: list[list[tuple[int, int, int, int, int, int]]] = [[] for _ in compact["blocks"]]
    for token in compact["tokens"]:
        by_block[token[5]].append(token)
    out = []
    for block, tokens in zip(compact["blocks"], by_block, strict=True):
        raw, _ = BLOCK.serialize_block(block, tokens)
        out.append(len(zlib.compress(raw, 9)) + FRAME_TAX)
    return out


def run(work: Path) -> dict:
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = V029._load(V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py", "r4_blockio_neutral")
    repair = V029._load(V029.REPAIR_PATH, "r4_blockio_repair")
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
    phys, compact = parse_for_both(comp)
    actual = zlib.decompress(comp, -15)
    if actual != expected or len(phys["parents"]) != len(actual) or compact["output_bytes"] != len(actual):
        raise RuntimeError("parser/reconstruction mismatch")

    frame_sizes = block_frame_sizes(compact)
    reqs = TOKEN.starts(len(actual))
    worst = None
    total = total_index = total_payload = total_blocks = 0
    failures = 0
    for start in reqs:
        end = min(start + PAGE, len(actual))
        nodes = TOKEN.closure(phys["parents"], start, end)
        payload = TOKEN.charge(phys, nodes, len(actual))
        bids = sorted({int(phys["block_ids"][n]) for n in nodes})
        index_bytes = sum(frame_sizes[bid] for bid in bids)
        combined = index_bytes + payload["compressed_bytes_touched"]
        row = {
            "start": start,
            "end": end,
            "request_bytes": end - start,
            "decoded_closure_bytes": len(nodes),
            "dependency_blocks": len(bids),
            "dependency_block_ids": bids,
            "index_frame_bytes_touched": index_bytes,
            "payload_bytes_touched": payload["compressed_bytes_touched"],
            "payload_ranges": payload["merged_ranges"],
            "combined_bytes_touched": combined,
            "combined_amplification": combined / max(1, end - start),
        }
        total += combined
        total_index += index_bytes
        total_payload += payload["compressed_bytes_touched"]
        total_blocks += len(bids)
        if combined > LIMIT:
            failures += 1
        if worst is None or combined > worst["combined_bytes_touched"]:
            worst = row
    assert worst is not None

    stored_sidecar = sum(frame_sizes)
    stored_candidate = BLOCK.DUAL_OWNER_BYTES + stored_sidecar
    density_margin = BLOCK.ACCEPTED_V029_ANALYTICS - stored_candidate
    passes = failures == 0
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
        "sidecar": {
            "frames": len(frame_sizes),
            "stored_sidecar_bytes": stored_sidecar,
            "min_frame_plus_tax_bytes": min(frame_sizes),
            "max_frame_plus_tax_bytes": max(frame_sizes),
            "median_frame_plus_tax_bytes": sorted(frame_sizes)[len(frame_sizes)//2],
            "owner_plus_sidecar_bytes": stored_candidate,
            "margin_to_v029_bytes": density_margin,
        },
        "selective_io": {
            "request_bytes": PAGE,
            "requests": len(reqs),
            "limit_bytes": LIMIT,
            "failed_requests": failures,
            "mean_dependency_blocks": total_blocks / len(reqs),
            "mean_index_frame_bytes": total_index / len(reqs),
            "mean_payload_bytes": total_payload / len(reqs),
            "mean_combined_bytes": total / len(reqs),
            "mean_combined_amplification": total / len(reqs) / PAGE,
            "worst_combined": worst,
        },
        "hypothesis": {
            "full_token_natural_block_sidecar_survives_8x_index_plus_payload_floor": passes,
        },
        "contract": {
            "diagnostic_only": True,
            "release_credit": False,
            "lower_bound_only": True,
            "parent_graph_is_still_gifted": True,
            "no_threshold_sweep": True,
            "no_page_size_sweep": True,
            "no_codec_sweep": True,
            "frame_auth_and_directory_tax_charged": FRAME_TAX,
            "important_limitation": "the exact parent graph still selects dependency blocks; a passing result would not prove a real cold reader, while a failing result is sufficient to reject this full-token sidecar layout for the 8x locality contract",
        },
        "next_if_supported": "implement cold frame deserialization/traversal with no parent graph and archive-rooted authentication, then test unaligned and hostile requests",
        "next_if_falsified": "preserve the negative and move to sparse token anchors with on-demand local DEFLATE parsing instead of persisting every token dependency",
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-blockio-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-blockio.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"sidecar": d["sidecar"], "selective_io": d["selective_io"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
