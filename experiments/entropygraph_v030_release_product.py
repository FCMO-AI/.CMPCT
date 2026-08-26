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
    """Prove the logs source predicate without materializing or sorting the complete tree.

    The only decision needed before constructing the real r24/logs candidates is whether at least two regular
    .gz/.zst sidecars have regular unsuffixed siblings. Pair discovery is monotonic, so the traversal may terminate
    exactly after the second proven pair. Symlinks are excluded identically to the predecessor prefilter. The
    nine-round oracle on a 12k-file early-positive tree measured ~0.17 ms versus ~214.6 ms for the predecessor while
    preserving eligibility on positive, single-pair, no-pair and orphan-sidecar adversarial cases.
    """
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


# Promotion changes only the source preflight used by the already-promoted logs terminal. Actual r24/logs candidate
# construction, admission, strong verification, publication and all external release gates remain unchanged.
_LOGS_PROMOTED.logs_source_prefilter = _logs_streaming_source_prefilter

# C25CC01's actual admission law is the already-audited four-feature envelope below. The source-only prefilter is a
# deliberately conservative subset used solely to avoid building a redundant r24 candidate on unrelated families.
# It does not grant publication: every prefiltered tree must still satisfy the exact r24/candidate byte ratios after
# those real artifacts exist. The frozen encrypted-like target plus independent 1162- and 1780-file entropy mosaics
# fall inside this cheap subset; developer/tiny-file/backups/medium-binary frozen families do not.
_CC_MIN_LOGICAL_BYTES = 1 * 1024 * 1024
_CC_MIN_REGULAR_FILES = 32
_CC_MIN_R24_TO_LOGICAL = 0.98
_CC_MAX_CANDIDATE_TO_R24 = 0.9995
_CC_PREFILTER_MIN_REGULAR_FILES = 1000
_CC_PREFILTER_MIN_AVG_REGULAR_BYTES = 4096


def _compact_control_module():
    # Lazy import is required because the candidate module delegates reconstructed r24 logical operations back to
    # this release-product facade. Importing it while this module is still initializing would create a cycle.
    from experiments import entropygraph_v030_r24_compact_control_profile as compact_control

    return compact_control


def _compact_control_source_shape(root: Path) -> dict:
    """Count regular files/bytes with a single DirEntry traversal.

    This is deliberately semantics-equivalent to the former ``os.walk`` + ``Path`` + ``lstat`` pass: symlinked
    files/directories are excluded, filesystem races remain fail-open for this cheap preflight, and only regular
    files contribute. ``os.scandir`` lets the OS-provided DirEntry cache carry type/stat information so high-file-
    count C25CC01 candidates do not burn part of their narrow ZIP speed margin constructing Path objects and issuing
    redundant metadata calls before the real r24 build even starts.
    """
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


def _build_compact_control_terminal_if_eligible(root: Path, out: Path) -> dict | None:
    """Publish C25CC01 only inside the measured identity-free structural envelope.

    The prefilter only decides whether the cheap r24+control preflight is worth paying. Publication is owned by the
    frozen exact admission rule: actual r24 must be effectively incompressible and actual compact control must save
    at least 0.05%. The selected candidate is strongly verified before atomic publication. No comparator result is
    consulted at runtime; ZIP/Zstd remain external release authorities.
    """
    started = time.perf_counter()
    root = Path(root)
    out = Path(out)
    shape = _compact_control_source_shape(root)
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
    terminal = _LOGS_PROMOTED._build_logs_terminal_if_eligible(root, out)
    if terminal is not None:
        return terminal

    media = _R24_MEDIA.analyze(root)
    if media["eligible"]:
        stats = dict(_locality_bounded_r24_build(root, out))
        return {
            **stats,
            "terminal_r24": True,
            "terminal_r24_reason": "opaque-media-entropy-v1",
            "terminal_r24_media_admission": media,
            "speculative_r25_search_skipped": True,
        }

    compact_control = _build_compact_control_terminal_if_eligible(root, out)
    if compact_control is not None:
        return compact_control
    return _BASE_IMPL.build(root, out)


def strong_verify(archive):
    if _is_compact_control_archive(archive):
        return _compact_control_module().strong_verify(archive)
    if _LOGS_PROMOTED._is_logs_archive(archive):
        return _LOGS_PROMOTED.strong_verify(archive)
    return _BASE_IMPL.strong_verify(archive)


def list_members(archive):
    if _is_compact_control_archive(archive):
        return _compact_control_module().list_members(archive)
    if _LOGS_PROMOTED._is_logs_archive(archive):
        return _LOGS_PROMOTED.list_members(archive)
    return _BASE_IMPL.list_members(archive)


def read_member_with_stats(archive, rel):
    if _is_compact_control_archive(archive):
        return _compact_control_module().read_member_with_stats(archive, rel)
    if _LOGS_PROMOTED._is_logs_archive(archive):
        return _LOGS_PROMOTED.read_member_with_stats(archive, rel)
    return _BASE_IMPL.read_member_with_stats(archive, rel)


def read_member(archive, rel):
    if _is_compact_control_archive(archive):
        return _compact_control_module().read_member(archive, rel)
    if _LOGS_PROMOTED._is_logs_archive(archive):
        return _LOGS_PROMOTED.read_member(archive, rel)
    return _BASE_IMPL.read_member(archive, rel)


def extract(archive, dst, *, max_output_bytes=POLICY.DEFAULT_MAX_EXTRACT_BYTES, safe_symlinks=True):
    if _is_compact_control_archive(archive):
        return _compact_control_module().extract(
            archive,
            dst,
            max_output_bytes=max_output_bytes,
            safe_symlinks=safe_symlinks,
        )
    if _LOGS_PROMOTED._is_logs_archive(archive):
        return _LOGS_PROMOTED.extract(
            archive,
            dst,
            max_output_bytes=max_output_bytes,
            safe_symlinks=safe_symlinks,
        )
    return _BASE_IMPL.extract(
        archive,
        dst,
        max_output_bytes=max_output_bytes,
        safe_symlinks=safe_symlinks,
    )


def _revision_for_archive(archive):
    if _is_compact_control_archive(archive):
        cc = _compact_control_module()
        return cc.REVISION, cc.PROFILE
    if _LOGS_PROMOTED._is_logs_archive(archive):
        return REVISION, _LOGS_PROMOTED.LOGS_PROFILE
    return _BASE_IMPL._revision_for_archive(archive)


LOGS = _LOGS_PROMOTED.LOGS
LOGS_MAGIC = _LOGS_PROMOTED.LOGS_MAGIC
LOGS_TAIL = _LOGS_PROMOTED.LOGS_TAIL
LOGS_PROFILE = _LOGS_PROMOTED.LOGS_PROFILE
logs_source_prefilter = _LOGS_PROMOTED.logs_source_prefilter

PROMOTED_LOGS_INVERSE = True
PROMOTED_LOGS_EVIDENCE = (
    "all-15 structural admission + external/v0.29 selector shadows + native production dispatch + Android/JNI"
)
PROMOTED_LOGS_STREAMING_PREFILTER = True
PROMOTED_LOGS_STREAMING_PREFILTER_EVIDENCE = (
    "exact adversarial eligibility + nine-round 12k-file A/B: ~99.9% prefilter speedup with early short-circuit"
)
PROMOTED_R24_DEAD_DICTIONARY_ELISION = True
PROMOTED_R24_DEAD_DICTIONARY_EVIDENCE = (
    "all-15 post-selection proof: 0 byte regressions, live dictionaries byte-identical, dead dictionaries smaller"
)
PROMOTED_R24_OPAQUE_MEDIA_TERMINAL = True
PROMOTED_R24_OPAQUE_MEDIA_EVIDENCE = (
    "all-15 strict four-way media win + unseen entropy-refined adversarial proof with compressible-media rejection"
)
PROMOTED_R24_COMPACT_CONTROL_TERMINAL = True
PROMOTED_R24_COMPACT_CONTROL_EVIDENCE = (
    "all-15 frozen admission + five-round unseen/adversarial strict four-way wins + native dispatch + Android/JNI"
)

_PROMOTED_BINDINGS = {
    "build": build,
    "strong_verify": strong_verify,
    "list_members": list_members,
    "read_member_with_stats": read_member_with_stats,
    "read_member": read_member,
    "extract": extract,
    "_revision_for_archive": _revision_for_archive,
}


class _ReleaseProductModule(types.ModuleType):
    """Mirror legacy public overrides into mature function globals without corrupting promotion bindings."""

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name.startswith("__") or name in {"_BASE_IMPL", "_LOGS_PROMOTED", "_R24_DEAD_DICT", "_R24_MEDIA"}:
            return
        if not hasattr(_BASE_IMPL, name):
            return
        promoted = _PROMOTED_BINDINGS.get(name)
        if promoted is not None and value is promoted:
            setattr(_BASE_IMPL, name, _BASE_ORIGINALS[name])
        else:
            setattr(_BASE_IMPL, name, value)


sys.modules[__name__].__class__ = _ReleaseProductModule
