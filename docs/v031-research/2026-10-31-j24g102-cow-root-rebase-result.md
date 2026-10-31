# J24G102 — exact physical COW root/epoch block economics

2026-10-31 UTC · O0 decision. **Scientific representation/oracle evidence only, product/release credit ZERO.** Preregistered before implementation in [\`292ee434d8578ab39e6550708029eb364d33e910\`](https://github.com/FCMO-AI/.CMPCT/commit/292ee434d8578ab39e6550708029eb364d33e910). Branch is a child of [#876](https://github.com/FCMO-AI/.CMPCT/pull/876), not a second writer/reader owner. Released \`main@80c358f8\` v0.30.0/r24 remains unmodified.

## Source and exactness

Original externally produced GitHub Actions run [#41120248525](https://github.com/FCMO-AI/.CMPCT/actions/runs/41120248525), genuine Builder and 63 Writer DELETE physical archives, checkout \`129edec976efe8bb604584517de39553487fec34\`:
- Ubuntu original artifact #13007508236, SHA-256 \`19e600a5c1f1798eb2ffeafffc3dd4fbaa81f09fc83090c4610d3d1f2ed42e0b\`.
- Windows original artifact #13007244298, SHA-256 \`c697febe772527c0bb488d406325470837774b6df6c30aea191e4e383c61fcab\`.

An independent parser (no CMPCT module) reconstructs the old genuine root checkpoint and the proposed compact final root using **the original, unchanged blob region and the actual compressed signed index from terminal physical checkpoint B**, with a zero-predecessor footer. All 63 DEL ops and every surviving index row, blob table, ownership/fsmeta value, and footer digest are checked for exact identity. This is a hypothetical r24 physical rewrite, **not a Builder/Writer/Reader product implementation**.

## Prospectively frozen H1/H2: complete charged bytes

Store every distinct payload block once, charge 44 B per SHA-keyed physical block record (32 B digest, 8 B offset, 4 B length), two separate 64 B root manifests, and 32 B for **every** original and new block reference. Relative to the **larger of the two complete root archive images**:

| Original source | Old→new image bytes | 4-KiB COW | 16-KiB COW |
|---|---:|---:|---:|
| Ubuntu, 4,096 members | 466,794 → 469,164 | **1.1146×** | **1.0942×** |
| Ubuntu, 8,192 members | 932,410 → 937,853 | **1.1088×** | **1.0928×** |
| Windows-origin, 4,096 | 435,152 → 436,684 | **1.0765×** | **1.0657×** |
| Windows-origin, 8,192 | 867,326 → 869,163 | **1.0778×** | **1.0623×** |

All eight measured cases satisfy the frozen <=1.20× H1 screen. All eight SHA-keyed manifests reconstruct the exact original pair of byte images, hash-check each root/block, refuse an altered block and detect a corrupted reference. An independently written referee reconstructs the byte charge and two archive SHA-256 identities, checks the adversarial one-byte shifted models and rejects two fabricated receipts. **This is a simulation of a packed SHA-keyed block store, not eight actually COW-cloned filesystems.**

A separate **local physical packed-store materialization** (not in the CI instrument) wrote all distinct blocks and two manifests to a Linux filesystem and measured \`st_blocks * 512\`: 475,136–1,044,480 allocated bytes across the four sources and two block sizes (source-dependent). This demonstrates actual Linux allocations for packed blobs only, **not** real block-clone/reflink behavior, full disk writes, crash-durable publication or reader performance.

Reproducibility:
\`\`\`
python research/j24g102_cow_root_oracle.py \
  --ubuntu original_ubuntu.zip --windows original_windows.zip --out receipt.json
python research/j24g102_referee.py \
  --ubuntu original_ubuntu.zip --windows original_windows.zip --receipt receipt.json
\`\`\`
The original local exact-source oracle receipt SHA-256 is \`d8cf06ddba8eb7014431222ddf832e7376f39e79589d69b3470064bb359ed9dd\`. Hosted GitHub Actions may produce a different JSON serialization if dependency versions change; it must be verified independently rather than asserted to match this local receipt. Original providers have finite retention.

## Strongest negative — one-byte shift destroys the structural win

Non-CMPCT adversarial physical **insertion of one byte near the start** raises the charged wire cost to **2.005–2.035×** across the sizes/hosts. The independent-random-byte control also approaches double storage. Block-aligned rotation retains sharing but is deliberately much easier than arbitrary byte displacement. Therefore **H3 does NOT establish general content-agnostic compression/deduplication**. A future candidate would need a source-independent content-defined ownership boundary or record-aware structural segmentation to handle shifts; neither receives credit here.

The stronger simpler J24G99 **no-rebase** append-only base/tail design measured only 1.004–1.019× active storage in its tested regimes. The present O0 is **not superior on those workloads**: it solves a different two-rewritten-checkpoint retention problem, with higher metadata. J24G101's ~1.98–1.99× copying result is not an impossibility lower bound; O0 demonstrates why physical sharing could avoid that specific duplication, but does **not** substitute for running the real publication protocol.

## Known debt, precedence and outcome

**Decision:** \`H1_H2_CHARGED_BLOCK_SHARE_O0_PASS__H3_SHIFT_NEGATIVE__NOT_PRODUCT\`. The next valuable test is an **actual physically materialized two-epoch lookup/read/garbage-collection and crash protocol** against the existing J24G99 owner, especially mixed PUT/RENAME with changed physical record offsets. Do not implement a persistent block-addressed Reader based on O0 alone.

This experiment does not establish: native block cloning; source acquisition or same-inode immutability; externally trusted head; compare-and-swap across two Writers; atomic crash cuts and durable publication; fixed memory and selective read amplification; Reader/native interpreter integration; inherited exact binary/ABI and release benchmarks; macOS/Windows runtime execution. Original physical artifacts were created on Ubuntu and Windows but the new O0 model was executed locally on Linux; this is not a new 2-host product claim.

#874/#875/#878 Reader import/replay work is independent and may be a better simpler product investment. #869/#876 retain physical ownership, #574 Discovery STATE, #857 and #290 integrity/concurrency. No merge, release, policy/evaluator alteration, product source edit or claim of default-path improvement.
