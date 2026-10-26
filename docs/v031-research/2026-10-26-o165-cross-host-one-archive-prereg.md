# O165 — Preregistered single-archive Linux→macOS filesystem topology transfer (2026-10-26 UTC)

**Status: prospective hypothesis only; no result is asserted.** This is a science/evidence lane stacked on O162 PR #500 (base `34fe4b6dc5cdf9e0bbe8cd61867f61b5c478ce15`), not a Reader/Builder/product patch or release request. Published CMPCT remains v0.30.0, revision-24 stable floor.

## Decision question and stronger control

O162 proved installed Builder→Reader same-host strict POSIX tree equality on Ubuntu and macOS, but independently generated different archives and observed 3 symlink-mode differences in separately constructed source trees. This does NOT prove that *one Linux-produced archive's bytes* can be transferred to macOS and reconstructed with an equivalent portable tree. O155 distinguishes inode-renumbered hardlink groups, file bytes, raw symlink target/name bytes and POSIX entry modes. Preserve O155 unmodified.

Question: Does **one genuine Ubuntu-built revision-24 CMPCT archive**, passed to a physically separate macOS job via GitHub Actions artifact without rebuilding, verify and extract on macOS with all source properties representable under an explicitly narrow cross-host projection? Compare against the Linux sender's actual source witness; never synthesize a second source on macOS.

## Falsifiable predictions (registered before instrument/CI)

1. The sender validates inherited Builder `663ef0922992b1fbb8f19e6eea88d55c10a56044`, Reader `e716233403dabd0966863c45635e18fa5ac6afb8`, O155 `0bef46e8d1944ff327063c66edc9bbc29fa58481`, and O162 harness `ed352ad593a41ed541b3cbb6774c8c5f447f3741`; installed CMPCT must be outside the source checkout. It builds O162's unchanged 10-entry fixture with one physical hardlink group and three symlinks. Same-host Ubuntu strict tree witness must match on actual r24 create/verify/extract.
2. The artifact-distributed archive's **SHA-256 and exact bytes** match the sender receipt on macOS, the archive verifies with installed CMPCT, and extraction preserves all member names/raw symlink targets, regular payload hashes, file/dir modes, root mode, and in-tree hardlink equivalence classes.
3. A separately labeled **portable semantic projection** removes only the `mode` field from entries whose physical `type == "symlink"`. It changes no original O155 manifest, legacy comparator, product or release contract. The producer's and receiver's projected manifests must match exactly. The unprojected O155 manifests and every physical symlink-mode delta must be preserved even if the direct strict comparison is red; do not reclassify that red as exact physical equality.
4. As a differently rooted negative control, after a successful macOS extraction sever the restored hardlink into an independent file with identical payload and mode. The portable projection must then change while the two files' bytes remain identical. The source archive SHA must remain unchanged.
5. A mismatch in any non-symlink-mode property, archive identity, installed source identity, physical hardlink, verification/extraction, or hostile negative control **falsifies** the portable roundtrip claim. Runner/dependency failure is infrastructure inconclusive, not product failure; log the full error and leave no PASS claim.

## Alternatives and PARETOBONK

- Same-host re-runs already answered by O162; low new information.
- Rebuilding on macOS introduces input/metadata confounding; rejected.
- Rewriting O155 to normalize all OS differences hides physical fidelity and destroys comparability; rejected.
- Broad xattr/ACL/timestamp cross-host projection cannot be priced until exact supported name/type/content/topology transfer is established; lower value and overlaps owner lanes.
- Simple receipt+one producer and one consumer is the cheapest decisive court; shell checksum alone would not establish installed Reader semantic preservation.

## Costs, evidence and independence

Expected one small r24 archive and two installed jobs; recorded archive bytes, checksums, source/receiver strict/portable manifests, source Git blobs, hosted run/job/artifact IDs. Process startup and CI latency are not product performance measurements. No compression improvement or release/parity credit. The strict physical witness remains exact and different from the portable semantic projection. No frozen experiments, thresholds, comparator semantics, release policy or product implementation may be modified.

## Concurrency

Checked current open PRs/branch ownership: O155 #496 and O162 #500 are the related provenance parents; current O160/O164 Win32 ZIP names, O149/O150 ZIP staging and O163 native CDC custody are separate surfaces. No competing one-archive Linux→macOS O155 topology transfer PR found at preregistration. Do not write shared `docs/discovery/STATE.json`, whose existing PR #440 owns reconciliation.

**Minimum decision-changing evidence:** source-identical hosted Linux producer receipt + authentic macOS consumer receipt showing PASS or explicit FAIL, exact-head Jobs and immutable artifact identity. Even PASS remains research/evidence, not release permission.