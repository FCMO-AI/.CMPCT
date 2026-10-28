from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest

from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


VECTORS = Path(__file__).with_name("conformance") / "v24-chunk-maps.json"


def _records() -> list[dict]:
    payload = json.loads(VECTORS.read_text())
    assert payload["schema"] == "cmpct-v24-golden-chunk-maps-v1"
    assert payload["format_revision"] == 24
    return payload["vectors"]


@pytest.mark.parametrize("record", _records(), ids=lambda r: r["name"])
def test_fixed_chunk_map_vector_is_byte_stable_and_readable(tmp_path: Path, record: dict) -> None:
    """Freeze builder-independent S_CHUNKS/S_CDC bytes before native support can define itself.

    Footnote: each range crosses the first chunk boundary and the chunks deliberately mix RAW,
    Zstd and raw Deflate. A reader therefore has to honor the authenticated logical chunk map rather
    than accidentally treating the member as one physical blob or testing only one codec path.
    """
    archive_bytes = base64.b64decode(record["archive_base64"], validate=True)
    assert len(archive_bytes) == record["archive_bytes"]
    assert hashlib.sha256(archive_bytes).hexdigest() == record["archive_sha256"]

    archive = tmp_path / f"golden-storage-{record['storage_kind']}.cmpct"
    archive.write_bytes(archive_bytes)
    summary = preflight_archive(archive)
    assert summary["version"] == 24
    assert summary["files"] == 1
    assert summary["blobs"] == 3

    want_range = bytes.fromhex(record["range"]["hex"])
    with CMPCT(archive) as ar:
        row = ar.by[record["name"]]
        assert row[4] == record["logical_size"]
        assert row[6][0] == record["storage_kind"]
        if record["storage_kind"] == 1:
            ids = row[6][1]
            lengths = [ar.blobs[i][1] for i in ids]
        else:
            lengths = [entry[0] for entry in row[6][1]]
            ids = [entry[1] for entry in row[6][1]]
        assert lengths == record["chunk_lengths"]
        assert [ar.blobs[i][3] for i in ids] == record["chunk_codecs"]
        raw = ar.read(record["name"])
        assert hashlib.sha256(raw).hexdigest() == record["logical_sha256"]
        assert ar.read_range(
            record["name"], record["range"]["offset"], record["range"]["length"]
        ) == want_range


def test_chunk_golden_set_covers_both_revision24_chunk_descriptions() -> None:
    assert {record["storage_kind"] for record in _records()} == {1, 5}
