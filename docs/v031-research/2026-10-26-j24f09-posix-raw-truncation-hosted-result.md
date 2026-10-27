# J24F09 — POSIX descriptor-bounded RAW extraction under same-inode truncation

2026-10-26/27 UTC. **Research result, not released product.** Exact source first hosted HEAD `f9ddd71c944a3392782ef7b370d46217b2dbfa46`; signed J24F09 preregistration precedes implementation in `76b617ba88e711342efeb710c81856181ddea44d`.

## Authority and question
Released v0.30.0 / revision-24 unaffected. J24F05 #540 parent `1885cb0658cacd34a50d05e45b541ecb76fc8497` Reader blob `41efeb9d3301fc06b1df56ab6bd42d9ee91f6d5e`. O103 issue #460/#459 proved same-inode archive truncation can signal SIGBUS on mapped reads. J24F05 immutably snapshots each 64KiB RAW transfer but still **dereferences mmap** to obtain those bytes. Can POSIX RAW extraction instead read immutable windows from its already-open descriptor and turn this fatal source mutation into a caught I/O integrity failure?

## Actual implementation
On hosts with `os.pread`, a small `_FdRawExtractWindows` source holds only `(fd, payload_offset, physical_length)`, independently checks physical RAW header via `pread` and `fstat`, and reads at most 64KiB per requested window. Each immutable window remains the exact byte object consumed by SHA-256 and the staged output write. Short `pread` is a typed Python I/O failure; no live source mmap is accessed after initial Reader open on this **all-RAW S_CHUNKS/S_CDC extraction path**. Unsupported hosts continue the original J24F05 mmap path. Ordinary `read`, compressed/mixed extraction, preflight, source-open and index paths still use mmap and are explicitly outside this fix. Format and release unchanged; full physical snapshot avoided.

Product Reader blob `a6a74068b34d726fc38bc151e5f191ce2dd45993`.

## Exact-host research evidence
Hosted GitHub Actions [#40424084560](https://github.com/FCMO-AI/.CMPCT/actions/runs/40424084560): Ubuntu 24.04 **SUCCESS**, macOS 14 **SUCCESS**. Each host installed candidate into an independent package environment and loaded **actual parent Reader source from its original Git commit** (not an approximation) into a crash-isolated process. Builder-independent physical revision-24 RAW fixtures of **8,617,989 logical bytes** were evaluated for both S_CHUNKS and S_CDC, with stable original, different-inode pathname replacement, and same-inode truncate-to-zero after first genuine verified stage write. Each host ran 12 distinct cases, 24 total.

| Case | Ubuntu | macOS |
| --- | --- | --- |
| Historical J24F05, stable and replaced inode | 4/4 exact reconstruction | 4/4 exact reconstruction |
| Candidate, stable and replaced inode | 4/4 exact reconstruction | 4/4 exact reconstruction |
| Historical J24F05, same-inode truncation | 2/2 SIGBUS (signal 7) | 2/2 SIGBUS (signal 10) |
| Candidate, same-inode truncation | 2/2 Python `OSError`, old destination preserved | 2/2 Python `OSError`, old destination preserved |

Candidate cases actually executed bounded `pread` (<=65536 bytes each) and bounded stage writes. In both truncated cases per host, the actor used a distinct process, the archive inode stayed unchanged, file size became zero, next `pread` returned short, the staged operation failed, and the preexisting destination remained intact. On path replacement the open descriptor retained the old original bytes. All stable/replacement logical SHA checks succeeded. No evidence suggests the fail-closed result applies beyond the source path specifically instrumented.

Original archives and stdout artifacts:
- Linux [#12699122181](https://github.com/FCMO-AI/.CMPCT/actions/runs/40424084560/artifacts/12699122181), SHA-256 `f69e8c1e78465a50717e75479d75cb781779f05c47347d712ec98bad6b78f8df`.
- macOS [#12698508804](https://github.com/FCMO-AI/.CMPCT/actions/runs/40424084560/artifacts/12698508804), SHA-256 `5ef20f8095c29f4c0e0c9bc231860e1c87b5d8c935f45ef55566483ab22f52e8`.

An independent artifact-structure and SHA-consistency auditor applied **438 original-evidence checks** to both downloaded JSON/ZIP records, zero discrepancies. This audit is evidence-consistency verification; it does not substitute independent native implementation or another full product run.

## Negative evidence and safety limitations
The historical implementation **really terminated SIGBUS** on both hosts and both representations. The candidate did not. This is not a global SIGBUS fix; random reads, mmap-dependent codec paths, source-open truncation and compressed/mixed extraction are still potentially fatal. The candidate does not defend against post-SHA stage pathname/inode substitution (Issue #528), symlink ancestry, or mutable source integrity outside all-RAW extraction. Windows uses the former mmap fallback. One `pread` per 64KiB transfer adds syscall/data-movement cost; its full CPU/wall, RSS, cache traffic and cold-start effects versus released v0.30.0, J24F04, J24F05, and alternatives are **unmeasured**.

The inherited J24F04 and J24F05 workflows verify **exact historic Reader blobs** and therefore fail their source-identity step on this descendant. Their original tests remain frozen. J24F09 is independently wired to replay the relevant transfer/source race semantics but does not claim full parent J24F05 test-suite parity. The core r24/ZIP performance workflow result must be inspected for whether numerical work ran; a green administrative title alone never confers benchmark credit.

## Interpretation and decision
**ADVANCED / PARTIAL PRODUCT REPAIR:** The descriptor lifetime counter-mechanism is real and source-exact, and removes a fatal failure for the scoped POSIX all-RAW stage. Preserve this candidate as a distinct, stacked draft. It does not earn merge or release until the complete parent safety court, Windows composition, source lifetime for other Reader paths, final-stage identity, exact-head general CI, true full-product economics, and source/format/release gates are satisfied.

## Counterfactual and next discriminator
The earliest prospective causal test is simpler than full archive rearchitecture: keep the same mapped Reader and change *only the RAW source transport* to descriptor-read while comparing same-inode truncation against authentic original code. This directly isolates the fatal mmap dereference from integrity/publication issues. A later gate should compare full-product RAW extraction memory/CPU and evaluate whether a consistent descriptor-backed physical-source abstraction can retire mmap lifetime risk for all required read paths at acceptable expense. This transferable observation is a scoped engineering lesson; it is not sufficient to rewrite Discovery Engine policy or `STATE.json`.
