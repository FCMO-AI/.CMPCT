# O218c — portable CPython C-admission execution court (prospective preregistration)

**Status:** preregistered before instrument/CI implementation. **Research only.** No product source, format, release or benchmark gate modification authorized.

## Live authority and provenance

2026-10-27 UTC: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, released v0.30.0/r24. Existing #569 Reader integration owns production source. O216 #570 (safe Python fast path) and O218 #577 supply stronger Python/native controls; O218b #627 exact `d3d87e5df39ab9e58043cab74d5b2a1d87f5bed5` measured native full-Reader Ubuntu speedup while leaving Windows/macOS ABI/build portability unmeasured. Branch this exact #627 HEAD. Existing Rust CLI #580 is a different, primary-checkpoint-only semantic contract and is not a substitute for this experiment. No concurrent PR found for the narrow three-host O218b C-extension transfer.

Pinned source blobs: Reader `dbd4ac576a05a47eae97e1e40de89cf1de440516`; Python validator `51c2849061f99a4afeddb7666956b24566ce7de0`; native C `a54f15181d9dbe667b9e8c9d52e927b09c80152f`. The C scanner can only return True for exact built-in list/long semantics and delegates every False to unchanged validator for original diagnostics.

## Single primary question

Can **the identical unmodified C source** be compiled with the supported host CPython extension toolchain, loaded and run inside the real installed Reader on Ubuntu 24.04, macOS 14 and Windows Server 2022, without admission or diagnostic drift, and retain a materially useful advantage over the strongest exact Python O216 control?

## Cheapest decisive comparison

Use built-in `setuptools`/`build_ext` to compile the unchanged C file into a host extension with native OS toolchains; capture compiler log, build wall, .so/.pyd size+hash, Python version, OS and exact HEAD/blob identities. Execute original inherited O215 suite on each host; include 24 named malformed/valid cases and 2,500 deterministic fuzz trials against the unchanged validator on each platform. Test true Reader constructor/open/read_range on independently built authentic r24 O215 archive. Compare three **strict** arms (`original`, `fast`, `native`) plus unsafe no-validation **timing floor only** on the **same archive per profile**. Use 65,536 and 262,144 repeated-reference cases plus one 65,536-reference/256-owner held-out. Randomized paired process blocks with two cycles and two workers per mode/cycle; five timed complete constructor+close samples per worker. Preserve raw wall, CPU, process RSS when platform-supported, true file hash and source identity; report missing RSS rather than manufacture values. Compilation and interpreter startup are separately charged, not included as constructor timings.

## Prospective decision and kill conditions

**PORTABLE_C_EXTENSION_RESEARCH_ROUTE** only when all three hosts can compile/load the identical C, the original O215 and native-vs-original adversarial semantics checks PASS, and native/fast median constructor wall >= 2.0x for **both** repeated 65,536 and 262,144 on each OS. An observed OS failure to compile/load, an unexpected acceptance/diagnostic mismatch, or failure of either benefit threshold yields an explicit scoped negative (`PORTABILITY_OR_ECONOMICS_NOT_PROVEN`). Evidence workflow may pass as an honestly audited negative; do not weaken threshold or selectively remove host/corpus.

## Confounders, limits and no-product-credit

Existing Rust native r24 CLI is **not** semantically equivalent on authenticated signed transaction recovery. Existing CPython research injector is not packaged product software. The `setuptools` build proves host buildability, **not** wheel distribution, stable ABI, PyPy, ARM, import lifecycle or release packaging. O215 3-host correctness is a necessary but insufficient representative of all r24 representations, filesystem recovery/updates and hardening. Windows/macOS RSS may be unavailable. Build wall/size and high-reference Reader cold constructor costs must be reported separately; unsafe bypass is not admissible. Exact-source O218b Linux historical timings are a provenance control, **not** used as contemporaneous cross-host ratios.

## Counterfactual / next action

If portability works and economics survive, hand off to #569 for optional native integration with Python fallback and release gates. If it fails, isolate architecture-specific build/semantics/economics before spending on packaging; consider already shipped Rust handler only after signed-journal parity. Do not edit `docs/discovery/STATE.json` (active independent #574 owner) or any CMPCT production source. Only prospective transferable repeated failure can justify discovery-policy mutation.
