from __future__ import annotations

"""Portable neutral/hostile substrate repair v4: add FFmpeg-independent media identity.

Repair-v3 remains immutable and continues to define the accepted Office/logs/backups identities. This
wrapper composes that repair and adds one new rule for `03_media_library`: the three files historically
produced by external FFmpeg codec builds are excluded from the portable benchmark identity.

The measured media workload remains a real valid-media corpus: 14 photography-like JPEGs, 10 PNG UI
screenshots and one deterministic stereo PCM WAV. Those bytes come from the pinned Python/Numpy/Pillow/
stdlib path rather than an unpinned system codec stack.

Footnote: because the excluded transcodes are deleted before measurement, the v4 generation hook does not
invoke FFmpeg merely to create throwaway bytes. It writes explicit excluded placeholders at those three
call sites; normalization then requires and removes them. Historical generator/evidence stays untouched.
"""

import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
V3_PATH = HERE / "neutral_hostile_determinism_repair_v1.py"
MEDIA_WORKLOAD = "03_media_library"
VOLATILE_MEDIA = (
    "clip_h264.mp4",
    "field_recording.flac",
    "field_recording.mp3",
)


def _load_v3():
    spec = importlib.util.spec_from_file_location("cmpct_neutral_repair_v3_for_v4", V3_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load neutral/hostile repair-v3 implementation")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V3 = _load_v3()
AFFECTED = set(V3.AFFECTED) | {MEDIA_WORKLOAD}


def install_generation_hooks(neutral_module) -> None:
    V3.install_generation_hooks(neutral_module)
    current = getattr(neutral_module, "run_ffmpeg", None)
    if current is None:
        raise RuntimeError("neutral hostile generator no longer exposes run_ffmpeg")
    if getattr(current, "_cmpct_v4_excluded_media_wrapper", False):
        return

    def excluded_media_call(args: list[str]) -> None:
        output = Path(args[-1])
        if output.name not in VOLATILE_MEDIA:
            # Footnote: fail closed instead of silently bypassing a future FFmpeg-generated corpus member
            # that v4 never preregistered for exclusion.
            return current(args)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes((f"CMPCT-v4-excluded-external-codec:{output.name}\n").encode("ascii"))

    excluded_media_call._cmpct_v4_excluded_media_wrapper = True
    neutral_module.run_ffmpeg = excluded_media_call


def _repair_media(workload: Path) -> None:
    missing = [name for name in VOLATILE_MEDIA if not (workload / name).is_file()]
    if missing:
        raise RuntimeError(f"media generator contract changed; missing excluded outputs: {missing}")
    for name in VOLATILE_MEDIA:
        (workload / name).unlink()

    # Footnote: fail closed if the repair accidentally strips the stable media core. This is not a broad
    # corpus simplifier: valid JPEG/PNG/WAV content must remain present before v4 can be accepted.
    suffixes = [path.suffix.lower() for path in workload.iterdir() if path.is_file()]
    if suffixes.count(".jpg") != 14 or suffixes.count(".png") != 10 or suffixes.count(".wav") != 1:
        raise RuntimeError("media repair no longer preserves the expected 14 JPEG / 10 PNG / 1 WAV core")


def normalize_workload(workload: Path) -> None:
    if workload.name == MEDIA_WORKLOAD:
        _repair_media(workload)
    else:
        V3.normalize_workload(workload)


def normalize_root(root: Path) -> None:
    for name in sorted(AFFECTED):
        path = root / name
        if path.exists():
            normalize_workload(path)
