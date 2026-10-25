# O92b — Locate the pre-Builder 300 MiB memory high-water

Date: 2026-10-25 UTC
Status: PROSPECTIVE. **No O92b measurements yet.** Independent episode following O92. Never edit original O88/O92 predictions, instruments or results.

## Baseline and causal uncertainty

True installed O92 [run #40210177911](https://github.com/FCMO-AI/.CMPCT/actions/runs/40210177911) found median Linux process `ru_maxrss` **300,348 KiB immediately after importing CMPCT modules but before Builder construction**, on both historical O63 and O86 sources. Reader phases did not raise that peak, falsifying O92's original Reader-lift prediction. O92 does not locate the source of the pre-Builder high-water or whether 300 MiB remains resident. O88's final complete-process peak is correct but not phase-attributable without further controls.

## Primary falsifiable question / prediction

Which import stage, if any, creates the ~300 MiB process high-water: Python/harness startup, CMPCT package initialization, imported Builder/codec, or Reader? Prediction: a large transient high-water appears during CMPCT package import, with live VmRSS (from Linux `/proc/self/status`) significantly below VmHWM if the peak reflects transient allocations. Strong counterprediction: even a fresh pure-Python harness enters with ~300 MiB or current VmRSS stays ~300 MiB after imports, making package-specific transient explanation wrong.

## Alternative, simpler control, disproof

The simpler control is to label O92 result "pre-Builder/import-stage unknown" and make no memory diagnosis. O92b is warranted only because locating the 300 MiB resource owner could remove a significant full-product deployment/performance cost. Import-hook warming and import order can change overhead: do **not** credit elimination or attribute causality from one after-the-fact stack observation. A pure runtime control in the same instrument child is required.

Disproof conditions: no >100 MiB transition between measured stages, pure runtime already above 200 MiB, or inconsistent independent children. Narrow to "unattributed" rather than inventing ownership. A prior `ru_maxrss` high-water without simultaneous `VmRSS` is insufficient to distinguish live from temporary memory. A native library may load code/data in arbitrary import order, and mapped virtual bytes are not necessarily resident.

## Cheapest decisive experiment

Install the original O63 and O86 source snapshots independently as in O92, pin Builder and codec blob SHA. In six fresh independent children (three AB/BA per engine), record Linux `ru_maxrss`, `/proc/self/status:VmRSS`, `VmHWM`, `RssAnon` at sequential steps: (a) instrument pure-runtime before CMPCT import; (b) `import cmpct`, which installs its historical release-policy hooks; (c) import `cmpct.builder`; (d) import `cmpct.codec`; (e) import `cmpct.reader`; (f) import `cmpct.native_codec`. Capture imported module origin paths, installed SHA source binding, and exact environment. **No file creation, no Reader or ZIP fixture**: it is an import-only micro/oracle rung. It cannot earn product compression/RSS savings or official parity credit.

This experiment is intentionally sequential: the first `cmpct` import may already import builder/codec transitively, so later no-op stages do not imply those modules are cheap separately. If required, follow with independent import-order controls as a distinct hypothesis, not alteration of frozen O92b results.

## Concurrency / safety / value of information

No overlap with O86 implementation or O88 economics. O92 has finished its main question; O92b tests a **different explanation** and preserves negatives append-only. Candidate change to product would require separately verifying cold-start, CPU/RSS, platforms, source/fidelity/Reader and native ABI without weakening any release gate. Public synthetic/no private inputs. One small hosted workflow; stop if diagnosis is ambiguous and leave bounded debt rather than endless import microtuning.

## Counterfactual and future decision

If a specific CMPCT import expands process RSS, next evaluate whether it is cold-start paid everywhere or only research harness and whether lazy loading preserves correctness. If pure harness already high, retire CMPCT import speculation and correct the measurement provenance story. Do not modify Discovery Engine policy without repeated transferable evidence.
