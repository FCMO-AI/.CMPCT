# J24P09c — Pip accepts a wheel whose installed payload disagrees with RECORD

Date: 2026-10-30 UTC. **Unexpected negative after J24P09, J24P09a and J24P09b. Pre-fix causal falsifier; prospective bounded repair described before implementation.**

## Causal result

Used the original 23-entry official-style Linux wheel, SHA-256 `07f2ebd657fd887570b953eaa8c5fa52073dc4d0e0d3e4ec0c8ffaf9d26761dd`. Repacked an otherwise identical self-consistent ZIP, appending only an inert Python comment to `cmpct/native_codec.py` **without updating `.dist-info/RECORD`**. Modified wheel SHA-256 `47644f317a07902961137ea3a7e570bb9d94daac126d166e3a7a1c3f0ae4dfa5`.

In a clean isolated Python3.13 venv, actual `pip install --no-compile --no-index --no-deps` returned exit 0. The current J24P09 installed-package SHA attestor returned `PASS`: installed source exactly equaled altered wheel bytes, despite wheel RECORD contradicting those bytes. This is a real local pip/attestor counterexample, no executed malicious code and no claim that real CMPCT releases have this defect.

## Implication

A complete wheel-to-installed package match is a **byte transport claim**, not a proof that the wheel itself meets its declared integrity metadata. The macOS physical #854 validator checks RECORD before install; the Ubuntu/Windows branch of J24P09 had only the #864 lexical/profile preflight. That asymmetry admits noncompliant wheels even if pip installs them.

## Frozen cheapest repair to evaluate

Extend **the existing** CMPCT-specific final-wheel preflight, not a third overlapping wheel tool: validate complete RECORD membership for every regular ZIP file with SHA-256 URL-safe base64, declared sizes, exactly one blank hash/size self-row, no duplicate/missing/extra RECORD rows, and bounded streaming over decompressed bytes. Reject incompatible algorithms/encoding; compare to genuine 23-member Ubuntu/macOS/Windows controls; reject the exact inert mismatch from this falsifier, plus metadata-only adversaries. Preserve current two-root/.data/casefold/device/path checks, independent macOS Mach-O/minOS oracle, post-install complete byte binding, and no cached code. Measured overhead is one bounded streaming pass over wheel members at CI publication time, not Reader/Writer runtime or a compression win.

**Kill condition:** any authentic supported unchanged CMPCT wheel rejected or any stale/missing/mismatched RECORD admitted. A re-signed attacker-generated RECORD could still attest malicious payload because neither RECORD nor wheel has independent publisher authentication. This repair does not earn supply-chain signatures, and changing validator rules is not permission to weaken older tests.
