from __future__ import annotations

"""Focused contract tests for the candidate media determinism repair-v4."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v4.py"


def _module():
    spec = importlib.util.spec_from_file_location("cmpct_media_repair_v4_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_media_ffmpeg_wrapper_injects_output_scoped_determinism_controls(monkeypatch) -> None:
    mod = _module()
    calls: list[list[str]] = []

    def fake_run(args: list[str]) -> None:
        calls.append(list(args))

    neutral = SimpleNamespace(run_ffmpeg=fake_run)
    # Footnote: this unit test isolates the media wrapper; repair-v3's ReportLab hook has its own tests
    # and would unnecessarily require document-generation dependencies in the ordinary regression job.
    monkeypatch.setattr(mod.BASE, "install_generation_hooks", lambda module: None)
    mod.install_generation_hooks(neutral)
    neutral.run_ffmpeg(["-i", "source.wav", "-c:a", "flac", "out.flac"])

    assert len(calls) == 1
    rendered = calls[0]
    assert rendered[-1] == "out.flac"
    assert rendered[-6:-1] == ["-bitexact", "-threads", "1", "-map_metadata", "-1"]


def test_media_ffmpeg_wrapper_is_idempotent(monkeypatch) -> None:
    mod = _module()
    calls = []
    neutral = SimpleNamespace(run_ffmpeg=lambda args: calls.append(list(args)))
    monkeypatch.setattr(mod.BASE, "install_generation_hooks", lambda module: None)
    mod.install_generation_hooks(neutral)
    first = neutral.run_ffmpeg
    mod.install_generation_hooks(neutral)
    assert neutral.run_ffmpeg is first


def test_media_normalization_does_not_rewrite_emitted_bytes(tmp_path: Path) -> None:
    mod = _module()
    workload = tmp_path / mod.MEDIA_NAME
    workload.mkdir()
    payload = workload / "clip_h264.mp4"
    payload.write_bytes(b"already-produced-media-bytes")
    mod.normalize_workload(workload)
    assert payload.read_bytes() == b"already-produced-media-bytes"
