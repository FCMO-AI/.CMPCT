# J24B07 — signed nonnegative hardlink alias undercounts extraction quota

Date: 2026-10-28 UTC
Status: **DECISIVE HOSTED SCIENTIFIC COUNTEREXAMPLE / NO PRODUCT FIX, MERGE OR RELEASE**.

## Frozen prospective scope
[Immutable preregistration](2026-10-28-j24b07-hardlink-zero-quota-prereg.md) commit `66c06567cc67c3924d2f539adbb4c7dafaa34ed4` landed before court or referee source. Exact parent product candidate is [J24B06-R1 #690](https://github.com/FCMO-AI/.CMPCT/pull/690) `adcf38cb5be022567c1faf6538aefeef2f6b72de`. Released v0.30.0 `main@80c358f8824ec1b20d349c92ed94c898090969b0` is unchanged.

Question: does #690's strict integer/nonnegative logical-length guard *fully* enforce the sum of reconstructible member lengths for genuine hardlinks with internally reauthenticated but contradicted alias sizes?

## Primary direct evidence
[Exact-head GitHub Actions #40741844935](https://github.com/FCMO-AI/.CMPCT/actions/runs/40741844935), `pull_request` science source HEAD `a71e5adc29aa39799aad41b463c18dbf5231ba98`, **SUCCESS on Ubuntu 24.04, macOS 14, Windows 2022**. Installed candidate wheel on each host. Original execution/scientific logs:
- Ubuntu job `123005196565`, original artifact `12838813539` (`j24b07-ubuntu-24.04-40741844935`, GitHub ZIP digest `sha256:1dc1092cb1dae0f3fd0509434f15a1646d29b7cb38afbf4dcdbbbe25458dbf1a`);
- macOS job `123005196870`, artifact `12840400672` (digest `sha256:f0920478b35a3baa0b79de0a432a818958e1416a89bd0b09b740cee8e028ab40`);
- Windows job `123005195987`, artifact `12839741866` (digest `sha256:51eb15be4b3c3e9d3d18d16f959cb44653b1c3fba28ba759a4f5d11115b332e8`).

### Measured behavior on each of all three hosts

| Authenticated index case | Sum declared for non-directory entries | max_bytes | Two visible output file lengths | Source exact? | Decision |
| --- | ---: | ---: | ---: | --- | --- |
| Genuine Builder hardlink alias=8192 | 16384 | 8192 | No output created | yes | Correct refusal |
| Genuine Builder hardlink alias=8192 | 16384 | 16384 | 8192 + 8192 | yes | Correct acceptance |
| Mutated hardlink alias=0 | 8192 | 8192 | **8192 + 8192** | yes, rehashed indexes | **Logical quota undercount by 8192** |
| Mutated hardlink alias=1 | 8193 | 8193 | **8192 + 8192** | yes, rehashed indexes | **Logical quota undercount by 8191** |

Both forged-size alias cases were also refused by the active guard when presented a limit one byte below their **declared** total; this proves the scan executed, but measured the wrong semantic value. Genuine target and alias are the **same physical inode** after extraction on each host; this does **not** assert 16384 unique physical disk bytes. The public `max_bytes` contract currently counts *all non-directory logical member sizes*, so the accounting discrepancy is meaningful in that explicit contract.

All mutant `verify()` calls returned 2 and `read_range('zz-alias.bin',0,1)` returned the real owner's first byte even for an alias declaring zero. The logical size inconsistency is accepted by the Reader, independent of cryptographic hash correctness.

### Independent controls

The research court uses actual first-party Builder to create the source archive, changes only signed index fields for the alias (plus explicitly documented Windows Builder `K_FILE`→`K_HARDLINK` normalization), compresses and rehashes primary and tail revision-24 indexes, preserves the physical region and emits source/physical hashes and byte-exact extracts.

A distinct referee imports **no CMPCT code**. It parses the binary header, primary and tail index, footer, Zstd and MessagePack, checks the hashes, compares the physical record bytes and unchanged original owner metadata, rejects any other index-field drift, and compares actual extracted physical files/inode equivalence. It passed on **3/3 hosts** and deliberately rejected **8/8 forged receipt variants per host, 24/24 total**.

The original experiment spent `0.004724s` (Ubuntu), `0.060651s` (macOS), `0.019520s` (Windows) on the small local court. These are **not comparable performance benchmarks**, process starts, cold-open, RSS or complete large-archive workloads. No product-speed credit.

**Source-file custody resolved:** Ubuntu/macOS installed Reader working-file SHA-256 is `4db8a6350f1389216222ceabceb8bbeb7c26f9cd34480c9e18b9ab608409d24b`; Windows working-file SHA-256 is `74ed9ec1b41bd61896659b210ca5ebb31d61e4e71cc331ed4edfbcfedc6c3d05`. The *exact same Git-tracked Reader blob* `20f6e257a07a61a4c1aebe23ae23e4109d6c41c8` was fetched at the parent HEAD and separately SHA-256-digested with its canonical LF bytes and LF→CRLF-only transformation. **Both digests match these two observed host hashes exactly**, proving line-ending normalization as the entire observed source-byte difference, not a source logic difference. Each hosted referee additionally confirmed installed source bytes equal that host's checkout; every host checked the exact Git HEAD. Preserve host worktree byte fingerprints separately, but the semantic source identity is common.

## Activation-local third-root reconciliation (separate from hosted court)

Downloaded all three original hosted ZIP artifacts and confirmed their published GitHub ZIP SHA-256 digests exactly. A **third independent implementation** outside the repository instrumentation used stdlib binary framing, MessagePack and the host `libzstd.so` via `ctypes` (not CMPCT or the hosted Python `zstandard` referee), then audited the **nine revision-24 images** (one control plus two reauthenticated mutants per OS), index SHA-256, footer structure, unchanged physical regions, all six logical quota undercounts and the extracted payload bytes.

The source 8192-byte payload SHA-256 was exactly `ffc819eb140590546ab1532e2024f060e540d2d9b2527c512186fc1f86aa7b81` on **all three hosts**, and the **entire physical CMPCT record span** SHA-256 was exactly `838218860939c2186d1f1d0e2b6ead241f33ed4e28ad85d86ecd87d90f2e6c73` on all three hosts, despite the documented Windows Builder alias-kind difference. This strengthens same-input/same-physical-source control without asserting original whole-archive byte identity (POSIX control 9096 B; Windows control 9080 B due metadata differences).

Adversarial self-critique: this local third-root audit **initially accepted a forged control-receipt SHA** because the checker failed to compare that receipt field with the parsed original. That false-green was found by an independently constructed artifact mutation, repaired without modifying any CMPCT product/evaluator/hosted result, then **4/4 distinct tampered artifact variants were rejected** (control receipt SHA, signed compressed index byte, extracted alias payload byte, Git source HEAD). This local replay supplements, never replaces, the original hosted detached referee's **24/24** forged-receipt rejection. A downloadable user evidence bundle with original archives and scripts was created in the activation; its bytes are not a GitHub source of authority, so the original GitHub Action artifacts remain the durable primary receipts.

## Decision and strict scope

**CONFIRMED_NONNEGATIVE_HARDLINK_LOGICAL_QUOTA_UNDERCOUNT — three-host installed science PASS; reject a claim of *complete* extractall max_bytes enforcement by #690 alone.** The previous signed-negative-size failure and its narrow #690 patch remain a distinct confirmed fix. A nonnegative integer alias length can still contradict its recursively owned physical size; SHA-256 proves index-byte integrity, not valid semantic lengths.

No proof of malicious cryptographic forgery, RCE, path traversal, 16384 physical storage bytes, full raw-byte expansion through pipes, or general reader acceptance across all kinds. This is a small source-exact deliberate index mutation. Windows source Builder sometimes records hardlinks as duplicate K_FILE; the test explicitly converts that alias row in the authenticated mutant. That different prior Windows defect is not counted as a new product implementation or hidden.

The response belongs to #690 (extractall owner), #610 (hardlink alias consistency), and #569 (composed Reader owner). Their exact branches and current state must be reread before any composition. A possible route is memoized, cycle-safe alias→final-owner resolution and equality of logical sizes during admission, maintaining a single O(files + alias edges) traversal and avoiding repeated deep chains. Measure 65k/262k owner cold-open CPU/wall/RSS and check signed checkpoint recovery and hardlink cycles; **no such repair or complexity result has been implemented or measured here**. A transactionally staged output byte meter has different costs and authority, and cannot be inferred.

## Scientific lesson / continuation

A cheap positive-value range/type oracle did not prove that a number accurately describes reconstructible output. **Counterfactual earlier discriminator:** derive the actual materialization length of each alias from its terminal owner and compare with authenticated descriptor before relying on it for resource accounting. This lesson is supported by J24B04's prior accepted signed alias-size contradiction plus the current three-host quota consequence; no Discovery policy/STATE update is warranted because shared state is owned by #574. Do not extend the same family into renamed microvariants without new decision-changing information.

## CI truth and release debt

Scientific run `40741844935` source exact and three-host **SUCCESS**. General CMPCT Tests, CI Topology, Engineering Evidence and broader parity for the *documentary successor commit* are independent, not implied green. PR #690's own targeted three-host run `40734382594` **SUCCESS** for its signed-negative fix. Its official core ZIP parity run `40734382793` **FAILED** on four inherited release fingerprint/surface-source tests (798 passed, 4 failed); no parity performance artifact was generated, so do **not** count it as a measured performance regression or an earned release pass. **Independent source-exact baseline discriminator:** [released main CMPCT Tests #37243801009](https://github.com/FCMO-AI/.CMPCT/actions/runs/37243801009), job `111557590255`, at `main@80c358f...` failed the **exact same four historical tests**, 782 passing / four failing on 2026-10-04 UTC, before either J24B06 or J24B07 existed. Thus those failures are inherited release-custody debt, not a causal code regression introduced by the current quota research; release parity remains unearned. Product merge/release remains blocked by full inherited gates. No frozen comparator/evaluator/threshold changed. No Builder/Reader/native ABI/format/version/product code modified in this PR.

Outcome: evidence-backed **science** and narrower product-boundary claim, no product win. Preserve both the confirmed predecessor fix and the remaining breach in permanent owner-linked project evidence.
