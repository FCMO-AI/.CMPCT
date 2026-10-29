# J24G51 — Signed hardlink inode/xattr fidelity falsifier: physical result

Date: 2026-10-29 UTC  
Status: **DECISIVE NEGATIVE FOR CURRENT INSTALLED CANDIDATE; RESEARCH EVIDENCE ONLY**. No product patch, release, format, benchmark-threshold, or evaluator mutation.  
Prospective preregistration: [J24G51](2026-10-29-j24g51-hardlink-fsmeta-inode-prereg.md), committed at `82f41251d6f17f8399b65993ff7e8b94e120a543` **before either instrument or workflow**.

## Exact execution boundary

- Canonical source: `FCMO-AI/.CMPCT`; published `main@80c358f8824ec1b20d349c92ed94c898090969b0`, v0.30.0 / r24.
- Installed experimental source base: [#778](https://github.com/FCMO-AI/.CMPCT/pull/778) `47c9a4d61cd764aa4252cad741f4b22537106c60`; research result-bearing test HEAD: `cb0c5c3267362cd815e86d57a385eaffe1858cc1`, PR [#780](https://github.com/FCMO-AI/.CMPCT/pull/780).
- Authenticated installed module SHA-256 on Ubuntu and macOS: `reader.py = 541eea34a49a6801c5d232daa68a70659c9eb451ab854656356d1e080390c45e`; `validation.py = 0c77dceeac0ae518b2e72f3dad8925c03225e8cb7b81b3f799a3f0c8de41e0eb`; `builder.py = 59e6787feb6ec9005b9ecea298bf39ff2434df81271b020f79f22e7314f18c9b`.
- Dedicated hosted [Actions #40950154805](https://github.com/FCMO-AI/.CMPCT/actions/runs/40950154805): `ubuntu-24.04 SUCCESS`, `macos-14 SUCCESS`. One installed-product physical test per host and independent signed-wire auditor per host. These CI successes indicate **successful reproduction of a product defect**, not passing correctness.
- All project product-source blobs equal inherited parent #778. No independently installed v0.30.0 release wheel was exercised.

## Pre-result predictions and observations

| Pre-registered prediction | Result | Decision |
| --- | --- | --- |
| P1: equal xattrs on true hardlinks survive strict extraction | **OBSERVED on both** | Positive admissible control |
| P2: contradictory signed alias metadata passes structural preflight and strong logical verify | **OBSERVED on both** | No inode-metadata consistency rejection |
| P3: strict extraction reports success but OS-native xattr reads disagree with at least one signed per-path value | **OBSERVED on both** | **Confirmed fidelity/strictness defect** |
| P4: independent regular inodes with identical payload bytes can store distinct xattr values | **OBSERVED on both** | Reject only inode conflicts, not matching-content aliases |

Physical mechanism: the signed revision-24 index contains `a-owner.bin` and `z-alias.bin` as two names for one physical hardlink inode. Their separately indexed xattrs request `owner\x00\xff` and `alias\x00\xfe`. The Reader first calls `os.link` and later applies xattrs by sorted row ordinal. In both hosted systems, the final alias assignment overwrites the owner's value **on the shared inode**. Neither `preflight_archive`, `CMPCT.verify()`, nor `extractall(..., require_xattrs=True)` reported failure. The independently named `b-copy.bin`/`c-copy.bin` are different inodes containing the same logical bytes and retained their own distinct xattrs correctly.

### Raw binary values and platform observations

| Path | Signed requirement | Reconstructed Ubuntu | Reconstructed macOS |
| --- | --- | --- | --- |
| `a-owner.bin` | `6f776e657200ff` | **`616c69617300fe` WRONG** | **`616c69617300fe` WRONG** |
| `z-alias.bin` | `616c69617300fe` | `616c69617300fe` | `616c69617300fe` |
| `b-copy.bin` | `696e646570656e64656e742d42` | identical | identical |
| `c-copy.bin` | `696e646570656e64656e742d43` | identical | identical |

`same_inode=true`, `preflight_accepted=true`, `verify_accepted=true`, `strict_extract_accepted=true`, `at_least_one_metadata_mismatch=true` on each host. `classification=ACCEPTED_WITH_INODE_CONTRADICTION` on each.

The independent referee (imports no CMPCT modules) verifies exact primary/tail physical index decoding and SHA-256, footer, unchanged physical blob region, and equality versus contradiction of sparse records. The reader of this result **must not call those self-checksums a digital signature establishing origin authenticity**.

### Original physical specimens

Both hosts independently started from an identical genuine Builder revision-24 archive SHA-256 `d51a37752ab28aa1c710605b9e522ad9bb69e85df54c3b05d4bb3da6f169`.

| Host | Compatible archive / size | Contradictory archive / size |
| --- | --- | --- |
| Ubuntu | `eeb847c301a6af2ff9198ef39bdbb02a345040f863e2099bea55964bb9698dec` / 1084 B | `dfac012ee9f5a40e413ed4bc0bdf5f251d94d0bc849220dc61b9d944e576f2f3` / 1090 B |
| macOS | `62fb44aa37f452016e0838b472eb94b90e47733c7c0c7e96e31ba9651c2bb055` / 1094 B | `43a5b6d5c24d8a2142162839393ab8dbea5464cd79385090c642926f9308ea7d` / 1100 B |

Both have identical physical blob-region SHA-256 `9fe8fc98a9a064e852e812df734017b37dd36824f913baa3cd7e0ff380d3d59f`, physical body 106 B. Different host-index bytes reflect host-built metadata; no cross-host identical archive claim. Source/test bytes and exact HEAD, raw JUnit, specimen archives, `result.json`, and independent referee outputs are in the retained workflow artifacts.

## Causal interpretation and strongest negative

The defect is *not* cryptographic SHA breakage or content loss: the hashes, bytes and original hardlink topology are correct. It is an impossible **per-name metadata contract** applied to an **inode-owned filesystem property**. A checksum-authenticated per-path table is insufficient proof of physically realizable metadata when multiple paths share one inode.

A stationary genuine Builder tree cannot naturally have two distinct xattr values on one real hardlink inode; this is a deliberate hostile but structurally valid r24 mutation. The test establishes the Reader's failure to reject *inconsistent signed inputs* under its explicit strict restoration option, not routine Builder miscapture. No remote exploit, Win32 ADS equivalence, privileged UID/GID behavior, full filesystem parity, large archive resource cost, or released-wheel reproduction has been measured.

## Counterfactual discriminator / downstream product boundary

A cheap semantic preflight can reject conflicting declared xattr key/value associations across all aliases resolving to the same terminal regular-file inode identity, **before creating the extraction destination**. The stronger correct control must still admit distinct xattrs on different inode owners even when logical content bytes/digests are identical. This principle may transfer to owner UID/GID overrides and per-inode mode/mtime, but those are unmeasured hypotheses, not confirmed extensions of this result.

Other alternatives: stripping the alias metadata would make the existing signed contract weaker, copying the hardlink would violate physical topology, or allowing last-writer-wins without an explicit downgrade violates `require_xattrs=True`. A source owner must decide exact compatibility/error semantics, test multi-hop aliases and hostile input, and verify portability/resource bounds. Avoid duplicating #778/#773 Reader and #757 provider implementation ownership.

## Decision / handoff

**Primary scientific question: decisive YES, negative product behavior.** A new general inode-consistency validation requirement is justified. The cheapest next decision-changing implementation is owned by Reader/preflight integrators; preserve the test as an immutable adversarial regression. This research PR stays OPEN/DRAFT, no merge or release. No shared discovery policy/STATE mutation (owner #574). Product credit: **0**; science/proof debt retired for this narrow contradiction on Linux/macOS.
