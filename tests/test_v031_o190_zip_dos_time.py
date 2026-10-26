"""O190: signed CMPCT metadata must not escape legal ZIP DOS calendar limits.

No file-format mutation is involved; these unit tests complement a cross-host test
with actual independently installed Builder/Reader and transferred r24 bytes.
"""
import os
import subprocess
import sys
import time

import pytest

from cmpct.reader import CMPCT


DOS_MIN = (1980, 1, 1, 0, 0, 0)
DOS_MAX = (2107, 12, 31, 23, 59, 58)


def unpack_dos(packed):
    tm, dt = packed
    return (1980 + (dt >> 9), (dt >> 5) & 15, dt & 31,
            tm >> 11, (tm >> 5) & 63, (tm & 31) * 2)


@pytest.mark.parametrize("ns,expected", [
    (-2**63, DOS_MIN),
    (-315619200_000_000_000, DOS_MIN),  # 1960, authentic O184 negative
    (0, DOS_MIN),                      # historical unspecified timestamp
    (2**63 - 1, DOS_MAX),
    (4417977600_000_000_000, DOS_MAX),  # 2110, before signed i64 ceiling
])
def test_signed_extremes_have_complete_legal_calendar(ns, expected):
    assert unpack_dos(CMPCT._zip_dos_time(None, ns)) == expected


def test_unambiguous_extremes_never_call_unsafe_host_localtime(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("CRT localtime must not receive signed extreme values")
    with monkeypatch.context() as patch:
        patch.setattr(time, "localtime", forbidden)
        for ns in (-2**63, -315619200_000_000_000, 0, 2**63 - 1):
            unpack_dos(CMPCT._zip_dos_time(None, ns))


@pytest.mark.parametrize("s", [
    946684800,   # 2000-01-01 UTC
    1136073600,  # 2006-01-01 UTC
    1704067200,  # 2024-01-01 UTC
    2147483647,  # just before signed 32-bit epoch rollover
])
def test_representable_local_dates_preserve_original_dos_encoding(s):
    tm = time.localtime(s)
    if not 1980 <= tm.tm_year <= 2107:
        pytest.skip("host zone maps this source outside DOS representable time")
    legacy_date = ((tm.tm_year - 1980) << 9) | (tm.tm_mon << 5) | tm.tm_mday
    legacy_time = (tm.tm_hour << 11) | (tm.tm_min << 5) | (tm.tm_sec // 2)
    assert CMPCT._zip_dos_time(None, s * 1_000_000_000) == (legacy_time, legacy_date)


def test_fractional_second_uses_integer_floor_not_float_rollover():
    # This input lies immediately below an integer-second boundary.
    sec = 2147483647
    actual = CMPCT._zip_dos_time(None, sec * 1_000_000_000 + 999_999_999)
    assert actual == CMPCT._zip_dos_time(None, sec * 1_000_000_000)


@pytest.mark.skipif(not hasattr(time, "tzset"), reason="POSIX host timezone override only")
@pytest.mark.parametrize("zone", ["UTC", "America/Los_Angeles", "Asia/Tokyo", "Pacific/Kiritimati"])
def test_complete_calendar_clip_under_real_timezone(zone):
    # Run in a child: changing TZ in a global pytest process would taint other tests.
    script = """
import time
from cmpct.reader import CMPCT
time.tzset()
def unpack(v):
    tm,dt=v
    return (1980+(dt>>9),(dt>>5)&15,dt&31,tm>>11,(tm>>5)&63,(tm&31)*2)
lo=(1980,1,1,0,0,0)
hi=(2107,12,31,23,59,58)
for ns in (-315619200000000000, 0, 315532799000000000,
           315532800000000000, 4354819198000000000,
           4354819200000000000, 2**63-1):
    v=unpack(CMPCT._zip_dos_time(None,ns))
    assert lo<=v<=hi,(ns,v)
assert unpack(CMPCT._zip_dos_time(None,-315619200000000000))==lo
assert unpack(CMPCT._zip_dos_time(None,2**63-1))==hi
"""
    env = dict(os.environ, TZ=zone)
    proc = subprocess.run([sys.executable, "-c", script], env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
