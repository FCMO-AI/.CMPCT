from __future__ import annotations

import base64
import copy
import json
from pathlib import Path

import msgpack
import pytest

from experiments import entropygraph_v030_fs_implicit_v4 as IFS4


ROOT = Path(__file__).resolve().parents[1]
VECTOR = ROOT / "tests" / "conformance" / "v030-r25-implicit-v4-native.json"
MAX_PATH = 4096
MAX_ENTRIES = 65_536


def _fixture() -> tuple[list, dict[str, tuple[int, bytes]]]:
    vector = json.loads(VECTOR.read_text(encoding="utf-8"))
    root = msgpack.unpackb(base64.b64decode(vector["implicit_v4_base64"], validate=True), raw=False)
    identities = {
        row["path"]: (int(row["size"]), bytes.fromhex(row["sha256"]))
        for row in vector["regular_identities"]
    }
    return root, identities


def _decode(root: list, identities: dict[str, tuple[int, bytes]]) -> None:
    IFS4.decode_to_v1(
        msgpack.packb(root, use_bin_type=True),
        regular_identities=identities,
        max_path_bytes=MAX_PATH,
        max_entries=MAX_ENTRIES,
    )


def test_native_hostile_wrong_version_fails_closed() -> None:
    root, identities = _fixture()
    root[0] = 5
    with pytest.raises(RuntimeError):
        _decode(root, identities)


def test_native_hostile_regular_count_mismatch_fails_closed() -> None:
    root, identities = _fixture()
    root[2] = root[2][:-1]
    with pytest.raises(RuntimeError):
        _decode(root, identities)


def test_native_hostile_unknown_metadata_mask_fails_closed() -> None:
    root, identities = _fixture()
    root[2][0] = [32]
    with pytest.raises(RuntimeError):
        _decode(root, identities)


def test_native_hostile_trailing_metadata_fields_fail_closed() -> None:
    root, identities = _fixture()
    root[2][0] = [0, 123]
    with pytest.raises(RuntimeError):
        _decode(root, identities)


def test_native_hostile_signed_delta_overflow_fails_closed() -> None:
    root, identities = _fixture()
    root[1][1] = (1 << 63) - 1
    root[2][0] = [2, 1]
    with pytest.raises(RuntimeError):
        _decode(root, identities)


def test_native_hostile_prefix_beyond_previous_path_fails_closed() -> None:
    root, identities = _fixture()
    root[3][1][0] = 1_000_000
    with pytest.raises(RuntimeError):
        _decode(root, identities)


def test_native_hostile_unsorted_explicit_paths_fail_closed() -> None:
    root, identities = _fixture()
    first = copy.deepcopy(root[3][0])
    second = copy.deepcopy(root[3][1])
    # Encode a second explicit path lexically before the first while keeping a valid zero prefix.
    first[0], first[1] = 0, "z-dir"
    second[0], second[1] = 0, "a-dir"
    second[2], second[4] = 1, None
    root[3][0], root[3][1] = first, second
    with pytest.raises(RuntimeError):
        _decode(root, identities)


def test_native_hostile_regular_explicit_path_collision_fails_closed() -> None:
    root, identities = _fixture()
    row = copy.deepcopy(root[3][0])
    row[0], row[1] = 0, "dir/alpha.bin"
    root[3] = [row]
    with pytest.raises(RuntimeError):
        _decode(root, identities)


def test_native_hostile_hardlink_owner_index_fails_closed() -> None:
    root, identities = _fixture()
    hardlink = next(row for row in root[3] if row[2] == 3)
    hardlink[4] = 999
    with pytest.raises(RuntimeError):
        _decode(root, identities)


def test_native_hostile_symlink_escape_fails_closed_at_product_policy_boundary() -> None:
    # IFS4 itself reconstructs filesystem-v1 semantics; the shared product filesystem decoder/materializer owns
    # symlink lexical safety. Preserve that ownership explicitly so native does not accidentally claim the compact
    # parser alone proves extraction safety.
    root, identities = _fixture()
    symlink = next(row for row in root[3] if row[2] == 2)
    symlink[4] = "../escape"
    decoded = IFS4.decode_to_v1(
        msgpack.packb(root, use_bin_type=True),
        regular_identities=identities,
        max_path_bytes=MAX_PATH,
        max_entries=MAX_ENTRIES,
    )
    row = next(row for row in decoded["manifest"]["entries"] if row[1] == "l")
    assert row[7] == "../escape"

# Footnote: this is a cross-language hostile-vector contract, not a second parser. The frozen compact bytes are
# mutated only to enumerate fail-closed cases the Rust reader must reject at the same trust boundary. Symlink target
# safety deliberately remains a downstream filesystem/materialization invariant, matching the Python ownership.
