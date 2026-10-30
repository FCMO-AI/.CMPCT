# J24I67 — hosted three-OS two-pointer predecessor camouflage verdict

2026-10-30 UTC. **Scientific evidence, not a product fix, format revision, release or benchmark success.** This decision document is appended after the hosted runs; the [original preregistration](2026-10-30-j24i67-double-parent-guard-prereg.md) at commit `36b3a7747018d2a1ee7313a5f4e17d10f8e1c300` remains prospectively distinct from the earlier exploratory O0.

## Current authority and ownership

Canonical published [main](https://github.com/FCMO-AI/.CMPCT/tree/main) is v0.30.0 physical revision-24 at `80c358f8824ec1b20d349c92ed94c898090969b0`; source exact Reader Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. This science is an independent test-only child [PR #859](https://github.com/FCMO-AI/.CMPCT/pull/859) of [single-pointer #856](https://github.com/FCMO-AI/.CMPCT/pull/856) at `f29561c5e2d36a8f47aa35f61191911c0611be6b`. Actual valid Writer-orphan recovery remains exclusively owned by active J24G93, separate. Shared Discovery STATE remains owned by #574; no state or policy change.

## Observed three-platform *installed* result

**[Actions #41133849943](https://github.com/FCMO-AI/.CMPCT/actions/runs/41133849943) SUCCESS: three independent jobs Ubuntu 24.04, Windows 2022 and macOS 15** on actual source `25f845e29f920ff2ecc55e2b04f8bd9f188e22a8`. All were substantially executed and each saved original generated archive bytes, negative/positive variants, source-head and instrument-blob attestation, pip freeze and JSON receipt. This is not merely an administrative workflow PASS.

Test corpus: original real Builder N=16 and N=128 files, followed by three real one-member Writer DELETE commits; four authenticated physical footers F0 root + F1/F2/F3 delta. The only modifications were (i) F3.prev:=F1, skipping F2's `del f00001.dat`, and (ii) F2.prev:=0, making that still-payload-SHA-valid footer unrooted.

| Actual host | Original files, N=16 / N=128 | Two-field files, N=16 / N=128 | Physical changed bytes, N=16 / N=128 |
| --- | --- | --- | --- |
| Ubuntu 24.04 | 13 / 125 | 14 / 126 | 4 / 4 |
| Windows 2022 | 13 / 125 | 14 / 126 | 3 / 3 |
| macOS 15 | 13 / 125 | 14 / 126 | 4 / 3 |

On all six hosted cases, installed CMPCT Reader `read()/verify()` and strict preflight *both* selected the manipulated latest footer, agreed on exactly the resurrected `f00001.dat`, and verified unchanged surviving member bytes. The original control passed with N-3. The corrupted latest-footer SHA control correctly recovered an earlier generation and a different expected set. The independent nearest-*rooted* footer guard accepted the unmodified original, rejected the one-field rewire, **but accepted the two-field camouflage** on all cases. It is a mathematical counterexample to that guard, not a claim about all possible guards.

## Independent original-provider artifact audit

Three ZIPs were downloaded via GitHub's artifact provider API for run #41133849943 and their byte SHA-256 recomputed independently against provider metadata, all three exact matches:

| Host | Artifact ID | Provider ZIP SHA-256 |
| --- | ---: | --- |
| Ubuntu | 13013659353 | `5ca13a53532ae4a239401cc52e64a477d612b0f980d14c3b27c7f30213939878` |
| Windows | 13014167865 | `67a96c87430907764927c5d315d8768060c9fdbf4891b13e2ba8d89bfa0b641b` |
| macOS | 13014886070 | `cd994d0df02ced57cae2624bff1f39e039ec874c84227a005bef0c32b564e756` |

Every ZIP contains **eight physical CMPCT archives**, two N sizes times (original, single, double, SHA-corrupted latest), for **24 original physical archives** total. A separate off-runner Python referee, importing no CMPCT product, parsed the exact bytes of all 24, reauthenticated four SHA-protected footer payloads and original index per case, audited the original **16/128 direct CMA4 blobs per case** for SHA-256 and CRC32 (6 cases, 432 distinct root blob records), verified modifications confined to two 8-byte predecessor fields, replayed member names independently, compared read/preflight receipts to expected SHA of input bytes, and rejected corrupt latest digest. Detached verdict **PASS**. This is second-rooted wire validation of original provider evidence, not six additional native C ABI tests.

The earlier independent O0 on original J24I56 64-footer mixed-operation cross-platform source archives also found a two-field camouflage: all three original hosted byte sets 119→120 live members, 3–4 changed pointer bytes, all 64 footer payload SHA digests and all 150 CMA4 checks valid per host. Its source Run #41051078269 and provider ZIP digests were reverified in this activation. O0 preceded prospective prereg; it is never labeled prospective hosted evidence.

## Negative evidence, limits and scientific decision

The unprotected r24 predecessor fields permit an adversarially edited footer to remain payload-SHA-authentic while altering *which* authenticated deletion history is reached. A rule checking only whether the latest footer skips a *rooted* SHA-valid predecessor is not sufficient: the adversary can also make the skipped valid footer unrooted by changing its unsigned backlink.

**Do not infer** cryptographic signature forgery, undetectable changes against a trusted external whole-archive SHA (which **does change**), universal impossibility of any backward-compatible recovery guard, genuine Writer production of the unrooted-F2 topology, atomic concurrent-modification protection, native ABI portability, or product size/CPU/RSS speedup. No benchmark, release, merge, format or version credit.

Naive checking of every candidate rooted ancestry independently also conflicts with the separately measured quadratic replay/decode-cost risk in [#649](https://github.com/FCMO-AI/.CMPCT/issues/649). Whether a bounded cache or fail-closed ambiguity rule can preserve both authentic interrupted-Writer recovery and correct deletion retention is **unresolved**; J24G93 is the cheapest strong control and current owner.

## CI fidelity / continuity

Initial hosted source/test HEAD `25f845e29f920ff2ecc55e2b04f8bd9f188e22a8`: specialized 3-host **SUCCESS**, Version Discipline **SUCCESS**, Generic Tests running at initial reconciliation. Engineering Evidence initially **FAILURE** due missing exact dossier headings; CI Topology initially **FAILURE** because SHA-keyed concurrency group made cancellation ineffective. The scheduler-only correction in `fad00230a920afb33a3076b4f9258a90655d7dee` changed the group to a stable PR/ref key, with exact-head checkout still asserted; **CI Topology then SUCCESS** and three-host specialized workflow **SUCCESS** again on that HEAD. No product code or instrument bytes changed. The PR dossier was brought up to the complete Evidence contract including explicit disproof and quality-ratchet. A third documentation-only HEAD should get its own exact-head CI attribution before any promotion claim.

**Next:** compare with real valid interrupted-Writer follow-up from J24G93, then decide whether an r24 rooted-ancestry rule has a sufficient independent provenance signal; if not, document explicit ambiguity and move to an independently authorized new format/hash-authenticated ancestry design. No silent permissive workaround.

## Counterfactual

An earlier two-link negative control would have invalidated the attractive nearest-rooted heuristic *before* implementing a potentially unsafe Parser/Reader guard. This is a transferable local testing lesson; no repeated evidence supports changing the global Discovery Engine policy.
