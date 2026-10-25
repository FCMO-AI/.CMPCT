# O95b — Same-engine O86 budget-toggle causal control

Date: 2026-10-25 UTC. **PROSPECTIVE — no O95b observations at preregistration.** O95 #453 genuine installed original O63/O86 18-child [source-exact run #40214780817](https://github.com/FCMO-AI/.CMPCT/actions/runs/40214780817) found O63 child-local VmHWM 304,756 KiB versus bounded O86 32,120 KiB on shared 65 MiB members, alongside 664,428 vs 52,641 complete archive bytes. O95c not planned; preserve the original immutable O95 hypotheses and observations.

## Narrow causal question

Is the enormous memory/size/CPU difference caused specifically by O86's **budget admission decision**, rather than an unrelated source change between O63 and O86? Use exactly the same installed O86 engine `6225e30f3e21c0783aa56726b52a3a3583540f99`, same O88 `shared_over` 65 MiB ZIP source bytes, three fresh children per budget condition, alternating order. Compare the default 64 MiB probe budget against opt-in `CMPCT_VZIP_PROBE_MAX_INFLATED_BYTES=134217728` (128 MiB), without altering the product.

**Prediction:** default O86 chooses `S_BLOB` and remains near the O95 ~32 MiB child `VmHWM`, while O86 with 128 MiB admits `S_VZIP`, inflates `VmHWM` by >=64 MiB, and produces the larger VZIP complete archive (expected same 664,428 bytes as true O63). The 128 MiB path is only a **research control** and is not recommended as a product default.

**Disproof/narrow:** if toggling budget does not change representation, cannot preserve source and reconstructed bytes, or fails to increase child VmHWM materially, then an O63-vs-O86 source difference or an instrumentation artifact remains plausible, and budget-specific causal attribution is unearned. Similar memory/size under both budgets would falsify the claimed mechanism.

## Strong controls, alternatives and cost

- Same physical 3-ZIP tree, deterministic O88 generator, source SHA256 before and after create/extract.
- Same installed O86 Builder/codec Git blobs, package origin, `Builder(..., workers=1, reproducible=True, reproducible_epoch_ns=0)`, unchanged format r24, genuine `CMPCT.verify/read/extractall(metadata=False)`.
- Sample `VmHWM/VmRSS/RssAnon/ru_maxrss` before import, after Builder and after Reader; `ru_maxrss` remains diagnostic of inherited floor only.
- Preserve raw children, archive bytes, create CPU/wall and source identities. Run on genuine Ubuntu Linux hosted CI, six original installed processes; no workload tuning after outcome. A simpler direct `codec.make_vzip_recipe` check alone cannot establish complete-product memory economics, so execute genuine Builder.
- Alternative explanation: a different source-level O86 change, rather than budget admission, caused the O95 memory savings; the same-engine toggle is a direct falsifier. A positive is cohort-specific and not universal budget-optimality.
- Concurrency: O86 owner #444 owns product code, O88 #447 and O92 #450 own historical research, O95 #453 owns this independent source-exact science. No other repo modified. Do not edit original O95 instrument or its results; only append a new distinct preregistration/instrument/workflow and outcome.
