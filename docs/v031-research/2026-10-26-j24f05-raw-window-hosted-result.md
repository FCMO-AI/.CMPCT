# J24F05 — exact-head bounded immutable RAW transfer: hosted result

Date: 2026-10-26
Status: **candidate, no merge or release**; result-bearing source Reader Git blob `41efeb9d3301fc06b1df56ab6bd42d9ee91f6d5e`.
Preregistration: `docs/v031-research/2026-10-26-j24f05-raw-window-prereg.md`, committed `361a7f995da69e83f63ab41de4656ced82f5ceea` **before** the source edit.
Parent: J24F04 #537 exact `d5aa5cbc1ef1e00b6e3c8c72cdd1598192d563a3`; original negative: J24F03 #530 and Issue #531.

## Primary question, genuine control, and result

**Can the previously demonstrated immutable-RAW-source authentication invariant be preserved without detaching an entire physical chunk?**

A fixed maximum 64-KiB detached `bytes` window is fed to both SHA-256 and the temporary stage write; borrowed mmap memory is a source cursor only. The strong whole-file SHA and size gate remain before stage publication. The alternative whole-chunk J24F04 copy is retained as the security control, but potentially allocates one physical chunk of ~1 GiB.

[GitHub Actions run 40392625571](https://github.com/FCMO-AI/.CMPCT/actions/runs/40392625571): **Ubuntu 24.04 and macOS 14 jobs both SUCCESS**, installed exact source (not in-checkout Reader), no r24 wire change.

| Court | Ubuntu | macOS |
|---|---|---|
| Inherited J24F04 small S_CHUNKS post-copy/future-copy | 2/2 PASS | 2/2 PASS |
| Inherited J24F04 small S_CDC post-copy/future-copy | 2/2 PASS | 2/2 PASS |
| New genuine 8-MiB RAW physical S_CHUNKS post/future | 2/2 PASS | 2/2 PASS |
| New genuine 8-MiB RAW physical S_CDC post/future | 2/2 PASS | 2/2 PASS |
| **Total** | **8/8 PASS** | **8/8 PASS** |

Each new large case uses one independently handwired valid r24 dual-index archive, genuine signed 8,617,989-byte logical content, and a distinct subprocess with ordinary write authority to pwrite **only the same archive inode**, intercepted at the Reader's first actual private-stage `os.write`. The first-window mutation occurs after copying that window, preserving full signed output; the future-window mutation occurs before copying that window, forcing indexed SHA failure and preserving the original destination. Exact original logical SHA:

`dfd8aa2e2d0e0ebc1b5aa2df47f25564b5ed356a5595dc3f361c4c7acaea76e5`.

All eight large trials used **132 stage write calls** of max **65,536 bytes**. Under `tracemalloc` started immediately before attacked extract, Python traced peak was **199,922–200,344 bytes** (2,097,152-byte prereg ceiling). **These are not peak total RSS measurements.**

### Original downloadable evidence and independent audit

- [Linux artifact #12686200577](https://github.com/FCMO-AI/.CMPCT/actions/runs/40392625571/artifacts/12686200577): ZIP SHA-256 `337552955cf44b27e87ff345235bc382b87511146d20918c52f2b010de90aec6`.
- [macOS artifact #12684482668](https://github.com/FCMO-AI/.CMPCT/actions/runs/40392625571/artifacts/12684482668): ZIP SHA-256 `980263d12d2e94bec26122f531f39c072c509b245d6ecd9a303a88735df84c6f`.

The two original ZIPs were downloaded and inspected independently, not inferred from green workflow summaries. A Python-only audit independently regenerated the deterministic 8,617,989-byte signed logical SHA and 6,915-byte inherited SHA from the documented synthetic byte recipes; checked both hosts, eight exact input/representation/attack combinations per host, actor mutation receipt SHA, actual immutable window bounds, full-file SHA, fail-closed target preservation and tracked allocations. **201 field/invariant checks PASS / 0 discrepancy**. The audited receipt is separate from CI acceptance; source mutation actor parent PID is not present in J24F05 JSON, so independent audit can confirm the recorded child PID but not independently compare parent/child PID from the artifact alone. The workflow source uses `subprocess.run` and J24F04's actor distinguishes its process.

### Independent micro evidence (NOT product credit)

A separate standalone same-input Linux mmap→SHA→stage-write proxy used 16 MiB deterministic input and **four fresh-process repetitions per arm**, alternating execution order. Whole-chunk vs 64-KiB window median:

| Metric | Whole-chunk copy | 64-KiB windows |
|---|---:|---:|
| `tracemalloc` peak | 16,777,837 B | 131,798 B |
| Wall, median | 96.915 ms | 90.543 ms |
| CPU, median | 95.783 ms | 90.543 ms |

**99.21% reduction in Python tracked peak bytes on this proxy.** Short measurements and setup-dominated ru_maxrss prevent a general CPU/wall/RSS conclusion. This is not installed CMPCT real extraction, no fsync, and is not release evidence.

## Explicit negative and decision

**Science disposition: `BOUNDED_WINDOW_CUSTODY_PASS` for the scoped threat model. Product promotion: NOT EARNED.**

Source archive changed physically while output remained signed-original on post-window mutation; pre-snapshot future mutation forced SHA failure, preserving prior destination. This is stronger than mere unsigned output equality but not a guarantee against every concurrent mutation, source truncation/SIGBUS (#460), malicious stage-name pivot (#528), output directory attacks or Windows metadata failures (#535/#536).

### Exact-head CI interpretation

The child J24F05 scientific workflow was green on `ee440b5e5d310fca908667b1cf1fd42b0bc9b391`. The inherited J24F04 parent workflow intentionally binds source Reader blob `8b5910725260e7b4db155ee0b393eb48a42f7efa`, therefore it **fails for this changed Reader by design**. Do not modify the parent's frozen witness or call its red a functional regression. This child explicitly reran its inherited attack cases.

The original J24F05 topology workflow initially failed because the concurrency key included exact SHA (which made cancel-obsolete ineffective), then the key was changed to stable PR/ref identity while retaining exact-SHA checkout and source validation. CI topology and material PR dossier are re-evaluated on later child HEADs. General tests and numerical performance promotion remain separately required; administrative performance workflow SUCCESS with numeric SKIPPED is no evidence of parity. Full same-runner output-size, CPU/wall, RSS/temp I/O, Windows and downstream source/stage combined attacks remain unmeasured.

## Counterfactual and next action

The earlier J24F04 source-code observation that its detached object could reach the parser's ~1-GiB physical limit was enough to motivate a **bounded ownership unit** rather than replaying more small-chunk attack runs. The 8-MiB hostile input plus traced Python allocation ceiling supplies the cheapest additional decision-changing discriminator. This is a scoped, prospective design lesson; it does not modify the Discovery Engine policy.

**Next highest-value independent action:** full installed same-input J24F04-vs-J24F05 process RSS/CPU/wall/temp write/read court under both 8-MiB and ~1-GiB eligible RAW chunk regimes, plus separate stage-name publication issue #528 integration. Require exact SHA and no historical gate relaxation. No merge or release without complete product gates and coordination with the parent owner.
