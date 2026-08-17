from __future__ import annotations

from pathlib import Path

import pytest

from cmpct.builder import Builder
from experiments import canonical_v25_geometry as BASE25
from experiments import canonical_v25_geometry_recovery as V25


def _fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "events.log").write_text(
        "".join(
            f"2026-08-17T12:{(i // 60) % 60:02d}:{i % 60:02d} INFO worker={i % 32:02d} "
            f"tenant=T{i % 380:04d} latency={8 + (i * 13) % 820}\n"
            for i in range(16000)
        ),
        encoding="utf-8",
    )
    (root / "small.txt").write_text("alpha beta gamma\n" * 200, encoding="utf-8")


def _build(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "src"; _fixture(root)
    r24 = tmp_path / "base.cmpct"; r25 = tmp_path / "candidate.cmpct"
    Builder(root, workers=1, reproducible=True).build(r24)
    V25.compile_r24_to_r25(r24, r25)
    return root, r25


def test_tail_recovers_when_primary_compressed_index_length_is_corrupt(tmp_path: Path) -> None:
    root, r25 = _build(tmp_path)
    data = bytearray(r25.read_bytes())
    fields = list(BASE25.HDR.unpack_from(data, 0))
    fields[3] = (1 << 63) - 1  # primary index compressed length: syntactically huge / unusable.
    data[:BASE25.HDR.size] = BASE25.HDR.pack(*fields)
    damaged = tmp_path / "header-length-corrupt.cmpct"; damaged.write_bytes(data)
    with V25.CMPCTV25(damaged) as reader:
        assert reader.read("small.txt") == (root / "small.txt").read_bytes()
        assert reader.read("events.log") == (root / "events.log").read_bytes()


def test_primary_recovers_when_tail_footer_is_corrupt(tmp_path: Path) -> None:
    root, r25 = _build(tmp_path)
    data = bytearray(r25.read_bytes())
    data[-V25.V25_FTR.size] ^= 0x7F
    damaged = tmp_path / "tail-corrupt.cmpct"; damaged.write_bytes(data)
    with V25.CMPCTV25(damaged) as reader:
        assert reader.read("small.txt") == (root / "small.txt").read_bytes()


def test_tail_record_base_tamper_invalidates_certificate_even_when_primary_survives(tmp_path: Path) -> None:
    _root, r25 = _build(tmp_path)
    data = bytearray(r25.read_bytes())
    footer_pos = len(data) - V25.V25_FTR.size
    fields = list(V25.V25_FTR.unpack_from(data, footer_pos))
    fields[8] += 1  # record_base; certificate intentionally left unchanged.
    data[footer_pos:] = V25.V25_FTR.pack(*fields)
    damaged = tmp_path / "tail-base-corrupt.cmpct"; damaged.write_bytes(data)
    # Tail validation fails cryptographically (and would also fail the physical-span proof); the independent
    # primary path remains valid and therefore recovers the archive.
    with V25.CMPCTV25(damaged) as reader:
        assert reader.index["v"] == 25


def test_tail_rejects_record_base_tamper_when_primary_is_also_unusable(tmp_path: Path) -> None:
    _root, r25 = _build(tmp_path)
    data = bytearray(r25.read_bytes())
    fields = list(BASE25.HDR.unpack_from(data, 0)); fields[3] = (1 << 63) - 1
    data[:BASE25.HDR.size] = BASE25.HDR.pack(*fields)
    footer_pos = len(data) - V25.V25_FTR.size
    footer = list(V25.V25_FTR.unpack_from(data, footer_pos)); footer[8] += 17
    data[footer_pos:] = V25.V25_FTR.pack(*footer)
    damaged = tmp_path / "no-valid-index.cmpct"; damaged.write_bytes(data)
    with pytest.raises(IOError, match="both CMPCT r25 indexes unavailable"):
        V25.CMPCTV25(damaged)


def test_tail_certificate_commits_to_record_base_and_index_bytes() -> None:
    kwargs = dict(kind=0, codec=1, flags=0, reserved=0, csize=100, usize=200, prev=0)
    index = b"canonical-index"
    first = V25._tail_certificate(**kwargs, record_base=1234, index_raw=index)
    assert first != V25._tail_certificate(**kwargs, record_base=1235, index_raw=index)
    assert first != V25._tail_certificate(**kwargs, record_base=1234, index_raw=index + b"!")
    assert len(first) == 32


def test_recovery_footer_resource_contract_is_bounded() -> None:
    assert V25.MAX_INDEX_COMPRESSED <= 256 * 1024 * 1024
    assert V25.MAX_INDEX_RAW <= 256 * 1024 * 1024
    assert V25.V25_FTR.size > BASE25.FTR.size
    assert V25.TAIL_CERT_DOMAIN.startswith(b"CMPCT25-")
