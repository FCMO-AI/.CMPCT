from __future__ import annotations

import builtins
import json
import sys
import wave
from pathlib import Path

import cmpct.builder as builder
from cmpct.cli import main


def _write_wav(path: Path) -> bytes:
    frames = b"\x00\x00" * 4096
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(frames)
    return path.read_bytes()


def test_cli_audio_without_optional_modules_uses_generic_codec_and_round_trips(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    wav_path = source / "tone.wav"
    original = _write_wav(wav_path)
    archive = tmp_path / "audio.cmpct"
    restored = tmp_path / "restored"

    real_import = builtins.__import__

    def no_audio_modules(name, *args, **kwargs):
        if name.split(".", 1)[0] in {"numpy", "soundfile"}:
            raise ModuleNotFoundError(f"blocked optional module: {name}", name=name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", no_audio_modules)

    monkeypatch.setattr(sys, "argv", ["cmpct", "create", str(source), str(archive)])
    main()
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv", ["cmpct", "extract", str(archive), str(restored)])
    main()
    assert (restored / "tone.wav").read_bytes() == original

    monkeypatch.setattr(sys, "argv", ["cmpct", "info", str(archive)])
    main()
    info = json.loads(capsys.readouterr().out)
    assert "wav-generic-fallback:no-audio-modules" in info["features"]
    assert info["codec_counts"].get("wavflac", 0) == 0
    assert sum(info["codec_counts"].get(name, 0) for name in ("zstd", "deflate")) > 0


def test_cli_audio_modules_available_keeps_wavflac_candidate(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _write_wav(source / "tone.wav")
    archive = tmp_path / "audio.cmpct"

    # A tiny winning FLAC payload exercises the installed-module route without requiring
    # machine-specific libsndfile behavior in this dependency-optional regression test.
    monkeypatch.setattr(builder, "_audio_modules", lambda: (object(), object()))
    monkeypatch.setattr(builder, "wavflac_compress", lambda raw: (b"f", b""))
    monkeypatch.setattr(sys, "argv", ["cmpct", "create", str(source), str(archive)])
    main()
    capsys.readouterr()

    monkeypatch.setattr(sys, "argv", ["cmpct", "info", str(archive)])
    main()
    info = json.loads(capsys.readouterr().out)
    assert info["codec_counts"].get("wavflac", 0) > 0
    assert "wav-generic-fallback:no-audio-modules" not in info["features"]
