# O196 — native CDC admission and performance-attribution preregistration

Date: 2026-10-26 UTC
Status: PRE-RESULT; experimental instrument not yet committed
Surface: existing Draft O185 PR #516 only. Released CMPCT v0.30.0 / r24 is unchanged.
Source: O185 exact HEAD `7b115f39aed095fe0273f906c5bd42db66e156f5`, source blob `native/cmpct_cdc.c=a6253beece20ce8aad3cdb605a6d9fcaa50d9364`.

## Problem / observed baseline

O185 exact-head [official performance #40340587167](https://github.com/FCMO-AI/.CMPCT/actions/runs/40340587167) is genuinely RED: `nested/cli/create` 64.118 -> 67.353 ms (+5.05%, +3.235 ms), despite 0 deterministic size regressions. Earlier unchanged implementation had another one-cell RED on AMD and a same-source full ABBA PASS on Intel. Preserve **all three** measured outcomes; neither a repeated green nor a red on unrelated code proves CDC overhead.

The O185 product diff changes only `native/cmpct_cdc.c`; `codec.py`, `builder.py`, `native_codec.py`, and `pyproject.toml` are unchanged from O173. `codec.py` dynamically loads only `libcmpct_cdc.so` adjacent to the Python package when that path exists. `pyproject.toml` declares a Rust cdylib extension but no explicit build/install step for that standalone C helper. The official ABBA gate uses normal `pip install -e '.[audio,test]'` and does not visibly compile C into the package. **Hypothesis:** ordinary installed O185 distributions do not admit the modified CDC engine, so the observed small benchmark time differences cannot be attributed to changed CDC execution. This is currently an inference from checked-in source, not measured runtime proof.

## One falsifiable question / prediction

In a **clean, fresh-interpreter installed wheel**, is `codec._cdc` actually present? Compare unmodified O185 wheel import and the deterministic `cdc_chunks` call with a *positively controlled*, explicitly injected copy of the exact checked-in C object on the same byte input.

Prediction: the clean wheel does **not** contain or load `libcmpct_cdc.so` and `codec._cdc is None`; default chunk boundaries are fixed `CHUNK=262144`. Explicitly compiling and admitting the C source should yield valid, *different* boundaries for the same >`CDC_MAX` deterministic input. A direct ABI call must agree with wrapper-native boundaries.

**Simpler control:** static `pyproject.toml`/loader audit implies absence, but is insufficient if an unstated build hook, generated artifact or ambient file is copied into the wheel. An independent wheel installation in a clean virtual environment is therefore the cheapest decisive rung.

**Alternative explanation:** packaging may include the C library through a source or build hook not yet inspected, or an environment-specific shared library may be present. In that case record a positive native admission, source provenance and distinct output; do not force a negative result. A failed build/network/runner, missing compiler or missing dependency is INFRASTRUCTURE / INCONCLUSIVE, not proof of absent helper.

## Experiment / exact acceptance

1. GitHub-hosted Ubuntu check out exact PR head; record Git blob of C and `pyproject.toml`, the full source SHA, compiler/wheel provenance.
2. `python -m pip wheel . --no-deps` and install exactly that wheel in a fresh virtualenv. Run the probe with working directory outside checkout and with PYTHONPATH unset; verify import path is within venv, list package `*.so` files and evaluate loader admission explicitly.
3. On a deterministic 2.24MiB nondictionary byte input, record default fixed boundaries and direct checked-in C native boundaries. Inject the compiled C helper *into a separate probe invocation*, demand that Python native wrapper cut lengths equal direct native cut lengths and differ from fallback. Check reconstructed bytes in both cases.
4. Record fail-closed JSON witness with source SHA, module/wheel identity, observed admission (true/false, never assumed), cuts/length and explanatory claim boundary. A source-bound workflow must upload the witness even if a claim fails.
5. Do not modify product, packaging, comparator or frozen performance gate. The experiment is not a new compression win nor a test of true CDC speed; it judges whether official installed-package ABBA is causally exposed to the changed source.

**Kill / narrow:** wrong source Git blob, non-wheel import, absent raw provenance, invalid native boundaries, nonexact reconstruction, silent native fallback in positive control, or missing actual result-bearing job -> NO POSITIVE CLAIM. If the clean wheel already admits C, disprove the predicted lack of admission and investigate source-causal differences with controlled data; no weakening. If helper is absent, retire the notion that unmodified packaging benchmarks measure native CDC and separately decide whether an explicit opt-in packaging path is worth maintaining (consider portability, startup, memory, signed wheels, fallback and maintenance).

## Product economics and safety

The test should not alter shipped behavior. Wheel building may take minutes but is cheaper than another 7-repetition × ABBA full-corpus benchmark for a question that import introspection decides. No private fixture or corpus identities. Product promotion still blocked by the exact-head RED, inherited O175 cache warm-scan debt, portability and general release criteria. A green admission oracle provides scientific attribution only.

**quality-ratchet:** improve runtime/packaging attribution without relabeling a failing benchmark as successful, removing fallback, changing decoder semantics or increasing shipping complexity.

**disproof:** source mismatch; native wrapper differs from checked-in C; inability to distinguish injected native from fallback; unverified wheel import; any rewrite of inherited performance evidence.
