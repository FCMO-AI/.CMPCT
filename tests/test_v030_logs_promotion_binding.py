from __future__ import annotations


def test_release_product_promotes_logs_without_recursive_fallback() -> None:
    from experiments import entropygraph_v030_release_product as product
    from experiments import entropygraph_v030_release_product_base as base
    from experiments import entropygraph_v030_release_product_logs_candidate as logs

    assert product.PROMOTED_LOGS_INVERSE is True
    assert product.build is product._PROMOTED_BINDINGS["build"]
    assert product.strong_verify is product._PROMOTED_BINDINGS["strong_verify"]
    assert product.list_members is product._PROMOTED_BINDINGS["list_members"]
    assert product.read_member_with_stats is product._PROMOTED_BINDINGS["read_member_with_stats"]
    assert product.extract is product._PROMOTED_BINDINGS["extract"]
    assert product._revision_for_archive is product._PROMOTED_BINDINGS["_revision_for_archive"]

    # Public promotion must not replace the mature implementation itself. The preserved Git blob remains the
    # authoritative fallback and public-module overrides are mirrored into its function globals by the bridge.
    assert product._BASE_ORIGINALS["build"] is base.build
    assert product._BASE_ORIGINALS["strong_verify"] is base.strong_verify
    assert product._BASE_ORIGINALS["extract"] is base.extract
    assert product.build is not base.build
    assert product.build is not logs.build
    assert product.strong_verify is not base.strong_verify
    assert product.strong_verify is not logs.strong_verify

    # Direct candidate/oracle imports keep a dynamic BASE.build delegate, while fixed non-build reader delegates
    # remain mature functions. This avoids circular promotion and preserves the historical candidate test surface.
    assert logs._BASE_BUILD is not logs.build
    assert logs._BASE_STRONG_VERIFY is base.strong_verify
    assert logs._BASE_LIST_MEMBERS is base.list_members
    assert logs._BASE_READ_MEMBER_WITH_STATS is base.read_member_with_stats
    assert logs._BASE_EXTRACT is base.extract
    assert logs._BASE_REVISION_FOR_ARCHIVE is base._revision_for_archive

    assert product.REVISION == base.REVISION == logs.REVISION
    assert product.LOGS_PROFILE == logs.LOGS_PROFILE
