# ONE-G0.2 incremental relocation persistent-directory experiment — 2026-09-07

Status: **implemented / exact-head CI pending; no performance promotion claim**

Branch: `research/cmpct1`

## Mission Lock / Referee

### Observed cost owner

The preceding relocation-cache seed reduced candidate state to one representative per unique `(SHA-256 digest, length)` identity, but movement-triggered lookup still lazily rebuilt that unique-identity index by scanning the entire previous cache. Low-cardinality inputs could therefore show tiny index payload while still paying O(previous-block-count) candidate-discovery traffic after movement was detected.

### Falsifiable hypothesis

A bounded writer-only identity directory constructed during the already-required current observation can be carried with the discovery cache and used by the next version to nominate moved content without rescanning the previous cache. If directory state is stale or corrupt, ordinary current-content identity plus cached-feature seal validation must make the failure fail closed to recomputation.

### Disproof / retirement result

Reform or retire this shape if any of the following occurs:

1. incremental and fresh fingerprint streams diverge;
2. a malformed/stale directory can cause corrupted cached features to be accepted;
3. aligned-movement lookup with a compatible directory still scans previous cache blocks;
4. directory construction/persistence cost erases the movement win under the frozen wall/CPU/resource gate;
5. persistent directory payload exceeds the existing bounded resource contract or becomes reader-visible state.

### Non-goals

- no arbitrary byte-shift resynchronization claim;
- no reader-visible index/opcode;
- no archive-byte change;
- no claim that current-source SHA-256 validation is free;
- no product/native authority from Python measurements.

## Builder change

`experiments/one/cache_relocation.py` now emits a `RelocationDirectory` beside the writer discovery cache. The directory stores at most one `(digest, length, block_index)` representative per unique current block identity, bounded by `max_relocation_entries`.

The directory is built incrementally while current blocks are already traversed. On a later update, the two-consecutive-positional-miss opportunity gate may consult the compatible prior directory instead of scanning all previous cached blocks to construct relocation candidates.

The prior lazy full-cache scan remains only as an explicit compatibility/control fallback when no compatible directory is supplied. New accounting exposes `prior_cache_index_scan_blocks`, directory output entry count, and lower-bound directory payload bytes.

## Hostile-review invariants

A directory entry is nomination metadata only. The nominated prior block must still:

- be in range;
- reproduce the current block's SHA-256 digest and length;
- satisfy the normal policy/shape-bound sealed fingerprint validation.

Thus a corrupt index, wrong key, stale policy, invalid representative, or damaged fingerprint payload can only lose reuse and force fresh computation.

New/updated tests attack:

- exact repeat with no relocation activation;
- one sparse mutation with no global search;
- aligned insertion with relocation reuse and zero prior-cache index scan;
- block reorder with zero prior-cache index scan;
- legacy no-directory fallback, which must expose its previous-cache scan explicitly;
- repetitive low-cardinality reorder;
- damaged unique representative;
- corrupt/out-of-range persistent directory entry;
- bounded directory/index cardinality;
- policy relabeling;
- arbitrary one-byte insertion;
- current digest identity after relocation.

## Resource accounting

The lower-bound persistent directory model is 48 bytes per unique identity:

- SHA-256 digest: 32 B;
- length: 8 B;
- representative block index: 8 B.

This is not an RSS claim. Python object/hash-table overhead and eventual native implementation cost remain open and must be measured directly.

The important mechanism-level change is different: with a compatible carried directory, candidate discovery for a moved update no longer requires scanning the previous cache at relocation activation. The current input is still fully SHA-256 validated block by block, and directory construction for the *next* generation is folded into the current traversal rather than a second previous-state pass.

## Frozen resource falsifier update

`benchmarks/one/one_incremental_relocation_cache.py` now passes the carried directory into the relocation candidate and fails the experiment if `prior_cache_index_scan_blocks != 0` on any candidate row. Existing wall/CPU gates remain unchanged:

- aligned block insert/reorder: feature recomputation <=0.10x positional baseline and wall/CPU <=0.90x;
- exact repeat: no relocation index/lookups and wall/CPU <=1.05x;
- sparse mutation: no relocation activation/index/lookups and wall/CPU <=1.08x;
- hostile one-byte insertion: wall/CPU <=1.15x;
- relocation index and output directory lower-bound payload each <=2% of current input.

No threshold was weakened to make the persistent directory pass.

## Evidence truth at commit time

Implementation, hostile tests, and the frozen benchmark contract are committed. Exact-head hosted CI/resource evidence was not yet complete when this receipt was written. Therefore there is **no claimed wall-time, CPU, RSS, stored-byte, access, decode, or Genesis-comparator win from this receipt alone**.

## Strongest self-critique

The persistent directory removes one avoidable scan, but it adds persistent writer state and per-current-block directory-maintenance work. In Python, hash-table insertion and object traffic may be large enough that the cure only shifts cost from update-time scan to previous-generation construction. The decisive test is whole repeated-version economics, not the appealing asymptotic story.

The directory also remains aligned-block identity. It does not solve one-byte shifts; solving those without semantics drift requires a different observation primitive such as content-defined anchors and must be evaluated separately.

## Next decisive action

Run the frozen positional-vs-persistent-directory relocation gate and inspect wall/CPU plus the new scan accounting. If aligned movement clears the gate with zero previous-cache scan, add direct peak-RSS measurement and then test the directory with more expensive real ONE observation features. If wall/CPU still fail despite removing the scan, localize whether the owner is current SHA validation, seal verification, directory construction, Python hash-table traffic, or insufficiently expensive cached features before changing the representation again.
