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
