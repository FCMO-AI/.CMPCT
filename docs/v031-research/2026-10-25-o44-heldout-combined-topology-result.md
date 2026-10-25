# O44 result — actual-source held-out combined hardlink topology

**UTC:** 2026-10-25.  
**Decision:** `ACTUAL_GENERATOR_TOPOLOGY_GAP_CONFIRMED` / `HELDOUT_RECONSTRUCTION_SURVIVES_TYPED_SNAPSHOT`.  
**Evidence class:** experimental benchmark-corpus semantics; **zero compression/archive/performance/release credit**.  
**Parent:** PR #328 exact source `36c5c737c2896b9ad9ee68c491ff921fbd36aaa4`; unchanged generator Git blob `2668948a64a03fc7f2b7c97fd97c8e0696aa9bee`.  
**Preregistration (before hosted result and before publishing code):** `c5effbee66682786b4787945819999eb2a5961ee`.  
**Result-bearing exact implementation HEAD:** `2f3c87db472d34c186a6d2de23042ca9afb1dd55`.  
**Hosted run:** [40153644282](https://github.com/FCMO-AI/.CMPCT/actions/runs/40153644282), Ubuntu 24.04, source-exact job SUCCESS, [raw artifact #12582954883](https://github.com/FCMO-AI/.CMPCT/actions/runs/40153644282/artifacts/12582954883), artifact archive SHA-256 `d4b945f2d8dffb489b87192cfb437cf8c924a0d9004b6cd1d506bbe666b59672`.

## Source-exact direct observations

The hosted court generated the **actual** `universal_bench.make_corpora()` source, did not modify `universal_bench.py`, then copied its unchanged categories into a separate held-out combined tree. The original combined tree remained unmodified.

| Measurement | Original combined | Held-out combined |
| --- | ---: | ---: |
| Regular files | 3,856 | 3,856 |
| Logical member bytes (aliases counted) | 84,760,369 | 84,760,369 |
| Distinct-inode-charged logical bytes | 84,760,369 | 83,711,793 |
| Physical hardlink groups with >1 regular path | 0 | 1 |
| `dedup_links/real.dat` and `dedup_links/hardlink.dat` alias one inode | **No** | **Yes** |
| Typed relative pathname/content SHA-256/mode/mtime/symlink target comparison | Baseline | **Exact equality** |
| Held-out complete relative inode partition matches independently measured category-source partition | N/A | **PASS** |

The original `dedup_links` category (outside `combined`) contains the physical hardlink pair; this is **not** a claim that the whole benchmark lacked all hardlinks. The held-out corpus reduces the **sum of distinct regular-file inode sizes** by **1,048,576 bytes**, precisely the paired 1 MiB source file. This measure is **not** on-disk allocated blocks, CMPCT archive bytes, or a performance win.

## Adversarial / independent controls

The focused suite completed **5/5 PASS** on hosted Ubuntu under the same code HEAD. It includes: unchanged stock `shutil.copytree(symlinks=True)` negative; correctly shared owner across nested directories; equal-byte independent source inodes never coalesced; relative symlink identity retained; external-inode names never linked into the destination; symlink root refused; and a miniature end-to-end combined reconstruction with byte-equivalent but physically distinct source objects.

Source provenance step required an immutable exact generator blob and checked that no `src/`, `native/`, `zip-parity.yml`, `universal_bench.py`, parity builder or comparator changed relative to the exact parent.

**A genuine initial hosted failure is retained:** [40153540090](https://github.com/FCMO-AI/.CMPCT/actions/runs/40153540090) failed before any materialized-corpus execution because the inherited repository-wide `tests/conftest.py` imported `msgpack`, absent from the intentionally minimal standalone scientific environment. The O44 workflow was corrected to run its dependency-free research tests with `pytest --noconftest`; the inherited full product suite remains a separate GitHub CI gate, unchanged. This is a test-harness dependency error, not evidence of physical-topology failure.

## Decision / generality / losses

The unchanged generator makes the original combined scenario physically **different** from its category-source hardlink relationships, despite retaining member contents. A **separate non-frozen** structurally faithful combined fixture is feasible on Ubuntu and preserves the independently checked source link partition.

This does **not** require editing the historical benchmark: source `dedup_links` already tests physical hardlinks, and the marginal value of a mixed-structure held-out product comparison is **not established** by this corpus-only oracle. A next product decision must require same-input/same-semantics authentic CMPCT/competitor archive creation, extraction, physical topology and cost evidence, along with measured additional generator overhead.

The copier is scoped to a trusted, quiescent tree on Linux/POSIX. Inode identity can change under concurrent mutation; hardlink creation can fail on another volume/OS; timestamps/xattrs/ACLs and symlink handling can differ on other filesystems. The test checks file mode/mtime and symlink targets, but **does not establish ACL, sparse-block, xattr or adversarial snapshot equivalence**. No Windows/macOS claim is made.

## Counterfactual discriminator

The cheapest earlier experiment is one exact `stat(st_dev,st_ino)` pair comparison for `dedup_links/real.dat` and `hardlink.dat` in both source and combined after generation. That would have detected the historical comment/code contradiction before full archive benchmarking. The follow-on *root-independent complete partition and typed snapshot* was needed to prove the proposed held-out repair did not silently deduplicate distinct equal-byte files or corrupt other metadata.

No change to discovery policy, frozen release thresholds, format revision, core version, source owner PR, official parity comparator or shared `docs/discovery/STATE.json` is justified by O44 alone.

## Next highest-leverage decision

Treat this as a **candidate independent mixed-structure held-out test**, not another core feature or official gate. Compare its incremental adversarial coverage against existing separate `dedup_links` and official release corpus evidence. Only if it exposes a meaningful *unmeasured* capability gap, run a separate source-bound real archive/extract differential. If it does not, preserve the negative marginal-value finding and retire this fixture family rather than adding permanent CI cost.


## O44b execution-custody correction — 2026-10-25 UTC (append-only)

Post-run log inspection of hosted [40153644282](https://github.com/FCMO-AI/.CMPCT/actions/runs/40153644282) and [40153914192](https://github.com/FCMO-AI/.CMPCT/actions/runs/40153914192) found that an infrastructure edit accidentally inserted *literal* `\\n` characters inside a Bash comment in the research-test step. Thus those runs **did execute the actual full generator and independent typed physical-partition assessor**, but **did not execute pytest** despite the green job statuses. Their earlier documentation's claim that 5/5 hosted tests passed is **incorrect and withdrawn**, without rewriting the earlier artifact. The substantive actual-generator physical-partition PASS from those jobs remains valid.

The exact workflow comment was corrected (without changing the corpus generator, tests, copier or assessor), then a dedicated hosted source-exact proof genuinely executed:

- **Result-bearing exact HEAD:** `30090b9960677c2921e8276c08b2be825adfdd38`.
- [O44 real six-test court, run 40154041500](https://github.com/FCMO-AI/.CMPCT/actions/runs/40154041500), job `121051439835`: **SUCCESS**, with explicit stdout `...... [100%]` and `6 passed in 0.07s`.
- The sixth test deliberately injects `os.link` failure and demonstrates the helper rejects it rather than silently copying bytes and losing topology.
- The **unchanged original full generator** was re-executed on that same exact head and produced **PASS** for the original-to-heldout semantic comparison and expected category-source hardlink partition.
- [Raw same-run evidence #12583926086](https://github.com/FCMO-AI/.CMPCT/actions/runs/40154041500/artifacts/12583926086), artifact ZIP SHA-256 `023bbc7418ffedc227f0f41c973217173b3a59d7c407fd79cc3749d12972b644`.

**Evidence conclusion:** Scientific corpus-topology claim + six focused adversarial tests now both have genuine hosted execution receipts on the same exact implementation head. The earlier falsely green test steps are retained as a separate *evidence-infrastructure negative* and are not counted. A general lesson is that CI step success does not prove a command actually ran: inspect the job log for meaningful test output/receipts. This is a local verification lesson; it does not justify altering the Discovery Engine or release evaluator.

No true archive creation/extraction/compression speed or physical-storage-block metric is measured. No promotion/merge/release approval is implied.


## O44c — permanent anti-false-green evidence receipt

To prevent the earlier commented-out test problem recurring, the dedicated **research** workflow now requires an independently readable JUnit XML receipt from the actual pytest invocation. The step parses it outside pytest and rejects a missing report, fewer than six cases, any failures/errors/skips, or absent individual testcase elements. This protects execution custody without changing any scientific evaluator, threshold, historical suite, production code or release gate.

- **Hosted source/test/workflow HEAD:** `45e0a26f1db9320a4b9a98832f971aae51793500`.
- [Run 40154191179](https://github.com/FCMO-AI/.CMPCT/actions/runs/40154191179): completed **SUCCESS**, real stdout `6 passed in 0.07s`, independently checked `O44_REAL_TESTS=6 FAILURES=0 ERRORS=0 SKIPS=0`, and actual-generator assessor JSON `verdict: PASS`.
- [Raw artifact #12583946201](https://github.com/FCMO-AI/.CMPCT/actions/runs/40154191179/artifacts/12583946201), ZIP SHA-256 `d0605694a23ea7c1014f0982218716d03bb3ebc5c3309804257ad7d6445d1c11`. Contains JUnit XML, console log, actual-generator receipt and source HEAD identity.

This is a stronger audit of the **execution of the tests**, not a new product-performance win. The original experimental falsifier and the old failed/false-green observations remain preserved without modification.
