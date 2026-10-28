from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import pytest

from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


VECTOR = Path(__file__).with_name("conformance") / "v24-wavflac.json"


def _record() -> dict:
    payload = json.loads(VECTOR.read_text())
    assert payload["schema"] == "cmpct-v24-golden-wavflac-v1"
    assert payload["format_revision"] == 24
    return payload["vector"]


def test_fixed_wavflac_vector_is_byte_stable_and_structurally_valid(tmp_path: Path) -> None:
    """Freeze codec-2 bytes independently of the Python builder before native implementation.

    Footnote: codec 2 stores a FLAC payload plus MessagePack metadata containing the exact WAV
    prefix/suffix required for byte-for-byte reconstruction. Keeping the complete archive as base64
    prevents a future encoder refactor from silently regenerating the conformance target.
    """
    record = _record()
    archive_bytes = base64.b64decode(record["archive_base64"], validate=True)
    assert len(archive_bytes) == record["archive_bytes"]
    assert hashlib.sha256(archive_bytes).hexdigest() == record["archive_sha256"]

    archive = tmp_path / "golden-wavflac.cmpct"
    archive.write_bytes(archive_bytes)
    summary = preflight_archive(archive)
    assert summary["version"] == 24
    assert summary["files"] == 1
    assert summary["blobs"] == 1

    with CMPCT(archive) as ar:
        row = ar.by[record["name"]]
        assert row[4] == record["logical_size"]
        assert row[6][0] == 0  # direct S_BLOB
        assert ar.blobs[row[6][1]][3] == record["codec"] == 2


def test_fixed_wavflac_vector_reconstructs_exact_wav_bytes(tmp_path: Path) -> None:
    # The audio extras are optional for ordinary CMPCT installs. Native-core CI installs them so this
    # fixed oracle is always decoded there; environments without the optional codec may skip cleanly.
    pytest.importorskip("numpy")
    pytest.importorskip("soundfile")

    record = _record()
    archive = tmp_path / "golden-wavflac.cmpct"
    archive.write_bytes(base64.b64decode(record["archive_base64"], validate=True))
    expected_range = bytes.fromhex(record["range"]["hex"])

    with CMPCT(archive) as ar:
        raw = ar.read(record["name"])
        assert len(raw) == record["logical_size"]
        assert hashlib.sha256(raw).hexdigest() == record["logical_sha256"]
        assert ar.read_range(
            record["name"], record["range"]["offset"], record["range"]["length"]
        ) == expected_range
