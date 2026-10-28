# J24P01 — final cross-host fixed-wire S_PACK conformance result

**Date:** 2026-10-28 UTC. **Decision:** `THREE_HOST_SOURCE_EXACT_INSTALLED_PACK_CONFORMANCE_PASS` for the *original fixed #307 RAW and Zstd r24 PACK archives*, only within the scope preregistered in `2026-10-28-j24p01-pack-crosshost-prereg.md`. This is research/conformance evidence and does not promote Reader, Builder, native ABI, r24 format or v0.30.0/v0.31 release.

## Source and experiment custody

- Published reference `main@80c358f8824ec1b20d349c92ed94c898090969b0` v0.30.0/r24.
- Original scientific owner: PR #307 at `256a263748b9f65b4bc00dd572799e4f00ae06e7`; original Builder-independent frozen `tests/conformance/v24-pack.json` has exactly two archive bytestrings, RAW 777 B and Zstd 764 B. No fixture regeneration or changes.
- Preregistration frozen **before** instrument at commit `07e8be776740e7a2dcf4d8afe31e29c9e9b0a7e0`.
- J24P01 first 3-host code head `06d8e62a5983e642b5b202cd83fb37738bdd3283`: [run #40769201049](https://github.com/FCMO-AI/.CMPCT/actions/runs/40769201049) **not a 3-host pass**: macOS aborted *before* Reader test because runner lacked `sha256sum`. CI preserved artifact #12852145931. This was an **infrastructure utility** red, not evidence of a PACK decoding defect.
- Repair preregistered **before** editing workflow, commit `b0ccf822f9226ab3334bca8018a799842a2e7d17`: replace solely the manifest hashing command with Python stdlib SHA-256, unchanged bytes/evaluators/criteria.
- **Actual product-science HEAD** `71d1cedb9007f0f4f866b6fe22a9146614bf3d8b`; [exact-head GitHub Actions #40769314911](https://github.com/FCMO-AI/.CMPCT/actions/runs/40769314911). `src/`, `native/` and frozen `tests/conformance/` are identical Git content to source owner #307.

## Original result-bearing jobs and artifacts

| Host | Job ID | Result | Original artifact ZIP, SHA-256 |
|---|---:|---|---|
| Ubuntu 24.04 | `123102202692` | **SUCCESS** | #12851721569, `35fedba2b86ade70d2fc67314c5ac66ff880b39ce5fb1b032009a93d6c5edbf7` |
| macOS 14 | `123102202644` | **SUCCESS** | #12852565770, `7d5ea9bcecd7d52ec3a8fbec6aff17fb649ce6e668d7f03e72f77f63838b47e2` |
| Windows 2022 | `123102202137` | **SUCCESS** | #12852441292, `d5b9bbd64223f3f7481244bfdf3e3f5fec34f2df547a1e7c081560c10c0c3461` |

**Verified by direct inspection of all three original job logs and GitHub artifact metadata** (separate from trusting the PR label): each job prints `{"head":"71d1cedb9007f0f4f866b6fe22a9146614bf3d8b","status":"PASS","vectors":["pack-raw","pack-zstd"]}` and `PASS: independent physical RAW/Zstd PACK decode, 8 members, two indexes each, forged receipt rejected`. The detached referee does not import the CMPCT product and reads the original wire using external `zstandard`, Python `struct`, `binascii`, `hashlib` and `msgpack`. It checks both duplicate compressed indexes, physical framed blob identity/CRC/SHA-256, all four named member ranges per archive, duplicate owner slices, frozen selective probes, and rejects a deliberately fabricated digest receipt.

Each product court additionally requires installed `reader.py`/`codec.py` source equality, correct imported location outside checkout, complete `read()`, selected `read_range()`, `verify()`, `extractall(metadata=False)`, refusal of physically corrupted PACK bytes and `preflight_archive()` refusal of an index-rehashed malformed PACK slice.

**Scope:** two archives, eight member-reconstruction cases *per host*, two codecs, three platforms. Three fake receipts in total (one per host) rejected. In a subsequent independent off-host audit, all **three original GitHub artifact ZIPs were downloaded**, their complete ZIP bytes SHA-256 matched GitHub's published digest, every entry passed ZIP CRC, and their recorded frozen archive SHAs, all eight logical member identities, exact Git source blob identifiers and installed module hashes agreed across all hosts. The detached referee had already run independently in each job; the off-host audit compared **original evidence** without importing the CMPCT product. One local off-host audit-script assertion initially checked dictionary keys rather than digest values; corrected without changing source artifacts, invariants or accepted results.

## Honest negative and unsupported claims

- No product implementation changed; no performance, RSS, startup, native ABI on macOS/Windows, large ownership/amplification, filesystem aliasing, recovery, encrypted/split formats or release claim earned.
- The authentic signed-malformed **ordinary** Python `S_PACK.read_range` acceptance defect is already established by issue #599 / PR #598, and fix candidate owner is #601. **This experiment only proves strict preflight** rejects the mutation, not that ordinary reading is repaired. The distinction is mandatory.
- The initial missing `sha256sum` was repaired without changing evaluator/fixture or threshold. The general CI and frozen performance gates for this branch are separate and may be red/pending; one green specialized court does not imply an overall green release.
- The exact original artifact ZIPs remain under the hosted run; the GitHub-provided digests above are archival metadata, not independent off-host hash recomputations.

## Counterfactual and next highest-value action

Existing #307 Linux proof could not prospectively establish real Windows/macOS install behavior. A small actual 3-host source-bound test, rather than a new portable codec, was the cheapest honest missing evidence. The first macOS failure could have been avoided by using cross-platform stdlib SHA from the start; this teaches an instrument-level lesson but does **not** justify modifying the Discovery Engine from a single incident.

Transfer the conformance result to #307, keep #314/#598/#601 owner boundaries intact. The next true product frontier is integrating the existing malformed PACK selective-range fail-close code with current Reader and generalized source-fingerprint/CI under unchanged parity, not adding a redundant S_PACK parser in this research branch.

**Conclusion:** source-exact installed Python frozen-wire cross-platform **PASS 3/3** at `71d1cedb`, strictly bounded to original RAW/Zstd shared PACK semantics. **NO MERGE / RELEASE / VERSION PROMOTION.**


## Subsequent off-host original-artifact custody audit — 2026-10-28 UTC

Three uploaded **original** GitHub artifacts were retrieved as unchanged ZIP files and audited independently in a separate Python environment with standard `zipfile`, `hashlib` and `json`, no CMPCT import. `ZipFile.testzip()` returned no corrupt entry in any artifact. Recomputed full original ZIP SHA-256 values exactly matched GitHub metadata: Ubuntu `35fedba2b86ade70d2fc67314c5ac66ff880b39ce5fb1b032009a93d6c5edbf7`; macOS `7d5ea9bcecd7d52ec3a8fbec6aff17fb649ce6e668d7f03e72f77f63838b47e2`; Windows `d5b9bbd64223f3f7481244bfdf3e3f5fec34f2df547a1e7c081560c10c0c3461`.

For each ZIP the `head.txt` is `71d1cedb9007f0f4f866b6fe22a9146614bf3d8b`; both fixed archive SHA-256 values agree across all three platforms: RAW 777 B `bd2557edc2c5db84ba125c6ba33627ddc72dd740c38a5c4744c0686c48c441cf` and Zstd 764 B `ced012e93917ac3c1e011aa503a601ff448237db88b4c4e920454a3cf3e6425c`. All eight logical member SHA-256 observations agree host-to-host, as do source `reader.py`, `codec.py`, immutable original manifest Git blob ID, tool Git blob IDs, and each recorded adversarial/referee PASS. `referee.json` in each ZIP has exactly `forged_receipts_rejected=1`.

**One interesting difference:** original manifest *text-file* SHA-256 is `c43802d1...` on Ubuntu/macOS but `f821bcc3...` on Windows. This is consistent with platform checkout CRLF translation, **not an observed difference in embedded original CMPCT archive bytes** (whose exact SHA is invariant). No claim of proven CRLF causation is made without independent raw-manifest inspection. The executable tests passed under their respective installed Python 3.12 versions.

Original ZIP bytes and a reproducible independent audit script/output were preserved in the activation evidence bundle; off-host receipt JSON SHA-256 `9ef9c98fe4c26f7b463684980e36325be489b0fc51b47816f00087fe7a075dfc`. The audit's first draft had an instrumentation-only typo testing `dict` keys rather than member SHA values; it failed locally before evidence publication, was corrected to test `.values()`, and then all hosts passed. This local typo did not change the GitHub-hosted experiment or any original receipt.
