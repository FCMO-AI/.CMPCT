# v0.30 r24 content-economic micro-pack selective-read result — 2026-09-13

Status: **research evidence; no release credit**

Exact measured head: `2873a1a74457e8d4d44112928d5391166984ced8`

Hosted run: `34742382849`

Receipt artifact: `v030-sel-CONTENT_ECONOMIC_SELECTIVE_READ_SURVIVES-dev-0.094-0.085-0.113-d540072-tiny-0.021-0.020-0.021-d5257-2873a1a74457e8d4d44112928d5391166984ced8`

Scientific verdict: **`CONTENT_ECONOMIC_SELECTIVE_READ_SURVIVES`**

## Mission lock

The path-blind content-economic micro-pack candidate had already earned substantial stored-byte savings while preserving the existing `<=8x` smallest-member locality law, but Developer exposed an absolute decode unit of `540,072 B`, far larger than the extension-bucket research control. The falsifiable hypothesis was that this larger but still legal unit would not create a confirmed selective-read timing regression under the repository's existing same-runner confidence envelope.

The disproof rule was frozen before execution: candidate median cold `read_range` wall time had to be both more than `5%` and more than `3 ms` slower per measured round than the same-grammar independent control. The extension-bucket mechanism was retained as a second research control. No locality, semantics, integrity, range size or comparator setting was relaxed.

## Result

The referee used five rounds and up to 32 fixed midpoint probes of at most `4096 B`, opening a fresh `CMPCT` reader for each probe and timing `read_range` separately from open. Every returned range was SHA-256 checked against source bytes. For `S_PACK`, accounting charged the whole decoded pack because the current r24 reader decompresses the full pack before slicing the requested member range.

Artifact-bound medians in milliseconds per probe:

| Source | independent | extension bucket | content-economic | content max decode |
| --- | ---: | ---: | ---: | ---: |
| Developer | `0.094 ms` | `0.085 ms` | `0.113 ms` | `540,072 B` |
| Tiny Files | `0.021 ms` | `0.020 ms` | `0.021 ms` | `5,257 B` |

Developer is directionally slower than both controls, but the absolute slowdown across the fixed probe round remains below the repository's `3 ms` confidence floor, so it is **not a confirmed timing regression**. Tiny Files is effectively tied at the displayed precision. The candidate preserved exact range bytes, strong verification, tail recovery and the unchanged `<=8x` locality contract.

## Interpretation

This result removes the immediate concern that the `540,072 B` legal Developer pack automatically turns the content-economic density win into a measurable selective-read product regression on the current Python r24 reader. It does **not** prove that larger decode units are free, and it does not grant a right to increase the 8x budget. The absolute decode-unit distribution remains a product cost that future current-portfolio, native and platform readers must expose.

The result also does not claim RSS improvement. This mechanism referee intentionally shares build/runtime state in one process; fresh-process RSS remains required before promotion.

## Next gate

Transfer the exact unchanged content-economic builder across the current 15-workload portfolio under the same-grammar independent and extension controls. Require zero losses against independent, strong reconstruction/recovery, path blindness and `<=8x` locality. This is current-fingerprint evidence only and must never be used to rewrite the frozen Genesis score.
