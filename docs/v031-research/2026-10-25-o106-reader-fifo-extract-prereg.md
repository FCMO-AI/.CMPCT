# O106 preregistration — existing FIFO leaf during installed Reader extraction (2026-10-25 UTC)

**Status:** frozen prospective prediction. No O106 installed-product observations exist at this commit.  
**Scope:** scientific availability falsifier only; no Reader/Builder/format change or release claim.  
**Exact baseline:** prospective `agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b`; expected `src/cmpct/reader.py` Git blob `e716233403dabd0966863c45635e18fa5ac6afb8`. Released checkpoint v0.30.0, physical revision 24.

## One question, falsifiable mechanism

When a genuine installed `CMPCT.extractall(dest)` encounters a pre-existing, **unconnected POSIX FIFO occupying a regular-file output leaf**, does its plain `os.open(full, os.O_WRONLY|os.O_CREAT|os.O_TRUNC,...)` block beyond a bounded child-process deadline rather than returning a controlled error, even though the *same* archive extracts promptly to a fresh directory or pre-existing regular leaf?

This is **Reader extraction into an existing destination**, not Builder publication (O87/#445), static symlink ancestry (#264/#269), or mutable Reader source mmap (O103/#459). Search of open/closed PR titles before freezing did not find a Reader FIFO-leaf extraction owner. Existing Reader destination hardlink/symlink topology research remains independently owned.

**Prediction (before running):** fresh and pre-existing regular leaf controls return within 8 seconds and reconstruct exact SHA256 source bytes; unwritten FIFO leaf blocks the installed Reader until the disposable child is terminated by the parent at 8 seconds. FIFO type remains intact. This is a *product availability defect* if observed, not product success. A deliberately different compressed/chunked extraction route can be checked later but receives no credit from this focused test.

**Strongest simple control:** direct `os.open(O_WRONLY)` on an unwritten FIFO has POSIX blocking semantics, but this alone cannot prove what CMPCT does. The decisive test must call the authentic `CMPCT.extractall()` after making an authentic archive with the unmodified `Builder`, and must verify the selected physical representation is the normal `S_BLOB` path. No monkeypatching or simulation of Reader code.

**Alternative explanation:** normal package startup, archive creation, or extraction may exceed eight seconds independently. The paired fresh/regular controls must finish on the same runner. Another possibility is that the Reader protects the leaf before write, in which case the hypothesis is falsified. If tests cannot construct a FIFO or cannot verify installed-source provenance, classify as infrastructure/unsupported platform rather than product result.

**Kill/narrow rule:** prompt rejection of FIFO falsifies blocking; a successful nonblocking FIFO extraction would refute the predicted failure but must still be assessed for safety; ordinary controls timing out makes the result ambiguous. A timed-out FIFO alone never proves infinite blocking or arbitrary file overwrite.

## Evidence design and boundaries

- Same frozen 4-KiB deterministic pseudo-random regular source, one authentic r24 Builder output per host; no replacement of product code or canonical test runner.
- Three independent disposable child processes: empty destination, pre-existing regular leaf, and pre-existing unwritten FIFO leaf; `subprocess.run` supervises each at 8 seconds and kills blocked children.
- Parent separately verifies the built archive with installed `CMPCT.verify()`, exact read and root-byte SHA256, and checks explicit `S_BLOB` storage before the extraction court.
- On success preserve per-case stdout/stderr/exit/timeout, archive hash, source blob, environment/OS, and JUnit; run Ubuntu 24.04 and macOS 14 in distinct jobs. Exact installed package outside checkout; source/head Git object checks; zero skipped mandatory tests.
- No Windows named-pipe extrapolation. No release benchmark, memory benchmark, generalized concurrency proof, destination snapshot guarantee, or product fix claim. The normal control performs logical reconstruction only (metadata disabled) to avoid unrelated platform timestamp scope.

## PARETOBONK / coordination

A. Productize known VZIP budget #444, already has measured owner, not an unclaimed implementation surface.  
B. Reprobe Builder FIFO #445, already answered and repaired in #448; redundant.  
C. **Chosen:** small, differently rooted Reader destination availability falsifier with direct code-level mechanism and an eight-second upper bound on CI opportunity cost. It can change Reader destination-admission policy without touching competing owners.

Do not edit `docs/discovery/STATE.json` (currently owned/reconciled by #440); no evidence-backed discovery-policy change is earned. If confirmed, notify the Reader destination-containment owner and propose a separate fail-closed output-leaf contract. Never silently replace an existing regular inode merely to bypass FIFO blocking without measuring hardlink/xattr effects.