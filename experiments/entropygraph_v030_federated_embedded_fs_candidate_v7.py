from __future__ import annotations

"""C25EG07: EG06 physical graph with hybrid scalar/RLE filesystem control.

EG06 recovered 8 bytes but exact evidence still left office 42 bytes short of a strict accepted-v0.29 win.
EG07 changes only the bounded filesystem-control wire encoding.  The EntropyGraph reconstruction graph, physical
packs, integrity model, locality limits, recovery layout and compression-effort search are inherited unchanged.
Research-only; shipping selector/native/Android dispatch remain untouched.
"""

from contextlib import contextmanager
from pathlib import Path

from experiments import entropygraph_v030_federated_embedded_fs_candidate_v6 as EG06
from experiments import entropygraph_v030_fs_implicit_v6 as IFS6

MAGIC = b"C25EG07\0"
TAIL_MAGIC = b"C25EG7T\0"
EMBEDDED_FS_KEY = 7
LEVEL_CAP = EG06.LEVEL_CAP
MAX_PATH_BYTES = EG06.MAX_PATH_BYTES
MAX_PROFILE_FILES = EG06.MAX_PROFILE_FILES
MAX_PROFILE_LOGICAL_BYTES = EG06.MAX_PROFILE_LOGICAL_BYTES
MAX_MANIFEST_ENTRIES = EG06.MAX_MANIFEST_ENTRIES
MAX_DECODE_UNIT = EG06.MAX_DECODE_UNIT
MAX_MEMBER_AMPLIFICATION = EG06.MAX_MEMBER_AMPLIFICATION
_LOCK = EG06._LOCK
_PENDING_CONTROL = EG06._PENDING_CONTROL


@contextmanager
def _variant():
    old = (EG06.MAGIC, EG06.TAIL_MAGIC, EG06.EMBEDDED_FS_KEY, EG06.IFS5)
    EG06.MAGIC = MAGIC
    EG06.TAIL_MAGIC = TAIL_MAGIC
    EG06.EMBEDDED_FS_KEY = EMBEDDED_FS_KEY
    EG06.IFS5 = IFS6
    try:
        yield
    finally:
        EG06.MAGIC, EG06.TAIL_MAGIC, EG06.EMBEDDED_FS_KEY, EG06.IFS5 = old


@contextmanager
def _engine(archive: Path, profile: Path | None = None):
    with _variant():
        with EG06._engine(archive, profile):
            yield


def _treehash(root: Path) -> str:
    return EG06._treehash(root)


def _profile_key(profile: Path) -> str:
    return EG06._profile_key(profile)


def _prepare_profile(source: Path, profile: Path) -> dict:
    with _variant():
        stats = dict(EG06._prepare_profile(source, profile))
    stats["filesystem_control_encoding"] = "implicit-v6-hybrid-scalar-rle"
    return stats


def finalize_research_archive(archive: Path, profile: Path, fs: dict | None = None) -> dict:
    with _variant():
        return EG06.finalize_research_archive(archive, profile, fs)


def extract(archive: Path, destination: Path) -> None:
    with _variant():
        EG06.extract(archive, destination)


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    with _variant():
        result = dict(EG06.strong_verify(archive, expected_tree=expected_tree))
    result["profile"] = "federated-eg07-hybrid-rle-fs"
    return result


def locality_report(archive: Path) -> dict:
    with _variant():
        return EG06.locality_report(archive)


def build(source: Path, archive: Path) -> dict:
    with _variant():
        result = dict(EG06.build(source, archive))
    result["profile"] = "federated-eg07-hybrid-rle-fs"
    result["filesystem_control_encoding"] = "implicit-v6-hybrid-scalar-rle"
    return result
