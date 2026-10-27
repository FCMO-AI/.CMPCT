# J24H03 — first-party Windows Builder × owner-first Reader composition (2026-10-27)

**Scope:** real product-source composition and platform falsification, not release evidence.
**Source at result-boundary:** PR #625 head `edaa9cca6dc8620850e394103d1d98fb47a25b10` before adding this note; base #621 `becb9587d8eeaf3024e88c28859e6adc7a8cd4b7`.
**Source identities:** Builder blob `6f60dfe63742ff4b777f959a15d6fb828ae29610` exact #401, Reader blob `243b46d68211a2b125e07f7c92966535f5f0bdc9` exact #262, O47 test blob `6c00ae49eea075957453d6d7238d988add6eedee` exact #401. Published main remains v0.30.0 / r24.

## Primary scientific question
Can genuine Windows Builder physical source-hardlink capture (#401) coexist with dependency-ordered Reader hardlink extraction (#262) and faithfully reconstruct valid first-party Writer append_rename journal generations without archive-format or semantic compromise?

**Decision at this boundary: NARROWED / Windows default metadata remains RED; isolated metadata-disabled three-host composition court PENDING.**

### Prospective chain and observed results

| Episode | Pre-source prereg | Source exact | Hosted evidence and verdict |
|---|---|---|---|
| J24H03 | `5ef58eb0` | `f5943daa` | [run 40594727366](https://github.com/FCMO-AI/.CMPCT/actions/runs/40594727366): Ubuntu/macOS success; Win original O47 2/2 pass, true Builder K_FILE/K_HARDLINK, then evidence-custody false stop because Windows checkout CRLF raw Reader bytes did not equal canonical Git source |
| J24H03b | `a9fdde9d` | `e6168db8` | [run 40595312767](https://github.com/FCMO-AI/.CMPCT/actions/runs/40595312767): Ubuntu/macOS success, Win true O47 2/2 pass, correct independent imported candidate/historical Reader Git blobs, real first-party signed Writer archive prepared; then **default extractall metadata NotImplementedError**, before alias A/B |
| J24H03c | `1a6edcec` | `edaa9cca` | [run 40596240736](https://github.com/FCMO-AI/.CMPCT/actions/runs/40596240736) dispatched; exact-head host conclusion **PENDING when this result was written**. Only this branch's J24H02 test copy uses `metadata=(os.name != 'nt')` on its three calls; Linux/macOS defaults and source, Reader, Writer, strict SHA and original parent #621 test are unchanged |

### Concrete directly observed scientific negatives and positives
- [CI #40595312767 Windows](https://github.com/FCMO-AI/.CMPCT/actions/runs/40595312767) actually emitted source hardlink OS identity (same device/inode and link count 2), Builder `b-owner` = K_FILE and `z-alias` = K_HARDLINK to `b-owner`, and an authenticated Writer-transacted r24 file, 1,063 bytes, SHA-256 `96962d0e692b25f059f958ddbe4ee46c5fc3fa73db88dde004528a6dee3f75b7`. Its unrenamed 961-byte archive SHA-256 was `12fe6669a48ac128dfc081f6a2ec8285467adbc476a68e66898da984f17ceda5`. The historical/candidate Reader comparison did **not** execute because even the original positive control under default metadata=True hit a Windows API limitation.
- Windows default metadata failure stack: `historical/src/cmpct/reader.py` line 474 `os.utime(full,ns=(mt,mt),follow_symlinks=False)` raises `NotImplementedError: utime: follow_symlinks unavailable on this platform`. It escapes `except OSError`. Dedicated **product correctness issue #626** is open. It is NOT a #262 graph algorithm regression, does not prove archive corruption, and is not cured by metadata=False.
- The original #401 O47 test is copied byte-for-byte. Genuine Win32 two-case evaluation passed 2/2, including independent same-byte regular copy not accidentally fused with physical hardlinks. Ubuntu/macOS source exact original J24H02 Writer forward-hardlink family passed on both source heads.
- First raw-byte imported Reader mismatch on Windows was a checkout EOL issue: git hash-object was canonical but Python Path.read_bytes differed. J24H03b now reconstructs actual checked-in bytes from `git show HEAD:src/cmpct/reader.py` and verifies full Git SHA including NUL-terminated blob header. It did **not** modify or relax the inherited Reader test.

### Source and concurrency custody
#625 is a child of #621; #401, #262, #621 source branches remain untouched. Read-only exact Git source blobs and true signed on-disk files are provenance. This result does not mutate `docs/discovery/STATE.json`; it is a staleable cache owned by #574 and its allocator is older than contemporary Reader work. Engineering Evidence on #625 was initially red for missing required PR dossier headings/markers; the PR body was amended with exact 11 headings and substantive disproof/quality-ratchet evidence; at `edaa9cca` [Engineering Evidence run 40596279296](https://github.com/FCMO-AI/.CMPCT/actions/runs/40596279296) **SUCCESS**. R36/CI Topology/Version Discipline also positive at that head; other CI pending. Default-inherited J24H02 hosted workflow now may remain red on Windows as a genuine product metadata failure; do not repaint.

### Negative / alternate explanation / counterfactual
The initial intended one-pass three-host test unknowingly coupled three independent facts: metadata-restoration portability, archive filesystem identity and dependency-driven hardlink reconstruction. The first Windows failure was only checkout text normalization. The second was a real metadata API portability failure. The prospectively revised J24H03c deliberately uses the supported public `metadata=False` flag on Windows **equally in historical and candidate Reader** to isolate ownership/reconstruction. A positive result would prove *only* this scoped dimension, not the default. The earlier cheaper discriminators would have been (a) actual imported source-byte SHA per OS before setup, and (b) an installed-product default Windows regular-file extract metadata smoke check before embarking on combined hardlink A/B. Both are prospective, transferable test-planning lessons, not a reason to weaken standards or policy.

### Remaining product and release debt
- Fix Windows default metadata=True in Reader without unsafe symlink following, silent metadata loss or compromising hardlink inode fidelity (issue #626).
- Check Windows J24H03c exact-head negative/positive court and raw artifacts; preserve any new failure as separate cause.
- Integrate with concurrent Reader and Validator sources #569/#609/#613/#615/#624, respecting own branches and the 27× open-cost regression of #569.
- Measure same-input complete archive bytes, creation/extraction CPU/wall/RSS, temp I/O, correctness, destination races/atomicity, authenticated recovery, symlink pivots, POSIX/Win32 filesystem modes, and official r24 parity. Cautiously compose: shared-file PRs are not mergeable simply because each passes focused tests.
- No version bump, format change, merge, or product-release credit. The Discovery Engine had no evidence-backed policy modification.

## Next high-value executable action
Review run 40596240736's **terminal source-bound** J24H03c raw receipts, including Win32 OS samefile and original parent rejection on identical signed bytes. If positive, hand off the composed source to #401/#262 and coordinate fix for #626; if negative, classify first divergence. The default Windows metadata=True bug remains actionable irrespective of J24H03c outcome.

**This is a bounded partial outcome note, not an unverified full-product result.**
