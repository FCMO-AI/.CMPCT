# J24G99 — Rolling immutable tail-pack countermechanism (preregistered 2026-10-31 UTC)

**O0 scientific hypothesis only; no installed Reader/Writer, format, benchmark or release change.** Parent research #869; J24G98 on the same branch will have a contemporaneous exact-provider hosted court, but its local independently reproduced per-footer physical-allocation negative already motivates this *materially different ownership layout*. This preregistration precedes implementing or measuring the J24G99 tail-pack.

## Question and stronger controls
Can **one immutable base + one immutable, incrementally recopied cumulative tail-pack + one atomically switched manifest** retain byte-exact authentic revision-24 append histories while removing the block-rounding and FD explosion of one-file-per-footer segments?

Control A: existing in-place Writer append (only ~97 B added per DELETE, not immutable snapshot custody). Control B: full immutable archive copy per generation (one file, O(archive bytes) copied at every append). Control C: J24G98 one-file-per-footer physical fragmentation (no base recopy; huge 4KiB allocations; up to 65 held FDs). The new route instead recopies only a small bounded journal tail, not the base, per generation. This is not the already examined per-footer hash modification family.

## Prospective prediction and kill/narrow rule
On eight exact original SHA-verified 4/64-footer physical archives from #856/#853, cut at the authentic root footer; store the exact base once. For each subsequent actual physical footer append, write a NEW cumulative tail file (old tail remains readable to prior generation), fsync it, write and fsync a new manifest, atomically replace the manifest, fsync its parent directory. Verify whole-archive bytes and SHA-256 for every authentic history prefix, and independently verify the last state and predecessor's held snapshot. Use genuine original bytes and unchanged footer grammar; do not call a virtual concat an installed Reader.

For all four **64-footer** cases, preregister a viable O0 physical-organization screen only if:
- final **allocated base+latest-tail+manifest** bytes <=1.05× one same-directory physical original contiguous archive, measured via `st_blocks*512` and with directory/inode metadata debt disclosed;
- **cumulative materialized tail-copy bytes** <=40× the sum of physical appended journal bytes and <=0.10× a full immutable archive copy at each generation; count every repeated tail rewrite;
- cached-FD 4KiB random-read median <=2× same-runner contiguous-file median, paired alternating rounds, with identical bytes in every sample.
- per-current-reader FD count <=3. Record old-tail retention and worst transient allocations separately; small files may fail and remain baseline/fallback, do not hide the negative.

Stop/productization rejection if exact bytes, prefix identity, corruption rejection, or any immutable current-reference invariant fails. If costs miss thresholds, narrow or retire the rolling-tail family; do not change budgets. If large-N survives, require held-out mixed PUT/RENAME/fsmeta/hardlink/xattr, actual multiwriter CAS and immutable trust ownership before product credit.

## Integrity / recovery / portability limitations
Manifest metadata and segment file SHA are not independent issuer authentication. The source file owner can mutate even chmod 0444 content, and a head read followed by later data consumption is not automatically immutable. Actual crash/power-loss and multiple concurrent Writers are **not** established by fsync+rename on a live runner; the staged timeline is an observability model. A production Reader needs virtual range seeks or a range descriptor, strict bounds, verified immutable snapshots, garbage collection and cross-OS semantics. Only Linux container measurements are prospective here, even if source ZIP bytes were produced on Windows. No source CMPCT import, new revision/version, frozen comparator, full promotion gate or broad security claim.

## Counterfactual and next decision
The J24G98 per-footer block-allocation excess is a prospective, observable predictor that *fragment unit smaller than filesystem allocation granule* can erase O0 savings. This experiment changes the ownership boundary from each 97B delta to an amortized immutable tail. Charge recopy amplification rather than hiding it as free CoW/reflink. Preserve failures and source exactness, and let the simpler direct-append product baseline win if this only moves the cost.
