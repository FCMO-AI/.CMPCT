from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_native_reader_bridge as B


def _info_payload(*, profile: str = "g04-r25", revision: int = 25, entries: int = 2, logical: int = 14) -> bytes:
    return (
        f"profile={profile}\n"
        f"revision={revision}\n"
        f"entries={entries}\n"
        f"logical_regular_bytes={logical}\n"
        "tail_metadata_authenticated=true\n"
        "declared_max_member_read_amplification=7.685\n"
    ).encode()


def test_verify_requires_canonical_g04_profile(monkeypatch, tmp_path: Path) -> None:
    cli = tmp_path / "cmpct-portable"
    cli.write_bytes(b"x")
    archive = tmp_path / "a.cmpct"
    archive.write_bytes(b"x")

    monkeypatch.setattr(B, "_run", lambda *_args, **_kwargs: B.NativeRun(b"ok profile=g04-r25\n", b""))
    receipt = B.verify_g04(cli, archive)
    assert receipt["ok"] is True
    assert receipt["profile"] == "g04-r25"

    monkeypatch.setattr(B, "_run", lambda *_args, **_kwargs: B.NativeRun(b"ok profile=prefixgraph-r25\n", b""))
    with pytest.raises(B.NativeReaderError, match="unexpected profile"):
        B.verify_g04(cli, archive)


def test_info_requires_canonical_profile_revision_and_bounded_totals(monkeypatch, tmp_path: Path) -> None:
    cli = tmp_path / "cmpct-portable"
    cli.write_bytes(b"x")
    archive = tmp_path / "a.cmpct"
    archive.write_bytes(b"x")

    monkeypatch.setattr(B, "_run", lambda *_args, **_kwargs: B.NativeRun(_info_payload(entries=9, logical=1234), b""))
    info = B.info_g04(cli, archive)
    assert info == {
        "profile": "g04-r25",
        "revision": 25,
        "entries": 9,
        "logical_regular_bytes": 1234,
        "tail_metadata_authenticated": True,
    }

    monkeypatch.setattr(B, "_run", lambda *_args, **_kwargs: B.NativeRun(_info_payload(profile="prefixgraph-r25"), b""))
    with pytest.raises(B.NativeReaderError, match="unexpected profile/revision"):
        B.info_g04(cli, archive)

    monkeypatch.setattr(B, "_run", lambda *_args, **_kwargs: B.NativeRun(_info_payload(revision=24), b""))
    with pytest.raises(B.NativeReaderError, match="unexpected profile/revision"):
        B.info_g04(cli, archive)

    malformed = b"profile=g04-r25\nrevision=25\nentries=2\n"
    monkeypatch.setattr(B, "_run", lambda *_args, **_kwargs: B.NativeRun(malformed, b""))
    with pytest.raises(B.NativeReaderError, match="omitted required integer fields"):
        B.info_g04(cli, archive)


def test_extract_enforces_caller_budget_before_native_publication(monkeypatch, tmp_path: Path) -> None:
    cli = tmp_path / "cmpct-portable"
    cli.write_bytes(b"x")
    archive = tmp_path / "a.cmpct"
    archive.write_bytes(b"x")
    destination = tmp_path / "out"
    calls: list[tuple[str, ...]] = []

    def fake_run(_cli: Path, *args: str, **_kwargs) -> B.NativeRun:
        calls.append(tuple(args))
        if args[0] == "info":
            return B.NativeRun(_info_payload(entries=2, logical=14), b"")
        if args[0] == "extract":
            return B.NativeRun(b"", b"")
        raise AssertionError(args)

    monkeypatch.setattr(B, "_run", fake_run)
    with pytest.raises(B.NativeReaderError, match="exceeding caller budget"):
        B.extract_g04(cli, archive, destination, max_output_bytes=13)
    assert [call[0] for call in calls] == ["info"]

    calls.clear()
    receipt = B.extract_g04(cli, archive, destination, max_output_bytes=14)
    assert receipt["ok"] is True
    assert receipt["entries"] == 2
    assert receipt["declared_regular_bytes"] == 14
    assert receipt["transactional_native_extract"] is True
    assert receipt["budget_preflight"] == "native-info-logical-regular-bytes-v1"
    assert [call[0] for call in calls] == ["info", "extract"]


def test_run_never_uses_shell_and_fails_closed(monkeypatch, tmp_path: Path) -> None:
    cli = tmp_path / "cmpct-portable"
    cli.write_bytes(b"x")
    observed = {}

    class Completed:
        returncode = 7
        stdout = b""
        stderr = b"bad archive"

    def fake_subprocess(argv, **kwargs):
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return Completed()

    monkeypatch.setattr(B.subprocess, "run", fake_subprocess)
    with pytest.raises(B.NativeReaderError, match="rejected operation"):
        B._run(cli, "verify", "archive.cmpct")
    assert observed["argv"] == [str(cli), "verify", "archive.cmpct"]
    assert "shell" not in observed["kwargs"]
    assert observed["kwargs"]["check"] is False
