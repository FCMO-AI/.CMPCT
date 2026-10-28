# J24G17 result — Native MessagePack syntactic token preflight versus canonical decoder

**Research only, 2026-10-28 UTC. Decision: CONDITIONAL RESEARCH SEED, NOT A PRODUCT PATCH.**

## Scientific question and custody

Can moving the J24G16 predecode token-count pass from pure Python to bounded native C make the scanner economically credible on ordinary admitted metadata, while retaining an early refusal path for structurally oversized metadata? Does that establish a compatible default Reader solution? These are two separate questions.

- Public release: `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0/revision 24, **unchanged**.
- Research parent #681: `5563b199bc03ed03c3e78918c51a7cf5396c2ff1`; unchanged Reader blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b`.
- Prospective question/acceptance criteria commit **`32099051333c9a23328bf3bc99778afe8ace8e0f`**, preceding quantitative measurement. Initial source draft/compilation occurred before preregistration, disclosed contemporaneously; no timing/RSS result was produced until after the prereg.
- Measured code/source/CI exact branch **`4d1735464943d2923a4fb76b833ef70b46680400`**. [Ubuntu Actions #40715752389](https://github.com/FCMO-AI/.CMPCT/actions/runs/40715752389) **SUCCESS**, genuine checked-out branch HEAD.
- Physical and raw data [artifact 12828855842](https://github.com/FCMO-AI/.CMPCT/actions/runs/40715752389/artifacts/12828855842), hosted ZIP digest `sha256:3b79b089051ab35f02f6fd976d93982fbc4c7b036ee508590b75cb0d8cc36941`. Includes source.json, native-build-sha256.txt, actual six .mpk inputs, result.json, referee log. Compiler `cc -O3 -std=c11 -Wall -Wextra -Werror -fPIC -shared`. Native C source SHA-256 `d917dd61c9efd868ab022fbf569de1156ed87758dca325f3e457e3b90df41191`.
- Runtime: GitHub-hosted Ubuntu 24.04, CPython 3.11.17, msgpack 1.1.2, 5 fresh workers per case/control and 3 repetitions per worker: **270 raw CPU/wall observations**. Source SHA-bound physical files and in-worker timings; exclude process startup, compilation, package setup. No tracemalloc.

## Controls and falsifiability

The controls are (a) direct original `msgpack.unpackb(raw=False)`; (b) C syntactic token-counter via ctypes **followed by unchanged direct unpack** for admitted payloads; and (c) `Unpacker.skip()` + unchanged unpack as cheaper but non-semantic counting control. This is an honest economic control, **not an acceptance oracle**: `skip()` alone does not reject a nested unhashable map key. The C pass is not an accepting semantic parser either; canonical MessagePack still decides acceptance after a structural pass succeeds.

The pre-registered H2 economic kill threshold is both ordinary 10,000-map CPU and wall no more than **2x** the direct original; H3's hostile RSS outcome is at least **16 MiB** less process peak RSS for explicit refusal of 200,000 tiny-map metadata. No benchmark threshold or product admission semantics were changed. All tests also require 2,510 seeded valid structural inputs, seven malformed cases including nested invalid keys, exact 65,536-node cap boundary, and an independent referee rejecting altered receipts.

## Hosted measurements at the measured-code HEAD

| Matched physical case / metric | Canonical direct | C prepass + original | Economic result |
| --- | ---: | ---: | --- |
| Ordinary 10k maps — median CPU | 2.769346 ms | **2.943435 ms** | **1.062862856x** (6.29% overhead) |
| Ordinary 10k maps — median wall | 2.772266 ms | **2.947084 ms** | **1.063059605x** (6.31% overhead) |
| Ordinary 1k maps — median CPU | 0.248510 ms | 0.302470 ms | 1.217x (larger relative overhead) |
| Opaque same-size 800,028-byte metadata — wall | 0.425098 ms | 0.469254 ms | 1.104x |
| Tiny-map 200k — process high-water RSS | 59,188 KiB | **22,384 KiB** | **36,804 KiB (35.94 MiB) lower by refusal**, not by decoding |
| Tiny-map 200k — semantic action | **Accepted** | **Refused: experimental node cap** | **NOT equivalent input acceptance** |

**H2 component-level PASS:** Native scanner avoids the pure-Python J24G16 ~6.3756x cost and passes the frozen 2x economical ceiling on this host, same-input admitted ordinary metadata. It **does not accelerate** the normal canonical decoder: it adds ~6.3% on ordinary 10k.

**H3 component-level PASS only under changed policy:** C scanner refuses previously valid oversized metadata before decoding, so a substantial RSS saving appears. This is not proof of memory reduction while retaining identical acceptance/recovery semantics. Claim scope is carefully limited.

All 2,510 valid generated structures passed both counter and original decoder. Seven malformed examples were rejected by canonical decoding; a deliberately invalid nested map key illustrates that syntactic C scanning alone can return a valid token count even when semantic decoding rejects the bytes. Exact cap boundary passes/refuses as predicted. Independent standard-library referee replayed physical-file hashes, 270 source/observation records, classification and medians: **1,216 assertions PASS, six manipulated receipts REJECTED**. Referee does not independently reconstruct physical `.cmpct` archives or validate a full MessagePack grammar.

## Conflicting/negative knowledge and adversarial self-review

1. **Semantic compatibility (blocking):** Refusing signed but valid deltas beyond 65,536 tokens is a new input-admission boundary that would change what the published Reader accepts and may alter recovery of an earlier checkpoint versus a resource error. Any actual Reader insertion requires explicitly resolving this contract without weakening format, validation, recovery or release law.
2. **Two parse passes:** Native scanning is an extra full O(input bytes/tokens) pass plus canonical parsing. On tiny messages its fixed FFI cost increases relative latency. Whole-product permanent overhead, deployment, startup, peak RSS and selective opens have not been measured.
3. **Negative controls are not semantic oracles:** `Unpacker.skip` is C-backed and cheap but can skip malformed nested keys; J24G15/16 proved a genuine mismatch. Do not present it as a safe replacement.
4. **C correctness is narrower than production conformance:** 2,510 random values and seven malformed witnesses are not a complete grammar proof, fuzz coverage or platform conformance; nested massive arrays and pathological byte counts require deeper security review. The C scan distinguishes framing/budget but not all decoder semantic errors, so error types may vary.
5. **RSS high-water is process-wide:** This experiment isolates vector creation in an exited subprocess and uses fresh workers to avoid earlier J24G15/J24G16 contaminated highwater. It cannot attribute every KiB to one allocation or claim a global maximum.
6. **Host dependence:** Separate local exploratory Python 3.13.5 microcourt (not identical source/host/runtime) saw larger ordinary relative overhead, around 1.25x. Do **not** average with Ubuntu 3.11 results. Exact-host portability on Windows/macOS and ABI3 extension packaging have not been tested.
7. **No complete-system credit:** No source modification under `src/` or `native/`; no changed archive bytes, create/extract/selective read/decode traffic, authentication/recovery/attack conformance, Windows/macOS portable binaries, published evidence gate, merge or release.

## Decisive action / counterfactual

**Decision:** The native predecode execution frame **rehabilitates the economic *feasibility* of scanning** and falsifies the explanation that any prepass must necessarily cost >2x direct parsing. It does **not** establish a shipping mechanism. The reusable prospective lesson is to distinguish *the ability to refuse an input early* from *memory safety with inherited acceptance semantics* at preregistration, before investing in product complexity. This distinction would have identified J24G16's RSS credit boundary earlier. No general discovery-policy amendment is yet earned: one new experiment plus prior related negatives is insufficient to prove a process-wide change.

**Next cheapest unclaimed decision-changing test:** Source-bound actual released/composed CMPCT Reader comparison on the same authentic revision-24 archive containing an earlier signed recoverable checkpoint plus a syntactically valid oversized signed orphan/delta tail. Compare exact original accept/reject, generation selected, full/range content, verify, RSS/CPU/work and detect whether predecode exception aborts the entire fallback search. If the contract cannot be preserved without changing published acceptance, retire this family as a default Reader optimization and seek a semantics-preserving schema-first projection or a different product bottleneck. A generalized variant requires multi-host tests and full accounting; the C microcourt alone cannot earn product or version credit.

**Concurrency:** #681 is the parent and remains untouched; independent #682 tests tuple-first chunk ownership, not this scanner. No discovery STATE write; #574 already owns that reconciliation. No frozen experiment, threshold, evaluator, format or release change.
