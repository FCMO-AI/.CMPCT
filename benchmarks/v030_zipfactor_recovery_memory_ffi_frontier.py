from __future__ import annotations

"""Recovery ZIP-factor frontier using the Rust verifier directly over reconstructed V3 bytes.

The recovery envelope remains byte-identical to the existing CMP25Z4 research candidate. This experiment changes
only verification transport/allocation: the authenticated recovery control reconstructs exact CMP25Z3 bytes in
memory and passes them to the preparity-derived Rust parser/verifier through a research-only C ABI. The generated
FFI verifier preserves the same parser, decompression, SHA-256 identity, locality and decode-unit checks, but streams
each reconstructed logical ZIP directly through SHA-256 instead of materializing a second full ZIP Vec solely to
hash it. Rust compilation/library load remain outside timing; the FFI call remains inside. No release credit.
"""

import argparse
import ctypes
import json
from pathlib import Path

from benchmarks import v030_zipfactor_recovery_native_ffi_frontier as BASE
from benchmarks import v030_zipfactor_recovery_oracle as REC


class MemoryNativeVerifier:
    def __init__(self, library: Path) -> None:
        self._lib = ctypes.CDLL(str(library))
        self._verify_bytes = self._lib.cmpct_zipfactor_v3_verify_bytes
        self._verify_bytes.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
        self._verify_bytes.restype = ctypes.c_int

    def verify_bytes(self, raw: bytes) -> None:
        if raw:
            buf = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
            ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte))
        else:
            buf = None
            ptr = ctypes.POINTER(ctypes.c_ubyte)()
        rc = int(self._verify_bytes(ptr, len(raw)))
        if rc != 0:
            raise RuntimeError(f"in-memory ZIP-factor verification failed rc={rc}")

    def rejects_bytes(self, raw: bytes) -> bool:
        try:
            self.verify_bytes(raw)
        except RuntimeError:
            return True
        return False


def _memory_recovery_verify(path: Path, verifier: MemoryNativeVerifier, _scratch: Path) -> str:
    raw = path.read_bytes()
    errors: list[str] = []
    try:
        primary_len = REC._control_len_from_primary(raw)
        tail_len, tail_start, _ = REC._tail_layout(raw)
        if tail_len != primary_len:
            raise RuntimeError("recovery control length mismatch")
        primary = raw[8 : 8 + primary_len]
        candidate = REC._v3_candidate(raw, primary, 8 + primary_len, tail_start)
        verifier.verify_bytes(candidate)
        return "primary"
    except Exception as exc:
        errors.append(repr(exc))
    try:
        control, tail_start = REC._tail_control(raw)
        candidate = REC._v3_candidate(raw, control, 8 + len(control), tail_start)
        verifier.verify_bytes(candidate)
        return "tail"
    except Exception as exc:
        errors.append(repr(exc))
    raise RuntimeError(f"in-memory native recovery verification failed closed: {errors!r}")


def run(work_root: Path, native_library: Path) -> dict:
    original_verifier = BASE.NativeVerifier
    original_verify = BASE._native_recovery_verify
    BASE.NativeVerifier = MemoryNativeVerifier
    BASE._native_recovery_verify = _memory_recovery_verify
    try:
        result = BASE.run(work_root, native_library)
    finally:
        BASE.NativeVerifier = original_verifier
        BASE._native_recovery_verify = original_verify

    verifier = MemoryNativeVerifier(native_library)
    corruption_rejected = verifier.rejects_bytes(b"CMP25Z3\0" + b"\0" * 96)
    if not corruption_rejected:
        raise RuntimeError("in-memory ZIP-factor ABI accepted malformed bytes")

    result["schema"] = "cmpct-v030-zipfactor-recovery-memory-ffi-frontier-v1"
    result["contract"].update(
        {
            "cmpct_timing": "direct-fused-recovery-build-plus-v3-reconstruction-plus-inmemory-rust-strong-verify",
            "scratch_v3_publication_inside_timing": False,
            "native_archive_open_inside_timing": False,
            "native_byte_slice_ffi": True,
            "ffi_preparity_semantics_preserved": True,
            "ffi_streams_reconstructed_zip_sha256": True,
            "ffi_full_reconstructed_zip_allocation": False,
        }
    )
    result["memory_ffi_corruption_rejected"] = corruption_rejected
    result["release_credit"] = False
    result["contract"]["release_credit"] = False
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
        raise SystemExit("ZIP-factor recovery memory-FFI frontier invalid")


if __name__ == "__main__":
    main()