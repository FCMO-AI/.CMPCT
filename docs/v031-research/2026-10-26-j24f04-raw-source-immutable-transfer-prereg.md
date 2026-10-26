# J24F04 — detached RAW chunk ownership before SHA + staging write (preregistration)

Date: 2026-10-26 UTC. Parent exact-head J24F03 #530 `713c67db65a0e7ee52091680317c1f1d1dfe5f7a`; released v0.30.0/r24 and development branch remain unchanged. This is a **separate draft product-fix candidate**, not a claim about publication identity (#528) or universal immutable source trees.

## Verified baseline and threat model
J24F03 #530 / Issue #531 independently proved on Ubuntu/macOS that `CMPCT._extract_chunked_verified` hashes a borrowed `memoryview(self.mm)` of each all-RAW S_CHUNKS/S_CDC source chunk before stage `os.write`. An independent writer with permission on the same archive inode can change source bytes between these operations, and existing code returns success but publishes foreign bytes. The original immutable-archive extraction and SHA controls succeeded.

## Mechanism hypothesis
Detach *one physical RAW chunk at a time* to an immutable Python `bytes` object before both `digest.update` and stage `os.write`. Explicitly release each borrowed `memoryview`. Same bytes, same authenticated SHA, same bounded stage flow. Every successful logical output then matches the indexed whole-file SHA in the J24F03 threat model; if source mutation taints the chunk during copying, the detached content is what both SHA and write consume, so an indexed SHA mismatch must fail closed. This is not a file-level snapshot guarantee.

## Controls and predictions (frozen before product mutation)
1. **Positive:** historical unmodified J24F03 source reproduces both RAW S_CHUNKS and S_CDC attack failures on Ubuntu/macOS; preserve its original unmodified court and artifacts.
2. **Candidate:** reuse independent real-wire J24F03 archives, real installed Reader and independent process source modification at first stage write. Candidate must either publish indexed-authentic bytes with `extractall` success or raise an integrity error without publishing foreign bytes. Require mutation event, same source inode/size, 2/2 representations and unchanged no-attack controls; output bytes indexed SHA if published.
3. **Adversarial:** if actor mutates a later *not-yet-snapshotted* chunk instead, candidate must fail indexed logical SHA rather than publish wrong bytes; original corruption behavior must remain intact.
4. **Economic:** the baseline RAW path intentionally avoided copies. New bound is at most one additional chunk of detached memory per consumed iterator chunk; count actual full-product wall/CPU/RSS, raw repeated outcomes, temporary I/O on same source before promotion. A microbench can constrain but cannot earn product credit. Do not weaken benchmarks, comparators, historical vectors or integrity criteria.
5. **Negative scope:** stage pathname replacement after full SHA (#528), mmap truncation SIGBUS (#460), ZIP export source lifetime (#286) and Win32 missing `fchmod` (#535/#536) are independent; no false closure.
6. **Kill/narrow:** if any unchanged genuine valid archive fails, attacker can still cause success with published SHA mismatch, the copy can be bypassed by a live mmap view, any requested allocation is unbounded beyond existing chunk-size contract, or material performance debt cannot be rehabilitated, do not promote.

## Alternatives
- Second SHA over borrowed mmap just before write: race simply moves; rejected.
- Full-file immutable copy/snapshot: stronger scope but potentially unbounded RSS/temp I/O; rejected for this narrow repair.
- Require immutable external source ownership: would narrow user contract and requires enforcement; unproven.
- Selected: one chunk-sized immutable buffer; preserve stage publication and other owners separately.

No version/format/release change. No automatic merge. Research source, failure cases, PR #530 and issue #531 are durable authority.