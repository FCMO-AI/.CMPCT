# O92c — Linux subprocess inherited RSS high-water falsifier

Date: 2026-10-25 UTC
Status: **PROSPECTIVE**, no hosted O92c evidence yet.

## Motivation and baseline

O88 [#447](https://github.com/FCMO-AI/.CMPCT/pull/447) measures `resource.getrusage(RUSAGE_SELF).ru_maxrss` in freshly executed Python child programs, after the research parent generated large 65 MiB-expanded ZIPs. O92 [#450](https://github.com/FCMO-AI/.CMPCT/pull/450) observed a **300,348 KiB high-water even before Builder construction** in both original O63 and O86 engines. O92b hosted import-only [run #40210747808](https://github.com/FCMO-AI/.CMPCT/actions/runs/40210747808) found **only ~23 MiB peak** after importing genuine CMPCT modules in otherwise fresh children. Thus normal imports cannot account for the ~300 MiB O92 floor.

A *separate local primitive* control (not product evidence) allocated and freed 300 MiB in a parent Python process before a `subprocess.run` child: parent `ru_maxrss=402,312 KiB`; child `ru_maxrss=402,312 KiB` but child `/proc/self/status VmHWM=95,368 KiB`. This is prospective mechanistic evidence for an inherited resource-accounting artifact; it is not enough to correct the hosted O88 economic claim without exact hosted replication.

## Primary falsifiable question

Does `resource.getrusage(RUSAGE_SELF).ru_maxrss` measured inside Python subprocess children **inherit a parent's earlier maximum resident set** even after `execve`, while `/proc/self/status VmHWM` independently reflects actual memory high-water in the child? Prediction: in a fixed-hosted Linux environment with an explicitly enlarged/free parent, the child's `ru_maxrss` matches or exceeds the parent pre-spawn peak, whereas child `VmHWM` remains dramatically lower.

**Strongest simpler control:** A fresh child of a parent without a large allocation should show broadly consistent RSS witnesses. Another explanation is an accidental large import/workload allocation inside O92, not inherited history; a child pure stdlib process tests this cleanly. If no inherited difference appears on the hosted runner, the local result is host/process-specific, and the O88/O92 memory discrepancy remains unresolved.

## Minimal experiment

One hosted Ubuntu Actions workflow runs one public, dependency-free Python instrument with two unmodified subprocess phases: before parent allocation and after 192 MiB allocation/free+GC. Each child is a new `sys.executable -c` process and records `resource.ru_maxrss`, `/proc/self/status VmHWM`, `VmRSS`, `RssAnon`. The parent records its own before, after allocation, and after free and retains exact child raw JSON in a downloadable artifact. Repeat the post-allocation child 3× to expose variation. A no-heap CMPCT source is not needed for this **OS measurement oracle**. No benchmark, product, source installation, or code mutation.

Observe the result, do not require success to mean hypothesis confirmation: scientific workflow must preserve both outcomes; fail only on instrument errors, invalid child output, or missing processes. Declare `CONFIRMED_INHERITED_ACCOUNTING`, `FALSIFIED`, or `AMBIGUOUS` from actual repeated witnesses. Specifically, `ru_maxrss > 4*VmHWM` for each large-parent child and `ru_maxrss` close to parent high-water is sufficient confirmation; a witness ratio near one falsifies inherited-accounting on this runner.

## Disproof / future product decision

If inheritance survives, **correct the interpretation of O88/O92 memory evidence**: historic same-source archive bytes, CPU and exact reconstruction remain valid; their Linux `ru_maxrss` observations may be dominated by parent's corpus-construction high-water, so do not attribute them to CMPCT Builder, VZIP or Reader. Run the actual two-engine O88 worker with `VmHWM` to gain true child-peak RSS only if it changes integration decision; do not rerun every benchmark out of inertia. No code/release/format gain is claimed from a resource-accounting oracle. Keep frozen O88/O92 negative history immutable.

## Coordination / carrying cost

This O92c refinement is an **independent causal mechanism** after two prior decisive results: O92 falsified Reader-lift and O92b falsified CMPCT imports. No duplicate codec implementation/threshold gardening or overlapping owner PR mutation. A local/hosted disagreement must be retained. This one-file oracle can be retired immediately if hosted evidence is decisive. Public synthetic values only, no private information or credentials.
