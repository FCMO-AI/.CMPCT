# J24I18b — Live-blob reachability oracle (frozen before execution)

Date 2026-10-29 UTC; SOURCE-EXACT FOLLOW-ON, not modification of initial J24I18 prediction.

## Decision fork

J24I18 all-indexed-blob physical relay passes the independent 8-case r24 fixture and retains exact logical filesystem semantics, but source delta-update output is 1,297 B versus the installed Builder/extract compaction baseline 1,176 B. The overhead is dead referenced-table content plus index, and larger output is **real negative**. Do not misrepresent it as product win. Hypothesis H2: on that exact input, a strict storage-descriptor reachability graph can discard the single dead physical blob and rebuild one checkpoint without changing logical member bytes, fsmeta or integrity.

## Pre-result prediction and kill

On the frozen `delta-update-source.cmpct` public artifact from #723/J24I06 (input SHA256 `e423777d4a6d668879bdd3c290d12aedc2a4bc4070ec8b325165e1c9d8de8471`), one of two indexed blobs is unreachable by current live rows. Removing just that blob should reduce physical output below 1,297 B without modifying any file metadata, logical hash or content. Predicted clean output is <=1,200 B, still **not assumed** to equal or beat the installed Builder baseline (1,176 B) until observed. All 7 non-journal cases should remain byte-identical, or conservatively refuse an unsupported descriptor rather than silently prune it.

The only allowed reference kinds in this lower-rung oracle are `S_BLOB, S_CHUNKS, S_CDC, S_SPARSE, S_PACK` and authenticated `dict_blob`. `S_VZIP`, unknown storage or unknown recipe references fail closed; no virtual-container support is claimed. Hardlink aliases follow their owner as logical references without a second blob. Preserve original descriptor order for retained blobs, rewiring indices bijectively. Rebuild indexes using the unchanged original metadata and report full source/output SHA256.

Adversarial independently rooted verification: source vs result vs #723 physical Builder compaction via the existing detached J24I06 parser. Reject corrupt blob hash, out-of-range descriptor, truncated blob body, dangling hardlink, and unsupported storage before writing a result. Include source-immutable test.

If any live-byte or topology drift, reject the family; if output remains above the existing Builder baseline, preserve an architecture-only seed with explicit byte-debt and no compaction superiority claim. This is still exploratory, with no installed product, cross-platform, bounded-RSS, racing-source or crash-durability credit.
