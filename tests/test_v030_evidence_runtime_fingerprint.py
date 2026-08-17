from __future__ import annotations

from pathlib import Path

from benchmarks import evidence_runtime_fingerprint as evidence
from experiments import entropygraph_v030_geometry as geometry


def test_runtime_fingerprint_names_serializer_and_native_codec() -> None:
    result = evidence.runtime_fingerprint()
    assert result["python"]
    assert result["python_implementation"]
    assert result["msgpack_python"]
    assert result["libzstd_version"]
    assert result["byteorder"] in ("little", "big")


def test_geometry_archive_fingerprint_closes_complete_size_equation(tmp_path: Path) -> None:
    source = tmp_path / "source"; source.mkdir()
    (source / "table.bin").write_bytes((b"key=000001,tenant=17,status=active,value=123\n" * 4000))
    archive = tmp_path / "geometry.cmpct"
    geometry._build_geometry(source, archive)

    fp = evidence.geometry_archive_fingerprint(archive)
    reconstructed = (
        geometry.HDR.size
        + fp["metadata_compressed_bytes_total"]
        + fp["physical_header_bytes"]
        + fp["physical_payload_bytes"]
        + geometry.FTR.size
    )
    # Footnote: the equality is deliberately complete-artifact accounting. If a future grammar gains a new
    # section, this test must be updated explicitly rather than letting evidence silently omit its bytes.
    assert reconstructed == fp["archive_bytes"] == archive.stat().st_size
    assert fp["metadata_raw_bytes"] > 0
    assert fp["metadata_compressed_bytes_each"] > 0
    assert len(fp["metadata_raw_sha256"]) == 64
    assert len(fp["metadata_compressed_sha256"]) == 64
    assert len(fp["merkle_root_sha256"]) == 64
