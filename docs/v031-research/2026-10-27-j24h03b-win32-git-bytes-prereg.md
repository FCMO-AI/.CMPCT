# J24H03b — Windows checkout byte-identity repair (prospective amendment)

**FROZEN 2026-10-27 UTC before workflow change.** Scope: evidence infrastructure ONLY. Product code, inherited historical test, test inputs, semantic checks and preregistered J24H03 pass criteria are immutable.

## Observed initial result and exact source boundary
J24H03 first hosted [run #40594727366](https://github.com/FCMO-AI/.CMPCT/actions/runs/40594727366) at source HEAD `f5943daa55148194b9bc47b1200f360731ef5800`:
- Ubuntu/macOS genuine Writer three-process court SUCCESS.
- Windows **O47 two genuine test cases PASS** using composed #401 Builder, including real physical hardlink and independent same-byte copy. Initial J24H02 source-backed Writer preparation reached correct signed Builder `K_FILE/K_HARDLINK` rows but STOPPED **before Writer parent/candidate comparison** because `reader_source` checks `Path(reader_module.__file__).read_bytes()` and obtained Git blob `9010154c9be85513b2b136df856966fd8db0d9bc` from Windows checkout, versus canonical Git HEAD blob `243b46d68211a2b125e07f7c92966535f5f0bdc9`. Git `hash-object` on that path nevertheless matched canonical source blob, demonstrating checkout text normalization (CRLF) rather than an actual Reader source change.
- Engineering Evidence #40594727272 FAILED solely for missing required headings in PR description; PR body subsequently amended with all required headings without changing source.

## Mechanism and falsifier
Source SHA custody must bind **on-disk imported Python bytes** as well as the canonical Git blob. Instead of weakening the original inherited J24H02 harness, adding an exception for Windows, changing expected blob, or accepting a normalized mismatch, explicitly rehydrate ONLY the two Reader files from each checked-out commit's authentic `git show HEAD:src/cmpct/reader.py` bytes. Run under Python `subprocess.check_output`, write with `Path.write_bytes`, compare rehydrated bytes to Git bytes and SHA-1 Git blob including `blob <len>\0` header. Do this BEFORE the historical/candidate Python imports/tests. The immutable original J24H02 source check must then pass the same expectation on all OS.

No archived bytes, historical Reader source, Builder, tests, oracle decisions or work/process boundaries change. If raw imported Reader bytes still mismatch canonical source, or either signed Writer archive deviates, or any original negative/positive result fails, preserve FAIL. This is a platform artifact/custody fix, **not** evidence of a Windows product win until that court actually runs.

## Alternative rejected
Source text canonicalization inside the inherited J24H02 tester could produce misleading evidence by testing nonidentical imported bytes. Replacing expected Git SHA with Windows checkout blob would pretend a different source identity. Set `core.autocrlf=false` after checkout can be too late. Hydrating the canonical committed bytes is narrower and independently verifiable.

## Outcome required
Re-run exact-head Ubuntu/macOS/Windows and preserve raw logs/receipts. Only real Windows parent-negative/candidate-positive success yields a composed product finding. Historical failure remains in evidence. No release/merge/state change.
