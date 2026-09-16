from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_geometry_overlay_g04 as research
from experiments import entropygraph_v030_geometry_overlay_g04_publish as release


def _fixture(root: Path) -> None:
    root.mkdir(parents=True)
    rows = [f"{index:05d},region-{index % 3},metric-{index % 11:03d}\n" for index in range(2500)]
    body = "".join(rows).encode()
    (root / "events-a.csv").write_bytes(body)
    (root / "events-b.csv").write_bytes(body.replace(b"region-2", b"region-7"))


def test_release_publication_wrapper_is_byte_identical(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _fixture(source)
    research_archive = tmp_path / "research.cmpct"
    release_archive = tmp_path / "release.cmpct"

    research_stats = research.build(source, research_archive)
    release_stats = release.build(source, release_archive)

    assert release_archive.read_bytes() == research_archive.read_bytes()
    assert release_stats["archive_bytes"] == research_stats["archive_bytes"]
    assert release_stats["v029_bytes"] == research_stats["v029_bytes"]
    assert release_stats["selected"] == research_stats["selected"]
    assert release_stats["saving_vs_v029_bytes"] == research_stats["saving_vs_v029_bytes"]
    assert release_stats["publication_identity_check"] == "streamed-sha256"
    assert release_stats["publication_hash_block_bytes"] == 1024 * 1024
    assert release_stats["selection_extra_payload_write_bytes"] == 0


def test_stream_hash_block_is_bounded(tmp_path: Path) -> None:
    path = tmp_path / "payload.bin"
    path.write_bytes(b"x" * 4097)
    assert release._sha256_file(path, block_bytes=1024) == release._sha256_file(path, block_bytes=2048)
    for invalid in (0, -1, 8 * 1024 * 1024 + 1):
        try:
            release._sha256_file(path, block_bytes=invalid)
        except ValueError:
            pass
        else:  # pragma: no cover
            raise AssertionError("expected bounded stream-hash block rejection")
