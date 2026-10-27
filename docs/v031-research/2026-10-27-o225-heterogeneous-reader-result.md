# O225 — Source-exact heterogeneous Reader execution-ownership result

Date: 2026-10-27 UTC. **Research/oracle evidence, not merged Reader/product credit.** Prospective [preregistration](2026-10-27-o225-heterogeneous-read-ownership-prereg.md) committed **before** the instrument at `294c9a460a49f8829dd50fe7996c78709ad61b11`. Scientific trial on **exact O225 source head `a35d92d2beb2235913098fd2271250b487123bbb`**, [Actions #40496313064](https://github.com/FCMO-AI/.CMPCT/actions/runs/40496313064) **SUCCESS**, original [artifact #12731175227](https://github.com/FCMO-AI/.CMPCT/actions/runs/40496313064/artifacts/12731175227). ZIP SHA-256: `95966be0b6810d0dccb22be5bf5c61dfd9b1b17fbe6713eda31326afe32ec151`; `results.json` SHA-256: `97cc2af394a1dd3aa9c3d4ab1894a1841fb26d647821524edcf49ddb98c08500`. Original artifact ZIP CRC checked; independently coded receipt auditor **PASS**: 90 fresh processes/distinct PIDs, 10 cases, 6 byte-sensitive held-out positive checks, 6 deliberately malformed physically referenced CRC refusals and source-bound reader blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`.

## Decision

Frozen `UNIVERSAL_SERIAL_CANDIDATE` **earned on the sampled authenticated r24 regimes**; `BOUNDED_SUBSET_SEED` **empty**. This is not proof that unconditional serial is superior for arbitrary data, all platforms or all Reader storage kinds. No production Reader code was changed.

The exact prospective numerical rule required (a) >=1.20x serial improvement on **both** 65,536-ref tiny RAW modes, (b) <=10% complete-open+read regression vs eager on both **distinct Zstd and distinct Deflate** modes, (c) <=8 MiB own `VmHWM` penalty for serial across all profiles, plus complete exactness and hostile controls. All passed in exact-head hosted raw evidence. Plain serial was the **strongest simpler control**; bounded64 did **not** earn its independent >=1.20x material candidate threshold against both controls.

### Complete open+read+teardown wall median, milliseconds

| Mechanism | Mode | Original eager | Serial | Eager/serial |
|---|---|---:|---:|---:|
| 65,536 refs / 8 tiny RAW owners | S_CHUNKS | 915.136 | 58.958 | 15.52x |
| 65,536 refs / 8 tiny RAW owners | S_CDC | 1000.128 | 97.455 | 10.26x |
| 128 distinct Zstd / 32 MiB logical | S_CHUNKS | 80.559 | 77.122 | 1.045x |
| 128 distinct Zstd / 32 MiB logical | S_CDC | 81.302 | 77.616 | 1.047x |
| 128 distinct Deflate / 32 MiB logical | S_CHUNKS | 86.921 | 81.250 | 1.070x |
| 128 distinct Deflate / 32 MiB logical | S_CDC | 87.438 | 81.272 | 1.076x |
| 96 distinct mixed RAW/Zstd/Deflate / 24 MiB | S_CHUNKS | 61.380 | 58.349 | 1.052x |
| 96 distinct mixed RAW/Zstd/Deflate / 24 MiB | S_CDC | 61.510 | 59.075 | 1.041x |
| 2,048 refs / 8 compressed Zstd owners / 64 MiB | S_CHUNKS | 119.299 | 95.378 | 1.251x |
| 2,048 refs / 8 compressed Zstd owners / 64 MiB | S_CDC | 120.979 | 96.680 | 1.251x |

The own-process Linux `/proc/self/status` `VmHWM` was **133,728 KiB eager vs 30,912 KiB serial** on tiny RAW fixed, **139,288 KiB vs 36,740 KiB** on tiny RAW CDC. On distinct compressed cases, serial was ~1.7–1.9 MiB lower than eager, and on cached Zstd repeats ~4 MiB lower. These are **fresh-child actual VmHWM**, not the inherited `ru_maxrss` proxy O224 falsified. CPU also favored serial on sampled compressed regimes, but small wall deltas are vulnerable to runtime noise.

## Controls and negative evidence

1. **Initial hosted failure preserved:** [run #40495795704](https://github.com/FCMO-AI/.CMPCT/actions/runs/40495795704) failed the hostile test: the generator corrupted physical index 0, but the quadratic logical-ref pattern never referenced index 0. The Reader correctly need not read or verify an unreferenced blob in a read() call. Instrument corrected to corrupt `refs[0]` (an actually referenced physical owner); it did **not** relax the refusal test or the admission evaluator. This is an experimental fixture flaw, **not** evidence of silent Reader acceptance of referenced corruption.
2. The first qualifying trial also executed on GitHub's synthetic PR merge ref `0b570117defeeb9c77b9d38f75aa2c816d90c9d7` [run #40496028161](https://github.com/FCMO-AI/.CMPCT/actions/runs/40496028161), whose source blob matched the Reader invariant. The workflow was then corrected to checkout actual `github.event.pull_request.head.sha`, yielding the separate **exact scientific head** run #40496313064 above.
3. The complete Reader's normal executor shutdown is now included in **all** arm session timing. It would have been an asymmetric hidden cost because bounded64 destroyed its local pool inside the candidate, while eager previously destroyed its pool outside measurement. The repair tightened the measurement boundary, not success thresholds.
4. The distinct Zstd/Deflate and mixed regimes were **real native codec frames** within authentic signed/hashed primary/footer r24 archives, constructed independently of Builder, strict-preflighted, verified, selectively read and checked against per-member logical SHA. Their payloads derive from **seeded repeated 4-KiB entropy-bearing patterns**, not representative of fully incompressible or large CPU-heavy frames.
5. All three candidate execution arms used the same installed J24C02 Reader and effective index; no second pathname or alternate admission. The direct experiment covers Linux/Python 3.12 only and no update, recovery, Windows/macOS, native ABI changes, ZIP64 or release-parity matrix.

## Counterfactual / implications

The cheaply prospective discriminator was to pair the O223 tiny RAW serial positive with **distinct genuine compressed physical streams and fully charged executor teardown**, not to extrapolate 11–18x to arbitrary workloads. The first experiment's unreferenced-corruption failure demonstrates another transferable rule: hostile physical mutation must target an **actually traversed** reconstruction dependency. These are scientific-design lessons; they do not justify a new global Discovery Engine policy from one activation.

There is **no measured >=20% compressed distinct speedup**; the ~4–8% serial advantage could move with runner/thread scheduler/codec complexity. A blanket Reader patch is premature. The next product-owner test should introduce a **small optional serial-versus-eager A/B inside #569's same Reader** and challenge it on large, truly expensive, high-diversity compressed physical units, across at least Linux/Windows/macOS, with full extract/verify/range, CPU/wall, own VmHWM, output SHA and hostile admission/parity gates. If parallelism wins on stronger controls, use bounded adaptive dispatch rather than deleting it.

**Status:** O225 scientific question decided on scoped sample, branch PR #592 remains **DRAFT / OPEN**, no merge, no release, no version/format change. No change to `docs/discovery/STATE.json`; #574 owns its reconciliation. All raw artifacts are linked above and science/source head remains immutable even if this document commit gets a separate HEAD/CI.
