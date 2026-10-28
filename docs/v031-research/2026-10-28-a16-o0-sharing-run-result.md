# A16-O0 — Sharing-class run coalescence, first scientific result

Date: 2026-10-28 UTC  
Status: **FROZEN PRIMARY JOINT THRESHOLD FALSE; SCIENTIFIC MECHANISM BOUNDED, NOT PROMOTED.**  
Preregistration: `docs/v031-research/2026-10-28-a16-o0-sharing-run-prereg.md` committed FIRST at `b9ead845f328e536113d1b74282295ca59f1d0f6`, before research code.  
Baseline published project: `main@80c358f8824ec1b20d349c92ed94c898090969b0` (v0.30.0, r24).  
Prior same-input control: A15-O1 [PR #680](https://github.com/FCMO-AI/.CMPCT/pull/680) at `a02034ed3c23f84d0827d1cbb448423c9e1e6bec`.  
Scope: standalone science envelopes, **not CMPCT archive bytes**, installed Reader, native ABI, or release evidence.

## Original question and mechanism

A15-O1's fixed 4-KiB sharing saved storage but required many small Zstd decode units. A16 instead tests whether choosing **physical owner boundaries from observed cross-member sharing-class runs** can improve complete bytes and reconstruction work simultaneously. The classifier marks each 4-KiB hash as shared if it occurs in at least two different member files, joins consecutive blocks in the same class, then deduplicates resulting runs only on SHA **plus exact byte equality**. It never branches on filename, seed, fixture identity or regime label. The decoder receives per-owner lengths, compressed streams, SHA-256; per-member length, references and SHA-256. A direct-member control and a **stronger fixed-chunk reference control without redundant owner-length words** receive the same source, Zstd-19 and member-level retrieval semantics.

The preregistered *primary* result required **>=1.0% complete byte reduction** AND >=1.5x member decode median CPU/wall on BOTH independently seeded prefix12 cases. The threshold is not adjustable after observation. Controls include identical members, suffix12 perturbation, alternating shared/unique membership and distinct blocks, with paid one-byte portfolio selector and all three candidate constructions exposed.

## Exact scientific observations, local Linux

Environment: Python 3.13.5 / x86_64 Linux, libzstd and independent zstd CLI v1.5.7. Two deterministic seeds: 20261028, 20261029. Each cohort has 32 members x 64 KiB, split on 16 x 4 KiB atomic candidate blocks. Size values below are identical for both seeds. All figures count full scientific-envelope header, owners, per-owner SHA, compressed Zstd frames, per-member SHA and refs. The one-byte selector applies to portfolio totals.

| Regime | Direct bytes | Strong fixed 4-KiB CHUNKREF | SEGREF | SEGREF vs CHUNKREF | Per-member SEGREF units |
| --- | ---: | ---: | ---: | ---: | ---: |
| All identical | 2,098,764 | 68,524 | 66,878 | -2.4021% | 1 |
| 12 shared prefix blocks | 2,098,764 | 582,132 | 576,446 | **-0.9768%** | 2 |
| 12 shared suffix blocks | 2,098,764 | 582,132 | 576,446 | -0.9768% | 2 |
| 8 alternating shared blocks | 2,098,764 | **1,095,740** | 1,096,796 | +0.0964% (loss) | 16 |
| All distinct | **2,098,764** | 2,122,956 | 2,100,044 | SEGREF below CHUNKREF; **direct still wins** | 1 |

On the 12-shared-prefix regime, coalescing changes owners 140 → 33 and refs/member 16 → 2. In repeated in-process libzstd+Python+SHA verified full-member reads, the original fixed-chunk control was 3.93x and 3.91x slower by wall, 3.92x and 3.91x slower by CPU across seeds. Suffix12 had comparable ~3.78–3.86x decode ratios. These are **component timing observations**, not end-to-end CMPCT measurements. No cold-open, RSS, selectable byte-range, temporary materialization, platform integration or write amplification was measured. All three encodings were attempted during creation; a reduced create-time claim is unsupported.

**Primary verdict = FALSE**: the source-exact mechanism wins verified decode by >1.5x but the full-byte improvement is 0.9768%, missing the locked >=1.0% requirement. This is a deliberately preserved close failure, not rounded up to success.

## Mechanism criticism that changed the decision

The first provisional local control unnecessarily stored a 4-byte *raw length* in each fixed 4-KiB owner record. It produced 582,692 B for prefix12, making SEGREF appear to win by about 1.07%. That was a weaker control because fixed raw length is already declared once in the shared header. After replacing that redundant word with a compact fixed-size owner record, the same physical samples and mechanism produced 582,132 B CHUNKREF and the locked joint threshold no longer passed. Neither the source fixture, SEGREF, numeric threshold nor definition of winner was changed. **This is the decisive counterfactual lesson: charge the strongest *nonredundant* specialized comparator before promoting a representation that wins by roughly one percent.**

The alternating structural perturbation also fails: no adjacent shared run survives for grouping and its variable-size owner words cost 1,056 extra bytes. A candidate portfolio therefore correctly chooses CHUNKREF. All-distinct correctly chooses the direct full-member control; it must not claim SEGREF's apparent advantage over an unnecessarily granular CHUNKREF as a global win.

## Integrity and independent reanalysis

The full local research instrument reconstructed all members with per-owner/per-member SHA-256. Ten cases x three envelopes x 32 members = **960 independently rebuilt members**; the detached independent Python stdlib referee used external `zstd -dc` with full wire reparse, without importing producer decoding. It independently recomputed byte totals, owner/decoder-unit counts, size ratios and 2,160 raw in-process timing observations. It rejected **10/10 forged receipts**. A separate hostile mutation suite rejected **60/60** selected corrupted SEGREF envelopes (physical SHA, payload, bad ref, wrong member length, truncation, appended bytes). The exact input bytes for six overlapping seed/regime cases were cross-checked against A15-O1 original GitHub artifact `#12822588405`: **6/6 same SHA and source bytes**.

The GitHub-hosted `research/a16_o0_sharing_run_court.py` is a separate concise, auditable replication of the complete-byte/owner-count decision and exact reconstruction, using libzstd for compression and Zstd CLI for independent frame decompression. Its CI receipts and host identity must be evaluated separately from the detailed local timing/hostile audit; a green hosted byte court is **not** a three-host performance or product gate.

## Decision / frontier / debt

- **A16-O0 primary claim FALSIFIED at preregistered joint criterion.** Keep the low-level mechanism as a bounded scientific seed because the decode-unit count and full-member read improvement are real in these synthetic regimes.
- **A16-O0 structural transfer NARROW:** shared prefix and suffix give small byte gains; alternating shared/unique grouping loses; all-distinct fallback is mandatory.
- No product, format, on-disk compatibility, v0.31 release or 1.0 matrix credit. No modification to `src/`, `native/`, Discovery STATE, existing owner branches or published benchmark thresholds.
- Higher-value next discriminator is an inexpensive fully charged held-out **natural** family that has long repeated **physical** runs not already captured more efficiently by solid Zstd, with create/search/allocation and selective-read economics; do not spin adjacent tuning variants on the same synthetic 32x64KiB generator. Alternatively prioritize the existing source-owned Reader correctness / recovery and native-fused productization frontier.
- Discovery Engine selection: primary question was value of coalescing physical ownership boundaries; result changes the scientific decision from probable >1% size+decode gain to a close fail with decode benefit. No concurrency claim collision observed, no POLICY/STATE change justified by one result. Counterfactual discriminator: nonredundant fixed-size control metadata could have killed the joint byte claim *before* any expensive full benchmark.

No merge or release authorization is implied by this result.
