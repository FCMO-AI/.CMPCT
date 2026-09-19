# R25 G0-G4 ML native in-process FFI reader v3 preregistration

Status: **FROZEN BEFORE RESULT-BEARING EXECUTION**

v3 supersedes only the invalid candidate-construction transport recorded in `R25_G04_ML_NATIVE_FFI_V2_INVALID_RESULT.md`. The scientific question is unchanged: on exactly `neutral_hostile_v1/09_ml_artifacts`, can the existing Rust G0-G4 semantic owner materially outperform canonical Python when authenticated decoded physical records are reused across members inside one verify/extract operation and both are exercised through the same in-process FFI boundary?

Frozen experiment and decision law are inherited unchanged from v2: exactly five alternating Python/native pairs; native library load outside timing; archive open, FFI call and all verify/extract work inside timing; `G04_ML_FFI_SHARED_CACHE_HEADROOM_SUPPORTED` only when native median verify and extract each improve by at least **20%**; valid failure of either floor is `G04_ML_FFI_SHARED_CACHE_HEADROOM_NOT_SUPPORTED`; construction or invariant failure is `CANDIDATE_INVALID`. There is zero release credit.

All representation and safety laws remain immutable: archive bytes, grammar and product selector unchanged; exact tree and full CRC/SHA integrity; hostile corruption rejected; caller extraction-output budget checked before publication; 8 MiB decode-unit bound; 8x member decoded-context locality; existing record/node memory ceilings; transactional publication semantics. Cache hits remain charged to member-local touched-record accounting; node state is never gifted across member boundaries.

The sole v3 repair is mechanical. Instead of depending on either malformed historical patch, `benchmarks/v030_g04_shared_record_cache_candidate_v3.py` performs fail-closed, exactly-once source substitutions against the frozen canonical Rust source shape. It introduces the same bounded operation-scoped record cache for G0-G4 verify and regular-file extraction, preserving fresh member-local node/touched state. PrefixGraph is untouched. The workflow must show the temporary Rust diff, compile it, pass canonical G0-G4 correctness tests, run the unchanged v1 oracle, restore source, and preserve execution under exact `github.sha` concurrency.

A positive result authorizes only a Builder integration attempt and full requalification; a valid negative retires this execution-reuse family for this exact ML/full-archive/in-process regime absent new causal evidence.
