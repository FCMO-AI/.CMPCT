#!/usr/bin/env python3
"""J24G79 detached physical signed-wire referee. Never imports cmpct.

Reuses solely the no-product-import raw struct/zstd/msgpack reconstruction
from the immutable J24G73 physical referee; checks a new hardlink/xattr fixture.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import msgpack
from j24g73_independent_wire import wire, reconstruct, FTR

EXPECT_HEAD_BLOB = "29a8be64f3acfb027750351c6a567fd82cf7dc97"
EXPECT_OPS = {"ren": 21, "del": 21, "put": 21}
EXPECTED_XATTR_PATHS = {"a-owner.dat", "z-alias.dat", "r000.dat"}

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def verify_physical(receipt: dict, raw: bytes) -> dict:
    assert receipt["schema"] == "cmpct-j24g79-owned-hardlink-v1"
    assert receipt["status"] == "PASS" and receipt["product_credit"] == 0
    assert receipt["source"]["blobs"]["src/cmpct/reader.py"] == EXPECT_HEAD_BLOB
    assert digest(raw) == receipt["physical_sha256"]
    assert digest(raw) == receipt["result"]["archive_sha256"]
    assert len(raw) == receipt["result"]["archive_bytes"]
    entries = wire(raw)
    index, operations, initial = reconstruct(entries)
    full_index_sha = digest(msgpack.packb(index, use_bin_type=True))
    assert full_index_sha == receipt["result"]["index_sha256"]
    assert operations == EXPECT_OPS and sum(operations.values()) == 63
    assert initial == 130
    assert len(index["files"]) == receipt["result"]["members"] == 119
    assert receipt["result"]["footer_count"] == 64
    assert receipt["result"]["owned_route_reached"] is True
    assert receipt["result"]["routes"]["OwnedCMPCT"] == "owned-fresh-decoder"
    assert receipt["result"]["routes"]["FactoredCMPCT"] == "factored"
    rows = {row[0]: row for row in index["files"]}
    assert len(rows) == len(index["files"])
    assert set(EXPECTED_XATTR_PATHS) <= set(rows)
    signed = index.get("fsmeta") or {}
    path_xattrs = {
        index["files"][record[0]][0]: record[1:]
        for record in signed.get("xattrs", [])
    }
    assert len(path_xattrs) == receipt["result"]["xattr_members"]
    if receipt["os"] in ("linux", "darwin"):
        assert receipt["builder"]["source_hardlink"]
        assert "z-alias.dat" in receipt["builder"]["encoded_hardlinks"]
        assert rows["z-alias.dat"][1] == 3
        assert rows["z-alias.dat"][6][0] == "a-owner.dat"
        assert set(path_xattrs) == EXPECTED_XATTR_PATHS
        assert path_xattrs["a-owner.dat"] == path_xattrs["z-alias.dat"]
    # Independently mutate authenticated footer digest in the physical file.
    damaged = bytearray(raw)
    first_footer_position = entries[0][2]
    damaged[first_footer_position + FTR.size - 1] ^= 0x5A
    try:
        wire(bytes(damaged))
    except (AssertionError, ValueError, RuntimeError):
        pass
    else:
        raise AssertionError("detached referee accepted tampered footer SHA")
    return {
        "result": "PASS",
        "host": receipt["os"],
        "head": receipt["source"]["head"],
        "archive_sha256": digest(raw),
        "physical_index_sha256": full_index_sha,
        "physical_footers": len(entries),
        "initial_members": initial,
        "final_members": len(index["files"]),
        "operations": operations,
        "hardlink_alias_in_auth_index": rows["z-alias.dat"][1] == 3,
        "xattr_paths": sorted(path_xattrs),
        "tampered_footer_rejected": True,
        "scope": "no-cmpct physical footer + complete signed index; physical payload blob byte verification remains inherited Reader court",
    }

def main(receipt_path: Path, directory: Path):
    receipt = json.loads(receipt_path.read_text())
    raw = (directory / "hardlink-journal-physical.cmpct").read_bytes()
    result = verify_physical(receipt, raw)
    bad = json.loads(json.dumps(receipt))
    bad["result"]["index_sha256"] = "0" * 64
    try:
        verify_physical(bad, raw)
    except AssertionError:
        result["forged_index_receipt_rejected"] = True
    else:
        raise AssertionError("forged index SHA receipt was accepted")
    bad = json.loads(json.dumps(receipt))
    bad["physical_sha256"] = "0" * 64
    try:
        verify_physical(bad, raw)
    except AssertionError:
        result["forged_archive_receipt_rejected"] = True
    else:
        raise AssertionError("forged archive receipt was accepted")
    target = directory / "j24g79-detached-wire.json"
    target.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("J24G79_DETACHED_PHYSICAL", json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    assert len(sys.argv) == 3
    main(Path(sys.argv[1]), Path(sys.argv[2]))
