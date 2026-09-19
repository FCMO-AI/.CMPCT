from concurrent.futures import ThreadPoolExecutor
from threading import Event

from experiments import entropygraph_v030_release_reader_policy as P
from experiments import entropygraph_v030_verified_restore as VR


def test_verified_staging_injects_bulk_inverse_without_global_mutation(tmp_path, monkeypatch) -> None:
    """Verified staging may opt into bulk parsing without changing strict/create shared ownership."""
    archive = tmp_path / "sample.cmpct"
    archive.write_bytes(P.R.G04.MAG)
    staging = tmp_path / "out"
    captured = {}

    promoted_default = VR.release_single_buffer_delimiter_inverse
    assert VR.C.SHARED.G.O.delimiter_inverse is promoted_default
    assert P.R.G04.O.delimiter_inverse is promoted_default

    def fake_stream(archive_arg, staging_arg, max_output_bytes, **kwargs):
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(P.R, "_stream_g04", fake_stream)
    result = P.extract_verified_into_staging(archive, staging)

    assert result == {"ok": True}
    assert captured["verify_nested_semantic_sha"] is False
    assert captured["delimiter_inverse"] is VR.release_bulk_one_byte_table_delimiter_inverse
    assert VR.C.SHARED.G.O.delimiter_inverse is promoted_default
    assert P.R.G04.O.delimiter_inverse is promoted_default


def test_verified_staging_bulk_inverse_is_concurrently_isolated(tmp_path, monkeypatch) -> None:
    """A staging extraction in flight must not mutate the inverse observed by strict/create-side users."""
    archive = tmp_path / "sample.cmpct"
    archive.write_bytes(P.R.G04.MAG)
    staging = tmp_path / "out"
    entered = Event()
    release = Event()
    captured = {}
    promoted_default = VR.release_single_buffer_delimiter_inverse

    def blocked_stream(archive_arg, staging_arg, max_output_bytes, **kwargs):
        captured.update(kwargs)
        entered.set()
        assert release.wait(timeout=5)
        return {"ok": True}

    monkeypatch.setattr(P.R, "_stream_g04", blocked_stream)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(P.extract_verified_into_staging, archive, staging)
        assert entered.wait(timeout=5)
        # This is the shared owner used by ordinary readers and create-side strong verification.
        assert VR.C.SHARED.G.O.delimiter_inverse is promoted_default
        assert P.R.G04.O.delimiter_inverse is promoted_default
        assert captured["delimiter_inverse"] is VR.release_bulk_one_byte_table_delimiter_inverse
        release.set()
        assert future.result(timeout=5) == {"ok": True}

    assert VR.C.SHARED.G.O.delimiter_inverse is promoted_default
    assert P.R.G04.O.delimiter_inverse is promoted_default
