"""J24G30: exact O190/O191 calendar semantics composed with O149 publication.

This is an additional adversarial acceptance suite, not a replacement for
the frozen O190/O191/O149/O140/O135 tests. Small forced ZIP64 dispatch tests
only the code branch; it does not prove genuine >=4 GiB behavior.
"""
from __future__ import annotations

import datetime as dt
import os
import time
import zipfile

import pytest

from cmpct.builder import Builder
from cmpct.reader import CMPCT


def dos_tuple(packed):
    ztime, zdate = packed
    return (1980 + (zdate >> 9), (zdate >> 5) & 15, zdate & 31,
            ztime >> 11, (ztime >> 5) & 63, (ztime & 31) * 2)


def test_fractional_second_custody_is_integer_floor():
    # Float conversion rounds ns immediately before an even-second boundary.
    ns = 1_577_836_801_999_999_999
    assert dos_tuple(CMPCT._zip_dos_time(None, ns)) == (
        2020, 1, 1, 0, 0, 0
    )
    assert CMPCT._zip_dos_time(None, ns) == CMPCT._zip_dos_time(
        None, 1_577_836_801_000_000_000
    )


@pytest.mark.skipif(not hasattr(time, "tzset"), reason="POSIX timezone override only")
def test_local_dos_1980_boundary_not_utc_cutoff(monkeypatch):
    # 1979-12-31 22:00 UTC is 1980-01-01 07:00 in Asia/Tokyo.
    # The abandoned J24G29 candidate clipped at midnight in UTC instead.
    old_zone = os.environ.get("TZ")
    try:
        monkeypatch.setenv("TZ", "Asia/Tokyo")
        time.tzset()
        assert dos_tuple(CMPCT._zip_dos_time(
            None, 315_525_600_000_000_000
        )) == (1980, 1, 1, 7, 0, 0)
    finally:
        if old_zone is None:
            monkeypatch.delenv("TZ", raising=False)
        else:
            monkeypatch.setenv("TZ", old_zone)
        time.tzset()


def test_future_leap_timestamp_saturates_whole_calendar():
    future = int(dt.datetime(2108, 2, 29, 12, tzinfo=dt.timezone.utc).timestamp())
    assert dos_tuple(CMPCT._zip_dos_time(None, future * 1_000_000_000)) == (
        2107, 12, 31, 23, 59, 58
    )


def test_staged_fast_and_forced_zip64_export_share_signed_calendar(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    item = source / "member.bin"
    payload = b"J24G30 exact lossless calendar and staged ZIP\x00" * 23
    item.write_bytes(payload)
    ordinary = 1_580_601_600_000_000_000  # 2020-02-02 UTC
    os.utime(item, ns=(ordinary, ordinary))

    archive = tmp_path / "source.cmpct"
    Builder(source, workers=1).build(archive)
    source_bytes = archive.read_bytes()
    old_target = tmp_path / "prior.zip"
    old_target.write_bytes(b"PREEXISTING ZIP BYTES SENTINEL")

    with CMPCT(archive) as ar:
        assert ar.read("member.bin") == payload
        assert ar.verify() == 1
        expected = dos_tuple(ar._zip_dos_time(ar.by["member.bin"][3]))
        assert expected[0] == 2020

        fast = tmp_path / "fast.zip"
        ar.export_zip(fast)
        with zipfile.ZipFile(fast) as z:
            assert z.read("member.bin") == payload
            fast_date = z.getinfo("member.bin").date_time
        assert fast_date == expected

        # A *branch-dispatch* oracle, not actual ZIP64 >4GiB evidence.
        # Patch only the branch choice; use identical physical r24 archive.
        monkeypatch.setattr(CMPCT, "_zip64_offset_fallback_required",
                            lambda self: True)
        ar.export_zip(old_target)
        with zipfile.ZipFile(old_target) as z:
            assert z.namelist() == ["member.bin"]
            assert z.read("member.bin") == payload
            assert z.getinfo("member.bin").date_time == expected

    assert archive.read_bytes() == source_bytes, "export mutated CMPCT input"
    assert old_target.read_bytes() != b"PREEXISTING ZIP BYTES SENTINEL"
