from pathlib import Path

import pytest

from cmpct.core import Builder, CMPCT
from cmpct.codec import S_CDC, S_CHUNKS


def _large_payload() -> bytes:
    # Large enough to force the chunked path even when the optional native CDC helper is unavailable.
    block = (b"CMPCT streaming extraction parity regression\n" * 8192)
    return (block * 8)[: 3 * 1024 * 1024]


def test_chunked_extract_streams_exact_bytes(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    payload = _large_payload()
    (src / "large.bin").write_bytes(payload)

    archive = tmp_path / "large.cmpct"
    Builder(src).build(archive)

    out = tmp_path / "out"
    with CMPCT(archive) as ar:
        assert ar.by["large.bin"][6][0] in (S_CHUNKS, S_CDC)
        ar.extractall(out, metadata=False)

    assert (out / "large.bin").read_bytes() == payload


def test_corrupt_chunk_does_not_replace_existing_destination(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "large.bin").write_bytes(_large_payload())
    archive = tmp_path / "large.cmpct"
    Builder(src).build(archive)

    out = tmp_path / "out"
    out.mkdir()
    final = out / "large.bin"
    final.write_bytes(b"KEEP-EXISTING")

    with CMPCT(archive) as ar:
        storage = ar.by["large.bin"][6]
        assert storage[0] in (S_CHUNKS, S_CDC)
        ids = storage[1] if storage[0] == S_CHUNKS else [entry[1] for entry in storage[1]]
        corrupt_id = ids[0]
        original_blob = ar._blob

        def corrupt_one(idx: int) -> bytes:
            raw = original_blob(idx)
            if idx != corrupt_id or not raw:
                return raw
            # Footnote: preserve the chunk length so the test reaches the whole-file SHA gate rather
            # than succeeding merely because the simpler per-chunk length invariant detected damage.
            return bytes([raw[0] ^ 0x01]) + raw[1:]

        ar._blob = corrupt_one
        with pytest.raises(IOError, match="file integrity failure"):
            ar.extractall(out, metadata=False)

    # Footnote: the previous implementation verified before opening the destination. Streaming must
    # preserve that safety property, so bytes are staged beside the target and committed atomically.
    assert final.read_bytes() == b"KEEP-EXISTING"
    assert not list(out.glob(".*.cmpct-part-*"))
