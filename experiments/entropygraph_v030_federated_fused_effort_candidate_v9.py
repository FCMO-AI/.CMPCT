from __future__ import annotations

"""C25EG09: EG08-equivalent adaptive effort fused into final-pack creation.

Research-only. This candidate exists to test whether EG08's exact selected physical bytes can be produced during
first-pass V25 pack construction instead of by a second archive decode/repack pass.  It intentionally preserves
EG07's capped level-1 behavior for probes, cold stream slabs and metadata; only V25 calls that request level 19
(the ordinary final object-pack emission sites) receive the exact EG08 effort ladder.
"""

from contextlib import contextmanager
from pathlib import Path

from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07

E5 = EG07.EG06.EG05
V25 = E5.V25
MAGIC = EG07.MAGIC
TAIL_MAGIC = EG07.TAIL_MAGIC
# Frozen by the EG08 mechanism/mission lock; keep local so an upstream symbol rename cannot silently change EG09.
EFFORT_LEVELS = (3, 6, 12, 19)
PH = V25.PH


@contextmanager
def _fused_final_pack_engine(archive: Path, profile: Path | None = None):
    """EG05 engine with EG08 effort only on requested-level-19 final ordinary packs."""
    with E5._LOCK:
        old = (V25.ROOT, V25.OUT, V25.MAG, V25.TAIL, V25.zc)
        original_zc = V25.zc
        V25.OUT = archive
        if profile is not None:
            V25.ROOT = profile
        V25.MAG = E5.MAGIC
        V25.TAIL = E5.TAIL_MAGIC

        def fused(raw: bytes, level: int = 19) -> bytes:
            requested = int(level)
            incumbent = original_zc(raw, min(requested, E5.LEVEL_CAP))
            # V25 requested-level 19 is the ordinary final object-pack emission path. Preserve EG07's
            # raw/compressed admission exactly: EG08 never upgrades a pack that EG07 stored RAW.
            if requested != 19 or len(incumbent) + 8 >= len(raw):
                return incumbent
            best = incumbent
            best_storage = len(best) + PH.size
            for effort in EFFORT_LEVELS:
                candidate = original_zc(raw, effort)
                storage = len(candidate) + PH.size
                if storage < best_storage:
                    best = candidate
                    best_storage = storage
                    continue
                if storage == best_storage:
                    # Exact EG08 law: a tie carries information and does not terminate the ladder.
                    continue
                break
            return best

        V25.zc = fused
        try:
            yield
        finally:
            V25.ROOT, V25.OUT, V25.MAG, V25.TAIL, V25.zc = old


@contextmanager
def _variant():
    # EG07 -> EG06 -> EG05 eventually resolves EG05._engine dynamically. Replace only that narrow engine
    # boundary while preserving all existing EG07 identity/IFS/open_ar variants around it.
    old_engine = E5._engine
    E5._engine = _fused_final_pack_engine
    try:
        yield
    finally:
        E5._engine = old_engine


def _treehash(root: Path) -> str:
    return EG07._treehash(root)


def extract(archive: Path, destination: Path) -> None:
    EG07.extract(archive, destination)


def strong_verify(archive: Path, *, expected_tree: str | None = None) -> dict:
    return EG07.strong_verify(archive, expected_tree=expected_tree)


def locality_report(archive: Path) -> dict:
    return EG07.locality_report(archive)


def build(source: Path, archive: Path) -> dict:
    source = source.resolve()
    archive = archive.resolve()
    with _variant():
        result = dict(EG07.build(source, archive))
    # Re-read with the ordinary EG07 reader after the build-time fusion patch has been removed. This proves
    # that no special decode state is required by the fused artifact.
    verified = strong_verify(archive, expected_tree=_treehash(source))
    locality = locality_report(archive)
    if not locality.get("within_release_bounds"):
        raise RuntimeError("EG09 fused candidate exceeds frozen locality/decode limits")
    result.update(
        {
            "profile": "federated-eg09-fused-final-pack-effort",
            "archive_bytes": archive.stat().st_size,
            "verified": verified,
            "locality": locality,
            "fused_effort_levels": list(EFFORT_LEVELS),
            "fused_scope": "requested-level-19-final-object-packs-only",
        }
    )
    return result
