"""An in-band footer inside primary RAW data is not a committed generation.

Builder-independent revision-24 physical witness. This is deliberately scoped
to primary data; it does not certify crash-tail/apparent-footer disambiguation.
"""
import binascii
import msgpack
import pytest

from cmpct.codec import (BHDR, BMAGIC, CODEC_RAW, FMAGIC, FTR, HDR, MAGIC,
                         S_BLOB, K_FILE, VERSION, sha, zc)
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


@pytest.mark.parametrize("form", ["oversized", "phantom"])
def test_footer_magic_inside_primary_raw_blob_is_data(tmp_path, form):
    phantom_index = msgpack.packb(
        {"v": VERSION, "files": [], "blobs": [], "recipes": []},
        use_bin_type=True,
    )
    if form == "oversized":
        injection = FTR.pack(FMAGIC, 0, 0, 0, 0, 0, 256 * 1024 * 1024 + 1,
                             0, bytes(32))
    else:
        injection = phantom_index + FTR.pack(
            FMAGIC, 0, 0, 0, 0, len(phantom_index), len(phantom_index),
            0, sha(phantom_index),
        )
    content = b"ordinary-user-content:" + injection + b":unchanged"
    index = {
        "v": VERSION,
        "files": [["payload.bin", K_FILE, 0o644, 0, len(content),
                    sha(content), [S_BLOB, 0]]],
        "blobs": [[0, len(content), len(content), CODEC_RAW, 0]],
        "recipes": [],
    }
    primary_index = msgpack.packb(index, use_bin_type=True)
    encoded = zc(primary_index, 3)
    physical = BHDR.pack(
        BMAGIC, CODEC_RAW, 0, 0, len(content), len(content),
        0, binascii.crc32(content) & 0xffffffff, sha(content),
    ) + content
    archive = tmp_path / "primary-only.cmpct"
    archive.write_bytes(HDR.pack(MAGIC, VERSION, 0, len(encoded),
                                 len(primary_index), len(physical),
                                 sha(primary_index)) + encoded + physical)
    with CMPCT(archive) as reader:
        assert reader.latest_footer_pos == 0
        assert list(reader.by) == ["payload.bin"]
        assert reader.read("payload.bin") == content
    assert preflight_archive(archive)["latest_footer"] == 0
