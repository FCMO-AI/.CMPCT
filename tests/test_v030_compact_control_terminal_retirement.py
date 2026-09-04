from pathlib import Path

from experiments import entropygraph_v030_release_product as product


def _negative_terminal_shape() -> dict:
    return {
        "logical_bytes": 10_182_899,
        "regular_files": 1425,
        "average_regular_bytes": 10_182_899 / 1425,
        "min_regular_bytes": 37,
        "max_regular_bytes": 131_072,
        "all_regular_bin": False,
        "has_nonregular_entries": False,
    }


def test_shipping_build_does_not_reenter_falsified_compact_control_terminal(monkeypatch, tmp_path: Path):
    """Exact negative authority must remove the losing build, not weaken its gate."""
    source = tmp_path / "source"
    source.mkdir()
    out = tmp_path / "out.cmpct"

    monkeypatch.setattr(
        product,
        "_shared_frontdoor_preflight",
        lambda _root: {
            "logs_eligible": False,
            "shape": _negative_terminal_shape(),
            "media_files": None,
            "metadata_error": False,
            "scanned_regular_files": 1425,
            "short_circuited": False,
        },
    )
    monkeypatch.setattr(product, "_media_admission_after_preflight", lambda _root, _preflight: {"eligible": False})

    def forbidden(*_args, **_kwargs):
        raise AssertionError("falsified compact-control shipping terminal was re-entered")

    monkeypatch.setattr(product, "_build_compact_control_terminal_if_eligible", forbidden)
    expected = {"selected": "canonical-final-sentinel", "archive_bytes": 123}
    monkeypatch.setattr(product._BASE_IMPL.C, "build", lambda _root, _out: expected)
    monkeypatch.setattr(
        product._BASE_IMPL,
        "build",
        lambda _root, _out: (_ for _ in ()).throw(AssertionError("duplicate base terminal scans were re-entered")),
    )

    assert product.build(source, out) == expected
    assert product.PROMOTED_R24_COMPACT_CONTROL_TERMINAL is False


def test_shared_preflight_matches_medium_binary_source_shape(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    for index, size in enumerate((32_768, 65_536, 131_072, 262_144)):
        (source / f"part-{index}.bin").write_bytes(bytes([index + 1]) * size)

    shared = product._shared_frontdoor_preflight(source)
    mature = product._BASE_IMPL._medium_binary_terminal_shape(source)
    assert shared["metadata_error"] is False
    for key in (
        "regular_files",
        "logical_bytes",
        "min_regular_bytes",
        "max_regular_bytes",
        "all_regular_bin",
        "has_nonregular_entries",
    ):
        assert shared["shape"][key] == mature[key]
    assert product._BASE_IMPL._medium_binary_terminal_source_eligible(shared["shape"]) is False


def test_shared_preflight_preserves_possible_medium_terminal(monkeypatch, tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    out = tmp_path / "out.cmpct"
    shape = {
        "logical_bytes": 32 * 65_536,
        "regular_files": 32,
        "average_regular_bytes": 65_536,
        "min_regular_bytes": 65_536,
        "max_regular_bytes": 65_536,
        "all_regular_bin": True,
        "has_nonregular_entries": False,
    }
    monkeypatch.setattr(
        product,
        "_shared_frontdoor_preflight",
        lambda _root: {
            "logs_eligible": False,
            "shape": shape,
            "media_files": None,
            "metadata_error": False,
            "scanned_regular_files": 32,
            "short_circuited": False,
        },
    )
    monkeypatch.setattr(product, "_media_admission_after_preflight", lambda _root, _preflight: {"eligible": False})
    expected = {"selected": "mature-terminal-check"}
    monkeypatch.setattr(product._BASE_IMPL, "build", lambda _root, _out: expected)
    monkeypatch.setattr(
        product._BASE_IMPL.C,
        "build",
        lambda _root, _out: (_ for _ in ()).throw(AssertionError("possible mature terminal was bypassed")),
    )
    assert product.build(source, out) == expected


def test_compact_control_reader_dispatch_remains_available(monkeypatch, tmp_path: Path):
    """Retiring construction must not strand existing research artifacts/readers."""
    archive = tmp_path / "legacy-c25cc01.cmpct"
    archive.write_bytes(b"C25CC01\0" + b"research")

    class ReaderStub:
        REVISION = 25
        PROFILE = "r24-compact-control-v1"

    monkeypatch.setattr(product, "_compact_control_module", lambda: ReaderStub)
    assert product._revision_for_archive(archive) == (25, "r24-compact-control-v1")
