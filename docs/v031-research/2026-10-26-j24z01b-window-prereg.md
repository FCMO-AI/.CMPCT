# J24Z01b — preregister one bounded decoder-call amortization falsifier

Date: 2026-10-26 UTC. This is a prospectively distinct *follow-up* to the original J24Z01 negative throughput result, not a replacement of its preregistration/evidence.

## Exact inherited decision
J24Z01 [run #40420064445](https://github.com/FCMO-AI/.CMPCT/actions/runs/40420064445), source `b40efa926d55515bd4b4af0edcc451007d0e9398`, original artifact #12696652594: 64MiB direct Zstd S_BLOB, one 1MiB selected range, same physical 7,612B archive. Full SHA+CRC bounded 64KiB native-streaming oracle cut fresh-child VmHWM by 111.68359375 MiB but took 2.3482x CPU and 2.3746x wall relative to authentic Reader. Strong negative remains binding and cannot be edited away.

## One question and causal hypothesis
Is most of the streaming throughput debt caused by **1,024 Python/ctypes/native streaming crossings** using 64 KiB output chunks, rather than inherent complete streamed verification work? A bounded 1 MiB output window requires ~64 crossings and at most 1 MiB per decoder output, while original Reader may require >128 MiB temporary decoding. Compare 64KiB, 256KiB and 1MiB streaming output and the original same-archive Reader in fresh independent children. Maintain identical libzstd semantics, same complete CRC/SHA, frame-termination controls, original archive bytes and output. The stronger simpler control is unchanged Reader; a product win cannot be earned by only comparing stream variants.

## Prospective observables / kill
- At least five interleaved fresh independent processes per arm (A original Reader, B64 streaming, B256 streaming, B1024 streaming), exact original physical frame bytes/source SHA and independently checked 1MiB selected SHA.
- If B1024 reduces B64 median CPU and wall by >=20% while retaining >=32MiB lower VmHWM than A, amortization is a useful causal mitigation. The complete A comparison remains the promotion-critical hurdle: B1024 CPU and wall must be <=2x A to consider additional product engineering.
- If changing call count by 16x alters CPU/wall less than 10%, call overhead is not the dominant explanation; next frame review should consider native checksum ownership or architecture, not more buffer tuning.
- Any incorrect SHA/CRC, mismatched original archive SHA, decoded frame metadata, unexpected memory growth > A, missing fresh receipts, or invalid direct comparison rejects positive claims.
- Preserve all original negative decoder cases; running them again is optional because exactly the same decoder function is reused with only output width changed.

## Scope
Linux kernel VmHWM, Python C ABI oracle only. No Reader/Builder/native package/format/release source change. No new benchmark claim. This is one bounded final granularity experiment; **do not reopen thresholds beyond 1 MiB after result** without materially different mechanism. Existing original evidence controls scientific interpretation.
