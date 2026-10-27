# O224 — Posthoc correction of O223 child `ru_maxrss` provenance

Date: 2026-10-27 UTC. **Evidence-measurement fault, not a product regression/win.** This causal issue was discovered **after** committing O224's immutable preregistration and while its source-exact hosted court was executing. It is separately labelled posthoc; no prospective threshold was changed.

## Original O223 artifact independent review

O223 original hosted [run 40484142645](https://github.com/FCMO-AI/.CMPCT/actions/runs/40484142645), [artifact 12723574557](https://github.com/FCMO-AI/.CMPCT/actions/runs/40484142645/artifacts/12723574557), ZIP SHA256 `bde8366fc48f41d733d9bbaf7ec2481309f69fcb13a576a2ae8908c9831772b1`. Audit of original `results.json` (not summaries): **180 records, 180 unique child PIDs**, but only **six** distinct `peak_rss_kib` values: `34192, 140156, 463872, 486152, 508740, 509308`. In original execution order there are 174 equal adjacent readings, five increases, **zero decreases**, even across independently spawned children with drastically different reference counts and modes.

The [O223 instrument](../../research/o223_read_futures_rss_court.py) records `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` in child subprocesses. Before each batch of children, the **parent** creates, independently preflights, fully verifies and reconstructs the next fixture; its own memory high-water can grow with the fixture. Linux child `ru_maxrss` need not represent the memory high-water of the new post-`execve` image.

## Independent local subprocess falsifier (non-product evidence)

An isolated controlled Linux experiment launched a Python child before and after its parent touched a freshly allocated 300 MiB bytearray. Representative independent repetition:

| Case | Child `ru_maxrss` | Child own `/proc/self/status:VmHWM` |
| --- | ---: | ---: |
| Before large parent allocation | 95,252 KiB | 95,448 KiB |
| After large parent allocation | 402,452 KiB | 95,444 KiB |

The child itself did not allocate an additional 300 MiB. Parent-induced `ru_maxrss` growth while actual child `VmHWM` remains stable demonstrates a source-local metric inheritance/custody error on this Linux host. Reproduction instrument: `research/o224_fork_ru_maxrss_custody.py`; its hosted invocation/output belongs to the O224 workflow. The exact numbers above come from the local reproduction; **not** from the hosted O224 run.

## Decision and epistemic scope

The original O223 claim that the Reader itself reaches ~453–497 MiB during open-only is **not established by its recorded `ru_maxrss`**, and its zero-difference memory comparisons are not a meaningful test of the actual child Reader memory. This reopens memory ownership; it does **not** prove the Reader is small or that bounds on full-read futures save material RSS. O223 wall/CPU and exact read-hash evidence are separate and remain valid within their own scope.

A correction must capture each new child process's `/proc/self/status:VmHWM`, live RSS/smaps and staged parser/validator snapshots, preferably with a fresh child before the parent's fixture work can affect the measurement; O224 does the first part and explicitly compares uninstrumented against instrumented child HWM. No products, validators, comparators, frozen thresholds, archives, native modules or release gates changed. The discovery lesson is **verify process metric semantics under parent allocation before inferring child RSS phase ownership**. This one run does not justify a normative Discovery Engine policy change.

Owner notifications: [#587](https://github.com/FCMO-AI/.CMPCT/pull/587) and [#569](https://github.com/FCMO-AI/.CMPCT/pull/569) comments, 2026-10-27. O224 source-exact [#590](https://github.com/FCMO-AI/.CMPCT/pull/590) remains a research-only DRAFT.
