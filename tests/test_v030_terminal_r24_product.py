from __future__ import annotations

from pathlib import Path

from experiments import entropygraph_v030_release_product as product


def _single_large_preflight(member_bytes: int) -> dict:
    return {
        "logs_eligible": False,
        "shape": {
            "regular_files": 1,
            "logical_bytes": member_bytes,
            "average_regular_bytes": float(member_bytes),
            "min_regular_bytes": member_bytes,
            "max_regular_bytes": member_bytes,
            "all_regular_bin": False,
            "has_nonregular_entries": False,
        },
        "media_files": None,
        "metadata_error": False,
        "scanned_regular_files": 1,
        "short_circuited": False,
    }


def test_terminal_r24_skips_r25_and_keeps_final_strong_verify(monkeypatch, tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    out = tmp_path / "out.cmpct"
    wide = product.R24_RELEASE_WIDE_CHUNK_BYTES

    # The promoted front door now owns the first complete source walk. Preserve the historical terminal test by
    # making that shared fact table agree with the mature single-large predicate being exercised below.
    monkeypatch.setattr(product, "_shared_frontdoor_preflight", lambda _root: _single_large_preflight(wide))
    monkeypatch.setattr(product, "_regular_user_shape", lambda _root: (1, wide))

    def fake_r24(_root: Path, candidate: Path):
        candidate.write_bytes(b"r24-candidate")
        return {
            "archive_bytes": candidate.stat().st_size,
            "large_file_chunk_policy": "fixed-8mib",
            "verification_state": "deferred-to-selected-artifact",
        }

    monkeypatch.setattr(product, "_locality_bounded_r24_build", fake_r24)
    monkeypatch.setattr(
        product,
        "strong_verify",
        lambda archive: {
            "ok": Path(archive).read_bytes() == b"r24-candidate",
            "format_revision": 24,
            "tree_sha256": "verified-tree",
        },
    )
    monkeypatch.setattr(
        product.C,
        "build",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("terminal envelope must not construct r25")),
    )

    result = product.build(root, out)

    assert out.read_bytes() == b"r24-candidate"
    assert result["selected"] == "r24-fallback"
    assert result["format_revision"] == 24
    assert result["r25_attempted"] is False
    assert result["r25_product_bytes"] is None
    assert result["terminal_r24"] is True
    assert result["final_strong_verify"]["ok"] is True
    assert result["r24"]["verification_state"] == "deferred-to-selected-artifact"


def test_nonterminal_shape_keeps_exact_r24_vs_r25_tournament(monkeypatch, tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    out = tmp_path / "out.cmpct"
    sentinel = {"selected": "canonical-tournament"}

    monkeypatch.setattr(product, "_regular_user_shape", lambda _root: (2, product.R24_RELEASE_WIDE_CHUNK_BYTES))
    monkeypatch.setattr(product.C, "build", lambda got_root, got_out: sentinel)

    assert product.build(root, out) is sentinel


def test_terminal_admission_requires_single_regular_file(monkeypatch, tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()

    monkeypatch.setattr(product, "_regular_user_shape", lambda _root: (1, product.R24_RELEASE_WIDE_CHUNK_BYTES - 1))
    assert product._terminal_r24_eligible(root) is False

    monkeypatch.setattr(product, "_regular_user_shape", lambda _root: (2, product.R24_RELEASE_WIDE_CHUNK_BYTES * 2))
    assert product._terminal_r24_eligible(root) is False

    monkeypatch.setattr(product, "_regular_user_shape", lambda _root: (1, product.R24_RELEASE_WIDE_CHUNK_BYTES))
    assert product._terminal_r24_eligible(root) is True
