from __future__ import annotations

"""Hostile control for the fixed-4KiB dependency framing negative.

The first page-framed receipt was a valid result for its frozen layout, but post-result review found a
confounder: it encoded every token start relative to the page base. That raised raw token descriptor
bytes from 22,917,512 in the global stream to 28,399,070 before compression. Therefore that receipt
cannot by itself retire page framing as a family.

Mission lock
============
Keep *everything* from the v1 4 KiB framed experiment fixed -- corpus, owner, page boundaries, zlib-9
per-frame compression, 32-byte digest charge, 16-byte directory charge, Huffman state, boundary-token
duplication, and v0.29 comparator -- while changing only token start coding:

- first token in a page: signed delta from page base (needed for a token crossing into the page);
- every later token: signed delta from the end of the previous token.

Because DEFLATE output tokens tile the output stream, ordinary later deltas are zero. This is a causal
control, not a threshold/page-size/codec sweep.

Disproof: if this corrected-delta page framing still makes owner+sidecar exceed accepted v0.29
Analytics, then fixed-4KiB page framing has a much stronger density falsification. A pass only survives
density; it does not prove <=8x cold index+payload I/O, exact reconstruction, authenticated-root proofs,
recovery, or reader CPU.
"""

import argparse
import json
from pathlib import Path

from benchmarks import v030_r4_deflate_dependency_index_framed_budget as V1
from benchmarks import v030_r4_deflate_dependency_index_budget as DEP

SCHEMA = "cmpct-v030-r4-deflate-dependency-index-framed-delta-budget-v1"


def serialize_page_delta(page: int, local: list[tuple[int, int, int, int, int, int]], blocks: list[dict]):
    base = page * V1.PAGE
    bids = sorted({t[5] for t in local})
    out = bytearray(b"DPD1")
    out += DEP.uvarint(page)
    out += DEP.uvarint(len(local))
    out += DEP.uvarint(len(bids))
    state_bytes = 0
    for bid in bids:
        b = V1.block_state_bytes(blocks[bid])
        out += DEP.uvarint(len(b)) + b
        state_bytes += len(b)

    prev_end = base
    prev_bit = 0
    token_bytes = 0
    for start, length, distance, bit0, bit1, bid in local:
        before = len(out)
        out += V1.svarint(start - prev_end)
        out += DEP.uvarint(length)
        out += DEP.uvarint(distance)
        out += DEP.uvarint(bit0 - prev_bit)
        out += DEP.uvarint(bit1 - bit0)
        out += DEP.uvarint(bid)
        prev_end = start + length
        prev_bit = bit0
        token_bytes += len(out) - before
    return bytes(out), {
        "tokens": len(local),
        "blocks": len(bids),
        "block_state_bytes": state_bytes,
        "token_descriptor_bytes": token_bytes,
    }


def run(work: Path) -> dict:
    original = V1.serialize_page
    V1.serialize_page = serialize_page_delta
    try:
        d = V1.run(work)
    finally:
        V1.serialize_page = original
    d["schema"] = SCHEMA
    d["hypothesis"] = {
        "corrected_delta_page_addressable_dependency_information_fits_density_budget": (
            d["economics"]["margin_to_v029_bytes"] >= 0
        )
    }
    d["contract"]["causal_control"] = "only token-start coding differs from frozen page-framed v1"
    d["contract"]["first_token_start"] = "signed delta from 4KiB page base"
    d["contract"]["later_token_start"] = "signed delta from previous token end"
    d["next_if_falsified"] = (
        "preserve both v1 and corrected-delta negatives; fixed-4KiB per-page dependency framing is "
        "density-incompatible without changing the representation family"
    )
    d["next_if_supported"] = (
        "build cold serialized-frame traversal and charge exact index+payload I/O; do not infer locality "
        "from density alone"
    )
    return d


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--work-root", type=Path, default=Path("benchmark-artifacts/v030-r4-depframe-delta-work"))
    p.add_argument("--output", type=Path, default=Path("benchmark-artifacts/v030-r4-depframe-delta.json"))
    a = p.parse_args()
    d = run(a.work_root)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(d, indent=2) + "\n")
    print(json.dumps({"framed_index": d["framed_index"], "economics": d["economics"], "hypothesis": d["hypothesis"]}, indent=2))


if __name__ == "__main__":
    main()
