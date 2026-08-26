from __future__ import annotations

from pathlib import Path

import pytest

from experiments import entropygraph_v030_native_reader_bridge as B


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


def test_list_parser_preserves_paths_and_rejects_bad_indexes(monkeypatch, tmp_path: Path) -> None:
    cli = tmp_path / "cmpct-portable"
    cli.write_bytes(b"x")
    archive = tmp_path / "a.cmpct"
    archive.write_bytes(b"x")
    payload = b"0\t0\t12\tdir/a.bin\n1\t1\t0\tdir\n2\t0\t7\tname-with-tab\tinside.bin\n"
    monkeypatch.setattr(B, "_run", lambda *_args, **_kwargs: B.NativeRun(payload, b""))
    entries = B.list_entries(cli, archive)
    assert [(entry.kind, entry.size, entry.path) for entry in entries] == [
        (0, 12, "dir/a.bin"),
        (1, 0, "dir"),
        (0, 7, "name-with-tab\tinside.bin"),
    ]
    assert B.declared_regular_bytes(entries) == 19

    monkeypatch.setattr(B, "_run", lambda *_args, **_kwargs: B.NativeRun(b"1\t0\t12\ta.bin\n", b""))
    with pytest.raises(B.NativeReaderError, match="invalid entry"):
        B.list_entries(cli, archive)


def test_extract_enforces_caller_budget_before_native_publication(monkeypatch, tmp_path: Path) -> None:
    cli = tmp_path / "cmpct-portable"
    cli.write_bytes(b"x")
    archive = tmp_path / "a.cmpct"
    archive.write_bytes(b"x")
    destination = tmp_path / "out"
    calls: list[tuple[str, ...]] = []

    def fake_run(_cli: Path, *args: str, **_kwargs) -> B.NativeRun:
        calls.append(tuple(args))
        if args[0] == "list":
            return B.NativeRun(b"0\t0\t9\ta.bin\n1\t0\t5\tb.bin\n", b"")
        if args[0] == "extract":
            return B.NativeRun(b"", b"")
        raise AssertionError(args)

    monkeypatch.setattr(B, "_run", fake_run)
    with pytest.raises(B.NativeReaderError, match="exceeding caller budget"):
        B.extract_g04(cli, archive, destination, max_output_bytes=13)
    assert [call[0] for call in calls] == ["list"]

    calls.clear()
    receipt = B.extract_g04(cli, archive, destination, max_output_bytes=14)
    assert receipt["ok"] is True
    assert receipt["declared_regular_bytes"] == 14
    assert receipt["transactional_native_extract"] is True
    assert [call[0] for call in calls] == ["list", "extract"]


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
