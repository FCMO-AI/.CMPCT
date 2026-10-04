from __future__ import annotations

"""Complete ZIP-factor V3 frontier using the byte-identical fused builder plus in-process Rust verification.

This composes independently validated, archive-byte-neutral mechanisms on the product-side builder path:
- fused group finalization, which preserves the exact CMP25Z3 bytes;
- the hardened EOCD-indexed ZIP source parser now used by the fused scanner; and
- the research-only Rust FFI verifier, which preserves the exact V3 verification semantics.

The external comparison remains the same rotated ZIP/Deflate-9 and solid Zstd-19 contract. Research-only until
recovery/platform/productization gates are earned on the same candidate.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_zipfactor_native_complete_frontier as BASE
from benchmarks.v030_zipfactor_native_ffi_complete_frontier import NativeVerifier
from experiments import entropygraph_v030_zipfactor_compact_v3 as V3
from experiments import entropygraph_v030_zipfactor_compact_v3_fused_finalize as FUSED


def run(work_root: Path, library: Path) -> dict:
    verifier = NativeVerifier(library)
    original_verify = BASE._native_verify
    original_build = V3.build
    BASE._native_verify = verifier
    V3.build = FUSED.build
    try:
        result = BASE.run(work_root, library)
    finally:
        V3.build = original_build
        BASE._native_verify = original_verify

    result["schema"] = "cmpct-v030-zipfactor-fused-ffi-complete-frontier-v2"
    result["contract"].update(
        {
            "cmpct_timing": "byte-identical-fused-v3-eocd-build-plus-inprocess-native-strong-verify",
            "source_parser": "EOCD-indexed-central-first-v1",
            "source_parser_is_fused_default": True,
            "native_process_startup_inside_timing": False,
            "native_ffi_call_inside_timing": True,
            "archive_open_inside_timing": True,
            "native_compile_inside_timing": False,
            "native_library_load_inside_timing": False,
            "fused_builder_required": True,
            "archive_bytes_changed": False,
            "selector_change": False,
            "release_credit": False,
        }
    )
    result["candidate"]["fused_group_finalize"] = bool(result["candidate"].get("fused_group_finalize"))
    if not result["candidate"]["fused_group_finalize"]:
        raise RuntimeError("complete frontier did not execute fused ZIP-factor builder")

    # The exact archive identity is the already-ratcheted CMP25Z3 level-3/group-7 candidate.
    if result["candidate"]["archive_sha256"] != "75bdc866b4b7b63c8f83f7d9a88c9ff3d712c51b93700033984433819b014e31":
        raise RuntimeError("fused+FFI frontier changed exact ZIP-factor V3 archive bytes")
    if int(result["sizes"]["cmpct"]) != 14033:
        raise RuntimeError("fused+FFI frontier changed exact ZIP-factor V3 archive size")

    # Explicit hostile ABI check remains mandatory on this combined path.
    malformed = work_root / "ffi-malformed.cmpct"
    malformed.write_bytes(b"CMP25Z3\0" + b"\0" * 96)
    corruption_rejected = verifier.rejects(malformed)
    if not corruption_rejected:
        raise RuntimeError("fused+FFI frontier accepted malformed archive")
    result["ffi_corruption_rejected"] = True
    result["release_credit"] = False
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--native-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.work_root, args.native_library)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2), flush=True)
    if not result["experiment_valid"]:
        raise SystemExit("ZIP-factor fused+FFI complete frontier invalid")


if __name__ == "__main__":
    main()
