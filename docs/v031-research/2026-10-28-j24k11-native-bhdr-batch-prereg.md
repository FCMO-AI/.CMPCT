# J24K11 — Native batch physical-header witness, fully charged (preregistration)

Date: 2026-10-28 UTC
Status: PREREGISTERED / UNMEASURED / COMPONENT RESEARCH ONLY
Parent: J24K09 #653 at `2d30cc6da41c136f3b1a412ccf3f1f5686dca54a` (published `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/r24).

## Primary question
Can a single native ABI3 entrypoint prove all preceding signed non-regenerated Virtual ZIP physical BHDR descriptor/stream-length matches, with *no persistent cache and no snapshot copy*, faster than the actual Python per-stream witness when the full Python->native bridge and source-read costs are charged? This addresses J24K09's 4,096-prefix cost while not taking the unproven J24K09b cached-immutability shortcut.

## Controls and forecast, before looking at results
- Baseline: exact logical conditions in `CMPCT._vzip_physical_stream_size`: signed descriptor fields vs same-buffer BHDR magic/codec/flags/reserved/decoded size/compressed size/meta size/record bounds, using the descriptor's `usize` for STORED/mode1 or `csize` for mode0. No decoding.
- Candidate: compiled limited-ABI CPython helper (or conservative C shared-library proof), one call per query; no inter-read memoization. If a descriptor is structurally unsupported or any witness fails, return failure so the unchanged Python guard can raise the inherited diagnostic; never treat a native negative as success.
- Stronger simpler control: Python `struct.Struct.unpack_from` in one loop, without repeated Reader method-call overhead; measure both to ensure an apparent win does not solely reflect a removable wrapper.
- Alternate hypothesis: Python tuple-to-FFI marshalling and buffer ownership work consume the whole win. If so, retire batch native as an unproven improvement.
- Geometries: 64, 512, 4096 physical streams, STORED, canonical Deflate mode0, retained mode1, exact physical byte arrays and same physical offsets. Include randomized owner placement and adversarial +1/-1 declared length, flags, codec, truncated record, overflow offsets, invalid index/types where applicable.
- Measurements: 12 fresh repeated samples per arm/geometry with ABBA order, wall and process CPU medians; explicitly charge every per-query bridge conversion, native call and returned result. Record source length, bytes allocated to bridge, number of headers proved, exact answers/errors. Compilation, import and process startup separate and declared; do not hide them in throughput.
- Decision: **material headroom only** if candidate beats both Python controls by >=1.5x wall AND CPU for 4096 headers while every negative rejects, without >2 MiB *persistent* extra per-reader data and no source copying. If it fails, retain the signed negative and do not implement product or extend this family by threshold gardening. One-host initial experiment sufficient for this bounded fork. Cross-host, actual installed Reader, full-product decode and official parity are separate promotion gates.
- Kill at once on any mismatch, unaccounted bridge work, byte semantics weakening, or acceptance of a signed/physical conflict. A C return value alone is not proof of equivalence; independent Python witness and mutations must agree.

## Inherited boundaries
J24K09 #653 already owns the *product* Python BHDR fix. J24K10 #657 owns copy-vs-per-query economics; J24C08 #641 and O218d #631 own `S_CHUNKS` ABI3 admission, **not** this VZIP BHDR question. Do not edit their branches or change `src/`, `native/`, historical tests, frozen vectors, discovery STATE, format or release gates. This is a prospective independent science oracle, not product credit.

## Continuation / decision provenance
Keep append-only raw observations, evaluator output and source SHA in a durable branch/PR; include negative and ambiguity. If a hosted workflow runs independently, record exact URL/head/artifact and continue another safe lane. An experimental Python/C scanner does not authenticate the partial byte's SHA or resolve mode2 prefix regeneration, cache invalidation, or same-inode mutation; do not claim it does.
