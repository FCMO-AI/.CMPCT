"""O10R: source-authenticated r24 journal resource ceilings, ordinary Reader vs strict preflight.

Expected to fail on inherited O9 Reader before corrective implementation. Do not
weaken this test: a valid index hash and compressed metadata can still demand
unbounded Reader work if its *decoded* size/depth declaration is trusted.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from cmpct.builder import Builder
from cmpct.codec import FTR
from cmpct.reader import CMPCT
from cmpct.transactions import _append_generation
from cmpct.validation import ResourceLimitError, preflight_archive


def _source(tmp_path: Path) -> Path:
    src = tmp_path / "input"
    src.mkdir()
    (src / "payload.txt").write_bytes(b"O10R-AUTHENTIC-GENERATION-CONTROL" * 7)
    archive = tmp_path / "real-builder.cmpct"
    Builder(src, workers=1, reproducible=True).build(archive)
    assert preflight_archive(archive)["files"] == 1
    with CMPCT(archive) as reader:
        assert reader.read("payload.txt") == (src / "payload.txt").read_bytes()
    return archive


def test_reader_enforces_decoded_authenticated_generation_limit_before_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = _source(tmp_path)
    with CMPCT(archive) as reader:
        previous_footer = reader.latest_footer_pos
        original = reader.read("payload.txt")

    # Valid, deliberately repetitive operations: the resulting logical tree is
    # the same but the signed generation's decoded MessagePack is much larger.
    footer_pos, _ = _append_generation(
        archive,
        {"blobs": [], "ops": [["ren", "absent.bin", "ignored.bin"]] * 1200},
        previous_footer,
    )
    with archive.open("rb") as stream:
        stream.seek(footer_pos)
        magic, kind, codec, flags, reserved, csize, usize, prev, digest = FTR.unpack(
            stream.read(FTR.size)
        )
    assert kind == 1 and codec == 1 and usize > 8192 and csize < usize
    assert prev == previous_footer
    with CMPCT(archive) as unbounded:
        assert unbounded.delta_depth == 1
        assert unbounded.read("payload.txt") == original
    assert preflight_archive(archive)["delta_depth"] == 1

    # A valid authenticated compressed generation must not bypass the same
    # resource policy in ordinary Reader simply because its compressed bytes fit.
    monkeypatch.setenv("CMPCT_MAX_GENERATION_BYTES", "8192")
    with pytest.raises(ResourceLimitError, match="generation|limit"):
        preflight_archive(archive)
    with pytest.raises(OSError, match="generation|limit"):
        CMPCT(archive)


def test_reader_enforces_authenticated_delta_chain_depth_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive = _source(tmp_path)
    with CMPCT(archive) as original:
        prev = original.latest_footer_pos
        payload = original.read("payload.txt")
    for name in ("absent-one.bin", "absent-two.bin"):
        prev, _ = _append_generation(
            archive,
            {"blobs": [], "ops": [["ren", name, "unused.bin"]]},
            prev,
        )
    with CMPCT(archive) as valid:
        assert valid.delta_depth == 2
        assert valid.read("payload.txt") == payload
    assert preflight_archive(archive)["delta_depth"] == 2

    monkeypatch.setenv("CMPCT_MAX_DELTA_DEPTH", "1")
    with pytest.raises(ResourceLimitError, match="generation|chain|depth|limit"):
        preflight_archive(archive)
    with pytest.raises(OSError, match="generation|chain|depth|limit"):
        CMPCT(archive)
