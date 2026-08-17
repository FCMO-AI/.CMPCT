"""Byte-preserving creation-cost rehabilitation for the CMPNX14 Geometry IR reactor.

The parent GIR encoder first prices G0/G1/G2 with ``G._encode_node``.  That operation already compresses the
raw node at Zstd-19 and records each winning transform's exact saving against that direct floor.  The original
G3/G4 audition then compressed the *same raw node again* only to rediscover the direct payload byte count.

This adapter removes that redundant level-19 compression without changing candidate nomination, transformed
bytes, exact finalist compression, rank order, archive grammar, metadata, or fallback.  It is deliberately a
separate research facade: once CI proves archive-byte identity, the small API change can be folded into the
owning Hierarchical Geometry module instead of keeping duplicate production logic.

Footnote: the direct floor is recovered algebraically as ``incumbent_payload + saving_vs_direct``.  This is
not an estimate: CMPNX13's encoder defines ``saving`` as exactly ``direct_payload_bytes - chosen_payload``.
Exact compressor calls still price every transformed finalist; only the already-known raw direct call is
elided.
"""
from __future__ import annotations

from experiments import entropygraph_v030_gir as gir

G = gir.G
HG = gir.HG

LEGACY_ENCODE_NODE = gir._encode_node


def _audition_hierarchy_with_direct_bytes(raw: bytes, direct_payload_bytes: int) -> dict:
    """Run the existing bounded G3/G4 tournament against a supplied exact direct-floor byte count."""
    if direct_payload_bytes < 0:
        raise ValueError("negative GIR direct payload byte count")
    best = {
        "kind": "direct",
        "primary": None,
        "secondary": None,
        "prefix_planes": False,
        "physical": None,
        "codec": None,
        "payload": None,
        "payload_bytes": direct_payload_bytes,
        "saving_bytes": 0,
        "screened_candidates": 0,
        "exact_finalists": 0,
    }
    if len(raw) < HG.MIN_NODE_BYTES:
        return best

    screened: list[tuple[int, int, int, bool, bytes]] = []
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
                screened.append((screen_bytes, primary, secondary, prefix_planes, transformed))

    screened.sort(key=lambda row: (row[0], row[3], row[1], row[2]))
    finalists = screened[: HG.MAX_EXACT_FINALISTS]
    for _, primary, secondary, prefix_planes, transformed in finalists:
        codec, payload = G._compress_physical(transformed)
        saving = direct_payload_bytes - len(payload)
        if saving < HG.MIN_PAYLOAD_SAVING:
            continue
        rank = (len(payload), 0 if prefix_planes else 1, primary, secondary)
        incumbent = (
            int(best["payload_bytes"]),
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


def _encode_node(raw: bytes) -> dict:
    """Tournament G0-G4 while reusing the direct floor already paid by G0-G2."""
    incumbent = G._encode_node(raw)
    incumbent_payload_bytes = int(incumbent["payload_bytes"])
    direct_payload_bytes = incumbent_payload_bytes + int(incumbent.get("saving", 0))
    if direct_payload_bytes < incumbent_payload_bytes:
        raise RuntimeError("GIR incumbent reports impossible direct-floor accounting")

    best = {
        "kind": incumbent["kind"],
        "param": incumbent.get("param", 0),
        "physical": incumbent["physical"],
        "codec": int(incumbent["codec"]),
        "payload": incumbent["payload"],
        "payload_bytes": incumbent_payload_bytes,
        "saving_vs_direct": int(incumbent.get("saving", 0)),
        "hierarchical_screened_candidates": 0,
        "hierarchical_exact_finalists": 0,
    }
    hierarchical = _audition_hierarchy_with_direct_bytes(raw, direct_payload_bytes)
    best["hierarchical_screened_candidates"] = int(hierarchical["screened_candidates"])
    best["hierarchical_exact_finalists"] = int(hierarchical["exact_finalists"])
    if hierarchical["kind"] == "hierarchical" and int(hierarchical["payload_bytes"]) < best["payload_bytes"]:
        # Footnote: this block intentionally mirrors the owning GIR encoder.  The rehabilitation experiment
        # changes only how the direct baseline is obtained; the authenticated node representation is identical.
        best = {
            "kind": "hierarchical",
            "param": 1 if hierarchical["prefix_planes"] else 0,
            "physical": hierarchical["physical"],
            "codec": int(hierarchical["codec"]),
            "payload": hierarchical["payload"],
            "payload_bytes": int(hierarchical["payload_bytes"]),
            "saving_vs_direct": int(hierarchical["saving_bytes"]),
            "hierarchical_screened_candidates": int(hierarchical["screened_candidates"]),
            "hierarchical_exact_finalists": int(hierarchical["exact_finalists"]),
        }
    return best


# ``_build_gir`` resolves its module-global encoder at call time, so installing the byte-equivalent adapter
# changes no archive call sites.  Tests retain ``LEGACY_ENCODE_NODE`` and build both paths from the same tree.
gir._encode_node = _encode_node

build = gir.build
_build_gir = gir._build_gir
strong_verify = gir.strong_verify
extract = gir.extract
treehash = gir.treehash
MAX_CHUNK = gir.MAX_CHUNK
MAX_DECODE_UNIT = gir.MAX_DECODE_UNIT
MAX_DECODER_MEMORY = gir.MAX_DECODER_MEMORY

if __name__ == "__main__":
    gir._main()
