from __future__ import annotations

"""Failure-localization harness for the v0.30 R4 cold sparse-anchor reader.

Mission Lock / Referee
======================
Observed fact: exact-head CI run 34680783568 reached the cold-reader execution step and failed after
checkout, dependency installation and compilation succeeded. The prototype produced no durable JSON,
so the failure cannot yet be classified as byte-exactness, locality, recursion/resource explosion or
an ordinary implementation exception.

Hypothesis: the failure is deterministic on the frozen Analytics source and can be localized to a
specific request while leaving the candidate reader, metadata representation, request set and all
scientific thresholds unchanged.

Disproof: if this harness cannot reproduce the failure, record that fact; do not infer that the reader
passes. If it does reproduce, persist the first failing request, exception, reader counters and the
last successful request. A green workflow for this file means only that the diagnostic receipt was
successfully captured, never that the sparse-anchor hypothesis passed.

Hostile-review constraints
==========================
- Import and execute the existing candidate implementation verbatim; do not monkey-patch it.
- Use the same deterministic corpus construction and same fixed request sequence.
- Do not alter PAGE, LIMIT, anchor spacing, codec, metadata framing or recursion ceiling.
- Validate every successful read against the independently inflated expected bytes.
- Persist a receipt even when setup or a request raises, so negative evidence cannot disappear with
  the process exit status.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import traceback
import zipfile
import zlib

from benchmarks import v030_r4_deflate_sparse_anchor_cold_reader as COLD

SCHEMA = "cmpct-v030-r4-sparse-anchor-failure-diagnostic-v1"


def _setup(work: Path):
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    neutral = COLD.V029._load(
        COLD.V029.ROOT / "benchmarks" / "neutral_hostile_corpus_v1.py",
        "r4_sparsecold_failure_diag_neutral",
    )
    repair = COLD.V029._load(COLD.V029.REPAIR_PATH, "r4_sparsecold_failure_diag_repair")
    repair.install_generation_hooks(neutral)
    corpus = work / "neutral"
    neutral.build(corpus)
    repair.normalize_root(corpus)
    source = corpus / "04_analytics_and_database"
    rel = COLD.DUAL._npz_relation(source)["accepted"]
    npz = source.joinpath(*Path(rel["npz_path"]).parts)
    info, comp, expected, method = COLD.CONE._raw_zip_member(npz, rel["member"])
    if method != zipfile.ZIP_DEFLATED:
        raise RuntimeError("expected DEFLATE")
    parsed = COLD.DEP.parse_tokens(comp)
    inflated = zlib.decompress(comp, -15)
    if inflated != expected or parsed["output_bytes"] != len(expected):
        raise RuntimeError("builder parse mismatch")
    anchors, blocks, metadata_stored = COLD._build_metadata(parsed)
    return rel, info, comp, expected, anchors, blocks, metadata_stored


def diagnose(work: Path) -> dict:
    t0 = time.perf_counter()
    base = {
        "schema": SCHEMA,
        "source_commit": os.environ.get("EVIDENCE_HEAD"),
        "candidate_module": "benchmarks.v030_r4_deflate_sparse_anchor_cold_reader",
        "candidate_schema": COLD.SCHEMA,
        "contract": {
            "reader_modified": False,
            "request_set_modified": False,
            "thresholds_modified": False,
            "diagnostic_only": True,
            "release_credit": False,
        },
    }
    try:
        rel, info, comp, expected, anchors, blocks, metadata_stored = _setup(work)
    except Exception as exc:  # persist setup failures instead of losing the receipt
        base.update(
            {
                "diagnostic_completed": True,
                "reproduced_candidate_failure": False,
                "setup_failure": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "traceback_tail": traceback.format_exc().splitlines()[-12:],
                },
                "elapsed_wall_s": time.perf_counter() - t0,
            }
        )
        return base

    reqs = COLD.TOKEN.starts(len(expected))
    last_success = None
    first_failure = None
    exact_mismatches = 0
    locality_excesses = 0
    max_combined = 0
    max_symbols = 0
    max_calls = 0
    max_depth = 0

    for index, start in enumerate(reqs):
        end = min(start + COLD.PAGE, len(expected))
        reader = COLD.ColdReader(comp, anchors, blocks, len(expected))
        req_t0 = time.perf_counter()
        try:
            got = reader.read(start, end)
            exact = got == expected[start:end]
            meta = reader.metadata_bytes()
            payload = reader.payload_bytes()
            combined = meta + payload
            row = {
                "index": index,
                "start": start,
                "end": end,
                "request_bytes": end - start,
                "exact": exact,
                "metadata_bytes_touched": meta,
                "payload_bytes_touched": payload,
                "combined_bytes_touched": combined,
                "combined_amplification": combined / max(1, end - start),
                "anchor_frames": len(reader.anchor_frames),
                "block_frames": len(reader.block_frames),
                "symbols_decoded": reader.symbols_decoded,
                "recursive_calls": reader.recursive_calls,
                "max_recursion_depth": reader.max_depth,
                "wall_s": time.perf_counter() - req_t0,
            }
            if not exact:
                exact_mismatches += 1
                first_failure = {
                    "kind": "byte_mismatch",
                    "request": row,
                    "expected_sha256": hashlib.sha256(expected[start:end]).hexdigest(),
                    "actual_sha256": hashlib.sha256(got).hexdigest(),
                }
                break
            if combined > COLD.LIMIT:
                locality_excesses += 1
            last_success = row
            max_combined = max(max_combined, combined)
            max_symbols = max(max_symbols, reader.symbols_decoded)
            max_calls = max(max_calls, reader.recursive_calls)
            max_depth = max(max_depth, reader.max_depth)
        except Exception as exc:
            # The reader itself is unchanged; capture its state at the throw site.
            first_failure = {
                "kind": "exception",
                "index": index,
                "start": start,
                "end": end,
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback_tail": traceback.format_exc().splitlines()[-16:],
                "reader_state": {
                    "metadata_bytes_touched": reader.metadata_bytes(),
                    "payload_bytes_touched": reader.payload_bytes(),
                    "anchor_frames": len(reader.anchor_frames),
                    "block_frames": len(reader.block_frames),
                    "symbols_decoded": reader.symbols_decoded,
                    "recursive_calls": reader.recursive_calls,
                    "max_recursion_depth": reader.max_depth,
                    "page_cache_entries": len(reader.page_cache),
                    "wall_s": time.perf_counter() - req_t0,
                },
            }
            break

    candidate_bytes = COLD.DUAL_OWNER_BYTES + metadata_stored
    base.update(
        {
            "diagnostic_completed": True,
            "reproduced_candidate_failure": first_failure is not None,
            "member": {
                "path": rel["npz_path"],
                "name": rel["member"],
                "compressed_bytes": len(comp),
                "raw_bytes": len(expected),
                "compressed_sha256": hashlib.sha256(comp).hexdigest(),
                "raw_sha256": hashlib.sha256(expected).hexdigest(),
                "crc32": info.CRC,
            },
            "metadata": {
                "anchors": len(anchors),
                "block_states": len(blocks),
                "stored_bytes_including_frame_auth_and_directory": metadata_stored,
                "dual_owner_plus_metadata_bytes": candidate_bytes,
                "margin_to_v029_bytes": COLD.DUAL.ACCEPTED_V029_ANALYTICS - candidate_bytes,
            },
            "requests": {
                "planned": len(reqs),
                "completed_exact_before_failure": 0 if last_success is None else last_success["index"] + 1,
                "exact_mismatches": exact_mismatches,
                "locality_excesses_before_failure": locality_excesses,
                "max_combined_bytes_before_failure": max_combined,
                "max_symbols_before_failure": max_symbols,
                "max_recursive_calls_before_failure": max_calls,
                "max_recursion_depth_before_failure": max_depth,
                "last_success": last_success,
                "first_failure": first_failure,
            },
            "elapsed_wall_s": time.perf_counter() - t0,
            "interpretation": (
                "Failure localized without changing candidate semantics; use the recorded throw site to choose the next causal repair."
                if first_failure is not None
                else "Original CI failure did not reproduce; this is not evidence that the candidate passes the full gate."
            ),
        }
    )
    return base


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-sparsecold-diag-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-sparsecold-diag.json"))
    a = p.parse_args()
    result = diagnose(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
