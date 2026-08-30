from pathlib import Path

from experiments import entropygraph_v030_release_product as product


def test_shipping_build_does_not_reenter_falsified_compact_control_terminal(monkeypatch, tmp_path: Path):
    """Exact negative authority must remove the losing build, not weaken its gate."""
    source = tmp_path / "source"
    source.mkdir()
    out = tmp_path / "out.cmpct"

    shape = {
        "logical_bytes": 10_182_899,
        "regular_files": 1425,
        "average_regular_bytes": 10_182_899 / 1425,
    }
    monkeypatch.setattr(
        product,
        "_shared_frontdoor_preflight",
        lambda _root: {
            "logs_eligible": False,
            "shape": shape,
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
    expected = {"selected": "base-product-sentinel", "archive_bytes": 123}
    monkeypatch.setattr(product._BASE_IMPL, "build", lambda _root, _out: expected)

    assert product.build(source, out) == expected
    assert product.PROMOTED_R24_COMPACT_CONTROL_TERMINAL is False


def test_compact_control_reader_dispatch_remains_available(monkeypatch, tmp_path: Path):
    """Retiring construction must not strand existing research artifacts/readers."""
    archive = tmp_path / "legacy-c25cc01.cmpct"
    archive.write_bytes(b"C25CC01\0" + b"research")

    class ReaderStub:
        REVISION = 25
        PROFILE = "r24-compact-control-v1"

    monkeypatch.setattr(product, "_compact_control_module", lambda: ReaderStub)
    assert product._revision_for_archive(archive) == (25, "r24-compact-control-v1")
