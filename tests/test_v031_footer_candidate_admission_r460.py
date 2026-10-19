"""Source-pinned revision-24 journal recovery regression.

The 501-byte physical seed was independently constructed outside cmpct.Builder
and frozen in R452/R453 (SHA-256 2d300fa483f7b664fa0df38868841ced04bf619c76809c89e873396ace5e94fa).
A later footer's correct SHA-256 is NOT sufficient to make its semantic payload
a committed generation. Keep this test RED if that fallback invariant fails.
No production reader/parser code or format rules are modified by this court.
"""
from __future__ import annotations

import base64
import hashlib
import struct

import msgpack
import pytest

from cmpct.reader import CMPCT

SEED = base64.b64decode(
    "Q01QQ1QyNAAYAAAAawAAAAAAAABeAAAAAAAAAJcAAAAAAAAAqqe5o0oziTRktXV/jha1+pmBrgtPauanNtwXTX/ZSN0otS/9BGjxAgCEoXYYpWZpbGVzkZeqbWVtYmVyLmJpbgDNAaQACMQgmsIZfZJYJXsa6EY+QhTkzQpXi8FRfyQVkouRvkKD/EiSAAClYmxvYnOSlQAICAAAlUgPDwAAp3JlY2lwZXOQeBstfUNNQTQAAAAACAAAAAAAAAAIAAAAAAAAAAAAAAActtxomsIZfZJYJXsa6EY+QhTkzQpXi8FRfyQVkouRvkKD/EhBQkNERUZHSENNQTQAAAAADwAAAAAAAAAPAAAAAAAAAAAAAAD/Fpr1EQPzZ5WApTvlRwrj9JcrhdzYaEBatK6wWXXJuFHNrHZzZWNvbmQtcmF3LWJsb2IotS/9BGjxAgCEoXYYpWZpbGVzkZeqbWVtYmVyLmJpbgDNAaQACMQgmsIZfZJYJXsa6EY+QhTkzQpXi8FRfyQVkouRvkKD/EiSAAClYmxvYnOSlQAICAAAlUgPDwAAp3JlY2lwZXOQeBstfUNNUFRGMjQAAAEAAGsAAAAAAAAAXgAAAAAAAAAAAAAAAAAAAKqnuaNKM4k0ZLV1f44WtfqZga4LT2rmpzbcF01/2Ujd"
)
FOOTER = struct.Struct("<8sBBBBQQQ32s")
OLD_FOOTER = 433
SEED_SHA256 = "2d300fa483f7b664fa0df38868841ced04bf619c76809c89e873396ace5e94fa"


def _archive_with_generation(payload: bytes, *, kind: int = 0, prev: int = 0) -> bytes:
    # Framing and SHA are deliberately correct; rejection must be semantic.
    footer = FOOTER.pack(
        b"CMPTF24\0", kind, 0, 0, 0, len(payload), len(payload),
        prev, hashlib.sha256(payload).digest(),
    )
    return SEED + payload + footer


def test_frozen_root_is_readable(tmp_path):
    assert len(SEED) == 501
    assert hashlib.sha256(SEED).hexdigest() == SEED_SHA256
    path = tmp_path / "original.cmpct"
    path.write_bytes(SEED)
    with CMPCT(path) as reader:
        assert reader.latest_footer_pos == OLD_FOOTER
        assert reader.read("member.bin") == b"ABCDEFGH"
        assert reader.read_range("member.bin", 2, 4) == b"CDEF"


@pytest.mark.parametrize(
    ("name", "kind", "payload", "prev"),
    [
        ("checkpoint_bad_msgpack", 0, b"\xc1\xc1", 0),
        ("checkpoint_array", 0, msgpack.packb(["not-a-map"], use_bin_type=True), 0),
        ("delta_bad_msgpack", 1, b"\xc1\xc1", OLD_FOOTER),
        ("delta_array", 1, msgpack.packb(["not-a-map"], use_bin_type=True), OLD_FOOTER),
    ],
)
def test_semantically_invalid_new_tail_preserves_previous_commit(
    tmp_path, name, kind, payload, prev
):
    path = tmp_path / f"{name}.cmpct"
    path.write_bytes(_archive_with_generation(payload, kind=kind, prev=prev))
    with CMPCT(path) as reader:
        assert reader.latest_footer_pos == OLD_FOOTER
        assert reader.read("member.bin") == b"ABCDEFGH"
        assert reader.read_range("member.bin", 2, 4) == b"CDEF"


def test_valid_new_checkpoint_is_not_ignored(tmp_path):
    payload = msgpack.packb({"v": 24, "files": [], "blobs": [], "recipes": []}, use_bin_type=True)
    path = tmp_path / "valid_checkpoint.cmpct"
    path.write_bytes(_archive_with_generation(payload))
    with CMPCT(path) as reader:
        assert reader.latest_footer_pos == len(SEED) + len(payload)
        assert reader.files == []
        assert reader.delta_depth == 0
