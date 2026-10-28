from __future__ import annotations

"""Focused command-policy tests for detached media determinism repair-v5."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "benchmarks" / "neutral_hostile_determinism_repair_v5.py"


def _module():
    spec = importlib.util.spec_from_file_location("cmpct_media_repair_v5_test", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_canonical_args_force_common_ffmpeg_cpu_surface() -> None:
    mod = _module()
    rendered = mod._canonical_ffmpeg_args(["-i", "source.wav", "-c:a", "flac", "out.flac"])
    assert rendered[:8] == [
        "-cpuflags", "0", "-cpucount", "1", "-filter_threads", "1", "-filter_complex_threads", "1"
    ]
    assert rendered[-6:] == ["-bitexact", "-threads", "1", "-map_metadata", "-1", "out.flac"]
    assert "-x264-params" not in rendered


def test_canonical_x264_args_pin_cross_cpu_encoder_path() -> None:
    mod = _module()
    rendered = mod._canonical_ffmpeg_args([
        "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30",
        "-c:v", "libx264", "-preset", "medium", "out.mp4",
    ])
    index = rendered.index("-x264-params")
    assert rendered[index + 1] == mod.X264_CANONICAL_PARAMS
    assert "cpu-independent=1" in rendered[index + 1]
    assert "asm=0" in rendered[index + 1]
    assert "lookahead-threads=1" in rendered[index + 1]


def test_v5_wrapper_is_idempotent(monkeypatch) -> None:
    mod = _module()
    calls = []
    neutral = SimpleNamespace(run_ffmpeg=lambda args: calls.append(list(args)))
    monkeypatch.setattr(mod.BASE, "install_generation_hooks", lambda module: None)
    mod.install_generation_hooks(neutral)
    first = neutral.run_ffmpeg
    mod.install_generation_hooks(neutral)
    assert neutral.run_ffmpeg is first
    neutral.run_ffmpeg(["-i", "x.wav", "-c:a", "flac", "x.flac"])
    assert calls and calls[0][0:2] == ["-cpuflags", "0"]
