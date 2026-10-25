# O92 — Attribute peak RSS by product phase, not full-process lifetime

Date: 2026-10-25 UTC
Status: **PROSPECTIVE PREREGISTRATION**. No O92 observations exist at this commit. Research only; no product, format, benchmark or release edits.

## Problem / baseline

O88 PR #447 / genuine Ubuntu Actions #40206269074 and #40206544638 compared original O63 `18e32cae012f5dca9fc47f10d194f8b81005c85c` with bounded O86 `6225e30f3e21c0783aa56726b52a3a3583540f99` on same physical 65 MiB-per-member 3-ZIP trees. O86 won complete stored bytes and create CPU. O88 records `resource.getrusage(RUSAGE_SELF).ru_maxrss` **after** `CMPCT.verify()`, three `reader.read()` calls and `extractall()`; this is **whole create+read+extract process peak**, not isolated Builder peak. Published medians on shared 65 MiB were 304,688 KiB (O63) and 300,676 KiB (O86), whose closeness could misleadingly suggest Builder memory was unaffected by the admission budget.

## Primary falsifiable question

Is O88's ~300 MiB RSS floor already reached during `Builder.build()`, or only during subsequent Reader verification/read/extraction? If the latter, the near-identical whole-process peaks cannot establish near-identical Builder peak RSS. This is a phase attribution fork, **not** a claim that VZIP budget reduces total product RSS.

## Prospective prediction / simpler control / alternative

Prediction: on the original shared 65 MiB source, O86's fresh-process post-Builder RSS is materially below its final post-read peak; and at least some of the ~300 MiB floor arises during Reader work. O63 may have elevated create RSS because it inflates speculative VZIP members; do not assert a difference without measurement.

Strongest simpler control: run the exact O88 benchmark unchanged and call its `peak_rss_kib_linux` whole-process peak, making no create-only memory claim. O92 earns value only if phase-separated measurements change the causal attribution. Alternative: Builder itself consumes ~300 MiB in both arms, so the Reader does not explain the common floor. A second alternative is Python allocator/VM high-water retention even after memory is freed, making post-Builder RSS a non-live but still valid peak-of-creation measure.

## Experimental custody / minimal decisive rung

Stack only a new instrument and workflow onto O88 scientific branch `7f42c7854a3b06f4d81e168a29b8d9855582c34d`; **never edit** frozen O88 instrument or its result. Use the very same O88 `fixture()` and one original **shared_over** tree generated in a **parent** process. Install original O63 and O86 source into separate locations; assert both installed Builder+codec Git blobs, exact source ZIP SHA, and source stability throughout. For each engine, execute three fresh children in AB/BA sequence, each recording `ru_maxrss` at (a) post-import/pre-build, (b) after `Builder.build()`, (c) after `verify()`, (d) after reading the three logical ZIPs, and (e) after `extractall(metadata=False)`. Record complete archive bytes/SHA, `Builder` wall/CPU, read/extract correctness, physical source hashes and actual storage modes.

The same-process monotone RSS witness permits **attribution of when a new peak was first reached** but does not measure current live memory, PSS, Python heap allocations, allocations freed before the snapshot, or independent memory of Reader when isolated in a new process. Do not call an unchanged high-water mark proof of absence of additional allocations.

## Kill/narrow conditions

- If before/after Builder RSS is already ~300 MiB for both O63 and O86, retire the claimed Reader-attribution hypothesis.
- If an O86 Builder phase is materially smaller but downstream Reader produces the same high-water peak, resolve **measurement-boundary confusion** without claiming product memory reduction.
- If source ZIP bytes or code identities differ, if any read/verify/extract fails, if tests are skipped, or if an installed engine silently falls back, invalidate the court.
- If runs exhibit volatile RSS, preserve each repetition and report ambiguous; do not tune workload or remove outliers.
- No change to source, benchmark, compression policy, thresholds, format or public scoreboards, and no release promotion.

## Concurrency and future leverage

O88 #447 owns original full-process scientific economics; O86 #444 owns budget implementation; O63 #418 owns VZIP. This O92 child owns **only post-stage memory attribution**; it does not duplicate implementation. Communicate results to #447/#444. Store raw per-process receipts and exact GitHub Actions IDs. Any further research depends on whether phase attribution changes a real decision; do not build an unnecessary memory dashboard.

## Disproof, adversarial self-review, public surface

One exact-source result showing Builder already at final peak falsifies the working explanatory hypothesis. Reader inflation is not automatically a CMPCT bug: reading three 65 MiB ZIPs intentionally materializes ~195 MiB of exact bytes and can fairly cost memory. Do not conflate measured process peak with resident usage at a single moment, or compare different host runs as matched peers. Only synthetic fixed-seed public files; no private identity, data or artifact. Product credit: **none**. Scientific attribution credit only after genuine hosted execution.
