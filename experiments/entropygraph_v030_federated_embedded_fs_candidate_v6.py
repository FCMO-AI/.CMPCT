from __future__ import annotations

"""C25EG06: EG05 physical graph with run-length implicit filesystem control.

EG05 left office only 50 bytes above the immutable accepted-v0.29 floor at the all-best physical-pack bound.
EG06 changes only the bounded filesystem-control encoding: consecutive identical regular metadata overrides are
run-length encoded and the embedded metadata key uses a compact integer key.  The EntropyGraph reconstruction
graph, physical packs, integrity model, locality limits, recovery layout and compression-effort search are
otherwise unchanged.  Research-only; shipping selector/native/Android dispatch remain untouched.
"""

from contextlib import contextmanager
from pathlib import Path

from experiments import entropygraph_v030_federated_embedded_fs_candidate_v5 as EG05
from experiments import entropygraph_v030_fs_implicit_v5 as IFS5

MAGIC = b"C25EG06\0"
TAIL_MAGIC = b"C25EG6T\0"
EMBEDDED_FS_KEY = 6
LEVEL_CAP = EG05.LEVEL_CAP
MAX_PATH_BYTES = EG05.MAX_PATH_BYTES
MAX_PROFILE_FILES = EG05.MAX_PROFILE_FILES
MAX_PROFILE_LOGICAL_BYTES = EG05.MAX_PROFILE_LOGICAL_BYTES
MAX_MANIFEST_ENTRIES = EG05.MAX_MANIFEST_ENTRIES
MAX_DECODE_UNIT = EG05.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = EG05.MAX_MEMBER_AMPLIFICATION
# Benchmark adapters temporarily rebind the historical V25 engine while changing candidate identity.  EG06 is a
# framing-only child of EG05 and must therefore expose the exact same semantic lock, not a fresh lock and not an
# implicit private dependency.  Sharing the lock preserves the existing single-owner mutation boundary when the
# selective-effort oracle swaps CAND from EG01/EG05 to EG06.
_LOCK = EG05._LOCK
_PENDING_CONTROL = EG05._PENDING_CONTROL


@contextmanager
def _variant():
    old = (EG05.MAGIC, EG05.TAIL_MAGIC, EG05.EMBEDDED_FS_KEY, EG05.IFS4)
    EG05.MAGIC = MAGIC
    EG05.TAIL_MAGIC = TAIL_MAGIC
    EG05.EMBEDDED_FS_KEY = EMBEDDED_FS_KEY
    EG05.IFS4 = IFS5
    try:
        yield
    finally:
        EG05.MAGIC, EG05.TAIL_MAGIC, EG05.EMBEDDED_FS_KEY, EG05.IFS4 = old


@contextmanager
def _engine(archive: Path, profile: Path | None = None):
    with _variant():
        with EG05._engine(archive, profile):
            yield


def _treehash(root: Path) -> str:
    return EG05._treehash(root)


def _profile_key(profile: Path) -> str:
    return EG05._profile_key(profile)


def _prepare_profile(source: Path, profile: Path) -> dict:
    with _variant():
        stats = dict(EG05._prepare_profile(source, profile))
    stats["filesystem_control_encoding"] = "implicit-v5-rle-regular-metadata"
    return stats


def finalize_research_archive(archive: Path, profile: Path, fs: dict | None = None) -> dict:
    with _variant():
        return EG05.finalize_research_archive(archive, profile, fs)


def extract(archive: Path, destination: Path) -> None:
    with _variant():
        EG05.extract(archive, destination)


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    with _variant():
        result = dict(EG05.strong_verify(archive, expected_tree=expected_tree))
    result["profile"] = "federated-eg06-rle-fs"
    return result


def locality_report(archive: Path) -> dict:
    with _variant():
        return EG05.locality_report(archive)


def build(source: Path, archive: Path) -> dict:
    with _variant():
        result = dict(EG05.build(source, archive))
    result["profile"] = "federated-eg06-rle-fs"
    result["filesystem_control_encoding"] = "implicit-v5-rle-regular-metadata"
    return result
