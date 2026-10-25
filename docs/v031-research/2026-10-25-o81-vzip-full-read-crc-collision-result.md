# O81 — VZIP full-read CRC32-collision result

Date: 2026-10-25 UTC. Status: **RESULT-BEARING SCIENCE — PHYSICAL CORRUPTION GAP CONFIRMED IN TESTED SCOPE**. Not a release or product fix.

## Exact-source custody
Original r24/v0.31 development `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; Builder blob `663ef0922992b1fbb8f19e6eea88d55c10a56044`, Reader `e716233403dabd0966863c45635e18fa5ac6afb8`, Codec `29526db4203723d83523fc95d074c346b63d7587`. All were checked with `git hash-object` on the hosted checkout. Product was installed into host Python 3.11 site-packages and each imported module path was independently verified outside the repository checkout. No product source changed.

Original hypothesis preregistered **before script** at commit `0b75156001bf9a828d6eb4ed969cde6d8c453a9f`. First hosted attempt [40193021164](https://github.com/FCMO-AI/.CMPCT/actions/runs/40193021164) failed on an invalid test-instrument assumption: S_VZIP file-row SHA is `None`, and authentic source SHA resides in recipe. The instrument was corrected to query unchanged `reader.file_sha256(name)`. No verifier/benchmark/positive case was weakened. Final result-bearing source HEAD **`76a9ad1b14503ebed7c24a18845049e9c23ddd7b`**.

## Direct repeated hosted outcome

Two independent GitHub Actions runs at the same instrument HEAD:

| Truth | Run [40193188582](https://github.com/FCMO-AI/.CMPCT/actions/runs/40193188582) | Run [40193185335](https://github.com/FCMO-AI/.CMPCT/actions/runs/40193185335) |
|---|---|---|
| Result | SUCCESS | SUCCESS |
| Original CMPCT complete bytes | 26,492 | 26,492 |
| Original ZIP complete bytes | 25,868 | 25,868 |
| Original SHA / changed SHA | Different | Different |
| Complete ZIP CRC32 (original vs changed) | **Identical** | **Identical** |
| Skeleton CRC32 (original vs changed) | **Identical** | **Identical** |
| Skeleton physical codec | **CODEC_RAW (0)** | **CODEC_RAW (0)** |
| Valid ZIP member bytes before/after | **Identical** | **Identical** |
| Decoded-skeleton injection `read()` | **Returned changed ZIP** | **Returned changed ZIP** |
| Decoded-skeleton injection `verify()` | **Rejected** | **Rejected** |
| Independently copied and physically changed CMPCT `read()` | **Returned changed ZIP** | **Returned changed ZIP** |
| Independently copied and physically changed CMPCT `verify()` | **Rejected** | **Rejected** |

Hosted raw original artifacts: #12599310341 SHA-256 `08d519371273642e1fe9d06c7b1fc3af846ea1615dfb5233e93ab7d3a20452a0`; #12599375176 SHA-256 `5b846a5a6cd1c258914d428835837d81d683055a04592bf507aa0974e88968f7`. These ZIP artifacts contain the original logs/results, not the modified CMPCT bytes; the experiment itself creates the physical modified copy at runtime. Byte-level reproduction is available via unchanged script and source.

### Witness hashes, original run 40193188582
- Original whole ZIP SHA-256: `a1f24dda781c74f5168cd6de370a5407da7048a525202a8861447e88eb5e391e`.
- Changed valid ZIP SHA-256: `ec5239ed129dde1b8f0ca1076355db4a7be1fcd659e5826674d962f11d9d7338`.
- Original physical CMPCT SHA-256: `ea7d6ab7840adbf84055838b70416cda5fdeb12f312d90fd1bea87005c128a76`.
- Physically mutated CMPCT SHA-256: `9d480f1f128898a96b39668776a3e55b60483f30e652d208a94652f1ae3c914c`.

The source ZIP creation uses current default ZIP member timestamps, so cross-run original ZIP SHA differs; **within each run**, the original and hostile files are identical except for corrected comment bytes. This variation was not disguised as exact byte repetition across executions. A future independent reproduction can freeze the ZIP timestamp prospectively, but the observed collision property and physical archive result already replicate twice.

## Mechanism / claim scope
The ZIP comment offers independent four-byte degrees of freedom. A 32-column GF(2) correction produces a different **valid same-length** ZIP with identical full CRC32. Because the modified tail is included in the VZIP skeleton, its CRC32 also remains identical. The original Builder happened to store the 25 KB high-entropy skeleton as RAW, allowing the test to mutate **only those physically stored skeleton bytes** in a copied CMPCT file, without editing the index, blob header or checksum fields. The ordinary real `CMPCT.read("sample.zip")` returned the different complete ZIP. The stronger genuine `verify()` compared indexed SHA-256 and rejected it. This is a concrete physically materialized difference between **CRC-tier read** and **SHA-tier verify** on the tested archive.

The experiment does **not** demonstrate a cryptographic signature forgery, generalized privilege exploit, silent passage of `verify()`, post-read persistence or all codecs/filesystems. Ordinary unmodified archives remain correct. It establishes that the documented comment `rebuild_vzip has already verified the virtual file's exact SHA-256` does not match this full-read path's actual guarantee.

## Counterfactual and decision
The cheapest earlier discriminator was code inspection of `codec.rebuild_vzip` (CRC/size only) together with the early S_VZIP return in `Reader.read`. But code inspection alone would not demonstrate physical archive tamper feasibility under existing blob checks. The two-stage CRC-preserving decoded oracle followed by actual RAW skeleton byte tamper provided strong independent evidence without product modification.

**Decision-changing:** full `read()` is not inherently SHA-authenticated for this VZIP representation; `verify()` remains stronger. Appropriate next fork belongs to Reader/product owners: (A) explicitly document fast CRC-tier `read` and expose opt-in SHA-tier reads; (B) apply SHA verification in `read` after measuring CPU/latency costs on actual VZIP workloads; or (C) strengthen physical ownership/proofs in a representation-agnostic way. Do not call the research finding a release-ready fix or silently spend the performance gate. O79 #436 is a related but **different** selective-range SHA proof; notify its owner because an explicit integrity-tier API may be reusable.

No Discovery Engine policy change earned. `docs/discovery/STATE.json` is a staleable global cache and was not modified because the durable result lives here and the draft PR. No overlapping source writes or discovery claims observed. No merge/release/version/format changes.
