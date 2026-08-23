from __future__ import annotations

"""C25EG07: EG06 physical graph with hybrid scalar/RLE filesystem control.

EG06 recovered 8 bytes but exact evidence still left office 42 bytes short of a strict accepted-v0.29 win.
EG07 changes only the bounded filesystem-control wire encoding.  The EntropyGraph reconstruction graph, physical
packs, integrity model, locality limits, recovery layout and compression-effort search are inherited unchanged.
Research-only; shipping selector/native/Android dispatch remain untouched.
"""

from contextlib import contextmanager
from pathlib import Path
import tempfile

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


def _fused_strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    """Strongly verify EG07 with one logical reconstruction instead of two.

    The inherited V25 strong verifier first authenticates every physical pack and then reconstructs the complete
    logical profile to prove the authenticated inner tree.  EG05 subsequently reconstructed that same profile a
    second time solely to restore canonical filesystem semantics and prove the canonical user tree.  C25EG07 owns
    both facts, so one reconstruction can prove both without weakening either boundary:

    1. authenticate primary/tail metadata and SHA-256 + CRC32 every decoded physical pack;
    2. reconstruct the logical profile once and compare its V25 tree to the authenticated inner tree;
    3. restore the authenticated canonical filesystem control on that same tree and verify the canonical tree.

    No digest, recovery route, decoded pack, filesystem entry or tree comparison is skipped.  The optimization
    removes only a duplicate full extraction/materialization pass.
    """

    # EG07 temporarily rebinds EG06, which in turn binds EG05 to the exact EG07 identity/key/IFS decoder.  Keep the
    # whole fused operation inside both existing semantic-owner locks so historical process-global state cannot
    # leak to another caller.
    with _variant():
        with EG06._variant():
            owner = EG06.EG05
            V25 = owner.V25
            control = owner._metadata_control(archive)

            with owner._engine(archive.resolve()):
                stream, metadata, packs = V25.open_ar()
                try:
                    for index, (offset, codec, usize, csize, crc, expected_sha) in enumerate(packs):
                        stream.seek(offset)
                        payload = stream.read(csize)
                        if len(payload) != csize:
                            raise RuntimeError(f"truncated pack {index}")
                        raw = V25.zd(payload, usize) if codec == 1 else payload
                        if len(raw) != usize:
                            raise RuntimeError(f"pack size {index}")
                        if (V25.binascii.crc32(raw) & 0xFFFFFFFF) != crc:
                            raise RuntimeError(f"pack CRC {index}")
                        if V25.H(raw) != expected_sha:
                            raise RuntimeError(f"pack SHA-256 {index}")
                    inner_expected = str(metadata["tree_sha256"])
                    metadata_version = int(metadata["v"])
                finally:
                    stream.close()

            with tempfile.TemporaryDirectory(prefix="cmpct-eg07-fused-verify-") as td:
                restored = Path(td) / "restored"
                with owner._engine(archive.resolve()):
                    V25.extract(restored)
                inner_tree = V25.treehash(restored)
                if inner_tree != inner_expected:
                    raise RuntimeError(
                        f"logical tree SHA-256 mismatch: {inner_tree} != {inner_expected}"
                    )
                decoded = owner._restore_profile(restored, control)
                canonical_tree = owner._treehash(restored)

    if expected_tree is not None and canonical_tree != expected_tree:
        raise RuntimeError(f"canonical user-tree mismatch: {canonical_tree} != {expected_tree}")
    return {
        "ok": True,
        "profile": "federated-eg07-hybrid-rle-fs",
        "canonical_user_tree_sha256": canonical_tree,
        "filesystem_entries": len(decoded["manifest"]["entries"]),
        "logical_reconstruction_passes": 1,
        "inner": {
            "ok": True,
            "tree_sha256": inner_tree,
            "packs": len(packs),
            "metadata_version": metadata_version,
            "physical_pack_sha256_verified": True,
        },
    }


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    return _fused_strong_verify(archive, expected_tree=expected_tree)


def locality_report(archive: Path) -> dict:
    with _variant():
        return EG06.locality_report(archive)


def build(source: Path, archive: Path) -> dict:
    with _variant():
        result = dict(EG06.build(source, archive))
    result["profile"] = "federated-eg07-hybrid-rle-fs"
    result["filesystem_control_encoding"] = "implicit-v6-hybrid-scalar-rle"
    return result
