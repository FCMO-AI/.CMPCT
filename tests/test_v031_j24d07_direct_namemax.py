"""J24D07: authentic r24 direct S_BLOB with a maximal POSIX basename.

This is a source-level and filesystem regression, not a general namespace-adversary
claim. J24D02's original ENOSPC rollback contract remains independently owned.
"""
from __future__ import annotations

import errno
import hashlib
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

import pytest

from cmpct.builder import Builder
from cmpct.codec import S_BLOB
from cmpct.reader import CMPCT


@pytest.mark.skipif(os.name != "posix", reason="POSIX NAME_MAX boundary")
def test_direct_staged_extract_full_posix_namemax_and_enospc_rollback(tmp_path: Path):
    # Canonical POSIX boundary: name has 255 bytes, not 255 Unicode codepoints.
    name = "n" * 251 + ".bin"
    assert len(os.fsencode(name)) == 255
    if os.pathconf(tmp_path, "PC_NAME_MAX") < 255:
        pytest.skip("this filesystem cannot represent a 255-byte basename")

    # The inexpensive syscall oracle fails for the inherited long-name prefix,
    # but succeeds for the chosen constant sibling prefix. This is independent
    # of CMPCT's parser and is not credited as product validation.
    with pytest.raises(OSError) as too_long:
        tempfile.mkstemp(prefix=f".{name}.cmpct-part-", dir=tmp_path)
    assert too_long.value.errno == errno.ENAMETOOLONG
    probe_fd, probe_path = tempfile.mkstemp(prefix=".cmpct-part-", dir=tmp_path)
    os.close(probe_fd)
    Path(probe_path).unlink()

    src = tmp_path / "source"
    src.mkdir()
    # Deterministic incompressible-like bytes ensure a genuine direct S_BLOB.
    raw = b"".join(hashlib.sha256(b"J24D07" + i.to_bytes(4, "little")).digest()
                   for i in range(2048))
    assert len(raw) == 65536
    (src / name).write_bytes(raw)
    digest = hashlib.sha256(raw).digest()
    archive = tmp_path / "long-name.cmpct"
    Builder(src, workers=1, reproducible=True).build(archive)
    dest = tmp_path / "output"
    dest.mkdir()
    target = dest / name
    with CMPCT(archive) as reader:
        assert reader.by[name][6][0] == S_BLOB
        assert reader.read(name) == raw
        assert reader.verify() == 1

        # An ordinarily writable 255-byte destination must be publishable.
        reader.extractall(dest, metadata=False)
        assert target.read_bytes() == raw
        assert hashlib.sha256(target.read_bytes()).digest() == digest
        assert sorted(dest.iterdir()) == [target]

        # Existing destination success is a separate publication branch.
        prior = b"J24D07 PRIOR TARGET\n" * 5
        target.write_bytes(prior)
        reader.extractall(dest, metadata=False)
        assert target.read_bytes() == raw
        assert sorted(dest.iterdir()) == [target]

        # Fail *after* one real kernel write, not before opening the stage;
        # the 255-byte existing target must retain its bytes and inode.
        target.write_bytes(prior)
        prior_inode = target.stat().st_ino
        original_write = os.write
        writes = []

        def injected_write(fd, data):
            writes.append(len(data))
            if len(writes) == 1:
                return original_write(fd, memoryview(data)[:7])
            raise OSError(errno.ENOSPC, "J24D07 injected disk full")

        with patch("cmpct.reader.os.write", side_effect=injected_write):
            with pytest.raises(OSError) as failed:
                reader.extractall(dest, metadata=False)
        assert failed.value.errno == errno.ENOSPC
        assert len(writes) == 2
        assert target.read_bytes() == prior
        assert target.stat().st_ino == prior_inode
        assert sorted(dest.iterdir()) == [target]

        # Recovery after fault must not poison Reader or leave a colliding stage.
        reader.extractall(dest, metadata=False)
        assert target.read_bytes() == raw
        assert sorted(dest.iterdir()) == [target]
