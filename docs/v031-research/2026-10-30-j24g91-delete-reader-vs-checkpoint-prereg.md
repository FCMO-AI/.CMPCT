# J24G91 — Prospective physical Reader replay versus checkpoint discriminator

**Status: preregistered before instrument or results. Research only. Product, format, release and promotion credit: zero.**

## Repository authority and ownership

- Parent: PR #848 exact `6ef210998f6f7002fd57a661133a895fb7e67307`.
- Released reference: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, CMPCT v0.30.0, r24.
- Reader source blob at parent: `e716233403dabd0966863c45635e18fa5ac6afb8`.
- Distinct scientific question: does the existing full r24 terminal checkpoint still earn its extra physical bytes **after** a private, delete-only *one-pass* replay alternative is given the identical physical journal? This is **not** the exact #823/#820 implementation or a second production Reader. The #823 owner retains ownership of general replay/production integration; #842 owns new checkpoint grammars.
- Discovery coordination: PR #574 owns shared discovery-state reconciliation; this experiment never edits that file.

## Baseline, simpler control, mechanism

- Use the exact J24G90 source module to produce (A) 63 physically committed single DELETE generations, (B) its same-index r24 full signed checkpoint, and (C) B with a corrupted terminal footer that must recover A. Generate 4,096 and 8,192 regular tiny-file cases, retaining all complete stored bytes and SHA-256 of each physical artifact.
- **Unmodified public r24 `CMPCT`** opens A/B/C. The primary countermechanism is a private research subclass that inherits every public r24 read/decode/checkpoint/recovery primitive; it changes only how an all-DELETE, no-new-blob, no-positional-fsmeta delta chain is materialized. It filters the freshly decoded initial file list once with the set of deleted paths, instead of repeated full-list scans/sorts. If eligibility is not proven, it delegates to the original method. No unverified public mutable alias may be reused.
- The stronger external/inherited control is #823's broader owned Reader; a DELETE-only result is a *bound* on this narrow corpus, not evidence that #823 itself is production-safe or has identical timing.

## Frozen falsifiable hypotheses / decisions

1. **H_integrity (hard gate):** the public and private Reader must reconstruct identical complete canonical index MessagePack bytes, logical names, each member's SHA-256 content and `verify()` count on A/B/C; depth = 63/0/63; the private Reader must reject the bad B tail and recover A; source archive bytes must not change. Any mismatch is a hard scientific failure.
2. **H_replay:** on each measured host and both sizes, the private A Reader median wall is at least 2.0× faster than the unmodified A Reader. Failure narrows the causal hypothesis; do not reinterpret another metric as success.
3. **H_checkpoint_marginality:** on each measured host and both sizes, the **unmodified B Reader is no more than 1.50× faster** than the private A Reader. If it passes with H_integrity, then the checkpoint's claimed 3.8–4.9× benefit primarily measures the inherited replay implementation and does not justify its measured 4.9–8.3% byte cost by Reader-open time alone. If B remains >=2.0× faster at both sizes, checkpoint headroom survives; intermediate results are ambiguous.
4. Require CPU medians, balanced order and a memory trace. No relative speed result earns release/product credit.

Use 2 balanced blocks of six cyclic rotations of the six variants public/private × A/B/C: 72 timed observations per case; on Windows use 64 independent open/close repetitions per observation to avoid zero CPU quantization (report amortized per-open values). Preserve raw observations and fixture SHA. Warm-up may run but is not measured. The exact same cases must feed both Reader classes on a given host.

## Alternative explanations and adversity

- Host/Python clock, filesystem cache and construction pressure may change the result: alternating orders and both CPU/wall help, but these are not cold-process startup measurements.
- The candidate is deliberately specialized; arbitrary PUT/RENAME, signed xattrs, owner-override positional metadata, ambiguous journal shapes and other archive semantics *must* fall back rather than silently elide reconstruction. The program must directly exercise this fallback with a deliberately noneligible chain before attributing a speedup.
- A corruption-recovery comparison is mandatory; a green healthy chain alone is insufficient.
- Full archive bytes, index equivalence, signed journal footer SHA, host identity, interpreter and memory are charged/disclosed. No new checkpoint format, benchmark promotion, release change or synthetic competitor comparison is authorized.

## Stop/next rule

After this narrow decision, stop nearby checkpoint cadence/bitmap variants. If H_checkpoint_marginality passes, prioritize shipping-safe general Reader ownership (#823/#817) and broader mixed mutation/cross-platform tests. If it fails, retain both mechanisms as nondominated research and identify what time belongs to base-index decode versus reconstructing the residual set; no casual promotion. Document contradictions and share the result with #823/#848/#842, preserving PR isolation.
