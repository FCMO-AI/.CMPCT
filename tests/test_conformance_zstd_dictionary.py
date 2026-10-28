from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


VECTOR = Path(__file__).with_name("conformance") / "v24-zstd-dictionary.json"


def _record() -> dict:
    payload = json.loads(VECTOR.read_text())
    assert payload["schema"] == "cmpct-v24-golden-zstd-dictionary-v1"
    assert payload["format_revision"] == 24
    return payload["vector"]


def test_fixed_zstd_dictionary_vector_is_byte_stable_and_readable(tmp_path: Path) -> None:
    """Freeze codec-3 bytes independently of the current encoder.

    Footnote: dictionary compression couples two physical blobs through the authenticated `dict_blob`
    index field. A builder-to-reader round trip can accidentally move both sides together; this fixed
    archive instead makes future Python/native readers consume one immutable dictionary relationship.
    """
    record = _record()
    archive_bytes = base64.b64decode(record["archive_base64"], validate=True)
    assert len(archive_bytes) == record["archive_bytes"]
    assert hashlib.sha256(archive_bytes).hexdigest() == record["archive_sha256"]

    archive = tmp_path / "golden-zstd-dictionary.cmpct"
    archive.write_bytes(archive_bytes)

    summary = preflight_archive(archive)
    assert summary["version"] == 24
    assert summary["files"] == 1
    assert summary["blobs"] == 2

    expected_range = bytes.fromhex(record["range"]["hex"])
    with CMPCT(archive) as ar:
        assert ar.dict_idx == record["dictionary_blob"]
        assert ar.blobs[ar.dict_idx][1] == record["dictionary_size"]
        row = ar.by[record["name"]]
        assert row[4] == record["logical_size"]
        assert row[6][0] == 0  # direct S_BLOB
        blob = ar.blobs[row[6][1]]
        assert blob[3] == record["codec"] == 3
        raw = ar.read(record["name"])
        assert hashlib.sha256(raw).hexdigest() == record["logical_sha256"]
        assert ar.read_range(
            record["name"], record["range"]["offset"], record["range"]["length"]
        ) == expected_range

        dictionary = ar._blob(ar.dict_idx)
        assert hashlib.sha256(dictionary).hexdigest() == record["dictionary_sha256"]
