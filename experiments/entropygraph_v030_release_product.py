"""CMPCT v0.30 promoted release-product front door.

The mature r24/r25 selector implementation is retained byte-for-byte in
``entropygraph_v030_release_product_base``.  This module exposes that exact implementation and adds the
structurally admitted logs-inverse profile that earned all-15 shadow, native production-dispatch and Android/JNI
promotion evidence on the parent fingerprint.  Non-logs operations remain transparent mature-product delegates;
no benchmark name participates in dispatch.

A release-only r24 materialization post-pass also removes a trained dictionary only when the finished authenticated
blob table proves that no selected physical record uses it.  Training and codec competition remain unchanged; live
dictionaries stay byte-identical.  This is a semantic no-op that removes pure dead payload after selection.

A compatibility bridge mirrors public-module overrides into the preserved mature implementation.  This retains the
established monkeypatch/introspection surface used by the release regression suite and by downstream diagnostic
code, even though mature function globals now live in the preserved base module.  Restoring a promoted public
operation restores the original mature delegate rather than recursively installing the promoted wrapper into the
base module.

Release authority remains the ordinary v0.30 authority.  This module does not weaken the v0.29 floor, ZIP/Zstd
per-workload size/create requirements, locality/decode ceilings, integrity, recovery, native or Android gates.
"""
from __future__ import annotations

from pathlib import Path
import sys
import types

from experiments import entropygraph_v030_release_product_base as _BASE_IMPL
from experiments import entropygraph_v030_r24_dead_dictionary as _R24_DEAD_DICT

# Post-selection r24 dictionary elision is release-only.  The base implementation already isolates its r24
# encoder policies from historical v0.29/research modules.  Replacing this one base-module global means both the
# overlapped prebuild path and direct fallback path receive the exact same post-pass, while all historical builders
# remain byte-stable evidence oracles.
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

# Populate the public module with the exact mature implementation first.  Constants, helpers, ablation machinery
# and shared objects therefore remain identical to the pre-promotion product surface, except for the measured
# release-only r24 materialization post-pass above.
for _name in dir(_BASE_IMPL):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_BASE_IMPL, _name)
# Ensure the public private-helper binding reflects the release wrapper rather than the pre-promotion copy.
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

# Candidate/oracle imports historically patch CAND.BASE.build directly.  Keep that direct-candidate contract
# dynamic while the promoted public path below uses transparent mature fallbacks.
_LOGS_PROMOTED._BASE_BUILD = lambda root, out: _LOGS_PROMOTED.BASE.build(root, out)


def build(root, out):
    """Build logs when structurally and empirically admitted; otherwise preserve the mature result exactly."""
    terminal = _LOGS_PROMOTED._build_logs_terminal_if_eligible(root, out)
    if terminal is not None:
        return terminal
    return _BASE_IMPL.build(root, out)


def strong_verify(archive):
    if _LOGS_PROMOTED._is_logs_archive(archive):
        return _LOGS_PROMOTED.strong_verify(archive)
    return _BASE_IMPL.strong_verify(archive)


def list_members(archive):
    if _LOGS_PROMOTED._is_logs_archive(archive):
        return _LOGS_PROMOTED.list_members(archive)
    return _BASE_IMPL.list_members(archive)


def read_member_with_stats(archive, rel):
    if _LOGS_PROMOTED._is_logs_archive(archive):
        return _LOGS_PROMOTED.read_member_with_stats(archive, rel)
    return _BASE_IMPL.read_member_with_stats(archive, rel)


def read_member(archive, rel):
    if _LOGS_PROMOTED._is_logs_archive(archive):
        return _LOGS_PROMOTED.read_member(archive, rel)
    return _BASE_IMPL.read_member(archive, rel)


def extract(archive, dst, *, max_output_bytes=POLICY.DEFAULT_MAX_EXTRACT_BYTES, safe_symlinks=True):
    if _LOGS_PROMOTED._is_logs_archive(archive):
        return _LOGS_PROMOTED.extract(
            archive,
            dst,
            max_output_bytes=max_output_bytes,
            safe_symlinks=safe_symlinks,
        )
    # The mature non-logs extraction contract remains, in this exact authenticated order:
    # POLICY.extract_verified_into_staging
    # VERIFIED_RESTORE.restore_verified_manifest_tree
    # C._publish_tree
    return _BASE_IMPL.extract(
        archive,
        dst,
        max_output_bytes=max_output_bytes,
        safe_symlinks=safe_symlinks,
    )


def _revision_for_archive(archive):
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
PROMOTED_R24_DEAD_DICTIONARY_ELISION = True
PROMOTED_R24_DEAD_DICTIONARY_EVIDENCE = (
    "all-15 post-selection proof: 0 byte regressions, live dictionaries byte-identical, dead dictionaries smaller"
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
        if name.startswith("__") or name in {"_BASE_IMPL", "_LOGS_PROMOTED", "_R24_DEAD_DICT"}:
            return
        if not hasattr(_BASE_IMPL, name):
            return
        promoted = _PROMOTED_BINDINGS.get(name)
        if promoted is not None and value is promoted:
            setattr(_BASE_IMPL, name, _BASE_ORIGINALS[name])
        else:
            setattr(_BASE_IMPL, name, value)


sys.modules[__name__].__class__ = _ReleaseProductModule
