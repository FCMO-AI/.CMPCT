# R42 live handoff — 2026-09-17 18:26 UTC

Authority remains `agent/v030-authoritative-integration` @ `285ff0cf5efed1352260f8dc07a2ce9d665024b4` (R41 merged). No R42 result below is release credit until measured and promoted under repository law.

## Primary extraction lane

`agent/v030-r42-native-oracle-authority` is based directly on current authority. Its current oracle executes the repository's already-existing fail-closed `benchmarks/v030_g04_ml_native_reader_oracle.py` against the exact frozen `neutral_hostile_v1/09_ml_artifacts` source, with source hash checked against accepted v0.29 evidence. The harness was tightened to generate only the measured frozen ML target; this changes setup cost only, not input bytes or timed extraction boundaries. Run `35257655403` was still executing the exact-frozen native/Python A/B when this handoff was written.

The native route is an oracle for execution-ownership headroom, not an automatic product win: the existing bridge requires an external `cmpct-portable` binary, so packaging/deployability cost must be charged before promotion.

## Independent reader hypothesis

Profile evidence says SHA-256 constructor/update work is a large ML extraction owner. Reader inspection establishes a narrower exact redundancy: for a G0-G4 record with `CODEC_RAW` and no physical transform, the physical payload and reconstructed original are the same bytes. The authenticated record leaf is `SHA256(payload)` while the physical header separately declares `original_sha256`. If those two digest declarations are equal, one SHA-256 computation can satisfy both exact-byte checks; CRC32 remains independently checked, so header-CRC corruption is not hidden.

`agent/v030-r42-reader-hash-dedup` run `35257995563` measures this without changing product code: seven alternating exact-tree extractions compare shipping reader behavior against a memoized-H oracle that reuses only consecutive same-object SHA results, while reporting hit count/bytes and raw/no-transform addressable bytes. This is research/oracle evidence only.

## New build-time contradiction requiring control

The prior pre-R41 R42 owner-diagnosis run `35251368048` completed its entire shipping-front-door profile in 48 seconds and its delimiter counterfactual in 96 seconds. By contrast, multiple current-authority R42 workflows were still inside a single exact frozen ML `PRODUCT.build` after many minutes. This is not yet attributed to R41: hosted-runner variance or another setup interaction remain alternatives.

Two controls are therefore in flight rather than narratively blaming R41:

- `agent/v030-r42-pre-r41-ml-build-control`, run `35258645596`: exact frozen ML one-build control on pre-R41 authority `94dd456ff508ae4e60ba9230bc071fdc9cc4708d`.
- `agent/v030-r42-r41-map-control`, run `35258740291`: current authority with only `cmpct.builder.ordered_worker_pull` replaced at runtime by the exact pre-R41 `ThreadPoolExecutor.map` semantics for the build. Archive/tree verification remains mandatory.

Interpretation rule: only if the pre-R41 and/or current-head map control materially outruns unchanged current-head setup on the same frozen source should R41 become a causal suspect. Do not revert or rewrite R41 from elapsed-step anecdotes alone.

## Next decision

1. Reconcile the native A/B and hash-dedup oracle first if they complete with exact identity.
2. Reconcile the two ML build controls before changing R41.
3. If native wins materially, compare its productization carrying cost against the smaller hash-dedup intervention rather than assuming the larger speedup is automatically the better product route.
4. If current-head build slowdown is causally assigned to R41, repair or revert that regression before claiming further extraction progress; a builder optimization cannot remain promoted if it catastrophically harms an important frozen workload.
