# O112 — authenticated binary-key root MessagePack parser divergence: result

Date: 2026-10-25. **Scientific NEGATIVE for draft parser product behavior; no merge/release/format change.**

## Immutable prediction and exact source

Prospective preregistration committed **before implementation and hosted execution**: `32c66a3c6af642914a8b59329180a7625c23e852` ([prereg](2026-10-25-o112-binary-map-key-prereg.md)).

Research branch originates from owner #316 `1ed92767e6438d9bb8835ddc7ae27160440c2014`, with no Python Reader, preflight, Rust native, format, codec, benchmark, policy or release changes. **Result-bearing source HEAD**: `26206de0d66fd5fe0db42b3c5d9412a982acbf3d`.

**Independent same-wire hosted scientific court**: [GitHub Actions #40229030203](https://github.com/FCMO-AI/.CMPCT/actions/runs/40229030203), authentic installed Python CMPCT 0.30.0 on PR316's candidate sources, Python 3.11.17, msgpack 1.2.3 and `cargo build --release --locked` of the PR316 native Rust C ABI. Job `121276574571`: **SUCCESS**. Raw [artifact #12611593428](https://github.com/FCMO-AI/.CMPCT/actions/runs/40229030203/artifacts/12611593428), SHA-256 `89cd1b07a5ea4b2a12fde7b8eac18c9cddecec1e8818dc24b928dd36850af4ca`; includes source witness, per-case JSON and complete court log.

## Observed results (3 independent physical codec golden archives)

| Stored codec (r24) | Original physical golden | One unique binary root key | **Two identical binary root keys** |
|---|---|---|---|
| RAW (codec 0) | Python/native read same SHA-valid member | Python, preflight, native **accept/read exact** | Python **ValueError**, preflight **ValidationError**, native **accept + exact read** |
| Zstd (codec 1) | Python/native read same SHA-valid member | Python, preflight, native **accept/read exact** | Python **ValueError**, preflight **ValidationError**, native **accept + exact read** |
| Deflate (codec 4) | Python/native read same SHA-valid member | Python, preflight, native **accept/read exact** | Python **ValueError**, preflight **ValidationError**, native **accept + exact read** |

**3/3 unaltered golden controls valid, 3/3 unique-bin controls valid, 3/3 duplicate-bin adversaries show a cross-reader acceptance discrepancy.** None skipped. The authentic Rust C ABI returned status `0`, file count `1`, successful range-read status `0`, and the original frozen logical SHA for all three hostile archives. The Python Reader rejects during index parse with `duplicate CMPCT MessagePack index key: b'O112-opaque-root-field'`. Python preflight likewise refuses the authenticated generation.

Hostile full-archive SHA-256:
- RAW `f1674361071d3411ce09f0e8e56cc67e4861349986c8c97d9eb358cff4017f2b`.
- Zstd `241fe04d3aaeb75ed08b2dda487e4815b0199043d99732246ef04c77a2ea362f`.
- Deflate `f28bace5330fe246bcee90d4164ba594ba79a266077641a0022f6803f2491079`.

The script rebuilds both identical index copies, computes the new primary SHA-256 and footer digest, verifies the data-span bytes are copied identically from each original golden, and performs same-wire product operations on the exact archive generated. This is not a checksum-bypass or unsound cross-input comparison.

## Causal mechanism and stronger control

The O0/O1 owner #316's Rust guard at `native/cmpct-core/src/lib.rs` records only `key.as_str()` names in `HashSet`, ignoring a MessagePack **bin** key such as `b'O112-opaque-root-field'`. Python's policy hook compares all hashable unpacked map keys. A unique bin key remains admitted by all three interfaces; the second identical bin key is the only semantic change between unique-control and adversarial arm. Therefore the difference is not explained by simply forbidding unknown binary keys, physical corruption, or a codec change.

The prior #316 string-root experiment remains true and separate. Its green string-root product test cannot establish parity over other MessagePack key types. The responsible decision is to keep #316 draft and widen its exactness scope only in the original implementation owner.

## Strongest negative / limitations / fallback

This is **negative current candidate product conformance** in an unmerged PR, not evidence of a defect in released v0.30.0 beyond #316's earlier original root-string evidence. No arbitrary nested-map, integer, extension, generational journal, Windows/macOS, untrusted index resource-limit or future canonical MessagePack grammar claim is earned. A bin key's exact semantic policy should be made explicit: allowing unique unknown bin keys requires rejecting duplicates consistently; alternatively reject unknown nonstring map keys **consistently in both readers** with legitimate archive compatibility tested.

The current instrument loads only three small signed independent golden members, not a full realistic corpus. It does not measure create/extract CPU/wall, peak RSS, temporary I/O, scalability, release parity or external competitor economics. A green scientific workflow indicates a **confirmed discrepancy**, not a product fix or release gate. No benchmark, threshold, evaluator, or code was relaxed.

## Counterfactual decision and owner handoff

The cheapest discriminator was one **unique binary extra field** plus the same field serialized twice, both index copies reauthenticated, on independent fixed goldens. Integers would have been rejected before Python's duplicate hook and were intentionally excluded from the primary experiment. No self-modification of discovery doctrine is earned from this single narrow residual.

**Next executable owner target:** in #316, implement and separately verify a bounded all-key/all-level consistent MessagePack ambiguity policy for Python and native Rust, preserve the three existing string-root negative vectors and nine O112 controls, and measure raw full-product costs before any merge. Preserve positive r24 archive compatibility. Reader composition remains #270, constructor cleanup #283, broader issue #317. If official release comparisons skip a substantive job, no performance approval can be claimed.

No `docs/discovery/STATE.json` mutation: this is one append-only research result, and that cache has concurrent owners.

## Exact-head CI truth

On result-bearing `26206de0d66fd5fe0db42b3c5d9412a982acbf3d` O112 scientific court, native core, version discipline, CI topology and R36 attribution were SUCCESS; Engineering Evidence initially failed required headings and passed after PR body correction on separate workflow #40229139039; generic tests and fuzz were in progress at first observation. The official r24/ZIP workflow was administratively SUCCESS but its **substantive benchmark was not inspected and receives no performance credit**. Later source/docs commits require independent exact-head reconciliation. Nothing is merged or released.
