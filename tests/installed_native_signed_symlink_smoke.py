#!/usr/bin/env python3
"""O3 installed-wheel court: true signed r24 unsafe symlink must fail before writes.

Linux constructs the five signed archives once with the real Builder, then
this verifier runs under the *clean-installed wheel interpreter* on three OS.
This is a hostile Reader proof, not atomic filesystem extraction or a release.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import tempfile

import cmpct
from cmpct.reader import CMPCT

SCHEMA = "cmpct-v031-signed-symlink-crosshost-o2-v1"
OWNER = b"CMPCT-O2-SIGNED-SYMLINK-OWNER\x00" * 8
EXPECTED = {
    "parent_escape": "../outside",
    "absolute_escape": "/absolute/outside",
    "win_root_escape": "\\outside",
    "win_drive_escape": "C:outside",
    "safe_relative": "a-first.bin",
}


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: installed_native_signed_symlink_smoke.py FIXTURE_DIR EXACT_HEAD")
    root = Path(sys.argv[1]).resolve()
    head = sys.argv[2]
    # Running from RUNNER_TEMP is not enough: prove the imported module resides
    # inside the isolated Python environment, never in the checkout/source.
    module = Path(cmpct.__file__).resolve()
    prefix = Path(sys.prefix).resolve()
    if not module.is_relative_to(prefix):
        raise AssertionError(f"expected wheel import under {prefix}, got {module}")
    manifest_file = root / "manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("schema") != SCHEMA or manifest.get("source_commit") != head:
        raise AssertionError("signed fixture schema/source HEAD mismatch")
    if set(manifest["objects"]) != set(EXPECTED):
        raise AssertionError("missing or extra signed fixture")
    required = {"parent_escape", "absolute_escape"}
    if os.name == "nt":
        required |= {"win_root_escape", "win_drive_escape"}
    results = []
    with tempfile.TemporaryDirectory(prefix="cmpct-wheel-o3-") as temp:
        for name, target in EXPECTED.items():
            record = manifest["objects"][name]
            archive = root / record["archive"]
            blob = archive.read_bytes()
            if (
                record["target"] != target
                or record["bytes"] != len(blob)
                or hashlib.sha256(blob).hexdigest() != record["sha256"]
            ):
                raise AssertionError(f"signed corpus substitution: {name}")
            dest = Path(temp) / name
            with CMPCT(archive) as reader:
                if reader.read("a-first.bin") != OWNER:
                    raise AssertionError(f"ordinary owner mismatch: {name}")
                if reader.read("z-link").decode("utf-8", "surrogateescape") != target:
                    raise AssertionError(f"signed target mismatch: {name}")
                if name in required:
                    try:
                        reader.extractall(dest, safe_symlinks=True, metadata=False)
                    except OSError as exc:
                        if "unsafe symlink target" not in str(exc):
                            raise AssertionError(f"unexpected rejection: {name}: {exc}") from exc
                    else:
                        raise AssertionError(f"unsafe signed target accepted: {name}")
                    if (dest / "a-first.bin").exists() or os.path.lexists(dest / "z-link"):
                        raise AssertionError(f"partial member publication: {name}")
                    results.append({"case": name, "result": "prewrite_rejected"})
                elif name == "safe_relative" and os.name != "nt":
                    reader.extractall(dest, safe_symlinks=True, metadata=False)
                    if (dest / "a-first.bin").read_bytes() != OWNER:
                        raise AssertionError("safe owner not restored")
                    if not (dest / "z-link").is_symlink() or os.readlink(dest / "z-link") != target:
                        raise AssertionError("safe symlink not restored")
                    results.append({"case": name, "result": "physical_relative_symlink_restored"})
                else:
                    results.append({"case": name, "result": "logical_identity_verified"})
    if sum(x["result"] == "prewrite_rejected" for x in results) != len(required):
        raise AssertionError("required signed hostile negatives incomplete")
    receipt = {
        "schema": "cmpct-v031-installed-wheel-signed-symlink-o3-v1",
        "source_sha": head,
        "installed_module": str(module),
        "host": platform.platform(),
        "required_prewrite_negatives": len(required),
        "physical_safe_symlink_restored": os.name != "nt",
        "fixture_manifest_sha256": hashlib.sha256(manifest_file.read_bytes()).hexdigest(),
        "results": results,
        "scope": "actual installed wheel; not destination TOCTOU, crash atomicity or release parity",
    }
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
