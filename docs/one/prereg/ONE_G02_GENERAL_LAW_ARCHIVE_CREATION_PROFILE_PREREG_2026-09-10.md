# ONE-G0.2 general Law archive creation profile — preregistration

Date: 2026-09-10
Branch: `research/cmpct1`
Experimental version: `ONE-G0.2`
Status: preregistered before result-bearing performance execution

## Mission Lock

Measure whether the automatic general-tree Law archive seed earns its stored-byte and source-traffic gains without exporting an unacceptable creation/RSS tax. This is transfer-only performance evidence. It must not touch the frozen 15-workload Genesis corpus.

The semantic boundary remains the preceding `ONE_G02_GENERAL_LAW_ARCHIVE_BOUNDARY_PREREG_2026-09-10.md`. If that semantic boundary is not green, this profile has no promotion authority even if timings look favorable.

## Comparator

Same-input authenticated Surprise-only archive seam: `experiments/one/authenticated_archive_envelope.py`.

Both sides produce a complete ONE0 Program carrying the same canonical filesystem manifest and persisted generic AuthTree metadata. Candidate changes only encoder discovery and resulting ordinary ONE Law roots.

## Frozen transfer cases

Use deterministic content independent of Genesis:

1. `unrelated-1m`: two unrelated 1 MiB cryptographic hash streams. Expected candidate outcome: no Law accepted, byte-identical wire to comparator.
2. `exact-copy-1m`: 1 MiB hash stream followed by an exact copy.
3. `add8-1m`: 1 MiB hash stream followed by ADD8(+37).
4. `mixed-8x512k`: eight 512 KiB files containing Surprise, exact reuse, ADD8, XOR, Fill and unrelated content.

Each case is generated once outside timed regions and reused read-only by both arms.

## Process boundary

Creation samples execute in fresh Python child processes so peak RSS is not contaminated by preceding archive builds. The child measures `process_time_ns` and `perf_counter_ns` strictly around its build call and reports `resource.getrusage(RUSAGE_SELF).ru_maxrss` with Linux KiB conversion. The parent alternates baseline/candidate launch order by round; process startup is reported separately as parent-observed elapsed and is not mixed into the algorithmic build CPU ratio.

Run 9 measured rounds after one untimed warm/import sanity launch per arm/case. Compare medians; retain every sample.

## Required semantic checks in every measured case

- candidate and comparator whole reconstruction are byte exact;
- candidate build is deterministic across an independent repeat;
- `unrelated-1m` candidate wire is byte-identical to comparator;
- no reader-visible operation outside `surprise/concat/repeat/fill/xor/add8`;
- no candidate authentication source reread;
- candidate source-read accounting equals one logical source pass;
- comparator source reread accounting is retained, not hidden.

## Falsifiable performance hypothesis

Cheap negative gating plus eliminating the authentication source reread should keep automatic discovery creation cost bounded on unrelated data, while productive Law cases trade additional proof CPU for material wire elimination.

### Frozen performance gates

Unrelated negative control:

- candidate/comparator median build CPU <= **1.15x**;
- candidate/comparator median build wall <= **1.15x**;
- worst candidate/comparator per-paired-round CPU <= **1.30x**;
- median peak RSS <= **1.10x** comparator;
- candidate wire bytes == comparator wire bytes;
- candidate exact relation proof bytes == 0.

Productive Law cases:

- every case candidate stored bytes < comparator stored bytes;
- median productive stored-byte ratio <= **0.70x**;
- median productive build CPU <= **2.00x** comparator;
- no productive case median build CPU > **2.50x** comparator;
- median productive peak RSS <= **1.20x** comparator.

These are seed viability gates, not product release gates. Passing them permits deeper discovery/profiling; it does not certify the Genesis candidate.

## Source/memory traffic interpretation

Report candidate `source_read_bytes`, `authentication_source_reread_bytes`, `discovery_sample_bytes`, `discovery_exact_proof_bytes`, `max_predictor_bytes`, manifest/auth-index bytes and node counts. Do not infer memory bandwidth from Python loop time alone.

## Hostile review / confounders

- Python generator/proof loops may dominate and make the Law seed slow despite lower disk-read accounting.
- Linux `ru_maxrss` includes interpreter/import baseline; ratios can therefore understate small incremental memory differences. Preserve absolute values and treat RSS as coarse until a native/profile-specific owner study.
- Filesystem cache state can influence wall time. CPU is the primary creation-compute measure; wall remains mandatory evidence.
- Fresh-process startup is intentionally not called build time, but parent launch elapsed is retained so this decision cannot later be mistaken for CLI cold-start authority.
- No threshold may be changed after observing results. A miss becomes HOLD/RETIRE evidence.

## Decision law

- `ADVANCE_CREATION_PROFILE` only if the semantic boundary is independently green and every frozen gate above passes.
- `HOLD_CREATION_COMPUTE` if correctness is intact but any creation/RSS gate fails.
- `RETIRE_OR_REPAIR` for any semantic, determinism, integrity or fallback-wire failure.

Regardless of decision, preserve all rows and the strongest regression.
