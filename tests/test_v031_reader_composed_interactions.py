"""Held-out integration: PACK physical SHA + dependency-first hardlinks in one real archive.

This is distinct from the unchanged source-owner tests: it constructs one
Builder archive whose hardlink alias sorts before its PACK-backed owner.
"""
from __future__ import annotations

import hashlib
import os

import pytest

from cmpct.builder import Builder
from cmpct.codec import BHDR, K_HARDLINK, S_PACK
from cmpct.reader import CMPCT


@pytest.mark.skipif(os.name != "posix", reason="inode identity court requires POSIX hardlinks")
def test_pack_backed_hardlink_owner_ignores_index_order_and_authenticates_physical_blob(tmp_path):
    source = tmp_path / "source"
    (source / "a").mkdir(parents=True)
    owner = source / "a" / "owner.bin"
    content = ("owner physical contents shared with packed peers\n" * 90).encode()
    owner.write_bytes(content)
    os.link(owner, source / "a!.bin")
    for i in range(12):
        (source / f"section-{i:02d}.md").write_bytes(
            ((f"section {i}: " + "common explanation " * 16 + "\n") * 17).encode()
        )

    archive = tmp_path / "test.cmpct"
    Builder(source, workers=1, reproducible=True).build(archive)
    with CMPCT(archive) as reader:
        assert reader.by["a!.bin"][1] == K_HARDLINK, "fixture must store a true hardlink alias"
        names = [row[0] for row in reader.files]
        assert names.index("a!.bin") < names.index("a/owner.bin")
        original_owner = reader.by["a/owner.bin"]
        assert original_owner[6][0] == S_PACK, "fixture must exercise a PACK-backed hardlink owner"
        pack_idx = original_owner[6][1]
        assert reader.verify() == len([row for row in reader.files if row[1] != 1])
        physical_header = reader.record_base + reader.blobs[pack_idx][0]
        destination = tmp_path / "output"
        reader.extractall(destination, metadata=False)

    extracted_owner = destination / "a" / "owner.bin"
    extracted_alias = destination / "a!.bin"
    assert extracted_owner.read_bytes() == extracted_alias.read_bytes() == content
    assert os.stat(extracted_owner).st_ino == os.stat(extracted_alias).st_ino
    for i in range(12):
        name = f"section-{i:02d}.md"
        assert (destination / name).read_bytes() == (source / name).read_bytes()

    # The physical PACK SHA is the durable commitment for both the owner and
    # the other packed members. Damage its header without changing CRC/payload.
    image = bytearray(archive.read_bytes())
    image[physical_header + BHDR.size - 1] ^= 1
    archive.write_bytes(image)
    with CMPCT(archive) as reader:
        assert reader.read("a/owner.bin") == content  # ordinary-read CRC tier
        with pytest.raises(OSError, match="physical PACK SHA-256 verification failure"):
            reader.verify()
    assert hashlib.sha256(extracted_alias.read_bytes()).digest() == hashlib.sha256(content).digest()
