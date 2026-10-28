from __future__ import annotations

"""Neutral/hostile benchmark substrate repair-v5 — CPU-canonical media production.

Repair-v4 proved path-local determinism but failed a fresh-run comparison: two GitHub hosts emitted
different media bytes despite `-bitexact`, single encoder threading and stripped metadata.  Repair-v5
therefore addresses the remaining variable explicitly: CPU feature dispatch.

The historical corpus and repair-v3 evidence remain immutable.  This module composes repair-v3 and adds
only a candidate media producer policy.  Acceptance requires byte-identical media manifests and exact
v0.28 bytes across multiple independent GitHub runner attempts.

Footnote: FFmpeg documents `-cpuflags 0` and `-cpucount` as testing controls for forcing CPU capability
selection. x264 exposes `cpu-independent` specifically for exact reproducibility across different CPUs;
its `asm` parameter can disable CPU-optimized code paths entirely.  The benchmark prefers reproducible
source identity over media-generation speed, so the 10-second synthetic H.264 clip uses the conservative
canonical path while remaining a real H.264/AAC MP4.
"""

import functools
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "neutral_hostile_determinism_repair_v1.py"
MEDIA_NAME = "03_media_library"


def _load_base():
    name = "cmpct_neutral_hostile_repair_v3_for_v5"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, BASE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BASE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_base()
AFFECTED = set(BASE.AFFECTED) | {MEDIA_NAME}
X264_CANONICAL_PARAMS = (
    "cpu-independent=1:asm=0:threads=1:lookahead-threads=1:"
    "sliced-threads=0:sync-lookahead=0"
)


def _canonical_ffmpeg_args(args: list[str]) -> list[str]:
    if not args:
        raise RuntimeError("FFmpeg repair received an empty argument vector")
    output = str(args[-1])
    body = list(args[:-1])

    # Footnote: these are global/test controls and must precede input options.  They make FFmpeg expose
    # one software CPU surface to filters/native codecs and prevent host core count from changing an
    # automatic thread decision.
    stable = [
        "-cpuflags", "0",
        "-cpucount", "1",
        "-filter_threads", "1",
        "-filter_complex_threads", "1",
        *body,
    ]
    if "libx264" in body:
        # Footnote: `cpu-independent` is x264's cross-CPU reproducibility switch. `asm=0` is deliberately
        # redundant defense for the benchmark fixture: the clip is tiny, while an ISA-dependent output
        # would poison every future compression comparison built on this supposedly fixed source tree.
        stable += ["-x264-params", X264_CANONICAL_PARAMS]
    stable += [
        "-bitexact",
        "-threads", "1",
        "-map_metadata", "-1",
        output,
    ]
    return stable


def install_generation_hooks(neutral_module) -> None:
    BASE.install_generation_hooks(neutral_module)
    current = getattr(neutral_module, "run_ffmpeg", None)
    if current is None:
        raise RuntimeError("neutral hostile generator no longer exposes run_ffmpeg")
    if getattr(current, "_cmpct_media_repair_v5_wrapper", False):
        return

    @functools.wraps(current)
    def deterministic_ffmpeg(args: list[str]) -> None:
        return current(_canonical_ffmpeg_args(args))

    deterministic_ffmpeg._cmpct_media_repair_v5_wrapper = True
    neutral_module.run_ffmpeg = deterministic_ffmpeg


def normalize_workload(workload: Path) -> None:
    if workload.name == MEDIA_NAME:
        # Producer determinism must stand on its own. Rewriting a finished MP4/MP3 after generation could
        # hide an encoder drift and turn the normalizer itself into an unreviewed transcoder.
        return
    BASE.normalize_workload(workload)


def normalize_root(root: Path) -> None:
    for name in sorted(AFFECTED):
        path = root / name
        if path.exists():
            normalize_workload(path)
