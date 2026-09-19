# CMPCT v0.30 release gates

This checklist is normative for the authoritative integration branch. Research success is necessary but never sufficient for release.

## Compression / causality
- [ ] full G0-G4 Geometry path survives complete-artifact accounting against accepted v0.29
- [ ] PrefixGraph is integrated as a bounded depth-1 graph/reference feature, not credited from a standalone oracle
- [ ] repaired 15-workload suite: 0 inherited byte regressions
- [ ] every credited row reproduces its frozen source-tree identity and accepted v0.29 byte count
- [ ] exact ablation: v0.29 / Geometry-only / PrefixGraph-only / combined
- [ ] no independent-savings arithmetic is used as combined evidence

## Locality / resource bounds
- [ ] per-member read amplification <=8x on every selected representation
- [ ] max decode unit <=8 MiB
- [ ] bounded transform search and descriptor counts
- [ ] bounded MessagePack declarations before allocation
- [ ] bounded archive-wide extraction/materialization

## Integrity / recovery
- [ ] payload CRC/SHA and authenticated tree identity
- [ ] malformed descriptor, record overlap/alias, offset, reference-id and traversal adversaries
- [ ] primary-metadata recovery from damaged tail
- [ ] tail recovery from damaged primary
- [ ] streamed strong verification
- [ ] transactional extraction and destination rollback on publication failure

## Performance
- [ ] create-time controlled repeated comparison against v0.29
- [ ] extract-time controlled repeated comparison
- [ ] selective-read comparison
- [ ] peak-memory accounting
- [ ] generic inherited scheduler uses same-filesystem zero-copy winner publication
- [ ] candidate scheduling/analysis does not retain the known unacceptable inherited create-time regression

## Portability
- [ ] Python reader/writer vectors
- [ ] native/shared-reader parity for every new promoted transform/reference and filesystem-control dialect
- [ ] canonical implicit-v4 filesystem control has builder-independent G04/PrefixGraph goldens, live-writer parity, exact public-tree reconstruction, <=8x selective-read observability, primary/tail two-way recovery and fail-closed both-metadata/payload corruption through the shared native reader
- [ ] hosted Android/JNI opens and verifies builder-independent canonical implicit-v4 G04/PrefixGraph archives through the shared portable C ABI, and its exact-fingerprint evidence records implicit-v4 dispatch explicitly
- [ ] any required physical ARM64 Android receipt is derived only from matching hosted evidence that proves canonical r25 + implicit-v4 + promoted dispatch surfaces on the same SHA/fingerprint
- [ ] logs inverse profile is admitted through production `cmpct-portable` dispatch, not a shadow parser
- [ ] logs inverse native parity preserves gzip+Zstd inverse reconstruction, SHA-256 identity, <=8x locality, <=8 MiB decode units and primary/tail recovery
- [ ] logs inverse public filesystem view preserves regular files, directories, symlinks and hardlinks without exposing internal manifest members
- [ ] Android/JNI opens and verifies a canonical Python-generated logs inverse archive through the shared portable C ABI
- [ ] deterministic builder-independent golden archives
- [ ] ZIP/export parity and recovery semantics
- [ ] malformed/fuzz corpus green
- [ ] platform/Android acceptance required by existing repository policy

## Competitive evidence
- [ ] exact external competitor matrix rerun on controlled substrate
- [ ] **every frozen workload produces a canonical CMPCT archive strictly smaller than ZIP/Deflate-9**
- [ ] **every frozen workload produces a canonical CMPCT archive strictly smaller than solid tar+Zstd-19**
- [ ] **every frozen workload creates its canonical CMPCT archive strictly faster than ZIP/Deflate-9**
- [ ] **every frozen workload creates its canonical CMPCT archive strictly faster than solid tar+Zstd-19**
- [ ] equality with ZIP or Zstd on size or creation time is a failure; aggregate or suite-level wins cannot offset a losing/tied row
- [ ] archive size comparisons disclose semantics/locality differences
- [ ] timing comparisons use symmetric controlled methodology and may not cherry-pick process/order effects

## Promotion
- [ ] canonical format/revision decision recorded
- [ ] version discipline green
- [ ] release notes generated from durable evidence
- [ ] website benchmark surface generated from accepted evidence only
- [ ] public-surface guard green
- [ ] gh-pages freshness/live verification green
- [ ] final release commit merged to `main`

Footnote: fallback can preserve correctness and no-regression size, but it cannot by itself satisfy release worthiness. v0.30 must demonstrate a material broad-system improvement, not merely contain dormant research mechanisms. The per-workload ZIP/Zstd dominance rule covers both complete archive size and creation wall-clock and may not be weakened to aggregate parity.
