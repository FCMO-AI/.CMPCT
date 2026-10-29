"""Detached J24G46 wire/source/result auditor; intentionally never imports CMPCT.

An accepted *negative* result means the archive violated metadata identity:
it is not a product security/correctness SUCCESS.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

MAGIC = b"CMPCT24\x00"
FOOTER = b"CMPTF24\x00"
ORIGINAL = b"z-owner authentic CMPCT content\x00" * 73
INSERTED = b"a-inserted distinct authentic CMPCT payload\x01" * 51

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def main(receipt_file: Path, output: Path) -> None:
    receipt = json.loads(receipt_file.read_text())
    errors = []
    manifest = receipt.get("artifact_manifest", {})
    required = (
        "source_owner", "source_inserted", "initial_archive",
        "stable_archive", "stable_compact_archive",
        "shifted_archive", "shifted_compact_archive",
        "restored_owner", "restored_inserted",
    )
    for label in required:
        item = manifest.get(label)
        if not isinstance(item, dict):
            errors.append("missing materialized artifact: " + label)
            continue
        target = (receipt_file.parent / item["relative_path"]).resolve()
        if receipt_file.parent.resolve() not in target.parents:
            errors.append("artifact escapes evidence directory: " + label)
            continue
        if not target.is_file():
            errors.append("artifact missing: " + label)
            continue
        raw = target.read_bytes()
        if sha(raw) != item["sha256"] or len(raw) != item["bytes"]:
            errors.append("artifact digest/length mismatch: " + label)
        if "archive" in label:
            if not raw.startswith(MAGIC) or FOOTER not in raw:
                errors.append("bad r24 header/footer: " + label)
            snapshot_key = {
                "initial_archive": "base",
                "stable_archive": "stable_update",
                "stable_compact_archive": "stable_compact",
                "shifted_archive": "lexical_insert",
                "shifted_compact_archive": "insert_compact",
            }[label]
            snapshot = receipt.get(snapshot_key, {})
            if sha(raw) != snapshot.get("sha256") or len(raw) != snapshot.get("archive_bytes"):
                errors.append("receipt vs physical archive: " + label)
        if label in ("source_owner", "restored_owner") and raw != ORIGINAL:
            errors.append("source/restored owner bytes mismatch")
        if label in ("source_inserted", "restored_inserted") and raw != INSERTED:
            errors.append("source/restored inserted bytes mismatch")

    if receipt.get("decision") == "EXPERIMENT_INVALID":
        errors.append("experiment did not execute")
    if receipt.get("original_content_sha256") != sha(ORIGINAL):
        errors.append("original content SHA mismatch")
    if receipt.get("restored_content_sha256") != {
        "a-inserted.bin": sha(INSERTED), "z-owner.bin": sha(ORIGINAL),
    }:
        errors.append("logical content mismatch")
    if receipt.get("base", {}).get("names") != ["z-owner.bin"]:
        errors.append("initial file index wrong")
    if receipt.get("lexical_insert", {}).get("names") != ["a-inserted.bin", "z-owner.bin"]:
        errors.append("insertion did not shift ordinal")
    if receipt.get("lexical_insert", {}).get("verified_members") != 2:
        errors.append("logical verify not complete")
    if receipt.get("insert_compact", {}).get("verified_members") != 2:
        errors.append("compacted logical verify not complete")

    native = receipt.get("native_os_xattrs_supported")
    decision = receipt.get("decision")
    if native:
        controls = receipt.get("independent_original_os_values", {})
        if controls.get("binary_value_correct") is not True or controls.get("empty_key_present") is not True:
            errors.append("independent native OS source fixture not proven")
        if receipt.get("stable_control_correct") is not True:
            errors.append("unshifted control failed")
        if decision == "JOURNAL_POSITIONAL_XATTR_REBIND_CONFIRMED":
            if receipt.get("insert_metadata_correct") is not False or receipt.get("compact_metadata_correct") is not False:
                errors.append("negative decision inconsistent with metadata")
            if receipt.get("physical_misapplication") is not True:
                errors.append("negative decision lacks independently witnessed wrong-file xattr")
            source_map = receipt.get("base", {}).get("xattrs_by_logical_name", {})
            rebind_map = receipt.get("lexical_insert", {}).get("xattrs_by_logical_name", {})
            compact_map = receipt.get("insert_compact", {}).get("xattrs_by_logical_name", {})
            original_key = "com.fcmo.cmpct.j24g46" if receipt.get("platform") == "darwin" else "user.cmpct_j24g46"
            for label, index_map in (("source", source_map), ("replayed", rebind_map), ("compacted", compact_map)):
                expected_member = "z-owner.bin" if label == "source" else "a-inserted.bin"
                if index_map.get(expected_member, {}).get(original_key) != b"J24G46 native journal identity\x00\xff\x01".hex():
                    errors.append("negative xattr lineage wrong: " + label)
                if index_map.get(expected_member, {}).get(original_key + ".empty") != "":
                    errors.append("empty attribute failed: " + label)
        elif decision == "POSITIONAL_IDENTITY_PRESERVED":
            if receipt.get("insert_metadata_correct") is not True or receipt.get("compact_metadata_correct") is not True:
                errors.append("preserved decision inconsistent with metadata")
        else:
            errors.append("inconclusive or mixed native result: " + str(decision))
    elif receipt.get("platform") == "win32":
        if decision != "WINDOWS_CONTENT_ONLY_NO_XATTR_POSITIVE":
            errors.append("Windows claims unsupported native xattr positive")
    else:
        errors.append("unknown native capability/platform")

    report = {
        "independent_wire_auditor": "J24G46",
        "experiment_platform": receipt.get("platform"),
        "decision": decision,
        "classification": "NEGATIVE_PRODUCT_EVIDENCE" if decision == "JOURNAL_POSITIONAL_XATTR_REBIND_CONFIRMED" else "RESEARCH_CONTROL",
        "physical_artifacts_verified": len(required),
        "errors": errors,
        "audit": "ADMITTED" if not errors else "REJECTED",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)

if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
