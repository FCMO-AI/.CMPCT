from __future__ import annotations


def test_release_product_promotes_logs_without_recursive_fallback() -> None:
    from experiments import entropygraph_v030_release_product as product
    from experiments import entropygraph_v030_release_product_base as base
    from experiments import entropygraph_v030_release_product_logs_candidate as logs

    assert product.PROMOTED_LOGS_INVERSE is True
    assert product.build is logs.build
    assert product.strong_verify is logs.strong_verify
    assert product.list_members is logs.list_members
    assert product.read_member_with_stats is logs.read_member_with_stats
    assert product.extract is logs.extract
    assert product._revision_for_archive is logs._revision_for_archive

    # The wrapper must retain the exact mature delegates captured before public rebinding. Otherwise a non-logs
    # source would recurse back through the promoted facade instead of executing the frozen r24/r25 selector.
    assert logs._BASE_BUILD is base.build
    assert logs._BASE_STRONG_VERIFY is base.strong_verify
    assert logs._BASE_LIST_MEMBERS is base.list_members
    assert logs._BASE_READ_MEMBER_WITH_STATS is base.read_member_with_stats
    assert logs._BASE_EXTRACT is base.extract
    assert logs._BASE_REVISION_FOR_ARCHIVE is base._revision_for_archive

    assert logs._BASE_BUILD is not logs.build
    assert logs._BASE_STRONG_VERIFY is not logs.strong_verify
    assert product.REVISION == base.REVISION == logs.REVISION
    assert product.LOGS_PROFILE == logs.LOGS_PROFILE
