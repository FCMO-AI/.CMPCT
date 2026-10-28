from __future__ import annotations

from pathlib import Path
import tempfile

from benchmarks import v030_r24_compact_control_oracle as CC
from cmpct import codec as R24
from experiments import entropygraph_v030_release_product as PRODUCT


def _fixture(root: Path) -> Path:
    source = root / "source"
    source.mkdir()
    # Exercise prefix-delta paths, derived S_PACK sizes, ordinary files and metadata defaults.
    for index in range(40):
        (source / f"family-{index:03d}.bin").write_bytes((bytes([index % 251]) * 4096) + b"tail")
    (source / "notes.txt").write_text("compact-control semantic fixture\n" * 32, encoding="utf-8")
    return source


def test_compact_control_expands_to_exact_current_shipping_index() -> None:
    with tempfile.TemporaryDirectory(prefix="cmpct-v030-compact-control-test-") as td:
        root = Path(td)
        source = _fixture(root)
        archive = root / "fixture.cmpct"
        PRODUCT._locality_bounded_r24_build(source, archive)
        verified = PRODUCT.strong_verify(archive)
        assert verified["ok"] is True
        assert verified["format_revision"] == 24

        index, physical = CC._read_index(archive)
        compact = CC._compact_index(index)
        expanded = CC._expand_index(compact, version=int(index["v"]), features=list(index["features"]))
        assert expanded == index

        measured = CC._compact_once(archive)
        assert measured["semantic_index_roundtrip_exact"] is True
        assert measured["physical_payload_records_unchanged"] is True
        assert measured["two_authenticated_control_copies_retained"] is True
        assert measured["projected_two_copy_archive_bytes"] <= physical["archive_bytes"]


def test_compact_control_does_not_depend_on_dead_dictionary_presence() -> None:
    # The transform operates on the authenticated finished index. Whether shipping already elided an unused
    # dictionary is therefore data, not a policy input. A missing dict blob must round-trip exactly.
    index = {
        "v": R24.VERSION,
        "files": [["a.bin", R24.K_FILE, 0o644, 0, 3, None, [R24.S_BLOB, 0]]],
        "blobs": [[R24.CODEC_RAW, 3, 3, b"x" * 32, b"", 0]],
        "recipes": [],
        "dict_blob": None,
        "fsmeta": {},
        "features": [],
    }
    compact = CC._compact_index(index)
    assert compact["z"] is None
    assert CC._expand_index(compact, version=R24.VERSION, features=[]) == index
