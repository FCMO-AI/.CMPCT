"""J24I16: Win32 leaf-only nofollow vs intermediate NTFS junction custody.

Scientific primitive only; may demonstrate a source-root security *design* gap,
not an installed CMPCT Builder exploit. Preregistered before this instrument.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import stat
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

from j24i15_win32_nofollow_handle import RejectedSource, api, win32_read_nofollow

SCHEMA = "j24i16-win32-ancestor-junction-v1"


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def mkjunction(link: Path, target: Path) -> str:
    """NTFS directory junction, not an ordinary file symlink; no admin needed."""
    command = f'mklink /J "{link}" "{target}"'
    proc = subprocess.run(
        ["cmd.exe", "/d", "/c", command],
        capture_output=True, text=True, check=False, timeout=15
    )
    if proc.returncode:
        raise OSError(
            "mklink /J unavailable (infrastructure, NOT a product pass): "
            + repr({"returncode": proc.returncode, "stderr": proc.stderr,
                    "stdout": proc.stdout})
        )
    return proc.stdout.strip()


def result_on_windows() -> dict:
    api()  # Match J24I15b cached ctypes setup, outside the comparisons.
    import cmpct
    checkout = Path(os.environ["CMPCT_J24I16_CHECKOUT"]).resolve()
    installed = Path(cmpct.__file__).resolve()
    if installed == checkout or checkout in installed.parents:
        raise AssertionError("CMPCT was imported from checkout, not installed site-packages")

    with tempfile.TemporaryDirectory(prefix="j24i16-") as tmp:
        sandbox = Path(tmp)
        root = sandbox / "selected-source-root"
        parent = root / "parent"
        parked = root / "parent-parked"
        outside = sandbox / "outside-root"
        root.mkdir()
        parent.mkdir()
        outside.mkdir()
        leaf_name = "payload.bin"
        inner = parent / leaf_name
        external = outside / leaf_name
        inside_bytes = b"J24I16 intended inside archive bytes | " + bytes(range(32))
        outside_bytes = b"J24I16 OUTSIDE SOURCE ROOT | must not be admitted " + bytes(range(32, 64))
        inner.write_bytes(inside_bytes)
        external.write_bytes(outside_bytes)
        assert sha(inside_bytes) != sha(outside_bytes)
        assert not outside.is_relative_to(root)
        outside_info = os.stat(external)
        inside_info = os.stat(inner)
        if (inside_info.st_dev, inside_info.st_ino) == (outside_info.st_dev, outside_info.st_ino):
            raise AssertionError("inside/outside fixtures alias the same source object")

        # Two positive oracle controls: stable root access via the candidate
        # and the original tree's own native file handle/file identity.
        stable_raw, stable_info = win32_read_nofollow(inner)
        if stable_raw != inside_bytes:
            raise AssertionError("ordinary inside-root source control changed")
        initial_os = {
            "inside": [int(inside_info.st_dev), int(inside_info.st_ino)],
            "outside": [int(outside_info.st_dev), int(outside_info.st_ino)],
        }

        # Leaf negative (existing J24I15 safety promise): last-component
        # reparse point to an external regular file MUST be rejected.
        final_leaf = root / "final-symlink.bin"
        try:
            os.symlink(str(external), str(final_leaf))
        except OSError as exc:
            raise OSError("host cannot create final symlink control (infra): " + repr(exc))
        leaf_stat = os.lstat(final_leaf)
        if not (stat.S_ISLNK(leaf_stat.st_mode) or
                getattr(leaf_stat, "st_file_attributes", 0) & 0x400):
            raise AssertionError("final symlink fixture not a reparse point")
        try:
            final_bytes, _ = win32_read_nofollow(final_leaf)
        except (RejectedSource, OSError) as exc:
            leaf_observation = {"rejected": True, "exception": type(exc).__name__}
        else:
            raise AssertionError("candidate unexpectedly followed final symlink: " + sha(final_bytes))

        # Deterministic interval: classify the exact regular pathname first;
        # then swap only its *ancestor* path, not the file content. A consumer
        # later using leaf-only nofollow opens the same textual pathname.
        pre_pivot = os.stat(inner, follow_symlinks=False)
        if (int(pre_pivot.st_dev), int(pre_pivot.st_ino)) != initial_os["inside"]:
            raise AssertionError("pre-pivot source identity drift")
        parent.rename(parked)
        junction_message = mkjunction(parent, outside)
        parent_stat = os.lstat(parent)
        attributes = int(getattr(parent_stat, "st_file_attributes", 0))
        if not (attributes & 0x400):
            raise AssertionError("ancestor is not an NTFS reparse point")
        if not (parent / leaf_name).samefile(external):
            raise AssertionError("junction does not actually target the external file")
        if not (parent / leaf_name).resolve().samefile(external):
            raise AssertionError("resolved source spelling does not identify outside fixture")

        pivot_raw, pivot_info = win32_read_nofollow(parent / leaf_name)
        retained_raw, retained_info = win32_read_nofollow(parked / leaf_name)
        # Two differently rooted independent oracles: pathname/stat and
        # actual bytes from the external original path.
        after_os = os.stat(parent / leaf_name)
        with external.open("rb") as independent:
            outside_check = independent.read()
        outside_admitted = (
            pivot_raw == outside_bytes
            and pivot_raw == outside_check
            and pivot_raw != stable_raw
            and retained_raw == stable_raw
            and (int(after_os.st_dev), int(after_os.st_ino)) == initial_os["outside"]
            and pivot_info["identity"] != stable_info["identity"]
            and retained_info["identity"] == stable_info["identity"]
        )
        # If this assertion changes, it is a real negative to investigate;
        # never reinterpret an unobserved case as a security success.
        if not outside_admitted:
            raise AssertionError("expected outside-junction read not observed; inspect receipt and host")

        return {
            "installed_package_path": str(installed),
            "sha256": {
                "inside": sha(inside_bytes),
                "outside": sha(outside_bytes),
                "stable_read": sha(stable_raw),
                "ancestor_pivot_read": sha(pivot_raw),
                "original_renamed_read": sha(retained_raw),
                "independent_outside_read": sha(outside_check),
            },
            "bytes": {
                "inside": len(inside_bytes),
                "outside": len(outside_bytes),
                "stable": len(stable_raw),
                "after_ancestor_pivot": len(pivot_raw),
            },
            "source_physical_ids": initial_os,
            "post_pivot_os_identity": [int(after_os.st_dev), int(after_os.st_ino)],
            "handle_identities": {
                "before": list(stable_info["identity"]),
                "after_ancestor_pivot": list(pivot_info["identity"]),
                "retained_original": list(retained_info["identity"]),
            },
            "ancestor_junction": {
                "reparse_attributes": attributes,
                "confirmed": True,
                "mklink_stdout": junction_message,
                "was_parent_path_rebound": True,
            },
            "final_leaf_control": leaf_observation,
            "outside_bytes_admitted": outside_admitted,
        }


def main() -> dict:
    result = {
        "schema": SCHEMA, "host": platform.platform(), "python": sys.version,
        "os_name": os.name, "head": os.environ.get("CMPCT_J24I16_HEAD", "UNBOUND"),
        "parent_research_sha": "8d4343defe2918257e153654f1e59cdb7253f265",
        "product_code_modified": False, "release_credit": False, "status": "RUNNING",
        "question": "Does final-leaf nofollow confine intermediate Win32 junctions?"
    }
    out = Path(os.environ["CMPCT_J24I16_RECEIPT"])
    try:
        if os.name != "nt":
            result["status"] = "INFRASTRUCTURE_BLOCKED"
            raise RuntimeError("Win32-only court cannot run outside Windows")
        result["observations"] = result_on_windows()
        result["status"] = "ANCESTOR_JUNCTION_TRAVERSAL_CONFIRMED"
        result["decision"] = (
            "Do not promote J24I15b leaf-only nofollow as root-confining; "
            "root/ancestor handle custody is required. This is primitive evidence, "
            "not a CMPCT Builder exploit or performance result."
        )
    except BaseException as exc:
        result["error"] = type(exc).__name__ + ": " + str(exc)
        result["traceback"] = traceback.format_exc(limit=10)
        if result["status"] == "RUNNING":
            result["status"] = "NONPASS"
        raise
    finally:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    witness = main()
    print(json.dumps({
        "status": witness["status"], "head": witness["head"],
        "outside_bytes_admitted": witness["observations"]["outside_bytes_admitted"]
    }, sort_keys=True))
