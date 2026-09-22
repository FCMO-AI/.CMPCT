from __future__ import annotations

import zipfile

from cmpct.hidden_zip import hidden_zip_preflight


def test_large_non_zip_stops_after_four_byte_head(tmp_path):
    p = tmp_path / "large.bin"
    p.write_bytes(b"NOPE" + b"x" * (8 * 1024 * 1024))
    pf = hidden_zip_preflight(p)
    assert not pf.eligible
    assert pf.reason == "local_signature_miss"
    assert pf.head_bytes_read == 4
    assert pf.tail_bytes_read == 0


def test_conventional_hidden_zip_reaches_bounded_tail_gate(tmp_path):
    p = tmp_path / "document.bin"
    with zipfile.ZipFile(p, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("shared.txt", b"cmpct" * 4096)
    pf = hidden_zip_preflight(p)
    assert pf.eligible
    assert pf.head_bytes_read == 4
    assert 0 < pf.tail_bytes_read <= 65557
    assert pf.entries == 1


def test_prefixed_zip_is_intentionally_false_negative(tmp_path):
    ordinary = tmp_path / "ordinary.zip"
    with zipfile.ZipFile(ordinary, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("payload", b"payload" * 128)
    p = tmp_path / "self-extracting.bin"
    p.write_bytes(b"MZXX" + ordinary.read_bytes())
    pf = hidden_zip_preflight(p)
    assert not pf.eligible
    assert pf.reason == "local_signature_miss"
    assert pf.head_bytes_read == 4
    assert pf.tail_bytes_read == 0
