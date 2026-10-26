# O143 — ZIP export ordinary-output failure-atomicity: decisive installed-product negative

**Date:** 2026-10-26 UTC. **Decision:** `FAILURE_ATOMICITY_FALSIFIED_TWO_HOSTS`, source-exact scientific negative, **no product fix**.

## Scope and authority

- Canonical v0.31 development remained `4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; shipping release v0.30.0 / format r24 unchanged.
- This independent O143 scientific lane stacks on O140 owner [PR #488](https://github.com/FCMO-AI/.CMPCT/pull/488), exact parent `d8b69758dbcbb66fe28fa7cf59598916df160d2d`. The unchanged installed Reader Git blob is `e46e6121842d485cb209118576ebf3ba3719080d`.
- Prospective [hypothesis](2026-10-26-o143-zip-export-failure-atomicity-prereg.md) committed at `d66f7b0883a56af03ff90f1de683ef64437b0125` before implementing either experiment.
- Result-bearing source head: `4cf89be369edc64e2c55146398b95c41ecd3e098`. [GitHub Actions 40264433185](https://github.com/FCMO-AI/.CMPCT/actions/runs/40264433185), Ubuntu 24.04 job `121383582190` and macOS 14 job `121383582270`, both SUCCESS. Exact-head installed pip package outside checkout. Test Git blob `b9e54b1964de8a3a9476dcff4ae2f0b2f848f3cd`.
- Raw artifacts: Ubuntu `12625802359`; macOS `12625454400`. Each stores HEAD/blob receipts, raw pytest/JUnit, independent observation audit and original CASE records. Each platform: **2 PASS / 0 SKIP / 0 FAIL**. Total: **4 negative-science cases successfully reproduced**. These PASS counts mean the **defect occurred**, not that output publication was safe.

## Direct measurements

| Test | Source control | Input rejection | Old target (valid ZIP) | Failed export outcome | Hosts |
|---|---|---|---|---|---|
| Independent RAW CRC | Frozen 386-byte r24 golden, archive SHA `5d1638fbe6e7b185dbbb04d5cf37c6a49dd90bad8bebc156fa072a3195c1893d` | Ordinary `CMPCT.read("raw.bin")` refuses with `OSError: blob integrity failure` after changing exactly one physical RAW record CRC32 byte | 190 B | **0 B**, SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, ZIP destroyed before first file | Linux + macOS |
| Two-member late physical corruption | Genuine Builder-produced separate `a_good.bin` and `z_bad.bin`; good passes, only later physical RAW payload byte changed | `CMPCT.read("z_bad.bin")` raises `OSError: blob integrity failure` after good file read succeeds | 190 B | **98,344 B**, first `PK\\x03\\x04` local entry and `a_good.bin`, no valid ZIP central directory; `zipfile.is_zipfile` false | Linux + macOS |

The frozen source `tests/conformance/v24-direct-codecs.json` is Builder-independent, Git blob `d10b7dab9126d39e819a74279c186363a163f2ef`. In both cases, the original archive remains a separate source file, target is an ordinary regular ZIP file with valid prior content, and the same reader fully exports independently decoded clean controls before corruption. The science deliberately does **not** use Deflate-stream direct reuse (owned by #284), own-source aliases (owned by #483), or FIFO/nonregular leaves (owned by #488).

The second Builder-generated archive SHA differs between Ubuntu and macOS due to underlying metadata; that is **not** cross-host archive identity evidence. What replicates is the same causal failure and the same observed corrupted target size. Original valid 190-byte ZIP hashes also differ across host local ZIP timestamp metadata. Preserve that difference; do not claim bit-identical full archives across hosts.

## Causal interpretation

The output is opened directly for writing **before** all member reads, integrity checks and ZIP central-directory publication complete. On a read failure, `export_zip()` raises after permanently altering an existing regular output file. Already-open source/destination alias and static special-output checks do not supply a transaction for valid regular destination outputs. The first result destroys a 190-byte ZIP at zero emitted bytes; the second produces a large incomplete ZIP and loses the prior valid ZIP. A managed exception does not imply failure-atomicity.

**Decision-changing distinction:** Testing only CRC/Deflate validity or rejecting special destination kinds cannot establish normal-file output atomicity. The next product question is what publication contract CMPCT should preserve when replacing existing regular ZIP outputs, including hardlinks/inodes and the handling of mid-write ENOSPC or I/O errors. A sibling temporary staged ZIP plus verified commit/rename is a plausible alternative, but it changes successful replacement identity and temp bytes; a preverify-then-in-place writer cannot guarantee recovery from output I/O failures. Both alternatives require honest total-system pricing and independent verification.

## Limits and negative knowledge

- These are explicit corruption cases with a stable filesystem namespace, **not** concurrent path swaps, power-loss recovery, input mutation after preverify, Windows, ZIP64 count limits, network filesystem behavior or disk-full injection.
- Python standalone `zipfile` is the independent output interpreter; Builder-generated second case is product-regression evidence rather than a frozen independent format oracle.
- The scientific workflow is deliberately **negative** and expects the baseline defect. Any repair needs a separate positive court that requires an intact prior destination under failure. Do **not** change O143's historical assertions to make a repaired implementation look green; retain the original result and refer to it.
- No product code changed; no format, version, release lock, benchmark gate, discovery policy, or frozen historical evaluator changed. No CPU/RSS/create/export throughput, temp-I/O, or official parity evidence earned.
- The exact-head specialized hosted result is authoritative for O143. General/native/fuzz/engineering/performance check statuses on subsequent documentation-only heads need independent verification; scientific green ≠ release.

## Discovery / counterfactual

The source's direct `open(out, "wb")` before the member loop is a prospectively recognizable cheap warning. The cheapest decisive first test was one known-corrupt frozen RAW member against a *preexisting valid regular ZIP*, not another FIFO or same-inode source test. The second later-corruption case increases decision value by proving a partial-ZIP publication failure **after successful bytes have been emitted**. This is a transferable test-design lesson, not sufficient repeated evidence to rewrite the normative Discovery Engine. No claim of concurrency collision or product repair.

## Owner handoff

- O140 #488 and O135 #483: special-leaf and own-source guards should be retained, not mistaken for full publication atomicity.
- Direct-Deflate export owner #284, ZIP64 owner #260: O143 touches a separate non-direct output-lifecycle gap expressly declared in #284's original PR and should be independently accepted/assigned.
- Next cheapest repair court: frozen RAW first-read failure + two-member mid-read failure against *existing regular ZIP*, then forced short writes/ENOSPC, and at least same-input clean ZIP content/method/physical Deflate reuse, output inode/hardlink/cross-platform semantics and temporary storage accounting.
- Draft research-only [PR #489](https://github.com/FCMO-AI/.CMPCT/pull/489) must not be merged as a product security fix or assigned release credit.
