from __future__ import annotations

"""In-process native verification frontier for the exact ZIP-factor v3 candidate.

This reuses the existing complete-frontier harness and changes only how the exact Rust V3 verifier is invoked:
ctypes calls a research-only C ABI in the already-running Python process. Archive open/read/decompression/identity
and locality work remain inside the timed verifier call; Rust compilation and dynamic-library loading are outside
timing. This isolates process-startup overhead without changing CMP25Z3 bytes or its verifier semantics.
"""

import argparse
import ctypes
import json
from pathlib import Path
import tempfile

from benchmarks import v030_zipfactor_native_complete_frontier as BASE


class NativeVerifier:
    def __init__(self, library: Path) -> None:
        self._lib = ctypes.CDLL(str(library))
        self._verify = self._lib.cmpct_zipfactor_v3_verify_path
        self._verify.argtypes = [ctypes.c_char_p]
        self._verify.restype = ctypes.c_int

    def __call__(self, _unused: Path, archive: Path) -> str:
        rc = int(self._verify(str(archive).encode("utf-8")))
        if rc != 0:
            raise RuntimeError(f"in-process ZIP-factor verification failed rc={rc}")
        return "ok profile=zip-framing-factor-binary-control-v3"

    def rejects(self, archive: Path) -> bool:
        return int(self._verify(str(archive).encode("utf-8"))) != 0


def run(work_root: Path, library: Path) -> dict:
    verifier = NativeVerifier(library)
    original = BASE._native_verify
    BASE._native_verify = verifier
    try:
        result = BASE.run(work_root, library)
    finally:
        BASE._native_verify = original

    # Exercise the ABI's fail-closed boundary independently of the timing corpus. The included Rust verifier is
    # the same implementation whose physical-payload corruption behavior is ratcheted by the preparity lane.
    with tempfile.TemporaryDirectory(prefix="cmpct-zf-ffi-hostile-", dir=work_root) as td:
        malformed = Path(td) / "malformed.cmpct"
        malformed.write_bytes(b"CMP25Z3\0" + b"\0" * 96)
        corruption_rejected = verifier.rejects(malformed)
    if not corruption_rejected:
        raise RuntimeError("in-process ZIP-factor ABI accepted malformed archive")

    result["schema"] = "cmpct-v030-zipfactor-native-ffi-complete-frontier-v1"
    result["contract"].update(
        {
            "cmpct_timing": "exact-v3-build-plus-inprocess-native-strong-verify",
            "native_process_startup_inside_timing": False,
            "native_ffi_call_inside_timing": True,
            "archive_open_inside_timing": True,
            "native_compile_inside_timing": False,
            "native_library_load_inside_timing": False,
            "ffi_reuses_exact_preparity_verifier": True,
        }
    )
    result["ffi_corruption_rejected"] = corruption_rejected
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
        raise SystemExit("ZIP-factor native FFI complete frontier invalid")


if __name__ == "__main__":
    main()
