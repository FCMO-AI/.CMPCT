# O223 — Genuine full-Reader futures RSS attribution: preregistered memory hypothesis falsified

Date: 2026-10-27 UTC. **Direct hosted research outcome / no shipping-product or release claim.**

## Identity and executed evidence

- Immutable prereg: `fc1b0347f06ef746d253614b516ead241e29ebed` ([prereg](2026-10-27-o223-bounded-reader-futures-prereg.md)).
- Product parent: J24C02 [#569](https://github.com/FCMO-AI/.CMPCT/pull/569) at `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`; unmodified Reader blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`.
- Code/workflow HEAD `3a896d0a6b4da092d2f148fd153d6ffe6f67cdb7`; [GitHub Actions #40484142645](https://github.com/FCMO-AI/.CMPCT/actions/runs/40484142645) **SUCCESS** on Ubuntu 24.04, Python 3.12.15.
- Original [artifact #12723574557](https://github.com/FCMO-AI/.CMPCT/actions/runs/40484142645/artifacts/12723574557) ZIP SHA-256 **`bde8366fc48f41d733d9bbaf7ec2481309f69fcb13a576a2ae8908c9831772b1`**, inspected independently after download, ZIP CRC and original raw audit **PASS**.
- Original `results.json` SHA-256 **`6b01fb71b79617e9472a92d3d43b6cc25399e5513387876e024eb72ad1d6828a`**; independent auditor recomputed exactly **180 unique samples**, **12 five-arm profile groups**, exact matched complete logical outputs and six variable-payload controls.
- Measured actual installed CMPCT Reader with authenticated independently constructed r24 files; none of the Reader/validator/format/benchmark/product files were changed. The experimental alternatives were outside the Reader and retained its exact same in-memory authenticated index and physical _blob calls.

## The decisive original-sample medians (N=262,144)

All medians are fresh child `CMPCT(path)` + full read, excluding process start (separate process wall retained). Small RAW blobs (one byte each), either one owner repeated or eight physical owners.

| Mode/layout | Eager original session | Bounded512 session | Serial session | HWM every arm INCLUDING open_only |
|---|---:|---:|---:|---:|
| Fixed / repeated | 4,097.48 ms | 2,945.78 ms | **222.88 ms** | **463,872 KiB** |
| Fixed / 8 owners | 4,075.53 ms | 2,934.96 ms | **223.60 ms** | **486,152 KiB** |
| CDC / repeated | 4,247.04 ms | 3,210.11 ms | **373.16 ms** | **508,740 KiB** |
| CDC / 8 owners | 4,227.26 ms | 3,235.05 ms | **371.07 ms** | **509,308 KiB** |

**Frozen decision: `BOUND_FUTURE_PRODUCT_HEADROOM_NOT_PROVEN`.** Every 262,144-ref median **bounded512–eager peak RSS delta is exactly 0 KiB**, versus the preregistered >=128 MiB required. Full-session bounded512/eager median wall ratios were **0.719 / 0.720 / 0.756 / 0.765** (about 1.39x, 1.39x, 1.32x, 1.31x faster); therefore the wall gate is passed but the RSS gate is falsified. Serial/eager session wall ratios were **0.0544 / 0.0549 / 0.0879 / 0.0878** (about **18.4x/18.2x/11.4x/11.4x faster** on this low-cost RAW regime). A claim that bounded parallelism is preferred is unwarranted: **serial is dramatically simpler and faster on these fixtures**.

Even the `open_only` control, which does **no physical member read and constructs no eager futures**, has the *same recorded process peak RSS* as every read variant. Therefore **the observed 453–497 MiB high-water memory is already reached at or before Reader open** on these exact inputs. This decisively falsifies attributing the original process-HWM headline to the eager `Executor.map` operation under this measurement. Local pure-stdlib trials independently establish futures *can* use much heap; that micro mechanism is real but **not the cause of the observed peak memory in these source-exact complete-Reader sessions**.

### Strongest negative and accounting boundary

The result **does not prove** futures allocate no memory; `ru_maxrss` reports a process lifetime high-water mark, hiding read-phase allocations below the existing open high-water. No read-phase `tracemalloc` attribution or differential actual USS/PSS was performed. No Zstd/Deflate heterogeneous expensive decoder, sizable logical file, cross-host/Windows/macOS, shared Rust ABI, signed-journal/latest-generation mutation, extractor/recovery, or general release gate was measured. This is a decision-changing **negative on the memory claim** and a compelling **scoped execution-cost signal** for low-cost cached RAW, **not** an earned global switch to serial.

## Causal interpretation, counterfactual, follow-up

The decisive counterfactual discriminator was **open-only peak HWM on identical wire**, cheaper than designing a bounded concurrency policy; it would have falsified the memory hypothesis immediately. Capture phase-specific RSS/heap and attribute parser/decompression/strict-validation memory before choosing a memory repair. The next cheapest independent trial should compare (a) after-index-decompression, (b) after `msgpack.unpackb`, (c) after `_validate_storage`, and (d) post-read live alloc/USS on the same exact physical signed archive. Place limits/hostile tests ahead of any promotion.

For speed, evaluate a small serial-vs-bounded policy with genuinely heterogeneous compressed blobs and repeated full production reads, taking all decoded data/CPU/RSS/Windows/macOS/journal effects; do not change production #569 from this court alone. Existing Builder bounded-worker implementation may inform future implementation if expensive decoders justify workers.

## Coordination and gates

O223 lives only on research draft [#587](https://github.com/FCMO-AI/.CMPCT/pull/587). Comments in [#569](https://github.com/FCMO-AI/.CMPCT/pull/569) and [#583](https://github.com/FCMO-AI/.CMPCT/pull/583) flagged the earlier hypothesis; send this falsifier explicitly so future agents do not inherit the stale story. `STATE.json` remains unchanged because #574 separately owns discovery-state reconciliation; no normative Discovery Engine policy lesson was earned from one experiment. No source, ABI, benchmark, format, version, release or product claim changed.

**No merge. No release. No 1.0 benchmark promotion.**
