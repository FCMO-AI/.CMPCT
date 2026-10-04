from __future__ import annotations

"""C25EG11: EG10 hybrid fusion with exact EG08 raw-incumbent economics.

Research-only. EG10 demonstrated that first-pass effort fusion plus a narrow cold-stream
rewrite can recover most of EG08's duplicate-work cost, but its first-pass wrapper
incorrectly assumed that a pack stored RAW by EG07 can never become compressed at a
higher effort. EG08 explicitly auditions every non-hot pack, including RAW incumbents.

EG11 changes only that equivalence bug. Geometry, effort ladder, admission law, cold
stream rewrite, reader, integrity, recovery and locality remain inherited.
"""

from contextlib import contextmanager
from pathlib import Path

from experiments import entropygraph_v030_federated_embedded_fs_candidate_v7 as EG07
from experiments import entropygraph_v030_federated_fused_effort_candidate_v9 as EG09
from experiments import entropygraph_v030_federated_hybrid_fusion_candidate_v10 as EG10

E5 = EG09.E5
V25 = EG09.V25
MAGIC = EG07.MAGIC
TAIL_MAGIC = EG07.TAIL_MAGIC
EFFORT_LEVELS = EG09.EFFORT_LEVELS
PH = V25.PH

_BUILD_STATS: dict[str, int] = {}


@contextmanager
def _fused_final_pack_engine(archive: Path, profile: Path | None = None):
    """Fuse EG08 economics into requested-level-19 ordinary pack compression exactly."""
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
            if requested != 19:
                return incumbent

            _BUILD_STATS["requested_level19_calls"] = _BUILD_STATS.get("requested_level19_calls", 0) + 1
            incumbent_admitted = len(incumbent) + 8 < len(raw)
            if not incumbent_admitted:
                _BUILD_STATS["raw_incumbent_calls"] = _BUILD_STATS.get("raw_incumbent_calls", 0) + 1

            # EG08's incumbent is the representation EG07 actually stored, not the raw
            # compressor return. Therefore a failed level-1 admission starts from RAW.
            best = incumbent
            best_admitted = incumbent_admitted
            best_storage = len(incumbent) if incumbent_admitted else len(raw)

            for effort in EFFORT_LEVELS:
                candidate = original_zc(raw, effort)
                admitted = len(candidate) + 8 < len(raw)
                candidate_storage = len(candidate) if admitted else len(raw)
                if candidate_storage <= best_storage:
                    if candidate_storage < best_storage:
                        best = candidate
                        best_admitted = admitted
                        best_storage = candidate_storage
                    # Exact EG08 law: ties carry information and continue the ladder,
                    # but retain the earlier selected bytes.
                    continue
                break

            if not incumbent_admitted and best_admitted:
                _BUILD_STATS["raw_incumbent_promotions"] = _BUILD_STATS.get("raw_incumbent_promotions", 0) + 1
                _BUILD_STATS["raw_incumbent_saved_bytes"] = _BUILD_STATS.get("raw_incumbent_saved_bytes", 0) + (len(raw) - best_storage)

            # When RAW remains selected, returning the original non-admitted level-1
            # frame makes the unchanged V25 caller store RAW exactly as EG07/EG08 do.
            return best if best_admitted else incumbent

        V25.zc = fused
        try:
            yield
        finally:
            V25.ROOT, V25.OUT, V25.MAG, V25.TAIL, V25.zc = old


@contextmanager
def _variant():
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
    _BUILD_STATS.clear()
    with _variant():
        base = dict(EG07.build(source, archive))

    before = dict(base["locality"])
    cold = EG10._cold_stream_repack(archive)
    verified = strong_verify(archive, expected_tree=_treehash(source))
    locality = locality_report(archive)
    if not locality.get("within_release_bounds"):
        raise RuntimeError("EG11 raw-incumbent fusion exceeds frozen locality/decode limits")
    if (
        locality.get("member_count") != before.get("member_count")
        or locality.get("max_decode_unit_bytes") != before.get("max_decode_unit_bytes")
        or locality.get("max_member_read_amplification") != before.get("max_member_read_amplification")
    ):
        raise RuntimeError("EG11 changed locality geometry")

    result = dict(base)
    result.update(
        {
            "profile": "federated-eg11-raw-incumbent-fusion",
            "archive_bytes": archive.stat().st_size,
            "verified": verified,
            "locality": locality,
            "cold_stream_effort": cold,
            "fused_effort_levels": list(EFFORT_LEVELS),
            "fused_scope": "requested-level-19-final-object-packs-with-raw-incumbent-promotion",
            "fusion_stats": dict(_BUILD_STATS),
        }
    )
    return result
