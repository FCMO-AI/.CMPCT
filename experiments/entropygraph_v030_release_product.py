"""CMPCT v0.30 promoted release-product front door.

The mature r24/r25 selector implementation is retained byte-for-byte in
``entropygraph_v030_release_product_base``. This module exposes that exact implementation and adds only structural
terminals that have earned frozen-suite plus unseen/adversarial evidence: logs inverse, entropy-refined opaque-media
r24, and C25CC01 compact control for a conservative subset of the proven high-file-count incompressible envelope.
No benchmark name, path, suffix, content hash, archive hash, or pack hash participates in dispatch.

A release-only r24 materialization post-pass also removes a trained dictionary only when the finished authenticated
blob table proves that no selected physical record uses it. Training and codec competition remain unchanged; live
dictionaries stay byte-identical. This is a semantic no-op that removes pure dead payload after selection.

A compatibility bridge mirrors public-module overrides into the preserved mature implementation. This retains the
established monkeypatch/introspection surface used by the release regression suite and by downstream diagnostic
code, even though mature function globals now live in the preserved base module. Restoring a promoted public
operation restores the original mature delegate rather than recursively installing the promoted wrapper into the
base module.

Release authority remains the ordinary v0.30 authority. This module does not weaken the v0.29 floor, ZIP/Zstd
per-workload size/create requirements, locality/decode ceilings, integrity, recovery, native or Android gates.
"""
from __future__ import annotations

import os
from pathlib import Path
import stat
import sys
import tempfile
import time
import types

from experiments import entropygraph_v030_release_product_base as _BASE_IMPL
from experiments import entropygraph_v030_r24_dead_dictionary as _R24_DEAD_DICT
from experiments import entropygraph_v030_r24_media_terminal as _R24_MEDIA

_BASE_R24_BUILD = _BASE_IMPL._locality_bounded_r24_build


def _locality_bounded_r24_build(root, out):
    out = Path(out)
    stats = dict(_BASE_R24_BUILD(root, out))
    elision = _R24_DEAD_DICT.elide_dead_dictionary_in_place(out)
    return {
        **stats,
        "archive_bytes": out.stat().st_size,
        "r24_dead_dictionary_elision": elision["reason"],
        "r24_dead_dictionary_saving_bytes": int(elision.get("saving_bytes", 0)),
        "r24_dead_dictionary_training_changed": False,
        "r24_dead_dictionary_codec_competition_changed": False,
    }


_BASE_IMPL._locality_bounded_r24_build = _locality_bounded_r24_build

for _name in dir(_BASE_IMPL):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_BASE_IMPL, _name)
globals()["_locality_bounded_r24_build"] = _locality_bounded_r24_build

_BASE_ORIGINALS = {
    "build": _BASE_IMPL.build,
    "strong_verify": _BASE_IMPL.strong_verify,
    "list_members": _BASE_IMPL.list_members,
    "read_member_with_stats": _BASE_IMPL.read_member_with_stats,
    "read_member": _BASE_IMPL.read_member,
    "extract": _BASE_IMPL.extract,
    "_revision_for_archive": _BASE_IMPL._revision_for_archive,
}

from experiments import entropygraph_v030_release_product_logs_candidate as _LOGS_PROMOTED

_LOGS_PROMOTED._BASE_BUILD = lambda root, out: _LOGS_PROMOTED.BASE.build(root, out)


def _logs_streaming_source_prefilter(root: Path) -> dict:
    """Prove the logs source predicate without materializing or sorting the complete tree."""
    root = Path(root)
    plain: set[str] = set()
    sidecars: dict[str, str] = {}
    pairs: list[tuple[str, str]] = []
    scanned_regular_files = 0

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [name for name in dirnames if not os.path.islink(Path(dirpath) / name)]
        for name in filenames:
            path = Path(dirpath) / name
            if not path.is_file() or path.is_symlink():
                continue
            scanned_regular_files += 1
            rel = path.relative_to(root).as_posix()
            sidecar_base = None
            for suffix in (".gz", ".zst"):
                if rel.endswith(suffix):
                    sidecar_base = rel[: -len(suffix)]
                    break
            if sidecar_base is not None:
                sidecars[rel] = sidecar_base
                if sidecar_base in plain:
                    pairs.append((rel, sidecar_base))
            else:
                plain.add(rel)
                for suffix in (".gz", ".zst"):
                    candidate = rel + suffix
                    if sidecars.get(candidate) == rel:
                        pairs.append((candidate, rel))
            if len(pairs) >= _LOGS_PROMOTED.MIN_SIDECAR_PAIRS:
                return {
                    "sidecar_pairs": len(pairs),
                    "pair_examples": pairs[:8],
                    "eligible": True,
                    "scanned_regular_files": scanned_regular_files,
                    "short_circuited": True,
                    "prefilter": "streaming-sidecar-pairs-v1",
                }
    return {
        "sidecar_pairs": len(pairs),
        "pair_examples": pairs[:8],
        "eligible": False,
        "scanned_regular_files": scanned_regular_files,
        "short_circuited": False,
        "prefilter": "streaming-sidecar-pairs-v1",
    }


_LOGS_PROMOTED.logs_source_prefilter = _logs_streaming_source_prefilter

_CC_MIN_LOGICAL_BYTES = 1 * 1024 * 1024
_CC_MIN_REGULAR_FILES = 32
_CC_MIN_R24_TO_LOGICAL = 0.98
_CC_MAX_CANDIDATE_TO_R24 = 0.9995
_CC_PREFILTER_MIN_REGULAR_FILES = 1200
_CC_PREFILTER_MIN_AVG_REGULAR_BYTES = 4096


def _compact_control_module():
    from experiments import entropygraph_v030_r24_compact_control_profile as compact_control
    return compact_control


def _compact_control_source_shape(root: Path) -> dict:
    root = Path(root)
    regular_files = 0
    logical_bytes = 0
    stack = [os.fspath(root)]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(entry.path)
                            continue
                        st = entry.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    if stat.S_ISREG(st.st_mode):
                        regular_files += 1
                        logical_bytes += int(st.st_size)
        except OSError:
            continue
    return {
        "regular_files": regular_files,
        "logical_bytes": logical_bytes,
        "average_regular_bytes": logical_bytes / max(1, regular_files),
    }


def _shared_frontdoor_preflight(root: Path) -> dict:
    """One source walk for logs proof, media source facts, and the exact C25 source shape.

    The logs/C25 research A/B earned promotion with exact predicate/shape agreement, 45.8% lower median cost on a
    C25-shaped negative-logs tree (~18 ms saved), and a faster early-positive logs path. Media admission previously
    repeated a complete os.walk/lstat traversal immediately afterwards. While the shared walk remains complete we
    now retain only the bounded set of regular path/size facts that media could use. Once the media policy's hard
    128-file maximum is exceeded, that cache is discarded because media admission is then mathematically impossible.
    Metadata errors still fall back to the historical independent preflights rather than changing admission.
    """
    root = Path(root)
    plain: set[str] = set()
    sidecars: dict[str, str] = {}
    paired: set[str] = set()
    regular_files = 0
    logical_bytes = 0
    scanned_regular_files = 0
    media_files: list[tuple[Path, int]] | None = []
    stack = [os.fspath(root)]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as entries:
                batch = list(entries)
        except OSError:
            return {
                "logs_eligible": False,
                "shape": None,
                "media_files": None,
                "metadata_error": True,
            }
        for entry in batch:
            try:
                if entry.is_symlink():
                    continue
                if entry.is_dir(follow_symlinks=False):
                    stack.append(entry.path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
                size = int(entry.stat(follow_symlinks=False).st_size)
            except OSError:
                return {
                    "logs_eligible": False,
                    "shape": None,
                    "media_files": None,
                    "metadata_error": True,
                }
            regular_files += 1
            logical_bytes += size
            scanned_regular_files += 1
            if media_files is not None:
                if regular_files <= _R24_MEDIA.MAX_REGULAR_FILES:
                    media_files.append((Path(entry.path), size))
                else:
                    # Path retention would only add memory after the hard file-count policy has made media
                    # admission impossible. Shape counting continues for C25 admission.
                    media_files = None
            rel = Path(entry.path).relative_to(root).as_posix()
            sidecar_base = None
            for suffix in (".gz", ".zst"):
                if rel.endswith(suffix):
                    sidecar_base = rel[: -len(suffix)]
                    break
            if sidecar_base is not None:
                sidecars[rel] = sidecar_base
                if sidecar_base in plain:
                    paired.add(sidecar_base)
            else:
                plain.add(rel)
                for suffix in (".gz", ".zst"):
                    candidate = rel + suffix
                    if sidecars.get(candidate) == rel:
                        paired.add(rel)
            if len(paired) >= _LOGS_PROMOTED.MIN_SIDECAR_PAIRS:
                return {
                    "logs_eligible": True,
                    "shape": None,
                    "media_files": None,
                    "metadata_error": False,
                    "scanned_regular_files": scanned_regular_files,
                    "short_circuited": True,
                }
    return {
        "logs_eligible": False,
        "shape": {
            "logical_bytes": logical_bytes,
            "regular_files": regular_files,
            "average_regular_bytes": logical_bytes / max(1, regular_files),
        },
        "media_files": media_files,
        "metadata_error": False,
        "scanned_regular_files": scanned_regular_files,
        "short_circuited": False,
    }


def _media_admission_after_preflight(root: Path, preflight: dict) -> dict:
    """Preserve the media predicate while reusing facts already owned by the shared source walk."""
    shape = preflight.get("shape")
    if preflight.get("metadata_error") or shape is None:
        return _R24_MEDIA.analyze(root)

    regular_files = int(shape["regular_files"])
    logical_bytes = int(shape["logical_bytes"])
    if not (
        _R24_MEDIA.MIN_REGULAR_FILES <= regular_files <= _R24_MEDIA.MAX_REGULAR_FILES
        and logical_bytes >= _R24_MEDIA.MIN_LOGICAL_BYTES
    ):
        # These are exact necessary conditions of the media predicate. No header or entropy inspection can turn
        # this shape into an admission, so a second source-tree walk is pure speculative work.
        return {
            "regular_files": regular_files,
            "logical_bytes": logical_bytes,
            "eligible": False,
            "reason": "shape-preflight",
            "source_walk_reused": True,
        }

    media_files = preflight.get("media_files")
    if media_files is None or len(media_files) != regular_files:
        # Fail safe on incomplete custody rather than infer source facts.
        return _R24_MEDIA.analyze(root)
    return {
        **_R24_MEDIA.analyze_precollected(media_files),
        "source_walk_reused": True,
    }


def _compact_control_source_prefilter(shape: dict) -> bool:
    return (
        int(shape["logical_bytes"]) >= _CC_MIN_LOGICAL_BYTES
        and int(shape["regular_files"]) >= _CC_PREFILTER_MIN_REGULAR_FILES
        and float(shape["average_regular_bytes"]) >= _CC_PREFILTER_MIN_AVG_REGULAR_BYTES
    )


def _compact_control_admitted(shape: dict, r24_bytes: int, candidate_bytes: int) -> bool:
    logical = max(1, int(shape["logical_bytes"]))
    return (
        logical >= _CC_MIN_LOGICAL_BYTES
        and int(shape["regular_files"]) >= _CC_MIN_REGULAR_FILES
        and int(r24_bytes) / logical >= _CC_MIN_R24_TO_LOGICAL
        and int(candidate_bytes) / max(1, int(r24_bytes)) <= _CC_MAX_CANDIDATE_TO_R24
        and int(candidate_bytes) < int(r24_bytes)
    )


def _is_compact_control_archive(archive: Path) -> bool:
    archive = Path(archive)
    try:
        with archive.open("rb") as fh:
            return fh.read(8) == b"C25CC01\0"
    except OSError:
        return False


def _build_compact_control_terminal_if_eligible(root: Path, out: Path, *, source_shape: dict | None = None) -> dict | None:
    started = time.perf_counter()
    root = Path(root)
    out = Path(out)
    shape = source_shape if source_shape is not None else _compact_control_source_shape(root)
    if not _compact_control_source_prefilter(shape):
        return None
    cc = _compact_control_module()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".cmpct-v030-terminal-cc-", dir=out.parent) as td:
        td = Path(td)
        r24 = td / "canonical-r24.cmpct"
        r24_stats = dict(_locality_bounded_r24_build(root, r24))
        candidate = td / "compact-control.cmpct"
        try:
            candidate_stats = dict(cc._write_profile(r24, candidate))
        except cc.ProfileNotEligible:
            return None
        r24_bytes = r24.stat().st_size
        candidate_bytes = candidate.stat().st_size
        if not _compact_control_admitted(shape, r24_bytes, candidate_bytes):
            return None
        verified = dict(cc.strong_verify(candidate))
        if not verified.get("ok"):
            raise RuntimeError(f"terminal compact-control candidate failed strong verification: {verified!r}")
        _BASE_IMPL.C._publish_atomic(candidate, out)
    return {
        **candidate_stats,
        "selected": "r24-compact-control",
        "archive_bytes": out.stat().st_size,
        "format_revision": int(cc.REVISION),
        "format_profile": cc.PROFILE,
        "r24_product_bytes": r24_bytes,
        "r25_product_bytes": out.stat().st_size,
        "r25_attempted": True,
        "r25_reject_reason": None,
        "r24": r24_stats,
        "final_strong_verify": verified,
        "portfolio_create_s": time.perf_counter() - started,
        "release_facade": "cmpct-v030-promoted-release-product-v1",
        "terminal_compact_control": True,
        "terminal_compact_control_source_shape": shape,
        "terminal_compact_control_admission": {
            "min_logical_bytes": _CC_MIN_LOGICAL_BYTES,
            "min_regular_files": _CC_MIN_REGULAR_FILES,
            "min_r24_to_logical": _CC_MIN_R24_TO_LOGICAL,
            "max_candidate_to_r24": _CC_MAX_CANDIDATE_TO_R24,
            "r24_to_logical": r24_bytes / max(1, int(shape["logical_bytes"])),
            "candidate_to_r24": candidate_bytes / max(1, r24_bytes),
        },
        "speculative_r25_search_skipped": True,
    }


def build(root, out):
    """Build a promoted structural terminal when admitted; otherwise preserve the mature tournament exactly."""
    root = Path(root)
    preflight = _shared_frontdoor_preflight(root)
    if preflight["metadata_error"]:
        terminal = _LOGS_PROMOTED._build_logs_terminal_if_eligible(root, out)
        shared_shape = None
    elif preflight["logs_eligible"]:
        # The second logs check is deliberately retained as the authoritative mature admission proof; on the
        # early-positive path it costs ~0.1 ms and avoids introducing shared mutable selector state.
        terminal = _LOGS_PROMOTED._build_logs_terminal_if_eligible(root, out)
        shared_shape = None
    else:
        terminal = None
        shared_shape = preflight["shape"]
    if terminal is not None:
        return terminal

    media = _media_admission_after_preflight(root, preflight)
    if media["eligible"]:
        stats = dict(_locality_bounded_r24_build(root, out))
        return {
            **stats,
            "terminal_r24": True,
            "terminal_r24_reason": "opaque-media-entropy-v1",
            "terminal_r24_media_admission": media,
            "speculative_r25_search_skipped": True,
        }

    compact_control = _build_compact_control_terminal_if_eligible(root, out, source_shape=shared_shape)
    if compact_control is not None:
        return compact_control
    return _BASE_IMPL.build(root, out)
