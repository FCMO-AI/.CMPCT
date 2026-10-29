# J24G32 — physical committed-journal → legacy ZIP cross-layer result

**Decision: PASS on the preregistered narrow semantic transfer; NO product/release promotion.** This is source-bound, real hosted evidence, not an inferred successful result from the Reader code. The scientific question changed from improving ZIP date helpers to validating that a committed generation is actually the information source consumed by an independent archive format. The next follow-up should be hostile mutation/audit controls or a substantially different product-convergence owner; not another ZIP calendar variant.

## Frozen boundaries
- Preregistration at `db008a224d6350a0d0fc62c31d1d2b4454d72153`, before instrument and CI.
- Exact result-bearing test/workflow HEAD: `f92d6527f9243d5768996fee884f8ec4e7d673b0`. Unmodified Reader blob: historical `e716233403dabd0966863c45635e18fa5ac6afb8`; composed `cd6a2971396d6fe02a1d7f460d850107b3dcc397`. Writer transactions blob same on both: `964f4dcf8c25cdd5885b6c43bbf3d92d16dd252c`.
- Result-bearing [Actions #40823020899](https://github.com/FCMO-AI/.CMPCT/actions/runs/40823020899): Ubuntu 24.04, macOS 14 and Windows 2022 **3/3 SUCCESS**. Every host executed three independent processes: released Builder/Writer and historic Reader, composed Reader, and separate stdlib-only ZIP auditor. All used actual installed packages, not checkout imports.
- Original provider artifacts: Ubuntu `12875800460` digest `sha256:8eee96ed0a2011211c5dcc35dd8e6de1f031fc0da4abca509565e3203cb33e44`; macOS `12875063581` digest `sha256:c3836845bc90a8cf7b3a028f58ed8a879ea3a3e418a4ae1d98d65f2c4594252a`; Windows `12875940041` digest `sha256:57cb27a16cfa1a92d32788f24ca36a41c3ac949d33102f1b8e2cc4083f755aba`.
- Raw logs and original physical .cmpct/.zip/manifest/receipt/audit files are in those provider artifacts, not only this narrative.

## Outcome and controls

Each host constructed an authentic 3-file Builder archive and committed **three** real journal operations: rename `alpha.txt` to Unicode `moved-α.txt`, delete `drop.bin`, and update `edit.txt`. Effective index depth 3. The expected live logical members were:

| Live member | Logical size | SHA-256 |
| --- | ---: | --- |
| `moved-α.txt` | 3,158 B | `ee5350a08c6f69ef65c38959586c1b6dbd92c329e47c62ed16bd5fe3ea2793a5` |
| `edit.txt` | 9,501 B | `fa1217b2a07a3fe5886ea141bee7eff47ba1e73d9efe5c77924bdc7690456426` |

Both Readers on each host read and verified these contents and exported a 729 B ZIP. A third stdlib-only process independently verified exact content SHA-256, CRC32, UTF-8 name flag, no duplicate/stale/deleted names, and that the ZIP reproduced the latest generation rather than the initial primary index. **Both historical and composed ZIPs were byte-identical on the same physical source and OS**, including a copy with 27 deliberately uncommitted nonfooter bytes appended after the last committed footer. The resulting ZIPs of committed vs orphan-tail copies were byte-identical, so orphan-tail bytes did not leak into output. Each host additionally ran installed Info-ZIP `unzip -t` successfully on the four ZIP outputs (12 total external checks).

Per-host source physical lengths/hashes from raw provider logs (same input to both Readers *within* each host):
- Ubuntu: archive 1,975 B / `5171804a1276fbc3b74c4c9e4d37ba039fdca27db98402cfdc7e8476d66603eb`; legacy ZIP 729 B / `2e00244819786368b53dcb24bbf76b923580ed73b0f1898e8062cbb973eab543`.
- macOS: archive 1,977 B / `92fc541e948afb843ec1f4abc20c01090f97f22af8ab365d0647eb8aa3f6255a`; legacy ZIP 729 B / `2e00244819786368b53dcb24bbf76b923580ed73b0f1898e8062cbb973eab543`.
- Windows: archive 1,967 B / `569ac264e3ffbf3665c65184f1e8ffd1b1bb9dc7e74581eb32220aa6ae210eb4`; legacy ZIP 729 B / `d02648a95544e21450693902ada555893bb175af9e1084aaafb06239a067873d`.

**Negative/self-critique:** Different hosts generated *different* CMPCT physical archive bytes despite identical logical payload hashes; therefore do **not** claim cross-host deterministic archive identity. Windows' ZIP hash also differs from POSIX and no causal byte-field assignment has been proven. Both outputs are exact under same-host pairing and independently decoded, but a cross-host ZIP determinism claim would be false. Info-ZIP count 12 checks shares four outputs per host and is not twelve independent work distributions. The uncommitted tail is an intentionally unauthenticated append, not corruption of an authenticated generation. All results are tiny inputs; no ZIP64, nested archives, symlinks, hardlinks, sparse holes, hostile crash/collision race, metadata full fidelity, CRC tampering or genuine performance/RSS conclusions. The stdlib audit belongs to the same experiment test file and is not a separately developed complete CMPCT physical wire parser.

## Decisions / remaining product debt
- **Passed, scoped:** committed update/delete/rename effective namespace and content transfer to ZIP under three actual runtimes, same-host Reader backward parity, Info-ZIP acceptance, and identical recovery from a simple orphan tail.
- **Not measured:** meaningful CPU/wall/RSS/temp-I/O; 4 GiB ZIP64, general filesystem topology, malicious concurrency, direct Deflate trailing bytes and robust crash durability.
- **No release credit.** Original historical workflows retain intentional SHA-bound failures when a candidate Reader blob changes; generic General Tests had inherited fixture/attribution/release-custody failures. Do not change historic comparators.
- **Counterfactual discriminator:** construct the multi-generation source first, then compare external ZIP, before writing new Reader logic. It would have detected a stale-index export bug cheaply if present. Only one episode; no discovery policy change.
- **Concurrency:** no collision found for this cross-layer narrow experiment, and the branch is stacked on #727 solely for source continuity; #492, #243/#245/#250 and #574 remain respective implementation/shared-state owners. Do not modify their lanes.

Next cheapest independent adversarial check: flip CRC/ZIP name/receipt data in *copies* of hosted artifacts and prove the independent auditor catches all seeded faults without touching the authentic evidence; no product credit from that test. Otherwise close the scientific question and select a different general-purpose product debt.


## Independent physical wire follow-up — J24G32b (local science, not new product credit)

After the hosted result, the **actual original three GitHub artifact bundles** (not reconstructed from logs) were downloaded via the provider and SHA-256 verified byte-for-byte:
- Ubuntu `8eee96ed0a2011211c5dcc35dd8e6de1f031fc0da4abca509565e3203cb33e44`;
- macOS `c3836845bc90a8cf7b3a028f58ed8a879ea3a3e418a4ae1d98d65f2c4594252a`;
- Windows `57cb27a16cfa1a92d32788f24ca36a41c3ac949d33102f1b8e2cc4083f755aba`.

A separate **stdlib + msgpack + external zstd CLI** wire examiner (no CMPCT Reader, Builder, Writer or native library) validated each original r24 header, primary-index decompressed SHA-256, authentic committed generation footer/payload hashes and previous-offset chain (checkpoint plus exactly rename/delete/update), all three source and updated physical blob framing and decoded CRC32/SHA-256, and final ZIP member content/CRC/UTF8/EOCD/modes against the authenticated effective index. It verified the same 340 B primary physical blob span SHA `f865c076ee8ffa854535ab59a5ceb933f9483247265d214f066f1ed67dbb443b` on all three hosts. Source data bytes are not the cause of the archive/ZIP SHA variance.

**Causal field localization (not cross-platform equality assertion):**
- Initial r24 file-row modes are `0644` on Ubuntu/macOS versus `0666` on Windows, faithfully inherited from the respective host's source filesystem. Initial authenticated `fsmeta.owner` is `[1001,1001]` on Ubuntu, `[501,20]` on macOS, and `[0,0]` on Windows. These are *different input filesystem metadata semantics*, so the nominally same logical payloads do not constitute same-semantics byte-identical input.
- Independently decoded classic ZIP central directory has exactly the same file contents, date 2020-02-02, compression methods, CRCs, sizes, and offsets on every host. Windows ZIP differs from Ubuntu's by precisely **two bytes** at zero-based offsets `635,689`, both high permission-mode bytes (`0xa4` vs `0xb6`, corresponding to `0644` vs `0666`). macOS ZIP matches Ubuntu byte-for-byte.
- The physical CMPCT index's compressed lengths vary 398 B Ubuntu / 399 B macOS / 394 B Windows because authenticated owner/mode metadata differ; do not attribute that difference to a codec regression.

**Adversarial auditor self-review and repair:** An initial weak stdlib-only ZIP checker failed to reject a mutation of the ZIP central directory's `external_attr` despite unchanged content SHA; this exposed a **test-oracle gap**, not a product bug. The independent examiner was strengthened to compare ZIP `external_attr` against the authenticated source's effective journal index, independently validate physical blob CRC/SHA, and require coherent EOCD counts/offsets. Its nine *local* hostile mutations of ZIP headers, modes, data and CMPCT header/primary/blob/footer fields were all rejected (**9/9**) with intact controls accepted. This is a local verifier self-test over the original hosted artifacts, not a second hosted product acceptance or complete general hostile-input proof. No original J24G32 preregistration, CI checks, fixed benchmark, thresholds, or product code were altered.

**Transferable discriminator:** Before interpreting cross-host archive hashes as encoder nondeterminism, independently compare the authenticated file mode/owner metadata and physically stored blob bytes. Cross-platform same-content is not cross-platform same-filesystem semantics. In a future test of `reproducible=True` (separately owned issue #353), normalize or fully charge mode/owner differences and compare exact same-semantics inputs before proposing Builder changes.
