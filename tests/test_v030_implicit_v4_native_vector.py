from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from experiments import entropygraph_v030_fs_implicit_v4 as IFS4
from experiments import entropygraph_v030_product_fs as FS


ROOT = Path(__file__).resolve().parents[1]
VECTOR = ROOT / "tests" / "conformance" / "v030-r25-implicit-v4-native.json"
MAX_PATH = 4096
MAX_ENTRIES = 65_536


def _vector() -> dict:
    data = json.loads(VECTOR.read_text(encoding="utf-8"))
    assert data["schema"] == "cmpct-v030-r25-implicit-v4-native-vector-v1"
    return data


def test_native_implicit_v4_vector_is_exact_python_wire_output() -> None:
    vector = _vector()
    v1 = base64.b64decode(vector["filesystem_v1_base64"], validate=True)
    expected = base64.b64decode(vector["implicit_v4_base64"], validate=True)
    encoded = IFS4.encode_v1(v1, max_path_bytes=MAX_PATH, max_entries=MAX_ENTRIES)

    assert len(v1) == vector["filesystem_v1_bytes"]
    assert encoded == expected
    assert len(encoded) == vector["implicit_v4_bytes"]
    assert hashlib.sha256(encoded).hexdigest() == vector["implicit_v4_sha256"]
    assert len(encoded) < len(v1)


def test_native_implicit_v4_vector_expands_to_exact_filesystem_v1_semantics() -> None:
    vector = _vector()
    v1 = base64.b64decode(vector["filesystem_v1_base64"], validate=True)
    implicit = base64.b64decode(vector["implicit_v4_base64"], validate=True)
    regular = {
        row["path"]: (int(row["size"]), bytes.fromhex(row["sha256"]))
        for row in vector["regular_identities"]
    }
    expanded = IFS4.decode_to_v1(
        implicit,
        regular_identities=regular,
        max_path_bytes=MAX_PATH,
        max_entries=MAX_ENTRIES,
    )
    original = FS.decode_manifest(v1, max_path_bytes=MAX_PATH, max_entries=MAX_ENTRIES)

    assert expanded["manifest"] == original["manifest"]
    assert expanded["regular"] == original["regular"]
    assert expanded["hardlinks"] == original["hardlinks"]


def test_native_implicit_v4_vector_contains_hostile_boundary_features() -> None:
    vector = _vector()
    rows = {row["path"]: row for row in vector["expected_entries"]}
    assert rows["dir"]["kind"] == "d"
    assert rows["dir/zz-alpha-hard.bin"]["kind"] == "h"
    assert rows["dir/zz-alpha-hard.bin"]["extra"] == "dir/alpha.bin"
    assert rows["link.bin"]["kind"] == "l"
    assert rows["dir/alpha.bin"]["mtime_ns"] < 0
    assert rows["dir/beta.bin"]["xattrs"] == [["user.demo", "dg=="]]
    assert rows["dir/beta.bin"]["uid"] != rows["dir/alpha.bin"]["uid"]

# Footnote: this fixture is intentionally generated from the Python executable specification but consumed as
# frozen bytes by native tests. Native parity must reproduce this wire result independently; it must not call back
# into Python or re-run encoder search at decode time.
