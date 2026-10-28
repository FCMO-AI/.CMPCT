# J24K06 — signed mode2 prefix-coordinate proof: correctness closed in focused court, economic debt exposed

**Date:** 2026-10-28 UTC. **Status:** source-exact **research candidate**, no merge/release. **Owner:** [draft PR #642](https://github.com/FCMO-AI/.CMPCT/pull/642), child of #638 source `f33fa91995043bf731e5a4a786fdec0b2dcfd4eb`. Executable/cost-evidence HEAD `1d69c2e774bb0ba2fbb75ad76b6d49b152e66713`. This note is later documentary work, not the tested code identity.

## Decision in one sentence

The genuine [J24C07c](https://github.com/FCMO-AI/.CMPCT/issues/640) signed 130→131-byte regenerated-Deflate wrong-byte suffix test now **passes unchanged on all three installed Reader hosts**, while same-source economic measurements expose **7.9–54.6 ms** of new mode2 suffix recompression for a **2-byte** range after 2 MiB of raw payloads; do not promote this implementation until the performance/ownership cost is addressed. The original false-length full read already failed closed; the missing property was the signed *coordinate* of a later selective slice, not merely its length.

## Source/preregistration custody

- Prospectively preregistered `35e379ff234668b71b5aac2a56ccec01c05654ca` **before source code**, including intact hostile test, early literal laziness, multistream +1/-1 cases, non-mode2 controls and explicit performance kill/debt.
- The zero-byte resource subcase was separately preregistered in `2b8babf7c235610fae7775d0c14d24dcb46a84c5` before its source edit.
- Code changes **only** `src/cmpct/codec.py::range_vzip`: after bounds, an empty range returns without decoding, each selected stream proves its actual `len` equals declared `csize`, and every preceding **regenerated Deflate mode2** stream verifies its actual length before allowing signed offsets to advance.
- `research/j24k06_source_guard.py` checks that complete candidate codec equals the frozen parent plus exactly those **two preregistered bounded substitutions**. `reader.py`, `validation.py`, the frozen ZIP vector, and original J24C07c/J24K05 tests are byte-identical to #638. Hosted parent codec SHA-256 `73b81adfc44336168c0d6045931c78a5ceab22e608c4e45341b58c992c7c4518`; candidate codec SHA-256 `b50eb54b3a23e03d45ff707d7f047c54dc1c3095e7e0e9ab680a64370a42ac0a`.

## Exact source product-path correctness evidence (not release gate)

[Final J24K06 three-host Scientific Court #40630810164](https://github.com/FCMO-AI/.CMPCT/actions/runs/40630810164) — **SUCCESS on Ubuntu 24.04, macOS 14 and Windows Server 2022**, CPython 3.11 actual non-editable CMPCT wheel. **95 pytest PASS + nine unittest subtests PASS per host** (285 pytest plus 27 subtests across hosts); `src/cmpct/codec.py` and Reader installed files were compared to exact Git content.

Includes *unchanged* preregistered J24C07c adversarial r24 signed test (original [three-host red #40626003178](https://github.com/FCMO-AI/.CMPCT/actions/runs/40626003178)), positive raw-ZIP SHA, full Reader `read`, `verify`, nested `zipfile` and selected reads. Separate two-stream independently concatenated zlib raw-Deflate oracle tests +1/-1 signed lies in earlier and overlapping streams, prefix/mid/suffix exactness, STORED/retained controls, zero-byte no-provider proof and a seeded 96-case held-out mixed representation/offset perturbation campaign. All tests are research-scope: independent multistream oracle is a component, not a second archive decoder or an independent signed multi-member r24 golden.

Original focused court before extra zero-byte/held-out/economics evidence [#40630071575](https://github.com/FCMO-AI/.CMPCT/actions/runs/40630071575) was also 3/3 SUCCESS at code-bearing `086d972a8cf5e978cc0926dd1dfe18610c4f831d` (94 tests + nine subtests per host).

Final raw evidence artifacts for exact executable HEAD: [Ubuntu #12791417860](https://github.com/FCMO-AI/.CMPCT/actions/runs/40630810164/artifacts/12791417860), [macOS #12790864404](https://github.com/FCMO-AI/.CMPCT/actions/runs/40630810164/artifacts/12790864404), [Windows #12791940632](https://github.com/FCMO-AI/.CMPCT/actions/runs/40630810164/artifacts/12791940632).

## Independent economic result — source-exact *component*, NOT product credit

`research/j24k06_prefix_cost.py` compiles actual parent `range_vzip` AST from exact frozen checkout and compares with the installed candidate function on the **same prebuilt in-memory recipe and raw inputs** (2 × 1 MiB), four ABBA cycles for each of six cases, eight samples/arm/case/host, **96 timed observations per host**, 288 across hosts. Raw observations capture wall, process CPU, number of `get_stream` calls, raw bytes recompressed, output compressed bytes and separate `tracemalloc` allocation peaks. Independent standard-library referee recalculates medians/ratios, rejects **three deliberately forged receipts per host** (9/9), and checks source SHA; all three pass. The unsafe historical suffix read performs *less verification*; its microsecond timing is a diagnostic lower bound on newly exported work, **not a security-equivalent product competitor**.

| Hosted platform | 2-byte suffix, repeating data | 2-byte suffix, incompressible data |
| --- | ---: | ---: |
| Ubuntu 24.04 | parent 0.00264 ms → guard **9.13 ms** | parent 0.00391 ms → guard **44.14 ms** |
| macOS 14 | parent 0.00565 ms → guard **13.49 ms** | parent 0.00365 ms → guard **54.64 ms** |
| Windows 2022 | parent 0.00205 ms → guard **7.85 ms** | parent 0.00385 ms → guard **47.60 ms** |

Both preceding mode2 raw streams are recompressed by the guard for each suffix selection; the original trusted declared offsets and recompressed **zero** skipped streams. The work amplification of the example is **2,097,152 raw input bytes processed to verify a 2-byte result** (1,048,576:1 raw-work-to-returned-byte ratio). Other valid prefix and overlapping stream reads do not acquire that two-stream suffix proof cost. The repeated-prefix nanosecond-scale ratios are runner-sensitive and not interpreted as meaningful speed differences. Incompressible suffix `tracemalloc` peak on Ubuntu: 2,710,752 bytes for guard vs 216 bytes for original; **this excludes native allocations and is not full-process RSS**. CPU samples on Windows may quantize to zero and were kept as zero, not invented.

**Strongest negative:** even though the selected-mode2 safety defect is fixed, the current suffix proof exports a material cost on legitimate mode2 archives. No full-product same-semantic-comparator wall/CPU/RSS/I/O, multi-GB case, alternative full rebuild, cold-open, mixed archive, filesystem mutation, native parity or official release parity was performed. The complete product may require a different proof/ownership/representation architecture. Do **not** mark #640 or #642 ready to merge from focused green tests.

## Alternative mechanisms and counterfactual

The strongest simpler strict correctness control is complete VZIP reconstruction/verification before slicing, with much higher logical materialization. The present prefix-only implementation avoids unselected *post-end* streams and whole logical ZIP materialization but still regenerates all preceding mode2 streams. Existing [O76 #433](https://github.com/FCMO-AI/.CMPCT/pull/433) showed massive clean-input range speedups from physically retaining Deflate at modest stored-byte cost; its O76b adversary disproved same-integrity-tier parity. [O79 #436](https://github.com/FCMO-AI/.CMPCT/pull/436) showed authenticated full-recipe SHA over retained compressed bytes as a stronger no-wire-change research route, with substantial benefits on eligible cases and a real random-data negative. Both are alternatives to benchmark under full matching semantics, not permission to skip CRC or waive release bytes.

Counterfactual: inspecting the actual source control-flow around `outpos += csize` and looking for a signed **wrong-byte full-length** suffix test (not merely a short read) could have revealed #640 before J24K05's length-only check. This prospective discriminator transfers across reconstruction layers. No discovery-policy self-modification is warranted from one instance.

## Scope and remaining gates

The inherited #638 source custodian *intentionally* reports `codec unexpected edit` for any downstream codec patch; preserve its evaluator unmodified. New isolated exact-parent two-substitution guard proves deliberate scope. Generic full-suite and latest-head workflow status must be checked separately; a green generic performance workflow with an inner SKIPPED numeric job does not grant release credit. Main remains v0.30.0/revision 24. No branch or file of #638/#624/#630/#569/#641 was modified. `docs/discovery/STATE.json` remains staleable and was not edited (separate #574 owner).

A distinct **unhosted next falsifier** was added to [Issue #623](https://github.com/FCMO-AI/.CMPCT/issues/623): signed **STORED/retained** payload `csize` lies can shift a suffix while still returning a byte of the correct length on ordinary Reader without strict preflight. This is a hypothesis from a minimal component reproduction, NOT yet a source-exact installed-Reader observation. Do not conflate the J24K06 mode2 success with full S_VZIP safety.

**Decision:** keep J24K06 draft as a validated local safety mechanism with explicit productization performance debt. Highest-value next fork: source-exact full Reader same-integrity economics versus complete reconstruction, retained Deflate plus full-recipe SHA, or a bounded authenticated ownership mechanism that avoids repeated mode2 prefix recompression; separately perform the cheap STORED/retained signed offset falsifier. Preserve all negative evidence, signatures and release thresholds unchanged.
