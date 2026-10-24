# O17 — Source-exact native terminal-owner × indexed-SHA composition: hosted result

Date: 2026-10-24 UTC. Status: **SCOPED RESEARCH SUCCESS; NOT MERGED OR RELEASED**.

## Authority and prospective question
Parent PR [#349](https://github.com/FCMO-AI/.CMPCT/pull/349) exact SHA `611d0ea67a94f552f9ebca07ba747f191dee160e` has terminal hardlink-owner ordinal and validated signed-index graph. Sibling PR [#340](https://github.com/FCMO-AI/.CMPCT/pull/340) has existing-index logical SHA metadata query, known to be absent for direct RAW. They had not been tested together in one native handle. O17's prediction was committed in `docs/v031-research/NATIVE_TOPOLOGY_INDEXSHA_UNION_O17_PREREG.md` at `07b3df97e06bd9ff62404890d83714a1bdec1e72` **before code**.

## Exact HEAD hosted evidence
**Run [40102360775](https://github.com/FCMO-AI/.CMPCT/actions/runs/40102360775) SUCCESS**, on source commit `d50f58f5c8dc69ae7f2f959e4a325a3d6db1d106`; job `120896945440`. Artifact `12563655894`, named `native-topology-sha-o17-40102360775`, includes O12, O14, O17 raw JSON, logs, source SHA and SHA256 manifest. [Artifact](https://github.com/FCMO-AI/.CMPCT/actions/runs/40102360775/artifacts/12563655894).

Actual job passed source Git custody, `cargo fmt --check`, `cargo test --locked`, `cargo clippy --all-targets -D warnings`, Rust release build, strict C compilation of BOTH exported declarations, prior native PACK golden, original O12 signed-index/RAW-negative oracle, original O14 hostile signed hardlink graph court, and new O17 same-handle test. Rust test suites recorded 24 nonempty test successes; no tests were weakened. This is specialized CI, **not** a full General Tests or official release ABBA verdict.

Original O12 test blob: `8b498d632220eaad2053a289180aef18dee6c3f1`. Original O14 test blob: `1c553ed572a4ae5bcb676745e24085f416993628`. Both custody-checked at runtime.

## O17 directly measured outcomes
- Full Builder-generated archive size: **1,588,787 B**, SHA-256 `bc084ccc40df503ea3d6371992eff24b4e9728a611dc8175ff1f6c2992c2918d`.
- **1,500,000 CDC logical bytes** reconstructed through public C 64-KiB ranges. SHA of actual streamed bytes, original Python bytes and authenticated index SHA all matched: `bf50be76335508a4e3975ccf5572291703c4a179251bdb7b21994591abe137ef`.
- Two distinct true POSIX hardlinks resolved by the native owner API to their respective correct regular-file ordinals in the **same** open handle used for SHA and PACK operations.
- A genuine Zstd S_PACK held **128 eligible members**; an actual authenticated batch reconstructed **48 members / 37,500 bytes**, checked byte-for-byte against original source.
- Correct rejection and zeroing were tested for RAW without signed logical row SHA, hardlink/non-file query, invalid index and null pointers. Direct RAW received no invented SHA guarantee.
- Inherited O12 verdict `RAW_GENERALITY_FALSIFIED_CDC_NARROWED_CANDIDATE` remains true. This O17 result is `SOURCE_EXACT_NATIVE_METADATA_COMPOSITION_CANDIDATE_PASS` **within the tested representation classes**.

## Independently checked source custody
On measured O17 HEAD, removing only the original **1,593-byte** O12 Rust function/docs yields PR #349's Rust source byte-for-byte (`3b4946d058f6bcfd0e39373d7828756d824450a2`). Removing only the original **952-byte** O12 C declaration/docs yields PR #349's header byte-for-byte (`e46058e567d2b1a558574dbbf1290e92ed44709b`). Everything else in the product source is identical to #349. Original O12 sibling file blobs `cf368d2a9ade23ce46e93d797c770ad52bdf1f68` (Rust) and `ae042de5c0af8e576c9e5497e8c242412d8c2fa9` (header) supplied the exact fragments.

## Negative/self-critique and next experiment
This is an ABI composition result, **not** compression or release/product proof. It does not measure end-to-end wall/CPU/RSS, native whole-tree extraction, physical RAW stream authenticity, hostile source mutation after open, atomic destination publication, portable Windows/macOS consumers, or installed package binding. It does not grant external-signer authenticity to an unsigned SHA. The 64-KiB consumer buffer is not a complete maximum RSS proof; native chunk decoding has its own allocation budget.

The next dependency-safe fork is a bounded, staged CDC-output verification and inode-preserving publication court compared to the existing Python Reader, with explicit source-change and destination-hostility controls; avoid reopening O12 RAW logical SHA without a new signed representation or independently trusted snapshot. Do not promote from an ABI microcourt. `docs/discovery/STATE.json` remains unchanged; another owner (#240) reconciles that staleable cache. No broad discovery-policy revision earned.
