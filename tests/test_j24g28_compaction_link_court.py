"""J24G28: authentic r24 compaction/link acceptance control, science only.

Run with pytest. Do not modify the Reader, Writer, Builder, format or historical
evaluator. A positive test demonstrates a source-exact incompatibility, not a
general repair or filesystem safety proof.
"""
import hashlib
import os
from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.transactions import compact_archive


@pytest.mark.parametrize(
    "target,should_fail",
    [
        ("/definitely-not-a-real-cmpct-compaction-target", True),
        ("../definitely-not-a-real-cmpct-compaction-target", True),
        ("owner.txt", False),
    ],
)
def test_compaction_rejects_valid_unsafe_link_but_preserves_source(
    tmp_path: Path, target: str, should_fail: bool
) -> None:
    if os.name != "posix":
        pytest.skip("physical symlink court requires POSIX to avoid privilege-dependent results")
    source = tmp_path / "input"
    source.mkdir()
    (source / "owner.txt").write_bytes(b"actual logical payload bytes")
    (source / "link").symlink_to(target)
    original = tmp_path / "original.cmpct"
    compacted = tmp_path / "compacted.cmpct"
    Builder(source).build(original)
    source_bytes = original.read_bytes()
    original_sha = hashlib.sha256(source_bytes).hexdigest()
    with CMPCT(original) as ar:
        assert ar.read("link") == os.fsencode(target)
        assert ar.read("owner.txt") == b"actual logical payload bytes"
        assert ar.verify() >= 1
    if should_fail:
        with pytest.raises(IOError, match="unsafe symlink target"):
            compact_archive(original, compacted)
        assert not compacted.exists()
    else:
        compact_archive(original, compacted)
        assert compacted.is_file()
        with CMPCT(compacted) as ar:
            assert ar.read("link") == os.fsencode(target)
            assert ar.read("owner.txt") == b"actual logical payload bytes"
            assert ar.verify() >= 1
    assert original.read_bytes() == source_bytes
    assert hashlib.sha256(original.read_bytes()).hexdigest() == original_sha
    assert os.readlink(source / "link") == target
