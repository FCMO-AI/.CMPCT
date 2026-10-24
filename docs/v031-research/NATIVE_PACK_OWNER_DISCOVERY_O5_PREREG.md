# O5 preregistration — authenticated physical-owner discovery for opt-in native batch

Status: **PREDICTION / UNMEASURED**. Frozen before product modification. Parent exact source: PR #322 `c8bddc71173c57516c76a8160f47ec5aae0bd0eb`; on-disk revision 24; published v0.30.0 unchanged.

## Primary question
Can a public native consumer discover a safe, operation-local Zstd S_PACK grouping key from an authenticated archive index, *without decoding data or guessing internal row layout*, so the independently measured PR #322 verified batching becomes practically addressable? No cross-open or persistence identity promise.

## Baseline and strong simpler control
The existing ABI exposes paths and logical `CmpctEntryInfo` but not physical owner. A caller currently can (a) repeat independently authenticated `cmpct_entry_read_range` with known O(N×PACK decode) expense; or (b) blind-try `cmpct_pack_read_batch` and receive unsupported on mixed owners. Control (a) is safe and preferred for singleton/RAW. Control (b) does not offer reliable generic admission for arbitrary filenames.

## Proposed bounded mechanism (hypothesis only)
Add opt-in `cmpct_entry_pack_owner(const CmpctArchive*, size_t entry_index, size_t* out_owner)`. It returns an opaque integer equality token for entries with `Storage::Pack`, codec Zstd and both declared compressed and decoded sizes within the existing 16-MiB batch cap. The number is *only* meaningful for comparing two entries on the **same live archive handle**; no ABI promise of persistent physical layout/owner ID. No file read, decode, allocation or hidden caching. Non-pack, RAW pack, unsupported or oversized pack fail with typed existing status. Null/out-of-range produce existing typed errors. All errors with a valid `out_owner` reset it to zero, including null archive. The query is **eligibility metadata**, never a guarantee of data integrity; every subsequent batch still independently authenticates the source.

## Predicted decisive tests / falsifiers
- Fixed Builder-independent Zstd and RAW r24 golden controls: Zstd same-owner keys equal; RAW returns Unsupported; output on errors zeroed.
- Real Builder two-Zstd-PACK 512-member corpus: discover at least two distinct owners from native metadata **alone**, form batches by group, and prove all returned bytes and SHA against separately read originals. No grouping via Python private `ar.files`.
- Mixed-owner batch still rejects without writing caller buffer; corrupted same-open physical data still rejects after metadata query.
- Null archive, null out-parameter, invalid entry index, unbatchable directory/codec, out-of-range outputs have typed error contracts. ABI C header must compile.
- N=1 remains an explicitly negative/no-guaranteed-improvement regime. Discovery per-member latency and sorting/allocations (caller owned), CPU/RSS must be accounted for before product credit.
- Kill/narrow: eligibility key differs for two entries from one physical owner; equal for two distinct owners; claims persistent identity across opens; metadata query touches/decodes payload; any silent malformed/corrupt acceptance; batch output altered on rejection; existing independent ABI broken; material discovery overhead erases value at realistic N.

## Alternatives and exported costs
No index/format change or new persisted metadata. Blind probing of every pair is quadratic, harms ergonomics and has failure paths; file-name heuristics are workload-biased; publicizing full physical blob/index structs expands ABI instability. One read-only scalar query is the smaller control. Still requires consumers to collect/group request descriptors; not a full multi-owner aggregator. Does not turn micro/ABI figures into end-to-end throughput claims.

## Ownership/concurrency and promotion
This is **adjacent O5 productization** stacked on active PR #322. Do not modify #322, PR #324, or their test gates. Dedicated candidate branch; source-identity and exact-head CI before accepting result. Coordinate with Issue #315; no merge/release/version changes. Separate PR #324 nested MessagePack hardening still needs composition before any promotion. Keep independent negative/performance receipts intact.
