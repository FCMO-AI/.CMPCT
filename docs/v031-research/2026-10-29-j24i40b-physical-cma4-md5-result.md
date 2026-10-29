# J24I40b — real revision-24 physical CMA4 transfer: Python and Rust agree

**Observed 2026-10-29 UTC · scientific strong-verify contract result · no product fix, merge or release.**

## Authentic physical witness
Parent J24I40 [#779](https://github.com/FCMO-AI/.CMPCT/pull/779) independently demonstrated a codec-private FLAC STREAMINFO MD5 mismatch: the Xiph `flac -t` reference rejects a one-bit wrong MD5 on genuine Builder FLAC, but Claxon's sample iterator reconstructs the original exact logical SHA-256/CRC32. That alone did not prove how a physical CMPCT archive behaves. J24I40b prospectively registered the transfer at commit `a539165e21cb0eeef19cdba0977a64d46ad42555`, before writing this archive mutation instrument.

[Actual installed Python/Rust court #40944926964](https://github.com/FCMO-AI/.CMPCT/actions/runs/40944926964) **SUCCESS**, complete job `123697697276`, pinned experimental source `ef6d9da937ad9fe02252e798e4226c29fe39b012`. All steps executed: genuine unmodified Builder source generation, independent physical libsndfile archive audit, exact source-pin verification, copied one-bit CMA4 reassembly, actual Python `CMPCT.verify()`, compiled Rust `Archive.verify_complete()`, status capture and fail-closed [physical evidence artifact #12929725111](https://github.com/FCMO-AI/.CMPCT/actions/runs/40944926964/artifacts/12929725111). Provider ZIP SHA-256 `709654f72ce1ebdc97c88047800c8065c705a0268e944ccc91a64835bfc663bf`; nested tar SHA-256 `f377530de9c5018fb9e42bb9f4975aae6dd8084294a3bf6578ef880ef5269c28`. Artifact is 30-day retention, outcome summary mirrored at `research/j24i40/hosted_physical_result.json`.

The original authentic archive is exactly **3,983,501 B** SHA-256 `9250964815f67891c3e106c9d87aadc67d4f2c3dce8b3e4e1873813a13a6fac7`. The one-bit mutant is also 3,983,501 B, SHA-256 `09d3ed612329cfd39bb7d1385507bbec2f326461cd529915fe3e18534c6e5f40`. Physical FLAC starts at archive byte **529**, STREAMINFO MD5 byte 26 is absolute archive byte **555**: exactly one byte XOR 1. The CMA4 header, indexes, footer, physical data sizes, decoded PCM frames and original logical WAV SHA-256/CRC32 were unchanged.

## Decisive court

| Actual physical archive | Python `verify()` | Rust `verify_complete()` |
|---|---|---|
| Genuine unchanged Builder WAV/FLAC | PASS, exit 0 | PASS, exit 0 |
| Same archive with one bit wrong FLAC-private STREAMINFO MD5 | **PASS, exit 0** | **PASS, exit 0** |

This **confirms parity of the two complete-verification APIs on this exact physical perturbation**. It does **not** mean either engine accepted altered reconstructed user data: both produced identical original logical WAV bytes under the existing CMA4 SHA-256 and CRC32 contract. Xiph `flac -t` rejects the internal codec-private MD5 as a separate, stronger codec-specific metadata-validation policy, while CMPCT's strong verifier prioritizes the logical identity it actually promises. There is no newly demonstrated archive-content integrity defect.

## Decision, negatives, and next work
The strongest outcome is a **scoped non-defect / closed MD5 policy discrepancy**: no extra PCM-MD5 pass should be added to the product merely to align exit codes with Xiph's broader FLAC-specific test. A zeroed STREAMINFO MD5 is legitimate under the reference test, so mandatory nonzero signature enforcement would reject a compatible case. If a future specification explicitly requires codec-private MD5 verification, charge SHA+CRC+MD5 CPU, memory, portability, parsing and compatibility costs, and implement only through native-owner authority.

This is not a proof that all malformed FLAC streams are accepted or rejected correctly. Only one Builder PCM16 source, a one-bit metadata mutation and the strong verify operation were tested; source-FD time-of-check/time-of-use custody, resource bounds, failure under changed PCM, extraction, selective reads, recovery, Windows/macOS native ABI and full product performance remain unmeasured. No format/version/frozen test/release/policy changes.

**Next highest product-leverage action:** owner #765/#759 should move the viable source-FD bounded PCM streaming oracle from detached split FLAC into a single-pass authenticated CMA4 verify path with exact archive-source identity and hostile frame/resource coverage. Earlier J24I38 and J24I39 establish expensive repeated WAV reconstruction and a promising lower-RSS oracle, but do not grant product speedup credit. This experiment shows that making the Claxon streaming path match Xiph's private MD5 checksum is not a prerequisite under the existing CMPCT logical-SHA contract.

## Counterfactual / discovery policy
Earlier J24I39 tail attacks only tested FLAC frame termination and couldn't isolate metadata-signature enforcement; a prospectively recognizable one-bit STREAMINFO mutation separates redundant codec metadata from reconstructed content cleanly. Transferring the same mutated bytes into real archive physical framing confirmed the result under both complete verify APIs without rewrites. This is a useful local experiment-design lesson, **not repeated evidence for changing the Discovery Engine's normative policy or shared state**. No concurrency collision; native implementation surfaces remained untouched.
