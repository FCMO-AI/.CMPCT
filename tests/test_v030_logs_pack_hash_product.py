from benchmarks.v030_logs_pack_hash_product_hostile import run


def test_logs_pack_hash_product_scope_and_post_crc_fault() -> None:
    result = run()
    assert result["result"] == "PASS"
    assert result["covered_packs"] == list(range(result["pack_count"]))
    assert result["post_crc_member_sha_rejected"] is True
    assert result["transaction_published"] is False
    assert result["strict_reader_distinct"] is True
