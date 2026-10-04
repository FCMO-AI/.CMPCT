from __future__ import annotations

"""Strict recovery ZIP-factor frontier with the recovery envelope itself verified by native FFI.

This is the productization follow-up to the proven byte-slice V3 FFI win. It preserves the exact CMP25Z4 bytes and
exact fused builder, but moves recovery-control parsing and V3 reconstruction into the native verifier rather than
performing that work in Python and copying the reconstructed V3 slice across the ABI. Rust compilation/library load
remain outside timing. The recovery archive read, byte-slice ABI call, recovery fallback logic, V3 authentication,
logical identity, locality and decode-unit verification remain inside the timed CMPCT boundary. No release credit.
"""

import argparse
import ctypes
import json
from pathlib import Path

from benchmarks import v030_zipfactor_recovery_native_ffi_frontier as BASE


class RecoveryEnvelopeNativeVerifier:
    def __init__(self, library: Path) -> None:
        self._lib = ctypes.CDLL(str(library))
        self._verify = self._lib.cmpct_zipfactor_v4_recovery_verify_bytes
        self._verify.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_size_t]
        self._verify.restype = ctypes.c_int

    def verify_bytes(self, raw: bytes) -> None:
        if raw:
            buf = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
            ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte))
        else:
            buf = None
            ptr = ctypes.POINTER(ctypes.c_ubyte)()
        rc = int(self._verify(ptr, len(raw)))
        if rc != 0:
            raise RuntimeError(f"in-memory recovery-envelope verification failed rc={rc}")

    def accepts_bytes(self, raw: bytes) -> bool:
        try:
            self.verify_bytes(raw)
        except RuntimeError:
            return False
        return True


def _native_recovery_verify(path: Path, verifier: RecoveryEnvelopeNativeVerifier, _scratch: Path) -> str:
    verifier.verify_bytes(path.read_bytes())
    # Timed rounds use a clean archive. Recovery-source behavior is ratcheted separately below with damaged controls.
    return "primary"


def run(work_root: Path, native_library: Path) -> dict:
    original_verifier = BASE.NativeVerifier
    original_verify = BASE._native_recovery_verify
    BASE.NativeVerifier = RecoveryEnvelopeNativeVerifier
    BASE._native_recovery_verify = _native_recovery_verify
    try:
        result = BASE.run(work_root, native_library)
    finally:
        BASE.NativeVerifier = original_verifier
        BASE._native_recovery_verify = original_verify

    # Prove the native recovery envelope itself preserves failover semantics instead of only accepting clean bytes.
    verifier = RecoveryEnvelopeNativeVerifier(native_library)
    from benchmarks import resemblance_hostile_corpus_v1 as CORPUS
    from benchmarks import v030_external_competitors as EXT
    from benchmarks import v030_zipfactor_recovery_oracle as REC
    import shutil

    hostile_root = work_root / "native-envelope-semantics"
    shutil.rmtree(hostile_root, ignore_errors=True)
    hostile_root.mkdir(parents=True)
    corpus = hostile_root / "corpus"
    CORPUS.build(corpus)
    stage = EXT._normalized_stage(corpus / "04_deflate_family", hostile_root / "normalized")
    clean_path = hostile_root / "clean.cmpct"
    stats = BASE._build_recovery_direct(stage, clean_path, level=BASE.LEVEL, group_size=BASE.GROUP_SIZE)
    clean = clean_path.read_bytes()
    control_len = int(stats["control_bytes"])
    _, tail_start = REC._tail_control(clean)
    primary_bad = REC._flip(clean, 8 + min(7, control_len - 1))
    tail_index = tail_start + min(7, control_len - 1)
    tail_bad = REC._flip(clean, tail_index)
    both_bad = REC._flip(primary_bad, tail_index)

    envelope_semantics = {
        "clean_accepted": verifier.accepts_bytes(clean),
        "primary_bad_recovers_from_tail": verifier.accepts_bytes(primary_bad),
        "tail_bad_uses_primary": verifier.accepts_bytes(tail_bad),
        "both_bad_rejected": not verifier.accepts_bytes(both_bad),
        "malformed_rejected": not verifier.accepts_bytes(b"CMP25Z4\0" + b"\0" * 96),
    }
    if not all(envelope_semantics.values()):
        raise RuntimeError(f"native recovery-envelope semantics failed: {envelope_semantics}")

    result["schema"] = "cmpct-v030-zipfactor-recovery-envelope-ffi-frontier-v1"
    result["contract"].update(
        {
            "cmpct_timing": "direct-fused-recovery-build-plus-inmemory-native-recovery-envelope-strong-verify",
            "scratch_v3_publication_inside_timing": False,
            "native_archive_open_inside_timing": False,
            "native_recovery_control_parse_inside_timing": True,
            "native_v3_reconstruction_inside_timing": True,
            "python_v3_reconstruction_inside_timing": False,
            "native_byte_slice_ffi": True,
            "ffi_reuses_exact_v3_preparity_semantics": True,
            "archive_bytes_changed": False,
            "selector_change": False,
            "release_credit": False,
        }
    )
    result["native_envelope_semantics"] = envelope_semantics
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
        raise SystemExit("ZIP-factor recovery-envelope FFI frontier invalid")


if __name__ == "__main__":
    main()
