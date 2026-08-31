from __future__ import annotations

import hashlib

import msgpack
import pytest

from experiments import entropygraph_v030_product_fs as FS
from experiments import entropygraph_v030_r25_manifest_admission as ADMIT

MAX_PATH = 4096
MAX_ENTRIES = 1024


def _manifest(entries: list[list]) -> bytes:
    return msgpack.packb(
        {
            "v": FS.FILESYSTEM_MANIFEST_VERSION,
            "profile": "cmpct-r25-filesystem-manifest-v1",
            "internal_path": FS.FILESYSTEM_MANIFEST,
            "entries": entries,
        },
        use_bin_type=True,
    )


def _regular(path: str, payload: bytes, *, mode: int = 0o644) -> list:
    return [path, "f", mode, 0, 0, 0, [], [len(payload), hashlib.sha256(payload).digest()]]


def test_strictly_smaller_exact_implicit_control_is_admitted() -> None:
    entries = [_regular(f"src/pkg/very_repetitive_component_{index:03d}.py", bytes([index % 251]) * 64) for index in range(80)]
    raw = _manifest(entries)
    selected = ADMIT.admit(raw, max_path_bytes=MAX_PATH, max_entries=MAX_ENTRIES)
    assert selected.encoding == "implicit-v4"
    assert selected.selected_bytes < selected.filesystem_v1_bytes
    assert selected.saving_bytes == selected.filesystem_v1_bytes - selected.selected_bytes

    identities = {row[0]: (int(row[7][0]), bytes(row[7][1])) for row in entries}
    decoded, encoding = ADMIT.decode(
        selected.raw,
        regular_identities=identities,
        max_path_bytes=MAX_PATH,
        max_entries=MAX_ENTRIES,
    )
    assert encoding == "implicit-v4"
    assert decoded["manifest"] == FS.decode_manifest(raw, max_path_bytes=MAX_PATH, max_entries=MAX_ENTRIES)["manifest"]


def test_tie_or_larger_candidate_keeps_filesystem_v1(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = _manifest([_regular("a", b"x")])
    monkeypatch.setattr(ADMIT.IFS4, "encode_v1", lambda *_args, **_kwargs: raw)
    selected = ADMIT.admit(raw, max_path_bytes=MAX_PATH, max_entries=MAX_ENTRIES)
    assert selected.encoding == "filesystem-v1"
    assert selected.raw == raw
    assert selected.saving_bytes == 0


def test_semantic_mismatch_fails_safe_to_filesystem_v1(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = _manifest([_regular("a-long-path.txt", b"payload")])
    monkeypatch.setattr(ADMIT.IFS4, "encode_v1", lambda *_args, **_kwargs: b"x")
    monkeypatch.setattr(ADMIT.IFS4, "semantics_equal", lambda *_args, **_kwargs: False)
    selected = ADMIT.admit(raw, max_path_bytes=MAX_PATH, max_entries=MAX_ENTRIES)
    assert selected.encoding == "filesystem-v1"
    assert selected.raw == raw


def test_filesystem_v1_decode_does_not_depend_on_graph_identity_argument() -> None:
    raw = _manifest([_regular("a.txt", b"a")])
    decoded, encoding = ADMIT.decode(
        raw,
        regular_identities={"hostile-extra": (1, b"z" * 32)},
        max_path_bytes=MAX_PATH,
        max_entries=MAX_ENTRIES,
    )
    assert encoding == "filesystem-v1"
    assert set(decoded["regular"]) == {"a.txt"}


def test_implicit_decode_requires_exact_authenticated_regular_identity_count() -> None:
    entries = [_regular(f"tree/member_{index:03d}.bin", b"q" * (index + 1)) for index in range(32)]
    raw = _manifest(entries)
    selected = ADMIT.admit(raw, max_path_bytes=MAX_PATH, max_entries=MAX_ENTRIES)
    assert selected.encoding == "implicit-v4"
    with pytest.raises(RuntimeError, match="unsupported or malformed"):
        ADMIT.decode(
            selected.raw,
            regular_identities={},
            max_path_bytes=MAX_PATH,
            max_entries=MAX_ENTRIES,
        )


def test_malformed_control_fails_closed() -> None:
    with pytest.raises(RuntimeError, match="unsupported or malformed"):
        ADMIT.decode(
            b"not-a-manifest",
            regular_identities={},
            max_path_bytes=MAX_PATH,
            max_entries=MAX_ENTRIES,
        )
