from __future__ import annotations

from copy import deepcopy

import pytest

from cmpct.codec import (
    CODEC_RAW,
    K_FILE,
    K_HARDLINK,
    S_BLOB,
    S_CDC,
    S_CHUNKS,
    S_PACK,
    S_SPARSE,
    S_VZIP,
    VERSION,
)
from cmpct.validation import ParserLimits, ResourceLimitError, ValidationError, _validate_index


# Footnote: these tests intentionally exercise the structural validator below the byte-decoding layer.
# That keeps each mutation focused on one archive-controlled invariant instead of requiring corrupt
# MessagePack/codec bytes to accidentally survive long enough to reach the intended check.
def _base_index() -> dict:
    return {
        "v": VERSION,
        "files": [["file.bin", K_FILE, 0o644, 0, 4, b"x" * 32, [S_BLOB, 0]]],
        "blobs": [[0, 4, 4, CODEC_RAW, 0]],
        "recipes": [],
        "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
    }


def _validate(index: dict, limits: ParserLimits | None = None) -> None:
    # The physical blob-header pass is tested separately. Give the logical index ample address space
    # here so a storage mutation cannot be masked by an unrelated archive-boundary failure.
    _validate_index(index, record_base=0, archive_size=1 << 20, limits=limits or ParserLimits())


def test_rejects_unknown_blob_codec_before_payload_decode():
    index = _base_index()
    index["blobs"][0][3] = 255

    with pytest.raises(ValidationError, match="unknown codec"):
        _validate(index)


def test_rejects_blob_declaration_above_policy_limit():
    index = _base_index()
    index["blobs"][0][1] = 4096

    with pytest.raises(ResourceLimitError, match="blob 0 size exceeds parser limit"):
        _validate(index, ParserLimits(max_blob_bytes=1024))


def test_rejects_pack_slice_past_physical_blob():
    index = _base_index()
    index["files"][0][6] = [S_PACK, 0, 2, 4]

    with pytest.raises(ValidationError, match="pack slice exceeds blob"):
        _validate(index)


def test_rejects_fixed_chunks_whose_lengths_do_not_match_logical_file():
    index = _base_index()
    index["files"][0][4] = 5
    index["files"][0][6] = [S_CHUNKS, [0]]

    with pytest.raises(ValidationError, match="chunk lengths do not equal logical size"):
        _validate(index)


def test_rejects_cdc_declared_length_that_disagrees_with_blob():
    index = _base_index()
    index["files"][0][6] = [S_CDC, [[3, 0]]]

    with pytest.raises(ValidationError, match="CDC chunk 0 length disagrees with blob"):
        _validate(index)


def test_rejects_sparse_extent_that_runs_past_logical_eof():
    index = _base_index()
    index["files"][0][6] = [S_SPARSE, [[2, 4, [0]]]]

    with pytest.raises(ValidationError, match="overlaps or exceeds file"):
        _validate(index)


def test_rejects_sparse_extent_whose_blob_bytes_do_not_match_extent():
    index = _base_index()
    index["files"][0][4] = 8
    index["files"][0][6] = [S_SPARSE, [[0, 3, [0]]]]

    with pytest.raises(ValidationError, match="sparse extent 0 length mismatch"):
        _validate(index)


def test_rejects_virtual_zip_reference_to_missing_recipe():
    index = _base_index()
    index["files"][0][6] = [S_VZIP, 0]

    with pytest.raises(ValidationError, match="virtual-ZIP recipe references missing object"):
        _validate(index)


def test_rejects_duplicate_logical_paths():
    index = _base_index()
    index["files"].append(deepcopy(index["files"][0]))

    with pytest.raises(ValidationError, match="duplicate logical path"):
        _validate(index)


@pytest.mark.parametrize("path", ["../escape", "dir/../escape", "/absolute", "dir//file", ""])
def test_rejects_lexically_unsafe_logical_paths(path: str):
    index = _base_index()
    index["files"][0][0] = path

    with pytest.raises(ValidationError, match="unsafe logical path"):
        _validate(index)


def test_rejects_hardlink_to_missing_target():
    index = _base_index()
    index["files"][0] = ["link", K_HARDLINK, 0o644, 0, 0, None, ["missing"]]

    with pytest.raises(ValidationError, match="targets missing path"):
        _validate(index)


def test_rejects_hardlink_cycle():
    index = _base_index()
    index["files"] = [
        ["a", K_HARDLINK, 0o644, 0, 0, None, ["b"]],
        ["b", K_HARDLINK, 0o644, 0, 0, None, ["a"]],
    ]

    with pytest.raises(ValidationError, match="hardlink cycle"):
        _validate(index)


def test_rejects_filesystem_metadata_reference_to_missing_file():
    index = _base_index()
    index["fsmeta"]["owner_overrides"] = [[1, 1000, 1000]]

    with pytest.raises(ValidationError, match="fsmeta owner_overrides file references missing object"):
        _validate(index)


def test_mutation_control_reference_index_remains_valid():
    # Guard against a false sense of coverage where every mutation test fails because the fixture
    # itself stopped matching revision 24 after a future schema change.
    _validate(_base_index())
