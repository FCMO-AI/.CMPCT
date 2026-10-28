from __future__ import annotations

"""Differently rooted adversarial check for the promoted release-only DGO1 inverse.

This is not a release receipt. It proves that the release front door actually installs the promoted dependency-free
fast path and compares it byte-for-byte with the preserved historical inverse over deterministic edge/hostile
shapes, including empty segments, ragged lengths, very large segment counts, and randomized payloads.
"""

import argparse
import json
from pathlib import Path
import random
import traceback


def _payload_without(value: int, size: int, rng: random.Random) -> bytes:
    if size <= 0:
        return b""
    # Deterministic arbitrary bytes excluding the delimiter so segment boundaries remain exactly controlled.
    out = bytearray(size)
    for i in range(size):
        b = rng.randrange(255)
        if b >= value:
            b += 1
        out[i] = b
    return bytes(out)


def run(seed: int = 0xC030F45A) -> dict:
    from experiments import entropygraph_v030_release_product as PRODUCT
    from experiments import entropygraph_v030_verified_restore as FAST

    C = PRODUCT.C
    O = C.SHARED.G.O
    installed = O.delimiter_inverse
    if installed is not FAST.release_single_buffer_delimiter_inverse:
        raise RuntimeError("release front door did not install promoted DGO1 inverse")
    if getattr(C.POLICY.R.G04, "O", None) is not None and C.POLICY.R.G04.O.delimiter_inverse is not installed:
        raise RuntimeError("release policy reader does not share promoted DGO1 inverse")

    oracle = C._PRESERVED_DELIMITER_INVERSE
    forward = C._PRESERVED_DELIMITER_FORWARD
    if oracle is installed:
        raise RuntimeError("historical inverse oracle was overwritten")

    rng = random.Random(seed)
    explicit_shapes = [
        [0],
        [0, 0],
        [0, 0, 0, 0, 0],
        [1],
        [1, 1],
        [0, 1, 0, 1, 0],
        [1, 0, 2, 0, 3, 0, 4],
        [27] * 64,
        list(range(0, 28)),
        list(reversed(range(0, 28))),
        [0, 27] * 128,
        [1, 27, 2, 26, 3, 25, 4, 24] * 64,
        [0] * min(45_000, O.MAX_DELIMITER_SEGMENTS),
        [1] * min(20_000, O.MAX_DELIMITER_SEGMENTS),
    ]
    random_shapes: list[list[int]] = []
    for _ in range(600):
        count = rng.randint(1, 256)
        mode = rng.randrange(5)
        if mode == 0:
            lengths = [rng.randint(0, 27) for _ in range(count)]
        elif mode == 1:
            choices = [0, 1, 2, 4, 8, 16, 27]
            lengths = [rng.choice(choices) for _ in range(count)]
        elif mode == 2:
            base = rng.randint(0, 27)
            lengths = [base] * count
        elif mode == 3:
            lengths = [(i * 7 + rng.randrange(4)) % 28 for i in range(count)]
        else:
            lengths = [0 if rng.random() < 0.55 else rng.randint(1, 27) for _ in range(count)]
        random_shapes.append(lengths)

    cases = 0
    logical_bytes = 0
    max_segments = 0
    for delimiter in (0, 1, 44, 127, 255):
        for lengths in explicit_shapes + random_shapes:
            # Respect the exact transform's existing cell-work contract; over-budget shapes belong to refusal tests.
            if len(lengths) > O.MAX_DELIMITER_SEGMENTS or len(lengths) * max(lengths, default=0) > O.MAX_DELIMITER_CELL_SCANS:
                continue
            parts = [_payload_without(delimiter, length, rng) for length in lengths]
            raw = bytes((delimiter,)).join(parts)
            if len(raw) > O.MAX_OVERLAY_RECORD:
                continue
            encoded = forward(raw, delimiter)
            historical = oracle(encoded, len(raw))
            promoted = installed(encoded, len(raw))
            if historical != raw or promoted != raw or promoted != historical:
                raise RuntimeError(
                    f"DGO1 inverse mismatch delimiter={delimiter} count={len(lengths)} logical={len(raw)}"
                )
            cases += 1
            logical_bytes += len(raw)
            max_segments = max(max_segments, len(lengths))

    refusal_cases = 0
    malformed = [
        (b"", 0),
        (b"DGO1", 0),
        (b"DGO1\x2c\x00", 0),
        (b"DGO1\x2c\x01\x00\x00", 1),
    ]
    for encoded, logical_size in malformed:
        try:
            installed(encoded, logical_size)
        except (RuntimeError, ValueError):
            refusal_cases += 1
        else:
            raise RuntimeError(f"malformed DGO1 input unexpectedly accepted: {encoded!r}")

    return {
        "schema": "cmpct-v030-g04-release-fastpath-promotion-check-v1",
        "status": "PASS",
        "product_release_credit": False,
        "seed": seed,
        "facts": {
            "release_frontdoor_installs_fastpath": True,
            "historical_oracle_remains_distinct": True,
            "exact_cases": cases,
            "exact_logical_bytes_checked": logical_bytes,
            "max_segments_checked": max_segments,
            "malformed_refusals_checked": refusal_cases,
            "delimiters_checked": [0, 1, 44, 127, 255],
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, default=Path("benchmark-artifacts/g04-release-fastpath-check.json"))
    args = ap.parse_args()
    try:
        payload = run()
    except BaseException as exc:
        payload = {
            "schema": "cmpct-v030-g04-release-fastpath-promotion-check-v1",
            "status": "FAIL",
            "product_release_credit": False,
            "error": {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc(limit=32)},
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n")
        raise
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
