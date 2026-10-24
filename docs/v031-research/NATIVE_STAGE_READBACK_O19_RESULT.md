# O19 — Stage read-back closes one fault window, not publication-time mutation

Date: 2026-10-24 UTC. **Decision:** `POSTWRITE_READBACK_NARROW_WIN_PUBLICATION_TOCTOU_UNRESOLVED`. Research **only**. v0.30.0 / format r24 released unchanged; no merge, product safety claim or release credit.

## Authority and preregistration
- Parent exact O18 PR #363 at `5cdbd00af01a3caa35c18357ac2e859b6cc05f02`. O18 C blob `f9c5af105827f5b08d19dfdf130f1b821ae5cd1d`; inherited native Rust and C header blobs `ce12c76d9f4901af1e2b95d5d88883ffb2a72d2e` / `dc6b689febd383618abe31d4d2ea3ccda7fb1d3b`, all independently enforced by hosted workflow. No original product/Reader/ABI mutation.
- Predictions frozen in `docs/v031-research/NATIVE_STAGE_READBACK_O19_PREREG.md` at commit `579ef9d5848f6229e426372f2b2f0937770bd150` before O19's real-archive measurements.
- Source HEAD actually tested: `9840684a4d119b149830c58fa1b9416fc6e08500`; [hosted run 40111427355](https://github.com/FCMO-AI/.CMPCT/actions/runs/40111427355), specialized job **SUCCESS**. [Artifact 12566842105](https://github.com/FCMO-AI/.CMPCT/actions/runs/40111427355/artifacts/12566842105), ZIP SHA-256 `13fd18c5c098b8797d5190deaa3b283a2cd329fa0ce3453e3abfed3c6c946799`; `result.json` SHA-256 `d72a162bf3e7ff69fe38b3319091876bbef03e5ad85a3c232dd1f9778b72e366`.
- Subsequent docs-only HEAD (this note) must not silently inherit exact-head CI. A new specialized run must confirm it.

## Falsifiable mechanism
Original O18 hashes **caller bytes before writing** and fsyncs a predictable named stage, then `linkat` publishes it. O19's separate research client changes only that boundary: `O_RDWR` stage; after full write, fsync, and existing indexed-SHA comparison, seek to zero and hash the actual staged inode through a second bounded 64-KiB read pass; refuse publication if mismatch. Its extra read and digest are **real costs**. No encryption, external signature, portable publication, format mutation or generic tree extraction.

The independent `LD_PRELOAD` fault shim flips exactly the first stage byte (XOR 1) after a successful `write` or immediately before `linkat`, while returning the underlying syscall's ordinary success. The log marker proves which intervention actually fired. Two true Builder CDC archives used distinct deterministic byte streams. A separate Python oracle checks the final filesystem bytes against independently regenerated original and modified sources—not against the client's stdout alone.

## Hosted observations (12/12 scenarios match preregistered predictions)

| Client and injected boundary | 1,500,000-byte CDC | 2,100,000-byte CDC | Decision |
| --- | --- | --- | --- |
| O18 unchanged, no fault | exit 0 / exact | exit 0 / exact | Baseline control |
| O18 unchanged, fault after write | exit 0 / **mutated published** | exit 0 / **mutated published** | Baseline misses actual stage bytes |
| O18 unchanged, fault at linkat | exit 0 / **mutated published** | exit 0 / **mutated published** | Baseline publication gap |
| O19 read-back, no fault | exit 0 / exact | exit 0 / exact | No false rejection |
| O19 read-back, fault after write | **exit 5 / no file** | **exit 5 / no file** | **Narrow postwrite correction PASS** |
| O19 read-back, fault at linkat | exit 0 / **mutated published** | exit 0 / **mutated published** | **Late mutation gap remains** |

The 2 corpus archives measured 1,501,402 and 2,101,634 complete bytes respectively. Both were confirmed genuine `S_CDC` with an existing correct logical row SHA and exact Python reference reconstruction. All 12 scenarios report no residual stage name. On every accepted corruption, the output SHA equals the independently generated first-byte-XOR-1 source SHA rather than the original SHA.

Totals: **4 exact control publications, 2 caught postwrite corruptions, 6 silent corrupted publications** across the two methods/threat positions. These are *not* 6 spontaneous storage faults; all faults were explicitly injected. The native library was source-exact and the two clients used the identical archive bytes for each comparison.

## Independent audit
A separate post-run Python audit read the original hosted ZIP, validated ZIP SHA / `result.json` SHA / exact source HEAD, regenerated both deterministic input streams from their published seeds, recomputed original and one-bit-mutant SHA-256, and checked each output digest, exit status, stage cleanup and injection marker. **12/12 matched**. Audit SHA-256: `2364b70a38683acedd0e5cbbc6fbe77fcbc1fa67d4d681944cc4104062580f78`. The independent audit does **not** independently rebuild CMPCT archive bytes in a second implementation: the original Builder/archive physical size and genuine CDC characterization are the hosted oracle's evidence.

## Strongest negative / threat boundary
Rehashing the staged inode just before publication **does not make stage publication safe against an adversary who can change the inode between that check and `linkat`**. This is demonstrated here, not inferred from code inspection. The original O18 stage name is predictable and writable to the same UID that owns the private extraction root; `O_NOFOLLOW` and `O_EXCL` on creation prevent distinct attacks but do not seal a mutable inode. A postwrite digest can catch pre-check corruption, but a same-UID/privileged adversarial mutator remains an independent threat.

The injector is an intentional in-process userspace fault hook; these observations do NOT imply ordinary SSDs naturally corrupt successful writes or that an unprivileged different-UID attacker can penetrate the private root. The readback may also read filesystem cache, not prove enduring media state after a crash. This result must not be presented as an exploitable vulnerability absent a realistic adversary, nor as a completed fix for hostile destinations.

## Performance and exported costs
Read-back adds one full sequential logical-file read (`+1×N` stage bytes), a second SHA-256 pass and an additional I/O syscall loop. The fixed C caller buffer remains 64 KiB but **whole-process RSS was not measured**. The action records single uncalibrated wall observations only; no ABBA/same-runner speed, full product creation/extraction or format-size benefit. The additional work could be unjustified if the chosen trust model already excludes concurrent stage writers and Linux returns reliable writes; assess this opportunity cost before integration.

## Decision / alternative frames
**Supported narrow claim:** O19 catches a one-byte mutation already present in stage storage before the readback, and fails closed without a published final file. **Falsified broad claim:** adding a final readback makes publication adversary-safe. Do **not** integrate this control by itself under a promise of hostile concurrent destination protection.

Before another stage-hash patch, decide the real authorized threat model. For concurrent mutators, compare anonymous/unlinked inode staging (`O_TMPFILE` where supported), separation from untrusted writers, stable named-root binding and atomic tree-level promotion. These options require portable fallbacks and exact source/destination identity checks; on-disk fsync, directory durability and read-time integrity remain separate obligations. Reuse #351/#359/#363 rather than creating another parallel extractor.

## Discovery outcome
Primary question **decision-changing**: quantified which failure class read-back closes and supplied a stronger hostile counterexample that a reread check alone cannot close. No hidden evaluation weakening, threshold tuning, fingerprint change, product promotion, shared discovery-cache update or process-policy rewrite. No concurrency collision observed; this branch owns only O19. The prospective discriminator transferable to other file publishers is **fault at the last mutation-capable boundary**, rather than relying on checks made just before it.

## Next executor handoff
PR #367 remains draft on O18. Preserve the 12-case court as negative science. A genuinely valuable next product action is not further timing of this research shim: construct an authenticated, source-pinned, unlinked/private-stage or explicit no-mutator publication boundary; measure its security, portability, crash failure and full-system economics, then decide whether postwrite readback earns its carrying cost.
