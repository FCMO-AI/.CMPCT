# v0.30 EG08 adaptive-effort hostile5 transfer — mission lock

Date: 2026-09-13
Status: preregistered hostile review; research only.

## Frozen mechanism

Use EG08 exactly as it passed Office: unchanged EG07 representation, fixed ladder `3,6,12,19`, best-so-far retention, continue on improvement/tie, stop on first worse rung, authenticated recipe-derived hot-root exclusion, no path/content/workload thresholds.

## Hostile surface

Run all five deterministic `resemblance_hostile_corpus_v1` workloads:

- shifted versions;
- false neighbors;
- boundary churn;
- related Deflate-family containers;
- incompressible control.

These target both highly exploitable related data and inputs where extra compression effort should quickly prove useless.

## Hypothesis H-EG08-HOSTILE-1

The effort ladder remains semantics- and locality-neutral under hostile relationship structure and does not export unreasonable CPU/RSS debt on low-yield data.

## Pass contract

`EG08_HOSTILE5_PASSES` requires:

- 5/5 EG08 builds and strong verifies complete;
- 5/5 deliberate primary-metadata corruption recovers from authenticated tail state;
- 5/5 preserve EG07 member count, maximum decode unit and maximum member amplification exactly;
- zero stored-byte regressions versus same-run EG07;
- for any workload gaining `<4 KiB`, EG08 creation CPU must be `<=1.50x` EG07;
- incompressible must not gain by violating raw/codec economics or decode bounds.

Peak RSS is reported without an arbitrary threshold; a material increase is explicit promotion debt.

No density-win count is required. A hostile input is allowed to produce a zero-byte tie if the ladder correctly discovers that more effort is uneconomic.

## Preservation

No format/version/release/locality/recovery/comparator/Genesis/ONE state changes. This review can block EG08 but cannot promote it by itself.
