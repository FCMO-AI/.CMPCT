"""J24B03-H4: direct Deflate ZIP export may not bypass physical header custody."""
from __future__ import annotations
import binascii
import hashlib
from pathlib import Path
import struct
import zipfile
import zlib

import msgpack
import pytest

from cmpct.codec import (BHDR, BMAGIC, CODEC_DEFLATE, FTR, FMAGIC, HDR, MAGIC,
                         K_FILE, K_SYMLINK, S_BLOB, VERSION, zc)
from cmpct.core import CMPCT
from cmpct.validation import ValidationError, preflight_archive

PAYLOAD = (b"safe-target-0123456789/" * 8)[:128]


def signed_wire(kind: int, declared: int = 128):
    member = "direct.bin" if kind == K_FILE else "link"
    co = zlib.compressobj(6, zlib.DEFLATED, -15)
    stream = co.compress(PAYLOAD) + co.flush()
    index = {"v": VERSION, "files": [[member, kind, 0o644, 0, declared,
                                     None, [S_BLOB, 0]]],
             "blobs": [[0, len(PAYLOAD), len(stream), CODEC_DEFLATE, 0]],
             "recipes": [], "dict_blob": None,
             "fsmeta": {"owner": [0, 0], "owner_overrides": [], "xattrs": []},
             "features": []}
    uncompressed = msgpack.packb(index, use_bin_type=True)
    encoded = zc(uncompressed, 3)
    h = hashlib.sha256(uncompressed).digest()
    frame = BHDR.pack(BMAGIC, CODEC_DEFLATE, 0, 0, len(PAYLOAD), len(stream), 0,
                      binascii.crc32(PAYLOAD) & 0xffffffff,
                      hashlib.sha256(PAYLOAD).digest()) + stream
    header = HDR.pack(MAGIC, VERSION, 0, len(encoded), len(uncompressed), len(frame), h)
    footer = FTR.pack(FMAGIC, 0, 1, 0, 0, len(encoded), len(uncompressed), 0, h)
    return member, header + encoded + frame + encoded + footer, frame, stream


@pytest.mark.parametrize("kind", [K_FILE, K_SYMLINK], ids=["file", "symlink"])
@pytest.mark.parametrize(("fault", "field", "value"),
                         [("valid", None, None), ("flags-1", 2, 1),
                          ("flags-128", 2, 128), ("reserved-1", 3, 1),
                          ("reserved-65535", 3, 65535), ("signed-size", None, 136)])
def test_fast_deflate_zip_export_respects_physical_owner(tmp_path: Path, kind, fault, field, value):
    member, original, frame, stream = signed_wire(kind)
    if fault == "signed-size":
        _, archive, new_frame, new_stream = signed_wire(kind, declared=136)
        assert new_frame == frame and new_stream == stream
    elif field is None:
        archive = original
    else:
        pos = original.find(frame)
        assert pos >= 0 and original.count(frame) == 1
        header = list(BHDR.unpack_from(frame))
        header[field] = value
        archive = original[:pos] + BHDR.pack(*header) + original[pos + BHDR.size:]
        assert archive[:pos] == original[:pos]
        assert archive[pos + BHDR.size:] == original[pos + BHDR.size:]
        assert len(archive) == len(original)
    path = tmp_path / "source.cmpct"
    out = tmp_path / "output.zip"
    path.write_bytes(archive)
    if fault == "valid":
        assert preflight_archive(path)["files"] == 1
        with CMPCT(path) as reader:
            assert reader.read(member) == PAYLOAD
            assert reader.verify() == 1
            reader.export_zip(out)
        with zipfile.ZipFile(out) as z:
            assert z.namelist() == [member]
            info = z.getinfo(member)
            assert z.read(member) == PAYLOAD
            assert info.compress_type == zipfile.ZIP_DEFLATED
            data = out.read_bytes()
            fields = struct.unpack_from("<IHHHHHIIIHH", data, info.header_offset)
            payload_start = info.header_offset + 30 + fields[-2] + fields[-1]
            assert data[payload_start:payload_start + info.compress_size] == stream
    else:
        with pytest.raises(ValidationError):
            preflight_archive(path)
        with CMPCT(path) as reader:
            with pytest.raises(IOError):
                reader.export_zip(out)
