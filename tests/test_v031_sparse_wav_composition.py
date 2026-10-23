"""Integrated source-identity court: existing WAV admission + sparse acquisition.

Unlike the individual owner tests this exercises all representations inside
one real revision-24 archive, and separately checks source bytes, stable
reproducible output, and the Reader's internal verification result.
"""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
import struct
import wave

from cmpct.builder import Builder
from cmpct.codec import wavflac_compress
from cmpct.reader import CMPCT


def _wav(*, sample_width: int) -> bytes:
    """Produce standards-conforming PCM WAV without relying on a codec library."""
    frames = 16_384
    buf = io.BytesIO()
    with wave.open(buf, "wb") as dst:
        dst.setnchannels(1)
        dst.setsampwidth(sample_width)
        dst.setframerate(22_050)
        if sample_width == 2:
            samples = b"".join(struct.pack("<h", (i * 7919 % 65536) - 32768) for i in range(frames))
        elif sample_width == 3:
            samples = b"".join(((i * 19937) & 0xFFFFFF).to_bytes(3, "little") for i in range(frames))
        else:
            assert sample_width == 4
            samples = b"".join(struct.pack("<i", (i * 11939 % (2**32)) - (2**31)) for i in range(frames))
        dst.writeframes(samples)
    return buf.getvalue()


def test_sparse_and_supported_unsupported_wav_share_one_exact_archive(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    p = root / "sparse.bin"
    with p.open("wb") as fh:
        fh.truncate(2 << 20)
        fh.seek(1 << 20)
        fh.write(b"NONZERO-SOURCE-IDENTITY" * 277)
    (root / "pcm16.wav").write_bytes(_wav(sample_width=2))
    pcm24 = _wav(sample_width=3)
    assert wavflac_compress(pcm24) is None, "unsupported PCM24 must use lossless fallback"
    (root / "pcm24.wav").write_bytes(pcm24)
    pcm32 = _wav(sample_width=4)
    # The historical WAV/FLAC candidate attempted an unsupported PCM_32 backend
    # conversion. PR #229 must refuse that optional codec before backend import.
    assert wavflac_compress(pcm32) is None, "unsupported PCM32 must not abort archive creation"
    (root / "pcm32.wav").write_bytes(pcm32)

    original = {p.name: p.read_bytes() for p in sorted(root.iterdir())}
    origin_sha = {name: hashlib.sha256(data).digest() for name, data in original.items()}
    epoch_ns = 1_729_468_800_000_000
    for member in root.iterdir():
        os.utime(member, ns=(epoch_ns, epoch_ns))

    archives = []
    for workers in (1, 2):
        dest = tmp_path / f"mixed-{workers}.cmpct"
        Builder(root, workers=workers, reproducible=True,
                reproducible_epoch_ns=epoch_ns).build(dest)
        archives.append(dest.read_bytes())
        with CMPCT(dest) as reader:
            assert reader.verify() == len(original)
            for name, data in original.items():
                rebuilt = reader.read(name)
                assert rebuilt == data
                assert hashlib.sha256(rebuilt).digest() == origin_sha[name]
    assert archives[0] == archives[1], "worker count cannot change archived bytes"
