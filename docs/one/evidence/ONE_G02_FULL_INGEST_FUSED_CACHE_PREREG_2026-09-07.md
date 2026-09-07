# ONE-G0.2 fused-cache whole-ingest falsifier — preregistration

Date: 2026-09-07
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Mission owner: ONE-07 discovery cache / incremental compilation

## Mission Lock / Referee

### Problem

The fused observation cache has earned component-level evidence: exact opportunity parity, conservative charged-traffic savings and repeated wall/CPU wins on positional repeat/sparse-update workloads. That does not establish that it materially lowers the cost of the broader ONE writer. Amdahl dilution, duplicate current-content hashing, relation admission, segmentation, Program construction, validation and canonical emission may erase most of the observer-local win.

The next decision is therefore system-scope: does the existing fused cache reduce **total adjacent-version research-writer creation cost** when its positional reuse premise holds, and what debt does it export on hostile cases where that premise fails?

### Baseline

Both arms use the current promoted research-writer shape already evidenced by the root-hash-charged direct-emitter gate:

`fresh/current observation -> SHA-256(previous,current) -> amortization-safe relation admission -> native one-pass segmentation when admitted -> bounded generic Law/Surprise Program -> full validation -> direct final-buffer canonical emission`

The candidate changes only the first stage:

`sealed positional fused-cache observation -> same remaining writer path`

The seed cache is produced from the previous version before the timed current-generation update. Its persistent payload remains charged as retained writer state; its build time is not charged to the current update, matching the ONE-07 repeated/versioned-use question. Cache state is never required by the reader.

### Hard invariants

- byte-exact output reconstruction;
- candidate observation run/reuse opportunities equal a fresh independent `observe()` oracle;
- canonical ONE wire bytes/stats equal for baseline and candidate on the same row;
- relation admission classification and native segment-plan semantics remain unchanged;
- full Program validation remains inside both timed writer paths;
- SHA-256 for both previous/current roots remains inside both timed paths;
- no reader-visible opcode, wire-format or canonical-version change;
- no weakening of existing bounds, exact reuse proof, integrity, locality or comparator semantics;
- frozen v0.29/v0.30 authorities are untouched.

### Falsifiable hypothesis

For positional version updates with substantial unchanged 4 KiB observation blocks, sealed fused observation reuse lowers **whole research-writer** wall and process CPU after root hashing and all existing downstream writer work are charged. The gain should remain material on exact repeat and a one-block edit, while an eight-block sparse edit should not become meaningfully slower.

The current positional cache is not expected to help one-byte-shifted or independent-random controls. Those rows are retained to expose exported cost rather than averaged away.

### Disproof / decision rules

Sizes: 64 KiB and 256 KiB. Repetitions: 15 paired alternating A/B-B/A runs. Observation block: 4 KiB; fingerprint chunk: 64 B.

Productive positional gates at **both** sizes:

- `exact_repeat`: candidate/baseline median wall <= 0.95 and CPU <= 0.95;
- `one_block_edit`: wall <= 0.98 and CPU <= 0.98;
- `eight_block_edit`: wall <= 1.02 and CPU <= 1.02.

Hostile controls:

- `shift_plus1` and `independent_random` are not required to win because positional cache identity is intentionally invalidated there;
- each hostile row must remain <=1.15 wall and <=1.15 CPU to avoid immediately indefensible carrying cost;
- hostile regression above 1.15 with productive positional success yields explicit **admission/regression debt**, not a weakened threshold or a false global promotion.

Terminal decisions:

- semantic/oracle/wire divergence -> `INVALIDATE_FULL_INGEST_CACHE`;
- any productive positional gate failure -> `REJECT_OR_REFORM_FULL_INGEST_CACHE`;
- positional gates pass, hostile controls all <=1.15 -> `ADVANCE_FUSED_CACHE_TO_BROADER_INGEST`;
- positional gates pass but one or more hostile controls exceed 1.15 -> `OPEN_CACHE_ADMISSION_DEBT`.

No threshold may be moved after seeing the result.

### Cost model

Record per row:

- total baseline/candidate wall and process CPU medians;
- baseline fresh-observation wall and candidate cached-observation wall medians;
- root-hash wall medians;
- downstream writer wall medians;
- baseline observation share of full baseline creation (Amdahl owner estimate);
- cache reused/recomputed blocks and bytes;
- cache validation reads;
- feature recompute/reuse bytes;
- independent complete seal-hash charge;
- cached feature payload reads;
- exact reuse-proof reads;
- persistent cache payload bytes/ratio;
- canonical wire/Law-Surprise accounting and reader work from the unchanged writer.

The experiment does not call modeled byte traffic equivalent to CPU cycles. Wall/CPU remain the performance authority.

### Independent evidence plan

- Fresh `experiments.one.observe.observe(target)` is the independent opportunity oracle for cached observation.
- Existing independent Python segment oracle must agree with the native segment plan whenever the relation path is admitted.
- Candidate wire is decoded through the ordinary ONE decoder/evaluator and must reconstruct `{previous,current}` exactly.
- Baseline/candidate canonical bytes and encoding stats must be identical.

### Hostile envelope

This first whole-ingest gate explicitly includes:

- exact repeat;
- one 4 KiB block changed by one byte;
- eight dispersed changed blocks;
- one-byte `shift_plus1` temporal movement from the existing relation corpus;
- independent deterministic-random target.

Tiny one-block cache economics, arbitrary insertion length changes, media/already-compressed inputs, append growth, RSS and authenticated physical placement remain separate debt. They must not be implied by a pass here.

## Builder constraints

The benchmark must compose existing modules rather than inventing a new reader or a second writer representation. It may add only experiment-side orchestration/accounting needed to time the integrated envelope.

## Hostile Reviewer focus

The strongest expected objection is that the candidate double-hashes current bytes: block SHA-256 for cache identity plus full-current SHA-256 for the root. If the integrated gain disappears, the result should be interpreted as a real system-level cost collision, not repaired by moving timing boundaries. If the cache wins but the hostile controls regress, the next task is an evidence-based admission mechanism or shared authentication/validation path—not permanent unconditional caching.

## Claim boundary

A pass establishes only that fused positional observation caching can reduce the measured **adjacent-version research-writer envelope** on the frozen positional matrix. It does not establish canonical product creation speed, authenticated placement/durability, arbitrary shifted updates, archive density superiority, selective-read authority, native writer authority or v0.29/v0.30 supremacy.
