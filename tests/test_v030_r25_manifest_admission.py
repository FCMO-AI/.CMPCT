from __future__ import annotations

import hashlib
from pathlib import PurePosixPath

import msgpack
import pytest

from experiments import entropygraph_v030_canonical_final_impl as FINAL
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
    monkeypatch.setattr(ADMIT.IFS4, "encode_decoded_v1", lambda *_args, **_kwargs: raw)
    selected = ADMIT.admit(raw, max_path_bytes=MAX_PATH, max_entries=MAX_ENTRIES)
    assert selected.encoding == "filesystem-v1"
    assert selected.raw == raw
    assert selected.saving_bytes == 0


def test_semantic_mismatch_fails_safe_to_filesystem_v1(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = _manifest([_regular("a-long-path.txt", b"payload")])
    monkeypatch.setattr(ADMIT.IFS4, "encode_decoded_v1", lambda *_args, **_kwargs: b"x")
    monkeypatch.setattr(ADMIT.IFS4, "semantics_equal_decoded", lambda *_args, **_kwargs: False)
    selected = ADMIT.admit(raw, max_path_bytes=MAX_PATH, max_entries=MAX_ENTRIES)
    assert selected.encoding == "filesystem-v1"
    assert selected.raw == raw


def test_admission_reuses_one_validated_filesystem_v1_decode(monkeypatch: pytest.MonkeyPatch) -> None:
    """Admission must not repay full filesystem-v1 parsing for encoding and semantic comparison."""
    raw = _manifest([
        _regular(f"tree/member_{index:03d}.bin", bytes([index % 251]) * 96)
        for index in range(48)
    ])
    real_decode = FS.decode_manifest
    calls = 0

    def counted_decode(*args, **kwargs):
        nonlocal calls
        calls += 1
        return real_decode(*args, **kwargs)

    monkeypatch.setattr(ADMIT.FS, "decode_manifest", counted_decode)
    selected = ADMIT.admit(raw, max_path_bytes=MAX_PATH, max_entries=MAX_ENTRIES)
    assert selected.encoding == "implicit-v4"
    assert calls == 1


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


def test_prepare_profile_tree_uses_same_strict_smaller_admission_seam(tmp_path) -> None:
    source = tmp_path / "source"
    for index in range(80):
        path = source / "src" / "pkg" / f"very_repetitive_component_{index:03d}.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes([index % 251]) * 64)

    staged = tmp_path / "staged"
    prepared = ADMIT.prepare_profile_tree(
        source,
        staged,
        max_path_bytes=MAX_PATH,
        max_profile_files=200,
        max_profile_logical_bytes=1024 * 1024,
        max_entries=MAX_ENTRIES,
    )
    assert prepared["selected_manifest_encoding"] == "implicit-v4"
    assert prepared["selected_manifest_bytes"] < len(prepared["source_manifest_raw"])
    assert prepared["manifest_control_saving_bytes"] > 0
    control_path = staged.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    assert control_path.read_bytes() == prepared["selected_manifest_raw"]
    assert hashlib.sha256(prepared["selected_manifest_raw"]).hexdigest() == prepared["selected_manifest_sha256"]


def test_canonical_product_staging_uses_manifest_admission_seam(tmp_path) -> None:
    """Prove the release-facing canonical writer cannot bypass generic implicit-v4 admission."""
    source = tmp_path / "source"
    for index in range(80):
        path = source / "src" / "pkg" / f"very_repetitive_component_{index:03d}.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(bytes([index % 251]) * 64)

    staged = tmp_path / "canonical-staged"
    prepared = FINAL._prepare_profile_tree(source, staged)
    assert prepared["selected_manifest_encoding"] == "implicit-v4"
    assert prepared["manifest_control_saving_bytes"] > 0
    control_path = staged.joinpath(*PurePosixPath(FS.FILESYSTEM_MANIFEST).parts)
    assert control_path.read_bytes() == prepared["selected_manifest_raw"]
    assert prepared["source_manifest_raw"] != prepared["selected_manifest_raw"]


def test_graph_bound_decoder_authenticates_control_and_rejects_extra_members() -> None:
    entries = [_regular(f"tree/member_{index:03d}.bin", b"q" * (index + 1)) for index in range(32)]
    raw = _manifest(entries)
    selected = ADMIT.admit(raw, max_path_bytes=MAX_PATH, max_entries=MAX_ENTRIES)
    assert selected.encoding == "implicit-v4"
    identities = {row[0]: (int(row[7][0]), bytes(row[7][1])) for row in entries}
    content = {
        FS.FILESYSTEM_MANIFEST: (len(selected.raw), hashlib.sha256(selected.raw).digest()),
        **identities,
    }
    decoded, encoding = ADMIT.decode_from_content_identities(
        selected.raw,
        content_identities=content,
        max_path_bytes=MAX_PATH,
        max_entries=MAX_ENTRIES,
    )
    assert encoding == "implicit-v4"
    assert set(decoded["regular"]) == set(identities)

    hostile_control = dict(content)
    hostile_control[FS.FILESYSTEM_MANIFEST] = (len(selected.raw), b"x" * 32)
    with pytest.raises(RuntimeError, match="graph identity mismatch"):
        ADMIT.decode_from_content_identities(
            selected.raw,
            content_identities=hostile_control,
            max_path_bytes=MAX_PATH,
            max_entries=MAX_ENTRIES,
        )

    hostile_extra = dict(content)
    hostile_extra["unexpected.bin"] = (1, b"y" * 32)
    with pytest.raises(RuntimeError, match="disagree on logical members"):
        ADMIT.decode_from_content_identities(
            selected.raw,
            content_identities=hostile_extra,
            max_path_bytes=MAX_PATH,
            max_entries=MAX_ENTRIES,
        )
