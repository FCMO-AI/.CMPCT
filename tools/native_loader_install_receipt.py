#!/usr/bin/env python3
"""Independent installed-package native selector receipt.

This intentionally probes the *current* loaded package, rather than
reconstructing a native selection from a synthetic fixture. It is not a
retrospective attestation of prior benchmark subprocesses.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from cmpct import native_codec


PATTERNS = ("cmpct_core*.so", "cmpct_core*.pyd", "cmpct_core*.dll", "cmpct_core*.dylib")


def main() -> None:
    root = Path(native_codec.__file__).resolve().parent
    matches = sorted(path for pattern in PATTERNS for path in root.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one package-owned native candidate, found {len(matches)}")
    selected = native_codec._library_path()
    if selected != matches[0] or selected.is_symlink() or not selected.is_file():
        raise RuntimeError("loader-selected native object is not the sole direct package binary")
    loaded_name = Path(native_codec._core._name)
    if not loaded_name.samefile(selected):
        raise RuntimeError("ctypes CDLL path differs from selected package binary")

    test_data = bytes(range(256)) * 16
    encoded = native_codec.compress(test_data, 3)
    if native_codec.decompress(encoded, len(test_data)) != test_data:
        raise RuntimeError("installed native codec roundtrip disagrees")

    # Prove the fail-closed path on the *real editable-installed* package, not
    # only on a synthetic copied module. The injected match is inert data, never
    # a second native library; it is removed even when the subprocess fails.
    injected = root / "cmpct_core-EXTRA-owner-control.so"
    if injected.exists() or injected.is_symlink():
        raise RuntimeError("refuse to overwrite an existing native candidate")
    injected.write_bytes(b"not a shared library; selection must refuse before CDLL")
    try:
        hostile = subprocess.run(
            [sys.executable, "-c", "from cmpct import native_codec"],
            capture_output=True, text=True, check=False,
        )
        if hostile.returncode == 0 or "ambiguous package-owned cmpct_core codec libraries" not in hostile.stderr:
            raise RuntimeError(
                "installed package did not fail closed on extra native match: "
                + hostile.stderr[-500:]
            )
    finally:
        injected.unlink()
    if sum(1 for pattern in PATTERNS for _ in root.glob(pattern)) != 1:
        raise RuntimeError("native candidate inventory not restored after hostile test")

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    expected = os.environ.get("EVIDENCE_HEAD")
    if expected and expected != head:
        raise RuntimeError("checked out source differs from advertised PR head")
    result = {
        "source_head": head,
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "candidate_count": 1,
        "candidate_name": selected.name,
        "native_size_bytes": selected.stat().st_size,
        "native_sha256": hashlib.sha256(selected.read_bytes()).hexdigest(),
        "native_roundtrip": "pass",
        "injected_match_preload_refused": True,
        "post_test_candidate_count": 1,
        "compressed_test_bytes": len(encoded),
        "claim_scope": "fresh installed package on this host only",
    }
    Path("native-loader-install-receipt.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
