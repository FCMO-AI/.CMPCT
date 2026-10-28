# O218d — stable-ABI native admission wheel, observed result

**Scientific disposition: `ABI3_WHEEL_MICRO_ROUTE_VIABLE`, for the exact scoped binary/micro experiments only. NOT a product merge, CMPCT release or whole-Reader performance result.**

## Exact provenance

- Historical product floor: released CMPCT v0.30.0, format revision 24, `main@80c358f8824ec1b20d349c92ed94c898090969b0`.
- Source-parent O218c PR #628: `a2d69c89769868fe4a454ce0556f6a19806f0647`, scientific 3-host full-Reader court [#40607917242](https://github.com/FCMO-AI/.CMPCT/actions/runs/40607917242) SUCCESS.
- Frozen hypothesis/kill conditions **before implementation**: `f96a54d058bdac24a6216ec66f47086a7ecfa1ec`, [preregistration](2026-10-28-o218d-abi3-distribution-prereg.md).
- Experiment code HEAD: `64cd5ecf6157207e4e275d398887527f2a9ea496` (O218d draft PR #631). All performance outcomes below are on precisely this source.
- [GitHub Actions #40613011184](https://github.com/FCMO-AI/.CMPCT/actions/runs/40613011184): **SUCCESS** on Ubuntu 24.04, macOS 14, Windows Server 2022, and cross-platform independent referee.
- Research-only source in `research/o218d_abi3_package/`, not published `src/cmpct/`. Pinned inherited Reader Git blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`, validator `51c2849061f99a4afeddb7666956b24566ce7de0`, original direct-PyList C `a54f15181d9dbe667b9e8c9d52e927b09c80152f`. Neither changed.

## Material result

The standalone `Py_LIMITED_API=0x030B0000` C predicate, using `PyList_Size`/`PyList_GetItem`, built an actual platform `cp311-abi3` wheel **once on CPython 3.11** and installed/imported **the exact same wheel on CPython 3.13** without recompiling it. Both Python versions passed all 5,000 deterministic valid/hostile reference cases on each of three OS runners. All six host/interpreter outcomes had identical decision SHA-256 `72ec2f66b39851add70a94be2363fcaa68f50ebe2bc99acfa40bb7039c80f694`. Three host judges rejected **5/5** tampered receipts each; cross-host court also passed. A separate offline Python audit inspected each downloaded original wheel ZIP, validated actual wheel and ABI tags/binary SHA-256, recalculated every published ABBA median from its raw sample arrays, checked receipts, source identity and the six semantic hashes. It agreed with all four hosted jobs. A separately installed **CI-produced** Linux wheel under local CPython 3.13.5 also produced zero disagreements in 100,000 additional hostile/valid cases against an independently written Python predicate (26,090 legitimate acceptances; 73,910 rejections).

### Whole-scan in-process microbenchmarks — strict Python vs stable ABI C

Times here exclude interpreter startup and one-time compilation, but both are separately charged. Each column is the **median strict-Python / median native** speedup for the same lists and expected size. Greater than one means the stable-ABI predicate was faster; the frozen 1.5x gate was passed at both requested cardinalities in all six host/minor combinations.

| Runner | Wheel bytes | Build wall | Python 3.11 65k / 262k | Python 3.13 65k / 262k |
|---|---:|---:|---:|---:|
| Ubuntu 24.04 | 7,580 | 1.365 s | 10.250× / 10.637× | 10.397× / 10.413× |
| macOS 14 | 4,809 | 1.369 s | 16.882× / 16.898× | 16.544× / 16.356× |
| Windows 2022 | 6,758 | 12.572 s | 18.545× / 18.523× | 19.648× / 19.337× |

Held-out 65,536 refs with 256 owners also passed the 1.5× threshold. The raw values are preserved in artifacts, not only the summary:

- [Ubuntu artifact 12783623103](https://github.com/FCMO-AI/.CMPCT/actions/runs/40613011184/artifacts/12783623103);
- [macOS artifact 12782919870](https://github.com/FCMO-AI/.CMPCT/actions/runs/40613011184/artifacts/12782919870);
- [Windows artifact 12784230556](https://github.com/FCMO-AI/.CMPCT/actions/runs/40613011184/artifacts/12784230556);
- [cross-host verdict artifact 12784455198](https://github.com/FCMO-AI/.CMPCT/actions/runs/40613011184/artifacts/12784455198).

The wheel raw SHA-256 values in platform order (Linux, macOS, Windows) are `08fa91eff83442e9dca3ec94854ebfa8434a1c30d151d7c79d54610b1d41061b`, `82ba6e06f4c8706007847706b4d1af044d85a19bbd609f1b4adf86239ade664f`, and `3c1bf98ed92c14859192c5673763165dafe7171998b976a6c26c70a67e6f1075`.

## What did NOT follow

1. **A 10–20x micro ratio is NOT a 10–20x Reader speedup.** The comparison uses an independently written strict Python predicate (different cost from actual O216 fastpath), not the installed complete Reader. The previous O218c O216-vs-direct-C whole-Reader source-exact gains were 3.328–4.706×, **a different experiment**; do not conflate these numbers.
2. A preliminary separate exact C-versus-limited-API CPython 3.13 local micro benchmark showed stable-list access approximately 1.77–1.84× slower than the direct PyList macro C control. A real strong control remains to be paid at the **whole Reader** level, with the same exact source and wire.
3. Shipping wheel trust, dependency lifecycle, PyPy/ARM, other Python minors, reproducible builds, signed journal correctness, full read/extract/verify/recovery, memory and final-form benchmark parity were **not measured**. The wheel is an optional standalone **research** binary.
4. Existing composed Reader #569 has a measured 27–28× high-reference cold-open regression. A micro scanner cannot retire that inherited product debt; all original correctness, portability and release gates remain in place. No product source was changed.
5. Windows builds took 12.572 s compared with ~1.37 s on the other two runner types, outside timed scan. That cost is nonzero even when per-scan speed is positive.

## Convergence decision

**Advance the wheel route to one bounded strong-comparator rung, not directly to product.** Next question: on identical authenticated revision-24 archives, same installed Reader source on each interpreter, does `cp311-abi3` actual installed wheel keep meaningful **whole-open** benefit against O216's safe Python validator, with direct macro C as stronger performance control, no changed strict error diagnostics and an explicit binary/fallback cost? Pre-register the threshold; preserve kernel/import/build and Reader constructor boundaries separately; include parent #569 exact source before granting integration credit. If it loses under this stronger comparator, leave the stable-ABI wheel as a negative/product-cost finding and prefer direct minor-specific wheels, Rust-native parity, or Python fastpath.

**Discovery policy:** no change earned. Scientific result and packaging feasibility are durable, but there is no repeated evidence for modifying the Discovery Engine, its state, the physical format, or release gates. Repo/state #574 remains the owner of state reconciliation.
