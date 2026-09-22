from __future__ import annotations

import io
import zipfile
from pathlib import Path

from cmpct.builder import Builder
from cmpct.reader import CMPCT
from cmpct.validation import preflight_archive


def test_shipping_builder_emits_current_vzip_schema_and_roundtrips(tmp_path: Path) -> None:
    """Writer->independent validator/reader regression for revision-24 S_VZIP.

    Golden reader vectors cannot catch an encoder that still emits an older payload shape.
    Keep fewer than eight ZIPs so Builder selects S_VZIP rather than S_PACK.
    """
    source = tmp_path / "source"
    source.mkdir()
    nested = source / "payload.zip"
    with zipfile.ZipFile(nested, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("hello.txt", (b"exact-vzip-schema\n" * 4096))
    expected = nested.read_bytes()

    archive = tmp_path / "out.cmpct"
    Builder(source).build(archive)

    summary = preflight_archive(archive)
    assert summary["version"] == 24
    with CMPCT(archive) as ar:
        row = ar.by["payload.zip"]
        assert row[6][0] == 2  # S_VZIP
        recipe = ar.recipes[row[6][1]]
        assert recipe[2]
        assert all(len(payload) == 6 for payload in recipe[2])
        assert all(payload[2] in (0, 1, 2) for payload in recipe[2])
        assert ar.read("payload.zip") == expected
        assert ar.read_range("payload.zip", 17, min(4096, len(expected) - 17)) == expected[17:17 + min(4096, len(expected) - 17)]

    with zipfile.ZipFile(io.BytesIO(expected)) as zf:
        assert zf.read("hello.txt") == (b"exact-vzip-schema\n" * 4096)
