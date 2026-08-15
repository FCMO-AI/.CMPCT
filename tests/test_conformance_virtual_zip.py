from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile
from pathlib import Path

from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


VECTOR = Path(__file__).with_name("conformance") / "v24-virtual-zip.json"


def _record() -> dict:
    payload = json.loads(VECTOR.read_text())
    assert payload["schema"] == "cmpct-v24-golden-virtual-zip-v1"
    assert payload["format_revision"] == 24
    return payload["vector"]


def test_fixed_virtual_zip_vector_is_byte_stable_and_structurally_valid(tmp_path: Path) -> None:
    """Freeze S_VZIP bytes independently of the encoder before native implementation.

    Footnote: builder round-trips cannot detect shared mistakes in recipe emission and reconstruction.
    This archive is hand-built from the revision-24 framing/schema and therefore remains an external
    acceptance target when encoder heuristics change.
    """
    record = _record()
    archive_bytes = base64.b64decode(record["archive_base64"], validate=True)
    assert len(archive_bytes) == record["archive_bytes"]
    assert hashlib.sha256(archive_bytes).hexdigest() == record["archive_sha256"]

    archive = tmp_path / "golden-virtual-zip.cmpct"
    archive.write_bytes(archive_bytes)
    summary = preflight_archive(archive)
    assert summary["version"] == 24
    assert summary["files"] == 1
    assert summary["blobs"] == 2

    with CMPCT(archive) as ar:
        row = ar.by[record["name"]]
        assert row[4] == record["logical_size"]
        assert row[6][0] == record["storage_kind"] == 2
        recipe = ar.recipes[row[6][1]]
        assert recipe[0] == record["recipe"]["skeleton_blob"]
        assert recipe[1] == record["recipe"]["literal_lengths"]
        assert [payload[2] for payload in recipe[2]] == record["recipe"]["payload_stream_modes"]


def test_fixed_virtual_zip_vector_reconstructs_and_ranges_exactly(tmp_path: Path) -> None:
    record = _record()
    archive = tmp_path / "golden-virtual-zip.cmpct"
    archive.write_bytes(base64.b64decode(record["archive_base64"], validate=True))

    with CMPCT(archive) as ar:
        nested = ar.read(record["name"])
        assert len(nested) == record["logical_size"]
        assert hashlib.sha256(nested).hexdigest() == record["logical_sha256"]
        for expected in record["ranges"]:
            got = ar.read_range(record["name"], expected["offset"], expected["length"])
            assert got == bytes.fromhex(expected["hex"])

    # The reconstructed logical file must remain a standards-compatible ZIP, not merely a byte blob
    # that happens to satisfy CMPCT's own recipe checks.
    with zipfile.ZipFile(io.BytesIO(nested)) as zf:
        member = record["member"]
        raw = zf.read(member["name"])
        assert len(raw) == member["logical_size"]
        assert hashlib.sha256(raw).hexdigest() == member["logical_sha256"]
