from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


VECTORS = (
    ("v24-virtual-zip.json", "cmpct-v24-golden-virtual-zip-v1"),
    (
        "v24-virtual-zip-deflate-mode1.json",
        "cmpct-v24-golden-virtual-zip-deflate-mode1-v1",
    ),
)


def _record(filename: str, schema: str) -> dict:
    vector = Path(__file__).with_name("conformance") / filename
    payload = json.loads(vector.read_text())
    assert payload["schema"] == schema
    assert payload["format_revision"] == 24
    return payload["vector"]


@pytest.mark.parametrize(("filename", "schema"), VECTORS)
def test_fixed_virtual_zip_vector_is_byte_stable_and_structurally_valid(
    tmp_path: Path, filename: str, schema: str
) -> None:
    """Freeze S_VZIP bytes independently of the encoder before native implementation.

    Footnote: builder round-trips cannot detect shared mistakes in recipe emission and reconstruction.
    These archives are hand-built from revision-24 framing/schema rules and therefore remain external
    acceptance targets when encoder heuristics change.
    """
    record = _record(filename, schema)
    archive_bytes = base64.b64decode(record["archive_base64"], validate=True)
    assert len(archive_bytes) == record["archive_bytes"]
    assert hashlib.sha256(archive_bytes).hexdigest() == record["archive_sha256"]

    archive = tmp_path / f"golden-{Path(filename).stem}.cmpct"
    archive.write_bytes(archive_bytes)
    summary = preflight_archive(archive)
    assert summary["version"] == 24
    assert summary["files"] == 1
    assert summary["blobs"] == (2 if record["member"]["method"] == 0 else 3)

    with CMPCT(archive) as ar:
        row = ar.by[record["name"]]
        assert row[4] == record["logical_size"]
        assert row[6][0] == record["storage_kind"] == 2
        recipe = ar.recipes[row[6][1]]
        assert recipe[0] == record["recipe"]["skeleton_blob"]
        assert recipe[1] == record["recipe"]["literal_lengths"]
        assert [payload[2] for payload in recipe[2]] == record["recipe"]["payload_stream_modes"]


@pytest.mark.parametrize(("filename", "schema"), VECTORS)
def test_fixed_virtual_zip_vector_reconstructs_and_ranges_exactly(
    tmp_path: Path, filename: str, schema: str
) -> None:
    record = _record(filename, schema)
    archive = tmp_path / f"golden-{Path(filename).stem}.cmpct"
    archive.write_bytes(base64.b64decode(record["archive_base64"], validate=True))

    with CMPCT(archive) as ar:
        nested = ar.read(record["name"])
        assert len(nested) == record["logical_size"]
        assert hashlib.sha256(nested).hexdigest() == record["logical_sha256"]
        for expected in record["ranges"]:
            got = ar.read_range(record["name"], expected["offset"], expected["length"])
            assert got == bytes.fromhex(expected["hex"])

    # The reconstructed logical file must remain a standards-compatible ZIP, not merely a byte blob
    # that happens to satisfy CMPCT's own recipe checks. The mode-1 vector additionally proves that the
    # retained exact RFC-1951 bytes form the nested member stream accepted by an independent ZIP reader.
    with zipfile.ZipFile(io.BytesIO(nested)) as zf:
        member = record["member"]
        raw = zf.read(member["name"])
        assert len(raw) == member["logical_size"]
        assert hashlib.sha256(raw).hexdigest() == member["logical_sha256"]
