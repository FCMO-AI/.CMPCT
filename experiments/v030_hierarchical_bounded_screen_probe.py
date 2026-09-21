from __future__ import annotations

"""Research-only exact Hierarchical Geometry audition with O(finalists) transformed-byte retention.

The canonical research owner currently stores every level-6 transformed candidate in ``screened`` even though
only the best three are ever recompressed at level 19.  This probe preserves nomination, inverse checking, screen
scores, sort/tie order and exact-finalist admission, but discards each screened transform after scoring and
recomputes only the <=3 finalists.  It therefore tests a memory-ownership change, not a representation change.
"""

from experiments import entropygraph_v030_hierarchical_geometry as HG


def audition(raw: bytes) -> dict:
    G = HG.G
    base_codec, base_payload = G._compress_physical(raw)
    best = {
        "kind": "direct",
        "primary": None,
        "secondary": None,
        "prefix_planes": False,
        "physical": raw,
        "codec": base_codec,
        "payload": base_payload,
        "payload_bytes": len(base_payload),
        "saving_bytes": 0,
        "screened_candidates": 0,
        "exact_finalists": 0,
    }
    if len(raw) < HG.MIN_NODE_BYTES:
        return best

    # Crucial difference from the incumbent: no transformed bytes survive the screen iteration.
    screened: list[tuple[int, int, int, bool]] = []
    for primary in HG.primary_candidates(raw):
        rows = raw.split(bytes((primary,)))
        for secondary in HG.secondary_candidates(rows, primary):
            for prefix_planes in (False, True):
                try:
                    transformed = HG.hierarchy_forward(raw, primary, secondary, prefix_planes=prefix_planes)
                except ValueError:
                    continue
                if HG.hierarchy_inverse(transformed, len(raw)) != raw:
                    raise RuntimeError("Hierarchical Geometry candidate failed exact inverse")
                screen_bytes = HG._compressed_size(transformed, HG.SCREEN_LEVEL)
                screened.append((screen_bytes, primary, secondary, prefix_planes))

    screened.sort(key=lambda row: (row[0], row[3], row[1], row[2]))
    finalists = screened[: HG.MAX_EXACT_FINALISTS]
    for _, primary, secondary, prefix_planes in finalists:
        # Deterministic recomputation trades <=3 extra transforms for eliminating up to 48 retained full-size
        # transformed buffers per record. Re-check the inverse so the finalist safety contract is unchanged.
        transformed = HG.hierarchy_forward(raw, primary, secondary, prefix_planes=prefix_planes)
        if HG.hierarchy_inverse(transformed, len(raw)) != raw:
            raise RuntimeError("Hierarchical Geometry finalist failed exact inverse after recomputation")
        codec, payload = G._compress_physical(transformed)
        saving = len(base_payload) - len(payload)
        if saving < HG.MIN_PAYLOAD_SAVING:
            continue
        rank = (len(payload), 0 if prefix_planes else 1, primary, secondary)
        incumbent = (
            best["payload_bytes"],
            0 if best["prefix_planes"] else 1,
            best["primary"] if best["primary"] is not None else 1 << 30,
            best["secondary"] if best["secondary"] is not None else 1 << 30,
        )
        if rank < incumbent:
            best = {
                "kind": "hierarchical",
                "primary": primary,
                "secondary": secondary,
                "prefix_planes": prefix_planes,
                "physical": transformed,
                "codec": codec,
                "payload": payload,
                "payload_bytes": len(payload),
                "saving_bytes": saving,
                "screened_candidates": len(screened),
                "exact_finalists": len(finalists),
            }
    best["screened_candidates"] = len(screened)
    best["exact_finalists"] = len(finalists)
    return best
