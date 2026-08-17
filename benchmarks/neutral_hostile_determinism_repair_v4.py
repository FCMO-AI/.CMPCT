from __future__ import annotations

"""Neutral/hostile benchmark substrate repair-v4 — deterministic media producer policy.

Repair-v3 remains immutable evidence for Office/log/backup producer drift.  Repair-v4 composes that
accepted repair and adds only the media producer boundary after a later inherited-frontier run proved
that ``03_media_library`` could still change bytes despite unchanged generator source, runner image,
FFmpeg package, x264 package and Python dependency pins.

The historical media row is not rewritten.  This module merely defines a candidate *new substrate
identity* whose acceptance requires two byte-identical regenerations under distinct parent directories.

Footnote: FFmpeg exposes ``-bitexact`` specifically to enable bitexact mode for demuxer/muxer and
(de/en)coders.  The wrapper also forces one encoder thread and strips inherited metadata.  These settings
are benchmark-production controls, not CMPCT compression knobs: every archive engine must consume the
same repaired files after the identity is accepted.
"""

import functools
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE_PATH = HERE / "neutral_hostile_determinism_repair_v1.py"
MEDIA_NAME = "03_media_library"


def _load_base():
    name = "cmpct_neutral_hostile_repair_v3_base"
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


def install_generation_hooks(neutral_module) -> None:
    """Compose repair-v3 hooks with a deterministic FFmpeg output policy for media only."""
    BASE.install_generation_hooks(neutral_module)
    current = getattr(neutral_module, "run_ffmpeg", None)
    if current is None:
        raise RuntimeError("neutral hostile generator no longer exposes run_ffmpeg")
    if getattr(current, "_cmpct_media_repair_v4_wrapper", False):
        return

    @functools.wraps(current)
    def deterministic_ffmpeg(args: list[str]) -> None:
        if not args:
            raise RuntimeError("FFmpeg repair received an empty argument vector")
        output = Path(args[-1])
        # Footnote: append output-scoped controls immediately before the output path.  ``-bitexact``
        # covers muxer + encoder state, ``-threads 1`` removes scheduler-dependent encoder decisions,
        # and ``-map_metadata -1`` prevents input/container metadata from becoming hidden identity.
        stable = [
            *args[:-1],
            "-bitexact",
            "-threads", "1",
            "-map_metadata", "-1",
            str(output),
        ]
        return current(stable)

    deterministic_ffmpeg._cmpct_media_repair_v4_wrapper = True
    neutral_module.run_ffmpeg = deterministic_ffmpeg


def normalize_workload(workload: Path) -> None:
    # Media determinism is enforced at generation time.  Post-generation byte rewriting would make it
    # harder to tell whether the codec/container producer is actually deterministic, so media is a no-op
    # here and must pass the cross-path proof on its naturally emitted bytes.
    if workload.name == MEDIA_NAME:
        return
    BASE.normalize_workload(workload)


def normalize_root(root: Path) -> None:
    for name in sorted(AFFECTED):
        path = root / name
        if path.exists():
            normalize_workload(path)
