# Genesis historical-comparator source-seal repair

Status: **REMEASUREMENT REQUIRED**

This note is an evidence quarantine, not a Genesis score or winner decision.

## Mission lock

The frozen historical comparators remain:

- v0.29: `02b8b27cb2d97af7c6e0797984a898e8fa8a8e5d`
- v0.30: `f4b158a55a08b9b18b50e4e4abe4b9251048c772`

No comparator source, workload identity, repetition count, scoring rule, locality rule, or semantic requirement is changed by this repair.

## Discovered failure

The v0.30 resume diagnostic run `34588634283`, job `103228550460`, completed the first two frozen v0.30 workloads and then failed on the first build for `neutral_hostile_v1/03_media_library`.

The captured traceback showed two independent harness defects:

1. The media path reached `import soundfile as sf`, but the Genesis environment had installed the system `libsndfile1` library without the frozen v0.30 product's declared Python audio dependency `soundfile>=0.12`.
2. More importantly, the traceback resolved `cmpct.builder` and `cmpct.codec` from the live harness checkout (`.../.CMPCT/src/cmpct/...`) rather than from the frozen v0.30 checkout. The historical worker had put the frozen checkout and its `experiments/` directory on `sys.path`, but not `<frozen-checkout>/src`.

The second defect violates the frozen-source premise even if resulting bytes happen to match prior evidence. Therefore the previously produced historical Genesis rows are **not admissible for final Genesis adjudication**. They are retained as diagnostic evidence only.

The frozen ONE candidate is not declassified by this finding: ONE executes through its separate frozen-candidate worker/runtime seal. This quarantine applies to measurements produced through the historical comparator worker before the source-seal repair.

## Builder repair

The historical worker now:

- places `<frozen-checkout>/src`, `<frozen-checkout>/experiments`, and `<frozen-checkout>` ahead of ambient imports before loading the product facade;
- fails closed unless every loaded `cmpct` / `cmpct.*` module with a file origin resolves under `<frozen-checkout>/src/cmpct`;
- repeats that source-origin check after the measured phase;
- emits the exact frozen `cmpct` module origins as `frozen_cmpct_import_roots`.

The workload measurement layer now also retains a stable `runtime_source_provenance` object for historical contenders and rejects samples when:

- the worker-reported source SHA differs from the frozen authority;
- a reported `cmpct` module lies outside the frozen checkout; or
- runtime provenance changes across fresh-process repetitions.

Hostile regression tests cover both ambient-package preference and a preloaded ambient `cmpct` module, plus provenance escape at the measurement layer.

The v0.30 diagnostic and real-gate workflows now provision `soundfile>=0.12`, matching the frozen v0.30 `audio` extra. This is environment preservation, not comparator modification.

## Referee consequence

Until fresh source-sealed rows are produced:

- do **not** use the earlier v0.29 aggregate as final Genesis evidence;
- do **not** count the interrupted v0.30 media row as a comparator loss;
- do **not** splice old unsealed historical rows with new sealed rows for a winner decision;
- do **not** change ONE, either historical comparator, or the 15-workload authority in response to this harness defect.

The next admissible sequence is:

1. complete the exact frozen-v0.30 15-workload diagnostic under the repaired source seal;
2. if it succeeds, rerun the full official 15-workload × 3-contender gate under the same repaired worker so v0.29 and v0.30 are both freshly source-sealed;
3. validate the 45 rows and their runtime provenance;
4. only then adjudicate `KEEP_CMPCT1_PRIMARY` vs `REACTIVATE_V030_NEAR_TERM` under the preregistered rules.

## Preserved negative result

The defect is itself a Genesis finding: a commit SHA and a frozen experiment facade were insufficient to guarantee a frozen historical runtime. The executable import cone must be sealed and evidenced, not inferred from the top-level module path.
