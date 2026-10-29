"""J24G46 physical source-independent xattr identity experiment.

Research-level executable: a SUCCESS means the instrument proved a stated
observation, never that the product passes its fidelity requirement.
The independent OS writer/reader is deliberately outside cmpct._xattrs.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import append_update, compact_archive

OS_NATIVE = sys.platform in ("darwin", "linux")
KEY = "com.fcmo.cmpct.j24g46" if sys.platform == "darwin" else "user.cmpct_j24g46"
VALUE = b"J24G46 native journal identity\x00\xff\x01"
EMPTY_KEY = KEY + ".empty"
ORIGINAL = b"z-owner authentic CMPCT content\x00" * 73
INSERTED = b"a-inserted distinct authentic CMPCT payload\x01" * 51


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def os_set_attr(path: Path, key: str, value: bytes) -> None:
    if sys.platform == "darwin":
        subprocess.run(["/usr/bin/xattr", "-wx", key, value.hex(), os.fspath(path)],
                       capture_output=True, text=True, check=True)
    elif sys.platform == "linux":
        os.setxattr(path, key, value, follow_symlinks=False)
    else:
        raise RuntimeError("xattr test unsupported")


def os_get_attr(path: Path, key: str) -> bytes | None:
    if sys.platform == "darwin":
        p = subprocess.run(["/usr/bin/xattr", "-px", key, os.fspath(path)],
                           capture_output=True, text=True)
        if p.returncode:
            return None
        return bytes.fromhex("".join(p.stdout.split()))
    if sys.platform == "linux":
        try:
            return os.getxattr(path, key, follow_symlinks=False)
        except OSError as exc:
            if exc.errno in (getattr(os, "ENODATA", -1), 61, 93, 95):
                return None
            raise
    return None


def attr_decision(path: Path) -> dict:
    if not OS_NATIVE:
        return {"supported": False}
    return {
        "supported": True,
        "binary_value_correct": os_get_attr(path, KEY) == VALUE,
        "empty_key_present": os_get_attr(path, EMPTY_KEY) == b"",
    }


def index_snapshot(path: Path, expected: dict[str, bytes]) -> dict:
    with CMPCT(path) as reader:
        verified = reader.verify()
        names = [row[0] for row in reader.files]
        assert names == sorted(expected), (names, sorted(expected))
        for name, data in expected.items():
            assert reader.read(name) == data, f"logical content mismatch: {name}"
        xattr_map = {}
        for i, attributes in reader.fsmeta.get("xattrs", []):
            if not (0 <= i < len(reader.files)):
                raise AssertionError("out-of-range xattr ordinal")
            xattr_map[reader.files[i][0]] = {
                str(key): bytes(val).hex() for key, val in attributes
            }
        return {
            "sha256": sha(path.read_bytes()),
            "archive_bytes": path.stat().st_size,
            "verified_members": verified,
            "names": names,
            "content_sha256": {name: sha(expected[name]) for name in names},
            "xattrs_by_logical_name": xattr_map,
        }


def prove(out: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="j24g46-physical-") as td:
        root = Path(td)
        source = root / "source"
        source.mkdir()
        owner = source / "z-owner.bin"
        owner.write_bytes(ORIGINAL)
        inserted_source = root / "insertion.bin"
        inserted_source.write_bytes(INSERTED)
        original_content_sha = sha(ORIGINAL)
        if OS_NATIVE:
            os_set_attr(owner, KEY, VALUE)
            os_set_attr(owner, EMPTY_KEY, b"")
            assert attr_decision(owner)["binary_value_correct"]
            assert attr_decision(owner)["empty_key_present"]
        original_attributes = attr_decision(owner)

        base = root / "initial.cmpct"
        Builder(source, workers=1, reproducible=False).build(base)
        expected_base = {"z-owner.bin": ORIGINAL}
        base_snapshot = index_snapshot(base, expected_base)
        if OS_NATIVE:
            assert base_snapshot["xattrs_by_logical_name"]["z-owner.bin"][KEY] == VALUE.hex()
            assert base_snapshot["xattrs_by_logical_name"]["z-owner.bin"][EMPTY_KEY] == ""

        stable = root / "stable.cmpct"
        shutil.copyfile(base, stable)
        append_update(stable, "z-owner.bin", owner)
        stable_snapshot = index_snapshot(stable, expected_base)

        shifted = root / "shifted.cmpct"
        shutil.copyfile(base, shifted)
        append_update(shifted, "a-inserted.bin", inserted_source)
        expected_shifted = {"a-inserted.bin": INSERTED, "z-owner.bin": ORIGINAL}
        shifted_snapshot = index_snapshot(shifted, expected_shifted)

        baseline_compact = root / "stable-compact.cmpct"
        compact_archive(stable, baseline_compact)
        baseline_snapshot = index_snapshot(baseline_compact, expected_base)
        shifted_compact = root / "shifted-compact.cmpct"
        compact_archive(shifted, shifted_compact)
        compact_snapshot = index_snapshot(shifted_compact, expected_shifted)

        restored = root / "materialized"
        with CMPCT(shifted_compact) as reader:
            reader.extractall(restored, require_xattrs=OS_NATIVE)

        restored_sha = {
            name: sha((restored / name).read_bytes())
            for name in expected_shifted
        }
        assert restored_sha == {
            name: sha(data) for name, data in expected_shifted.items()
        }
        actual_restored = {
            name: attr_decision(restored / name) for name in expected_shifted
        }
        assert sha(owner.read_bytes()) == original_content_sha

        shift_xattrs = shifted_snapshot["xattrs_by_logical_name"]
        compact_xattrs = compact_snapshot["xattrs_by_logical_name"]
        stable_xattrs = stable_snapshot["xattrs_by_logical_name"]
        baseline_xattrs = baseline_snapshot["xattrs_by_logical_name"]

        if OS_NATIVE:
            key_hex = VALUE.hex()
            # Stable updates and compaction are the stronger control.
            stable_correct = (
                stable_xattrs.get("z-owner.bin", {}).get(KEY) == key_hex
                and baseline_xattrs.get("z-owner.bin", {}).get(KEY) == key_hex
            )
            shifted_correct = (
                shift_xattrs.get("z-owner.bin", {}).get(KEY) == key_hex
                and KEY not in shift_xattrs.get("a-inserted.bin", {})
            )
            compact_correct = (
                compact_xattrs.get("z-owner.bin", {}).get(KEY) == key_hex
                and KEY not in compact_xattrs.get("a-inserted.bin", {})
            )
            physical_misapplication = (
                actual_restored["a-inserted.bin"]["binary_value_correct"]
                and not actual_restored["z-owner.bin"]["binary_value_correct"]
            )
            # Explicitly distinguish metadata association from content validity.
            if not stable_correct:
                decision = "CONTROL_FAILED"
            elif shifted_correct and compact_correct:
                decision = "POSITIONAL_IDENTITY_PRESERVED"
            elif (not shifted_correct and not compact_correct and physical_misapplication):
                decision = "JOURNAL_POSITIONAL_XATTR_REBIND_CONFIRMED"
            else:
                decision = "MIXED_OR_INCONCLUSIVE"
        else:
            stable_correct = None
            shifted_correct = None
            compact_correct = None
            physical_misapplication = None
            decision = "WINDOWS_CONTENT_ONLY_NO_XATTR_POSITIVE"

        # Preserve actual input and archive bytes for an independent wire auditor.
        evidence_dir = dest.parent / "artifacts"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        originals = {
            "source_owner": owner,
            "source_inserted": inserted_source,
            "initial_archive": base,
            "stable_archive": stable,
            "stable_compact_archive": baseline_compact,
            "shifted_archive": shifted,
            "shifted_compact_archive": shifted_compact,
            "restored_owner": restored / "z-owner.bin",
            "restored_inserted": restored / "a-inserted.bin",
        }
        manifest = {}
        for label, original_path in originals.items():
            suffix = ".cmpct" if "archive" in label else ".bin"
            artifact_path = evidence_dir / (label + suffix)
            shutil.copyfile(original_path, artifact_path)
            raw = artifact_path.read_bytes()
            manifest[label] = {
                "relative_path": "artifacts/" + artifact_path.name,
                "sha256": sha(raw),
                "bytes": len(raw),
            }

        return {
            "artifact_manifest": manifest,
            "experiment": "J24G46 positional fsmeta journal insertion",
            "platform": sys.platform,
            "python": sys.version,
            "published_r24_format_changed": False,
            "native_os_xattrs_supported": OS_NATIVE,
            "independent_original_os_values": original_attributes,
            "original_content_sha256": original_content_sha,
            "base": base_snapshot,
            "stable_update": stable_snapshot,
            "stable_compact": baseline_snapshot,
            "lexical_insert": shifted_snapshot,
            "insert_compact": compact_snapshot,
            "restored_content_sha256": restored_sha,
            "restored_native_attributes": actual_restored,
            "stable_control_correct": stable_correct,
            "insert_metadata_correct": shifted_correct,
            "compact_metadata_correct": compact_correct,
            "physical_misapplication": physical_misapplication,
            "decision": decision,
        }


if __name__ == "__main__":
    dest = Path(sys.argv[1])
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        record = prove(dest)
    except Exception as exc:
        record = {
            "experiment": "J24G46 positional fsmeta journal insertion",
            "platform": sys.platform,
            "decision": "EXPERIMENT_INVALID",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        dest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=2, sort_keys=True))
        raise
    dest.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))
