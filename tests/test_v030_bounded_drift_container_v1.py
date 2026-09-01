from __future__ import annotations

import hashlib

import pytest

from experiments import entropygraph_v030_bounded_drift_container_v1 as C


def _family() -> list[bytes]:
    seed = (b"abcdefghijklmnop" * 8192)[:100000]
    return [
        seed,
        seed[:1000] + b"INSERT" + seed[1000:],
        seed[:40000] + b"replace-me" + seed[40010:],
        seed[:70000] + seed[70033:],
    ]


def _canonical(members: list[bytes]) -> list[bytes]:
    return sorted(members, key=lambda data: (hashlib.sha256(data).digest(), data))


def test_container_is_content_only_order_invariant_and_round_trips() -> None:
    members = _family()
    a = C.encode_container(members)
    b = C.encode_container(list(reversed(members)))
    assert a == b
    expected = _canonical(members)
    assert C.decode_all(a) == expected
    assert [C.decode_member(a, i) for i in range(len(expected))] == expected


def test_duplicate_members_preserve_multiplicity_deterministically() -> None:
    members = _family()
    members.extend([members[1], members[1]])
    blob = C.encode_container(members)
    assert C.decode_all(blob) == _canonical(members)


def test_container_corruption_and_truncation_fail_closed() -> None:
    blob = C.encode_container(_family())
    corrupt = bytearray(blob)
    corrupt[len(corrupt) // 2] ^= 1
    with pytest.raises(ValueError):
        C.parse_container(bytes(corrupt))
    with pytest.raises(ValueError):
        C.parse_container(blob[:-1])
    with pytest.raises(ValueError):
        C.parse_container(b"WRONGBD2" + blob[8:])


def test_member_index_contract_fails_closed() -> None:
    blob = C.encode_container(_family())
    with pytest.raises(IndexError):
        C.decode_member(blob, -1)
    with pytest.raises(IndexError):
        C.decode_member(blob, len(_family()))
    with pytest.raises(TypeError):
        C.decode_member(blob, True)
    with pytest.raises(TypeError):
        C.decode_member(blob, 1.0)  # type: ignore[arg-type]


def test_member_count_and_resource_caps_are_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError):
        C.encode_container([])
    monkeypatch.setattr(C, "MAX_MEMBERS", 2)
    with pytest.raises(ValueError):
        C.encode_container(_family())


def test_non_bytes_and_oversized_member_inputs_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(TypeError):
        C.encode_container([b"ok", bytearray(b"bad")])  # type: ignore[list-item]
    with pytest.raises(TypeError):
        C.parse_container(bytearray(b"bad"))  # type: ignore[arg-type]
    monkeypatch.setattr(C.BD, "MAX_DECODE_UNIT", 64)
    with pytest.raises(ValueError):
        C.encode_container([b"x" * 65])
