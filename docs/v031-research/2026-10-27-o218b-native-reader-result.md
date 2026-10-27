# O218b — source-exact full-Reader native admission result

Date: 2026-10-27 UTC
Scientific decision: **NATIVE_READER_ROUTE_WORTH_PRODUCTIZATION**, not permission to merge or release.

## Authority and preregistration

- Published main: `80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / on-disk revision 24 unchanged.
- Composed v0.31 Reader scientific source: #569 / `c5e13bb3fbb4cdade8b64246658ce7c7818de41f`, installed Reader Git blob `dbd4ac576a05a47eae97e1e40de89cf1de440516`.
- Native C scanner from original #577: exact Git blob `a54f15181d9dbe667b9e8c9d52e927b09c80152f`; unchanged strict validator blob `51c2849061f99a4afeddb7666956b24566ce7de0`.
- Frozen prediction BEFORE instrument: `4ad8b7770693832940e766300bcac4a1ea4f0a84`.
- Actual result-bearing scientific source HEAD: `89ba69d31a85092b2e3d198719fca7a7beaa9694` (later documentation-only heads are not substitutes).
- Authentic GitHub Actions hosted experiment: [run #40600841920](https://github.com/FCMO-AI/.CMPCT/actions/runs/40600841920), conclusion **SUCCESS**; original [artifact #12777644140](https://github.com/FCMO-AI/.CMPCT/actions/runs/40600841920/artifacts/12777644140).
- Independent original JSON receipt SHA-256: `009cbb560163278558de94b6e6315565946c45fa3d2ea302eca64efd81125c9b` (not the ZIP hash).
- Scientific workflow includes unchanged O215 tests **12 PASS**; full native four-arm court **144 subprocess workers / 720 timed constructor-close opens**, six profiles, three cycles, two workers/arm/cycle, original/fast/native/unsafe control. Named semantic controls 24 + inherited O216 controls 19 + 2,500 deterministic fuzz cases; independent receipt auditor PASS and **5/5 deliberately forged receipts rejected**.
- Host: Ubuntu 24.04, CPython 3.11. Process startup and extension compilation deliberately outside per-open timing; binary research extension **16,496 B** (additional packaging/wheel burden not yet charged).

## Direct source-identical full-Reader observations

Values are median cold-open constructor+close wall milliseconds, all four arms executed against identical Builder-independent authenticated r24 archive bytes for each profile.

| Refs | Physical owners | Original strict | O216 fast strict | Native strict fallback | Unsafe lower bound | O216/native |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1 | 0.075913 | 0.069914 | 0.069039 | 0.068758 | 1.013x |
| 4,096 | 1 | 1.295113 | 0.390135 | 0.134958 | 0.105588 | 2.891x |
| 65,536 | 1 | 18.981123 | 4.996231 | 1.334082 | 0.814207 | **3.745x** |
| 262,144 | 1 | 74.712113 | 19.983475 | 5.082836 | 3.028845 | **3.932x** |
| 65,536 | 256 | 19.279985 | 5.719543 | 1.450100 | 0.975858 | **3.944x** |
| 262,144 | 256 | 76.732413 | 22.486533 | 5.393564 | 3.540609 | **4.169x** |

The primary preregistered repeated-reference decision meets both conditions:
- 65,536: native speedup over O216 strict fast **3.745x** (required >=2.5); native/unsafe **1.639x** and +**0.520 ms** (required <2x and <=5 ms).
- 262,144: **3.932x** (required >=2.5); native/unsafe **1.678x** and +**2.054 ms** (required <2x and <=20 ms).

256-owner heldout cases are also favorable; 1-ref case gains nothing meaningful. The unsafe unguarded arm **cannot** serve as product control because it accepts malformed inputs. Native success is not a reason to remove admission or loosen the timing gates.

## Causal interpretation, self-critique and counterfactual

O218's detached native micro reported ~6–7x, but its whole installed Reader transfer is **3.7–4.2x over O216** on measured high-reference regimes. The lower end is consistent with unchanged index MessagePack decode, open, setup and mmap overhead; these are not eliminated by compiled iteration. Relative to original strict installed Reader, the native-scanner experiment is substantially faster, but startup, compiler/wheel installation, and portability are unpaid. A 16,496-byte standalone native shared library is not the complete shipped storage or maintenance cost.

The prospective lesson is that a detached 6–7x micro should trigger **one** installed Reader ABBA, not native integration by inference; here that cheap higher-rung test changed the decision favorably. This is a specific scientific process observation, not a repeated-evidence justification to modify policy. O216/O217 negatives remain durable; O218 C scanner itself is reused unchanged.

Potential invalidators: Windows/macOS CPython packaging, PyPy fallback, native ABI maintenance/security review, unmeasured peak RSS across platforms, real heterogeneous archives, unusual object subclasses/large ints, journal/recovery, multi-reader pressure, and full release parity. The adversarial case set covers original class/message on named/fuzz inputs; it is not an exhaustive C extension safety proof. The experimental scanner's `False` path always uses the unchanged original strict validator.

## Decision and next accountable implementation

Research **positive**, product **unpromoted**. Before an owner #569 integration:
1. Decide if invoking a research-only CPython compiled helper is justified relative to an already-existing memory-safe native C/Rust core. Prefer an existing supported API with the same exact predicate when possible.
2. Introduce an *optional* source-pinned native path with strict fallback on absent/unsupported systems; prove no false success / identical errors for every rejected index and full same-inode Reader behavior.
3. Run three-host installed-wheel tests, true RSS and cold open wall/CPU ABBA against exact original/fast sources, hostile parser/resource tests, and official immutable parity/release gates. Require full archive/Reader semantics, not only callback speed.
4. Preserve native artifact size/build/wheel/ABI and ongoing reader complexity as part of total product economics. No format/version change earned.

Scientific research remains stacked PR #627 Draft. Its owner is not #569, and it edits neither Reader nor validator. No merged release or public benchmark headline should reflect this run. Discovery STATE remains exclusively owned by #574 reconciliation and was not modified.

**Negative that matters most:** native is still 1.5–1.7x slower than deliberately unsafe baseline at high references even in the favorable test. Its remaining +0.5–2.1ms is measured, not assumed free; more distinct/large real indices are required before promotion.
