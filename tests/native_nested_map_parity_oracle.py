"""Independent fully-authenticated r24 nested/non-text duplicate map oracle.

Prerecorded negative prediction: PR #321 rejects duplicated text root keys but
Rust opens duplicated fsmeta.owner and integer/bytes root map keys. No fixture
identity-based workaround, no builder-generated corpus, no weakened SHA.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import tempfile
from pathlib import Path

import msgpack

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from native_duplicate_root_index_oracle import (  # noqa: E402
    GOLDEN, FTR, HDR, Zstd, native_lib, native_read, sha,
)
from cmpct.reader import CMPCT  # noqa: E402
from cmpct.validation import preflight_archive  # noqa: E402


def mutated_index(original: bytes, zstd: Zstd, family: str, first: bool) -> bytes:
    magic, rev, flags, csize, usize, physical_size, digest = HDR.unpack_from(original)
    assert magic == b"CMPCT24\0" and rev == 24
    old_index = zstd.decompress(original[HDR.size:HDR.size + csize], usize)
    assert sha(old_index) == digest
    root = msgpack.unpackb(old_index, raw=False)
    assert len(root["files"]) == 1 and isinstance(root.get("fsmeta", {}), dict)
    pack = msgpack.Packer(use_bin_type=True)
    wire = [pack.pack_map_header(len(root) + (2 if family.startswith("root") else (0 if "fsmeta" in root else 1)))]
    if family.startswith("root"):
        key = 7 if family == "root-int" else b"ignored-extension"
        values = (0, 1) if first else (1, 0)
        wire.extend([pack.pack(key), pack.pack(values[0]),
                     pack.pack(key), pack.pack(values[1])])
    for key, value in root.items():
        wire.append(pack.pack(key))
        if key != "fsmeta" or family != "nested-owner":
            wire.append(pack.pack(value))
            continue
        assert "owner" in value and isinstance(value["owner"], list)
        base_owner = value["owner"]
        extra_owner = [1001, 1002] if base_owner != [1001, 1002] else [2001, 2002]
        wire.append(pack.pack_map_header(len(value) + 1))
        for field, old in value.items():
            if field != "owner":
                wire.extend([pack.pack(field), pack.pack(old)])
                continue
            ordered = [extra_owner, base_owner] if first else [base_owner, extra_owner]
            wire.extend([pack.pack("owner"), pack.pack(ordered[0]),
                         pack.pack("owner"), pack.pack(ordered[1])])
    if family == "nested-owner" and "fsmeta" not in root:
        # Independent goldens may omit optional filesystem metadata.
        # Add an otherwise valid fsmeta object, then duplicate owner.
        wire.extend([
            pack.pack("fsmeta"), pack.pack_map_header(4),
            pack.pack("owner"), pack.pack([0, 0] if first else [1001, 1002]),
            pack.pack("owner"), pack.pack([1001, 1002] if first else [0, 0]),
            pack.pack("owner_overrides"), pack.pack([]),
            pack.pack("xattrs"), pack.pack([]),
        ])
    new_index = b"".join(wire)
    assert new_index != old_index
    # Ordinary decoder silently selects one value: the signed bytes are
    # semantically ambiguous despite being cryptographically intact.
    decoded = msgpack.unpackb(new_index, raw=False)
    assert decoded["files"] == root["files"]
    if family == "nested-owner":
        assert decoded["fsmeta"]["owner"] != []
    new_compressed = zstd.compress(new_index)
    physical = original[HDR.size + csize: HDR.size + csize + physical_size]
    assert len(physical) == physical_size
    h = sha(new_index)
    forged = (
        HDR.pack(magic, rev, flags, len(new_compressed), len(new_index), physical_size, h)
        + new_compressed + physical + new_compressed
        + FTR.pack(b"CMPTF24\0", 0, 1, 0, 0, len(new_compressed), len(new_index), 0, h)
    )
    assert forged[HDR.size + len(new_compressed):HDR.size + len(new_compressed) + physical_size] == physical
    assert forged[-FTR.size - len(new_compressed):-FTR.size] == new_compressed
    assert sha(zstd.decompress(new_compressed, len(new_index))) == h
    return forged


def rejected_by_python(path: Path) -> bool:
    try:
        with CMPCT(path):
            pass
    except (ValueError, TypeError, IOError):
        return True
    return False


def rejected_by_preflight(path: Path) -> bool:
    try:
        preflight_archive(path)
    except (ValueError, TypeError, IOError):
        return True
    return False


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--phase", choices=("negative", "fixed"), required=True)
    args = cli.parse_args()
    manifest = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert manifest["schema"] == "cmpct-v24-golden-direct-codecs-v1"
    zstd = Zstd()
    native = native_lib()
    cases = []
    with tempfile.TemporaryDirectory(prefix="cmpct-duplicate-map-depth-o2-") as td:
        temp = Path(td)
        for vector in manifest["vectors"]:
            original = base64.b64decode(vector["archive_base64"], validate=True)
            assert sha(original).hex() == vector["archive_sha256"]
            path = temp / (vector["codec"] + "-good.cmpct")
            path.write_bytes(original)
            with CMPCT(path) as reader:
                assert len(reader.files) == 1
                assert sha(reader.read(vector["name"])).hex() == vector["logical_sha256"]
            good_count, good_bytes = native_read(native, path, vector["logical_size"])
            assert good_count == 1 and sha(good_bytes).hex() == vector["logical_sha256"]
            # The independent conformance vector is a positive baseline for both.
            for family in ("nested-owner", "root-int", "root-bytes"):
                for first in (False, True):
                    forged = mutated_index(original, zstd, family, first)
                    hostile = temp / f"{vector['codec']}-{family}-{first}.cmpct"
                    hostile.write_bytes(forged)
                    python_reject = rejected_by_python(hostile)
                    preflight_reject = rejected_by_preflight(hostile)
                    assert python_reject and preflight_reject, (
                        "Python policy failed to detect signed duplicate map",
                        vector["codec"], family, first,
                    )
                    handle = __import__("ctypes").c_void_p()
                    status = native.cmpct_open(str(hostile).encode(), __import__("ctypes").byref(handle))
                    try:
                        if args.phase == "negative":
                            assert status == 0 and handle.value, (
                                "Native refused before O2 fix: falsified O2 prediction",
                                vector["codec"], family, first, status,
                            )
                            n, content = native_read(native, hostile, vector["logical_size"])
                            assert n == 1 and sha(content).hex() == vector["logical_sha256"]
                        else:
                            assert status != 0 and not handle.value, (
                                "Native accepted ambiguous authenticated MessagePack",
                                vector["codec"], family, first, status,
                            )
                    finally:
                        if handle.value:
                            native.cmpct_close(handle)
                    cases.append({
                        "codec": vector["codec"], "family": family, "first": first,
                        "archive_sha256": sha(forged).hex(), "archive_bytes": len(forged),
                        "python_reject": python_reject,
                        "preflight_reject": preflight_reject,
                        "native_status": int(status),
                        "physical_blob_bytes_unchanged": True,
                        "primary_tail_footer_authenticated": True,
                    })
    assert len(cases) == 18
    receipt = {
        "schema": "cmpct-v031-nested-map-cross-reader-o2-v1",
        "phase": args.phase,
        "result": ("PYTHON_NATIVE_REJECTION_DIVERGENCE_18_OF_18" if args.phase == "negative"
                   else "SIGNED_MAP_AMBIGUITIES_REJECTED_18_OF_18"),
        "source_sha": os.environ.get("EVIDENCE_HEAD", "local-unknown"),
        "controls": 3, "hostiles": len(cases),
        "cases": cases,
        "no_product_benchmark_credit": True,
    }
    folder = ROOT / "nested-map-evidence"
    folder.mkdir(exist_ok=True)
    (folder / (args.phase + ".json")).write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(receipt["result"])


if __name__ == "__main__":
    main()
