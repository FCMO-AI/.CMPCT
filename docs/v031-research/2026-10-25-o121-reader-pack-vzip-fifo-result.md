# O121 — Authentic installed Reader S_PACK/S_VZIP FIFO court: CONFIRMED scientific negative

Date: 2026-10-25 UTC. **Decision: direct-output FIFO availability failure confirmed in BOTH newly tested representations on Linux and macOS. Product repair NOT implemented.**

## Authority / prospective contract / exact source

- Canonical unmerged v0.31: `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`.
- Shipping checkpoint **v0.30.0**, archive format **revision 24**; no version/format/Reader/Builder/native mutation.
- Reader original blob: `e716233403dabd0966863c45635e18fa5ac6afb8`; Builder original blob: `663ef0922992b1fbb8f19e6eea88d55c10a56044`.
- Prospective prediction/prereg branch commit **`0c4f723b7e09be3d0b1c430f8cfb8497f93fe0d9`** was committed before the source of this instrument. Test blob **`5cf1792b1a0e77f29e02623f8b4473d04e645960`**.
- Hosted result-bearing HEAD **`7bb2a0ea6d5bec93665a1ccff0f3c87afc985e98`**.
- Original [two-host Actions run 40237296369](https://github.com/FCMO-AI/.CMPCT/actions/runs/40237296369), macOS job `121301475041`, Linux job `121301475331`: **both SUCCESS**, each **8 PASS / 0 SKIP / 0 FAIL**. The success is from a *scientific defect reproducer*, not product safety.

## Product-level matrix with actual Builder storage assertion

Each original Builder-built archive was reused unchanged for all four leaf cases per mode. CMPCT installed independently under `site-packages` outside checkout. The harness verified the stored `row[6][0]` *before* attempting hostile extraction:

| Authentic representation | Storage tag | Source member | Fresh / existing regular | Existing FIFO without reader | Existing symlink to FIFO |
| --- | ---: | --- | --- | --- | --- |
| `S_PACK` | **4** | `payload.txt` (8,192 B) | exact / exact | **child timeout >8s** | **child timeout >8s** |
| `S_VZIP` | **2** | `payload.zip` (168 B) | exact / exact | **child timeout >8s** | **child timeout >8s** |

Eight genuine observations per host (16 total): each platform reported **4 normal exact extractions, 4 true child timeouts**, zero omitted. Each child emitted `O121_CHILD_INDEX_OPENED` before any hostile timeout. The original source, archive SHA and both FIFO objects remained intact. POSIX `mkfifo` prerequisites and genuine storage type passed on both hosts.

### Raw time observations (seconds; bounded subprocess wall, not performance benchmark)

| Host | PACK fresh / regular | PACK FIFO / symlink→FIFO | VZIP fresh / regular | VZIP FIFO / symlink→FIFO |
| --- | --- | --- | --- | --- |
| Ubuntu 24.04 | 0.055707 / 0.056274 | **8.005180 / 8.005660 (timeout)** | 0.057576 / 0.058362 | **8.010601 / 8.010660 (timeout)** |
| macOS 14 | 0.050068 / 0.049695 | **8.002803 / 8.005518 (timeout)** | 0.055175 / 0.052508 | **8.007825 / 8.003553 (timeout)** |

### Source and per-host archive fingerprints

Identical deterministic logical source SHA across both hosts:

- PACK source `88bb52fc070bc8f0f2ceb5541fb4343a16d998b6a87c3437318d453b9012edc8`.
- VZIP source `53c745a8857772bff213bb66c0fd72c0870dffeb1fa77b8c7a9d794c9b3d0bb7`.

Original CMPCT archive SHA per host (cross-platform metadata bytes differ; **do not claim cross-platform archive parity**):

| Mode | Ubuntu SHA-256 | macOS SHA-256 |
| --- | --- | --- |
| PACK | `bbf39116bdd04d0913e2761e6850e0cd851dfd7eeec9db7574c60fec46aabef0` | `3a34420b6d1bc266ed4dca3095ac1ae9bb7fa6947ca9c095e5ec0cf74ebc6692` |
| VZIP | `57be2ef4c971fea19d42c3e97fb39ffc535fbfd770d1f62910871511c451a413` | `b12159f8f0b6a783c04f6803ff6dd29e93149cf4fa8ec2d13c29f87471085251` |

### Immutable raw evidence and independent audit

- [Actions run 40237296369](https://github.com/FCMO-AI/.CMPCT/actions/runs/40237296369).
- Linux artifact **12615467478**, SHA-256 **`3bcac11c4d2c172a629841442877e0e82b46c98a21b660767be5aa6f6c3dde22`** (GitHub artifact digest).
- macOS artifact **12615003172**, SHA-256 **`1d4e9cdda55785cd2da948d9959d6d20f28cbc1d6654ea203affc910d7f685c9`**.
- Hosted test blob `5cf1792b1a0e77f29e02623f8b4473d04e645960`.
- Audit runs **after** JUnit with strict 8-case count, 0 fail/error/skip, complete Cartesian `{pack,vzip} × {fresh,regular,fifo,symlink_fifo}`, per-mode SHA invariant, four expected negative child timeout receipts, source/Reader/Builder identities. Both independent audit steps ended SUCCESS.

## Mechanism, decision and scientific frontier

The source Reader's `extractall()` routes both genuine PACK and VZIP through the **same `else` direct `os.open(...O_WRONLY|O_CREAT|O_TRUNC)`** as S_BLOB; S_SPARSE has a separate direct open with the same dangerous flag family. Under POSIX FIFO without a reader, opening for blocking write stalls the process before payload publication. This full installed-product test confirms the code-path explanation for two new storage types and removes a dangerous temptation to fix only a named representation. Prior O108 #463 proved S_BLOB/S_SPARSE and distinguished S_CDC verified staging; this O121 expands the authentic sampled coverage to S_PACK and S_VZIP, not an independent product correction.

**Decision-changing:** the strict Reader security test for existing output leaves must be **publication-primitive-wide** rather than case-specific: S_PACK and S_VZIP can hit the same terminal direct-open as S_BLOB; S_SPARSE is separately direct; S_CDC/S_CHUNKS stage and replace. No other direct branch from the source `extractall()` code is known, but this is not universal proof against future representations or modes. A succeeding test on a reproducer indicates a **known unsafe Reader**.

## Strongest negative / limitations / alternatives

- No product repair; no integrated #269 test on this branch; released behavior remains unchanged. A static `lstat` guard may catch existing FIFO but does not solve adversarial TOCTOU races. O108's descriptor microcontrol is a promising separate low rung, not product repair.
- `8s` timeout bounds a **demonstrated availability failure**; it does not prove mathematical indefinite blocking or all possible FIFO readers. No Windows named pipes, UNC, cross-device reparent races, hardlink destinations, power-loss crash consistency, memory exhaustion or alternate permission policies evaluated.
- Identical logical input sources across hosts do **not** imply identical CMPCT archive output bytes: filesystem timestamps/ownership metadata differ. Within a single mode/host, the archive SHA was fixed across all four trials.
- The successful normal 50–60ms subprocess controls show the observed negative was not just interpreter startup or decompression, but not a statistically controlled benchmark; elapsed timeout duration is imposed by test harness.
- No complete format economics, CPU, wall, RSS, temporary I/O, cold listing, selected bytes, decoder amplification, native parity, official ABBA benchmark, competitor size/create or release-score improvement. **Performance/release credit: zero**.
- No Discovery Engine policy/self-modification or shared STATE.json write; #440 remains current owner of cache reconciliation. Reader security owner remains #269 / Issue #462.

## Counterfactual and owner handoff

Earliest prospective discriminator was the Reader branch control-flow map, which would have correctly predicted direct `S_PACK`/`S_VZIP` risk without eight expensive child timeouts. However, the exact classification would not be defensible as installed-product evidence without authentic Builder-produced physical modes and positive controls. A reusable practice is **derive the publication-primitive partition statically, then run at least one authentic representative per distinct path and hostile destination**. O108's previous partition lacked two real kinds despite sharing a terminal direct write, so this new evidence fills the bounded blind spot.

Next highest-value action belongs to Reader product owner #269: implement one bounded fail-closed output-leaf contract for all direct-open modes, preserve regular-file inode/permissions and exact content, and preserve the original negative O121 (2×4) and O108 (3×4) courts **unchanged** as historical defect evidence; for any proposed repair, reuse the same Builder-authentic fixtures, storage assertions and hostile leaf arrangements in a **separately preregistered repair-verdict suite** requiring prompt managed refusal for FIFO and safe reconstruction for ordinary files. Do not run the original timeout-expecting negative tests as if they should pass after repair. Then add malicious symlink/hardlink/ancestor and Windows/portability tests. Reject silent FIFO blocking without replacing file identity unexpectedly. Full release benchmark and CI are mandatory before promotion. No duplicate #269 implementation or merge/release proposed here.

**Result class:** genuine installed-product scientific defect evidence, no product code modification. **Hypothesis:** CONFIRMED in both POSIX hosts and both modes. **Policy lesson:** local prospective methodology only, not normative discovery-policy amendment.
