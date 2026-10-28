from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


VECTOR = Path(__file__).with_name("conformance") / "v24-sparse.json"


def _record() -> dict:
    payload = json.loads(VECTOR.read_text())
    assert payload["schema"] == "cmpct-v24-sparse-golden-v1"
    assert payload["format_revision"] == 24
    return payload


def test_fixed_sparse_vector_is_byte_stable_and_readable(tmp_path: Path) -> None:
    """Freeze S_SPARSE semantics independently of the contemporary builder.

    Footnote: the vector deliberately includes leading/interior/trailing holes and a data extent
    spanning Zstd plus raw Deflate blobs. Range checks cross hole/data and codec boundaries so a
    future native implementation cannot pass by materializing only the data extents or assuming one
    physical codec.
    """
    record = _record()
    archive_bytes = base64.b64decode(record["archive"]["base64"], validate=True)
    assert len(archive_bytes) == record["archive"]["bytes"]
    assert hashlib.sha256(archive_bytes).hexdigest() == record["archive"]["sha256"]

    archive = tmp_path / record["archive"]["name"]
    archive.write_bytes(archive_bytes)
    summary = preflight_archive(archive)
    assert summary["version"] == 24
    assert summary["files"] == 1
    assert summary["blobs"] == 3

    member = record["member"]
    with CMPCT(archive) as ar:
        row = ar.by[member["path"]]
        assert row[4] == member["size"]
        assert row[6][0] == member["storage_kind"]
        assert [
            {"offset": extent[0], "length": extent[1], "blob_ids": extent[2]}
            for extent in row[6][1]
        ] == member["extents"]
        ids = [blob_id for extent in row[6][1] for blob_id in extent[2]]
        assert [ar.blobs[i][3] for i in ids] == member["blob_codecs"]

        raw = ar.read(member["path"])
        assert len(raw) == member["size"]
        assert hashlib.sha256(raw).hexdigest() == member["sha256"]
        for expected in member["ranges"]:
            got = ar.read_range(
                member["path"], expected["offset"], expected["length"]
            )
            assert got.hex() == expected["hex"]
            assert hashlib.sha256(got).hexdigest() == expected["sha256"]


def test_sparse_vector_covers_holes_and_all_native_direct_codecs() -> None:
    member = _record()["member"]
    assert member["storage_kind"] == 3
    assert member["blob_codecs"] == [0, 1, 4]
    assert member["extents"][0]["offset"] > 0
    last = member["extents"][-1]
    assert last["offset"] + last["length"] < member["size"]
