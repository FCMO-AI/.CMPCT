# J24I63 hosted red/green result — held native index authentication after same-inode rewrite

Status: **DECISIVE NARROW CORRECTION EVIDENCE**; candidate is **DRAFT / NO MERGE / NO RELEASE / NO PRODUCT SPEED CLAIM**. Report recorded 2026-10-30 UTC. This is a result note for already-preregistered J24I63, not a new research episode or revised threshold.

## Original question and immutable controls

Can a native revision-24 `Archive` that was opened against and cached authenticated index A later return `verify_complete() == SUCCESS` by authenticating the different, valid index B written into **the same inode**? The red candidate #846 and patched #847 share an exact 386-byte public fixed-vector A/B adversarial case. A has `raw.bin`, B has `new.bin`; both independently authenticate; both have a 61-byte encoded and 52-byte decoded primary/tail index, the same authenticated 64-byte RAW payload, and an exactly equal physical extent. They differ in primary/tail index digest and member identity. The open native handle persists across a stable in-place overwrite of A with B. `os.stat` proves inode and physical length retained; B is separately verified by the actual Python Reader, a newly opened native C ABI handle and CLI. No racing thread is required.

Inherited law: native complete verify must not certify cached A's member table by consulting a later valid B header. On unsupported latest-generation semantics, status must be typed `Unsupported=-7` with `verified_count=0`. Existing physical checksum, format, ABI, public test, and zero-byte / >5% AND >3 ms release gates remain untouched.

Preregistered before implementation: `ccfc1f94335248415f404543e1e5331c307ce37d`. Original test-only HEAD: `96295dee06512740686417db6b7c4a0e3dd2a348`. Original proposed code HEAD: `c0c1ebeec78e2fb425e55b42d3916f649bfc2016`.

## Failure-class repairs — do not confuse with experiment outcomes

1. Initial old-code red run [#41101116433](https://github.com/FCMO-AI/.CMPCT/actions/runs/41101116433) failed prematurely at `tests/native_complete_verify_abi.py:325`, because its valid-index generator passed a `bytearray` to `cmpct.codec.zd`, which calls `ctypes.create_string_buffer` and requires `bytes`. The old verifier had **not** been exercised. Parent test-only commit `c116223b17390ae130e0384089c03b0fc684e025` converts the two slices to immutable `bytes`, without modifying the archive content, oracle semantics, required error status or old native product code.
2. Initial patched run [#41101531870](https://github.com/FCMO-AI/.CMPCT/actions/runs/41101531870) did not compile: `native/cmpct-core/src/lib.rs` lacked the `}` closing `pub struct Archive` before its `impl Archive`. The initial General Tests/fuzz/performance red were downstream Rust installation failures, **not** performance/correctness results. Commit `f070595a299c1f15052a58efec05475d00ca0d4f` adds only this closing brace. Commit `70a6fdebf3e2dd1816406bc2b0bb9d949fd6a229` applies the same immutable-`bytes` court repair to the patched branch.

## Actual hosted exact-source result

| Test | Exact HEAD | Native Core GitHub Actions | Native C ABI court | Meaning |
| --- | --- | --- | --- | --- |
| Pre-patch falsifier #846 | `c116223b17390ae130e0384089c03b0fc684e025` | [#41108906302](https://github.com/FCMO-AI/.CMPCT/actions/runs/41108906302) **FAILURE** | Actual stale handle reported **`status=0, verified=1`** while court expected `-7,0` | The older native code wrongly certifies retained A table against B index, as preregistered |
| Patched candidate #847 | `70a6fdebf3e2dd1816406bc2b0bb9d949fd6a229` | [#41108877140](https://github.com/FCMO-AI/.CMPCT/actions/runs/41108877140) **SUCCESS** | Whole `tests/native_complete_verify_abi.py` passed, including stale handle `-7,0`, ordinary fixed WAV/FLAC `0,1`, fresh B `0,1`, journal generations `-7,0`, C ABI and CLI controls | Small pin of the exact opening header defeats this stable same-inode crossing without refusing a valid fresh B |

Direct failing old-code log: `AssertionError: ('held decoded primary must not inherit new index's success', 0, 1)` at `tests/native_complete_verify_abi.py:350`. Patched Native Core stdout contains the completed native-ABI court JSON (`normal_abi=success-1`, `latest_signed_put_delete_native=typed-unsupported-count-0`, `latest_signed_checkpoint64_native=typed-unsupported-count-0`, `valid_foreign_path_reopen=both-pass-different-source-and-member`) and the job returns SUCCESS. The new expected stale `-7,0` has an explicit assertion; its execution is not merely inferred from a green top-level workflow.

The patch stores the 68-byte authenticated primary header in the open `Archive` and compares it to the same held descriptor's current header before complete latest-generation verification. It does not open a new pathname for that guard. It does not modify list/range behavior, archive grammar or public ABI.

## Independent oracle / held-out structural transfer

A separate Python standard-library + MessagePack + Zstd CLI physical oracle (no CMPCT Reader or Builder) sampled 250 unique seven-character logical member names of form `[a-z]{3}.bin` with fixed seed `20261030`. Each distinct index remained a well-formed 386-byte r24 archive with 61-byte compressed / 52-byte decoded primary/tail index, same 128-byte CMA4 block and payload bytes, correct SHA-256 and CRC32. All 250/250 had zero need to change geometry. A retained `os.open` descriptor exposed the new index after a stable same-inode overwrite. This is **oracle evidence of generality of the A/B physical premise**, not Rust verification or broad corpus performance credit. Independent script/receipt retained by the experimental activation; the hosted C ABI result above is the product-mechanism proof.

## Losses, alternative explanations and release debt

The initial contradictory fail statuses were **instrument Rust syntax and ctypes type errors**, resolved without weakening the preregistered oracle. The decisive old-code `(0,1)` result cannot be explained by source-incompatible archive B: fresh Python and native B both succeed, physical geometry remains equal, the test passes before the stale-handle assertion, and patched code on identical protocol returns `(-7,0)`.

Scope remains narrow: this is a **stable** same-inode rewrite between open and verify. It is not a guaranteed atomic snapshot against a concurrent same-inode writer, not journal-aware native replay/recovery, and not a product-release claim. Three OS families and full package/installed mobility remain unproven by this one hosted Linux C ABI court. The additional 68-byte header state and comparison have no full-product CPU/wall/RSS attribution yet. Parent #844 already had a confirmed r24/ZIP `binary/library/create` +22.99%/+32.02ms red; it remains a release gate until independently resolved. #847 full `General Tests`, r24/ZIP, Engineering Evidence, installed/native portability and other exact-head CI must be separately inspected, including skipped and cancelled jobs; Native Core green is not full promotion authority. The final documentation-only commit, if any, is a new Git HEAD and inherits neither code-head tests automatically nor new performance credit.

## Decision and continuation

**Scientific decision: H1 supported for this exact source/fixed and held-out same-geometry index family; no global product promotion.** Keep the red witness #846 and green candidate #847 distinct, preserve the old-code fail in the repo, ensure both CI SHAs and signed controls remain available, and reconcile the stacked PR ancestry without blind overwrite. The cheapest next scientific/falsification target is a bounded immutable-handle mutation court across a distinct index schema/geometry (not just renamed path) if a still-open risk can change merge acceptance; otherwise prioritize independent full CI, strict release parity, and integration with the native ABI owner #807. Concurrency, actual journal recovery, hardlink ownership, checksum and portable reader remain separate owners.

**Counterfactual:** Had the original court explicitly asserted that its Zstd validator accepted `bytes` before dispatch, and had `cargo fmt --check` / `cargo check` been run before an expensive full CI, the two setup-only initial failures would have been detected earlier. The transferable lesson is local test/harness preflight, not a change to Discovery Engine or evaluator law.
