# J24P07 — Wheel installed-target injectivity, source-exact preregistration

Date: 2026-10-30 UTC. **Experimental product-side candidate only; unmerged, no release/version/format/ABI authority.**

## Boundary and ownership
Stack on #854 exact `57bc9a00a6dbba079131de15f88995fd75ea91b6`. #854 owns wheel physical/Mach-O verification, #858 owns reproduced PEP 427 native overwrite, #862 owns separate Python-spread falsification, #850 owns release packaging. This lane owns a **new portable static install-target collision guard**, not those other implementations, workflows, claims, or Discovery STATE.

## Baseline and local exploratory observation (not prospective)
#858 demonstrated real pip-install collision: `cmpct/cmpct_core.cpython-311-darwin.so` and `cmpct-0.30.0.data/purelib/cmpct/cmpct_core.cpython-311-darwin.so` coexist in a self-consistent wheel but overwrite the same physical installed destination. The #854 read-only archive/Mach-O/RECORD validator accepts both. Before committing this preregistration, I constructed a local exploratory stdlib-only canonical target map and checked four supplied *historical* real wheels: original and disjoint accepted, spread-before and spread-after rejected. These are **retrospective exploratory data**, not new prospective hosted proof.

## Question and falsifiable mechanism
Can a **separate, read-only, portable, stdlib-only** guard reject unsafe member-to-installed-package path aliases **before pip**, while accepting genuine official-style wheels, without requiring a full second installer, running untrusted native bytes, or weakening #854?

Competing solutions: (A) verify only archive-level RECORD and native Mach-O (#854, already falsified for installed targets); (B) verify installed native SHA afterward (insufficient if Python module overwritten; #862); (C) model *just* the shared destination namespace for root, `.data/purelib`, `.data/platlib`, with conservative cross-platform normalization and reject ambiguous installs (this experiment); (D) post-install whole-tree hashed attestation (stronger actual-state scope, extra runtime/I/O and trust-root requirements).

## Frozen hosted acceptance
On independently hosted Ubuntu, macOS 15 and Windows 2022, use `python3` and self-contained inert stdlib wheel fixtures:
1. Accept a positive baseline with original package member and distinct unrelated extra package member.
2. Reject *both* ZIP-member orderings of one `.data/purelib` native collision.
3. Reject a `.data/platlib` Python-module collision, independent of whether its name matches any native binary.
4. Reject an ordinary root-path casefold collision, even on case-sensitive Linux; portability is a deliberately stronger cross-platform contract.
5. Reject unsafe `../`, `./`, doubled separators, backslash, trailing-dot and Windows-device spellings, without relying on host path behavior.
6. Against an authentic official-style CMPCT wheel from existing source evidence, accept genuine original and disjoint variants, reject both previous PEP 427 spread variants.
7. Independent tests should verify the guard fails if one of the collision branches is removed (mutation); do not weaken tests/controls to make the guard pass.
8. Run local and hosted tests without importing or executing modified CMPCT code or native modules.

**Kill/narrow condition:** Reject an authentic unmodified official-style wheel, accept a spread collision, or require bypassing existing physical/RECORD checks: nonpromotable pending causal analysis. A passing static check never certifies actual installed file hashes, signed publisher provenance, race freedom, extra installer schemes, symlink behavior, or direct runtime compatibility. It must not replace real macOS Intel executable smoke testing.

## Costs and policy
Read-only O(member count × path length), bounded path/component count; no decompression, module import or runtime hot-path cost. A conservative casefold/NFD collision policy can reject legal Linux-only wheels: that is explicitly a **portable package** boundary, not universal wheel-spec conformance. No product performance or released compatibility credit until deliberately adopted by the #850 owner and actual install tests pass. Do not update `docs/discovery/STATE.json` (owned by #574), version, format, frozen benchmark, evaluators, or other agent branches.

## Next decision
Implement the smallest checker plus independent real-wheel fixtures and a three-OS Actions court. If it passes, hand off to #854/#850 owners for release integration; if it fails, preserve the negative and evaluate a post-install trusted whole-tree manifest instead.
