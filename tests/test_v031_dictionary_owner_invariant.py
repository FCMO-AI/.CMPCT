"""Revision-24 authenticated Zstd dictionary dependency regression, independent of Builder."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import msgpack
import pytest

from cmpct.codec import CODEC_ZSTDDICT, FMAGIC, FTR, HDR, MAGIC, VERSION, sha, zc, zd
from cmpct.validation import ValidationError, preflight_archive


GOLDEN = Path(__file__).parent / "conformance" / "v24-zstd-dictionary.json"


def _frozen() -> tuple[bytes, str, int]:
    entry = json.loads(GOLDEN.read_text())["vector"]
    data = base64.b64decode(entry["archive_base64"], validate=True)
    assert hashlib.sha256(data).hexdigest() == entry["archive_sha256"]
    return data, entry["name"], entry["logical_size"]


def _authenticated_mutation(data: bytes, dest: Path, dict_id: int) -> None:
    magic, revision, flags, csize, usize, physical_span, _ = HDR.unpack_from(data)
    assert magic == MAGIC and revision == VERSION and flags == 0
    index = msgpack.unpackb(zd(data[HDR.size:HDR.size + csize], usize), raw=False)
    assert index["dict_blob"] == 0
    assert len(index["blobs"]) == 2
    assert index["blobs"][0][3] != CODEC_ZSTDDICT
    assert index["blobs"][1][3] == CODEC_ZSTDDICT
    index["dict_blob"] = dict_id
    payload = msgpack.packb(index, use_bin_type=True)
    encoded = zc(payload, 12)
    digest = sha(payload)
    stored = data[HDR.size + csize:HDR.size + csize + physical_span]
    header = HDR.pack(MAGIC, VERSION, 0, len(encoded), len(payload), len(stored), digest)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(encoded), len(payload), 0, digest)
    dest.write_bytes(header + encoded + stored + encoded + footer)


def test_frozen_dictionary_golden_roundtrip(tmp_path: Path) -> None:
    from cmpct.reader import CMPCT

    data, member, logical_size = _frozen()
    archive = tmp_path / "valid.cmpct"
    archive.write_bytes(data)
    preflight_archive(archive)
    with CMPCT(archive) as reader:
        assert len(reader.read(member)) == logical_size


@pytest.mark.parametrize("dict_id", [1, -1, 2])
def test_authenticated_bad_dictionary_owner_fails_closed(tmp_path: Path, dict_id: int) -> None:
    import cmpct

    data, member, _ = _frozen()
    archive = tmp_path / "invalid.cmpct"
    _authenticated_mutation(data, archive, dict_id)

    # Preflight and ordinary Reader are independent entry points. The hostile index carries
    # valid index/footer digests; only dictionary reference semantics are invalid.
    with pytest.raises(ValidationError):
        preflight_archive(archive)

    probe = "import sys;from cmpct.reader import CMPCT;r=CMPCT(sys.argv[1]);r.read(sys.argv[2])"
    package_root = str(Path(cmpct.__file__).resolve().parent.parent)
    env = dict(os.environ, PYTHONPATH=package_root + os.pathsep + os.environ.get("PYTHONPATH", ""))
    try:
        child = subprocess.run(
            [sys.executable, "-c", probe, str(archive), member],
            capture_output=True, text=True, timeout=3, env=env,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("ordinary Reader deadlocked on authenticated dictionary dependency")
    assert child.returncode != 0
    assert (
        "dictionary blob cannot require its own Zstd dictionary" in child.stderr
        or "invalid Zstd dictionary blob reference" in child.stderr
    )
