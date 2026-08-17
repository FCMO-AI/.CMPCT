"""Search-policy safety facade for v0.30 Bitplane Algebra.

The primitive BPA module deliberately exposes transform construction/inversion and the first search sketch.
This facade pins the benchmark-facing selection law: every exact finalist is compared to the same original
safe G0/G1/G2 Geometry incumbent, and the smallest legal finalist wins regardless of enumeration order.

Footnote: the first child-research implementation thresholded a later finalist against the current BPA winner.
That could reject a slightly better candidate merely because its *incremental* improvement was <64 bytes even
when both candidates beat Geometry by far more than 64 bytes.  Preserving the primitive file and fixing the
policy here keeps the caught search-order bug visible rather than silently rewriting research history.
"""
from __future__ import annotations

from experiments import entropygraph_v030_bitplane_algebra as BPA

G = BPA.G


def audition(raw: bytes) -> dict:
    incumbent = G._encode_node(raw)
    incumbent_bytes = int(incumbent["payload_bytes"])
    result = {
        "kind": "geometry-incumbent",
        "payload": incumbent["payload"],
        "payload_bytes": incumbent_bytes,
        "physical": incumbent["physical"],
        "incumbent_kind": incumbent["kind"],
        "saving_vs_incumbent_bytes": 0,
        "width": None,
        "alignment": None,
        "predictor": None,
        "basis": None,
        "screened_candidates": 0,
        "exact_finalists": 0,
    }
    if len(raw) < 16 * 1024 or len(raw) > BPA.MAX_NODE_BYTES:
        return result

    sample = raw[: BPA.SCREEN_SAMPLE_BYTES]
    screened: list[tuple[int, int, int, int, str, tuple[str, int]]] = []
    ordinal = 0
    for width in BPA.WORD_WIDTHS:
        for alignment in BPA.rank_alignments(raw, width):
            for predictor in BPA.PREDICTORS:
                for basis in BPA._basis_options(width * 8):
                    try:
                        transformed = BPA.forward(sample, width, alignment, predictor, basis)
                    except ValueError:
                        continue
                    if BPA.inverse(transformed, len(sample)) != sample:
                        raise RuntimeError("BPA screen candidate failed exact inverse")
                    screened.append((BPA._screen_size(transformed), ordinal, width, alignment, predictor, basis))
                    ordinal += 1

    screened.sort(key=lambda row: (row[0], row[2], row[3], row[4], row[5]))
    finalists = screened[: BPA.MAX_EXACT_FINALISTS]
    for _, _, width, alignment, predictor, basis in finalists:
        transformed = BPA.forward(raw, width, alignment, predictor, basis)
        if BPA.inverse(transformed, len(raw)) != raw:
            raise RuntimeError("BPA finalist failed exact inverse")
        payload = G.zc(transformed, BPA.EXACT_LEVEL)
        if len(payload) >= len(transformed):
            payload = transformed
        saving_vs_incumbent = incumbent_bytes - len(payload)
        if saving_vs_incumbent < BPA.MIN_PAYLOAD_SAVING:
            continue
        candidate_rank = (len(payload), width, alignment, predictor, basis)
        incumbent_rank = (
            int(result["payload_bytes"]),
            int(result["width"]) if result["width"] is not None else 1 << 30,
            int(result["alignment"]) if result["alignment"] is not None else 1 << 30,
            result["predictor"] or "~",
            result["basis"] or ("~", 1 << 30),
        )
        if candidate_rank < incumbent_rank:
            result = {
                "kind": "bitplane-algebra",
                "payload": payload,
                "payload_bytes": len(payload),
                "physical": transformed,
                "incumbent_kind": incumbent["kind"],
                "saving_vs_incumbent_bytes": saving_vs_incumbent,
                "width": width,
                "alignment": alignment,
                "predictor": predictor,
                "basis": basis,
                "screened_candidates": len(screened),
                "exact_finalists": len(finalists),
            }

    result["screened_candidates"] = len(screened)
    result["exact_finalists"] = len(finalists)
    return result


# Re-export the primitive/resource surface used by focused tests and benchmarks.  A future integration should
# fold this policy into the owning module once the mechanism itself survives; research callers use this facade.
forward = BPA.forward
inverse = BPA.inverse
rank_alignments = BPA.rank_alignments
RESOURCE_LIMITS = dict(BPA.RESOURCE_LIMITS)
MAX_NODE_BYTES = BPA.MAX_NODE_BYTES
WORD_WIDTHS = BPA.WORD_WIDTHS
PREDICTORS = BPA.PREDICTORS
