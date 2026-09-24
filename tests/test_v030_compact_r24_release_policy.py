from __future__ import annotations


def test_compact_r24_candidate_changes_only_preregistered_policy_owners(tmp_path):
    from experiments import entropygraph_v030_release_product_compact_r24 as candidate

    base = candidate._BASE
    assert candidate.R24_COMPACT_DEFLATE_REUSE_MIN_BYTES == 64 * 1024
    assert base.R24_RELEASE_DEFLATE_REUSE_MIN_BYTES == 64 * 1024
    assert candidate.R24_COMPACT_MEDIUM_BINARY_PACKING is False
    assert candidate.R24_COMPACT_MEDIUM_TERMINAL is False

    hints = base._ReleaseTextHints()
    assert ".bin" not in hints
    assert set(hints) == set(base._R24_ORIGINAL_TEXT_EXT)
    assert len(hints) == len(base._R24_ORIGINAL_TEXT_EXT)

    # The medium-binary terminal's proof depended on the removed packing policy.  The bounded
    # candidate must fail closed rather than silently reuse that old terminal evidence.
    root = tmp_path / "root"
    root.mkdir()
    out = tmp_path / "candidate.cmpct"
    assert base._build_medium_binary_terminal_if_eligible(root, out) is None
    assert candidate._PRODUCT._build_medium_binary_terminal_if_eligible(root, out) is None


def test_compact_r24_candidate_preserves_unrelated_release_constants():
    from experiments import entropygraph_v030_release_product_compact_r24 as candidate

    base = candidate._BASE
    assert base.R24_RELEASE_MICRO_MAX_FILE_BYTES == 256 * 1024
    assert base.R24_RELEASE_PACK_CAP_BYTES == 2 * 1024 * 1024
    assert base.R24_RELEASE_WIDE_CHUNK_BYTES == 8 * 1024 * 1024
    assert candidate.REVISION == base.REVISION
