from __future__ import annotations

import base64
import hashlib
import json
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VECTOR = ROOT / "tests" / "conformance" / "v24-wavflac.json"
BINARY = ROOT / "native" / "cmpct-core" / "target" / "release" / "cmpct-wavflac-conformance"
HDR = struct.Struct("<8sHHQQQ32s")
BHDR = struct.Struct("<4sBBHQQII32s")


def main() -> None:
    payload = json.loads(VECTOR.read_text())
    assert payload["schema"] == "cmpct-v24-golden-wavflac-v1"
    record = payload["vector"]
    archive = base64.b64decode(record["archive_base64"], validate=True)
    assert hashlib.sha256(archive).hexdigest() == record["archive_sha256"]

    magic, revision, _flags, index_csize, _index_usize, data_span, _index_sha = HDR.unpack_from(archive)
    assert magic == b"CMPCT24\0"
    assert revision == 24
    data_base = HDR.size + index_csize
    assert data_base + data_span <= len(archive)

    bmagic, codec, _bflags, _reserved, usize, csize, meta_len, _crc32, _sha = BHDR.unpack_from(
        archive, data_base
    )
    assert bmagic == b"CMA4"
    assert codec == record["codec"] == 2
    assert usize == record["logical_size"]
    meta_start = data_base + BHDR.size
    payload_start = meta_start + meta_len
    payload_end = payload_start + csize
    assert payload_end <= data_base + data_span

    tmp = Path("/tmp/cmpct-native-wavflac")
    tmp.mkdir(exist_ok=True)
    meta_path = tmp / "meta.msgpack"
    flac_path = tmp / "payload.flac"
    wav_path = tmp / "reconstructed.wav"
    meta_path.write_bytes(archive[meta_start:payload_start])
    flac_path.write_bytes(archive[payload_start:payload_end])

    run = subprocess.run(
        [str(BINARY), str(meta_path), str(flac_path), str(usize), str(wav_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    summary = json.loads(run.stdout)
    wav = wav_path.read_bytes()
    assert summary["logical_size"] == len(wav) == record["logical_size"]
    assert summary["sha256"] == hashlib.sha256(wav).hexdigest() == record["logical_sha256"]

    r = record["range"]
    got = wav[r["offset"] : r["offset"] + r["length"]]
    assert got.hex() == r["hex"]

    # Corrupting authenticated codec metadata is a cheap way to prove the Rust component does not
    # silently guess WAV reconstruction parameters. This test intentionally mutates metadata only;
    # physical SHA enforcement belongs to the archive core when the component is wired into the ABI.
    bad_meta = bytearray(meta_path.read_bytes())
    bad_meta[-1] ^= 1
    bad_meta_path = tmp / "bad-meta.msgpack"
    bad_meta_path.write_bytes(bad_meta)
    failed = subprocess.run(
        [str(BINARY), str(bad_meta_path), str(flac_path), str(usize), str(tmp / "bad.wav")],
        capture_output=True,
        text=True,
    )
    assert failed.returncode != 0


if __name__ == "__main__":
    main()
