# J24C16 installed Reader negative: in-memory mutation invalidates retained authenticated prefix hints

Date: 2026-10-28 UTC. **Independent signed-source installed product-correctness falsifier, NOT an on-disk malicious archive admission bypass and NOT a product fix.**

## Exact baseline, hypothesis and source

Owner source PR #662 `a66fd593a83cc4c71556d3d86d835c51abd20a96`, Reader Git blob `c4d1dee0a31527b814d6e1f41b77abe1cc987996`; original research source measured at **`74a9c5ce66db2f18b4ed0309a0f48b8e577f2750`** in isolated draft PR #672. [Prospectively frozen preregistered question](2026-10-28-j24c16-mutable-index-prereg.md), commit `cb88367fcd8203e7bffffa3de499660de0905998` **before implementing** the real instrument.

The public Reader uses a signed R24 index initially validated by native ABI3 and then retains stride-256 prefix maps across reads. Its Python `index/files/by` descriptor lists are caller-visible and mutable. The question: does swapping two valid refs across a stride boundary **after** trusted initial admission make an old prefix hint return wrong bytes, without altering any archive file bytes?

## Actual installed result

**`STALE_HINT_INSTALLED_WRONG_BYTES` — scientifically reproduced.** Source-exact [Ubuntu Python 3.11 hosted court #40683558265](https://github.com/FCMO-AI/.CMPCT/actions/runs/40683558265) **SUCCESS**, [original GitHub artifact #12814470538](https://github.com/FCMO-AI/.CMPCT/actions/runs/40683558265/artifacts/12814470538) downloaded and independently reconciled.

| Requirement | Actual |
| --- | --- |
| Actual installed source | `.../lib/python3.11/site-packages/cmpct/reader.py` |
| Source HEAD | `74a9c5ce66db2f18b4ed0309a0f48b8e577f2750` |
| Product Reader Git blob | `c4d1dee0a31527b814d6e1f41b77abe1cc987996` |
| Real native ABI3 helper | Loaded, generated nontrivial tuple `(0,257)` |
| Complete authenticated signed r24 file | **635 bytes**, SHA-256 `2d4a118563bb712977afe6a41dd09ae4b34ebe6f3c6449355358c669c6af9337` |
| Original strong `verify()` and full read | PASS before mutation |
| Original `read_range(257,1)` | `b'A'` |
| Mutation | Swap only in-memory refs at positions 0 and 256; no archive/physical blob mutation |
| Post-mutation logical length | Remains exactly 512, including zero-length owner |
| True prefix at reference 256 | 255, versus retained 257 |
| Indexed `read_range(257,1)` | **`b'B'` — incorrect** |
| Same live ref list with index bypassed | `b'A'` — exact linear control |
| Signed archive hash after mutation | Unchanged |

The independent second-root referee `J24C16_SECOND_ROOT_PASS` also rejected seven deliberately forged receipt fields. A *third* local extraction independently verified the two archived JSON SHA-256 values against `SHA256SUMS.txt`, the commit and reader blob identities, the native mark and both contrasting answers. Exact archived JSON SHA-256: raw **`2a1af5a3593358ae0c23bf515e018e389787294eae3ce3ee0dc26d8e6e26ac0e`**, referee **`37b4f555fc7ea3dc698d2888f5b7839de4b76a84a4d2e2ad0b8143a120cbaef9`**. Artifact ZIP flattens `receipts/` folder on download; verifier matched the filenames against preserved SHA256SUMS entries, without changing artifact content.

## Interpretation, strongest negative and limits

This establishes the previously hypothetical **post-construction mutable Python descriptor / retained search hint consistency failure** in a real installed Reader and a genuinely authenticated archive. It **does not demonstrate** that a malformed signed on-disk archive can bypass the Reader constructor; that archive was initially correct and still passes strong verification before the deliberate **in-process** caller mutation. It does not prove a vulnerability when the caller never mutates the exposed index, or that arbitrary untrusted code can remotely mutate these objects.

The result is product-correctness *research evidence* for a mutability boundary, **not a ready product fix**, and not a claim about Windows/macOS, Python 3.10 fallback, concurrency, recovery/extraction or frozen release gates. Existing owner docs already acknowledged the risk; this experiment makes it concrete and falsifies the assumption that retained marks remain exact under arbitrary public list mutation.

**Future owner-safe fork:** freeze a private logical-descriptor view used for range operations, or establish an API/epoch contract that fails closed on mutation. Charge duplicate memory, copy CPU, per-reader mark budget and short-Q1 cost; rehash/revalidate O(N) before every read would erase the proven repeated-range Q64 gains. The extra alternative must preserve correct archive semantics, stronger guarded-reader validation and 0-byte compression/format regressions. An immediate shallow-copy oracle on local CPython 3.13 showed `tuple(refs)` copies 262,144 refs in ~0.404ms and adds 2.10MiB; `array('I')` ~1.397ms and 1.05MiB (u32 only), **not measured full-product improvement**.

## CI/evidence accounting

Initial hosted [run #40683338094](https://github.com/FCMO-AI/.CMPCT/actions/runs/40683338094) failed **before the J24C16 falsifier** because inherited `test_j24c13` expected no native extension despite deliberately installed native ABI3. The fix set the two inherited EXPECT_NATIVE environment signals in the research workflow only, without changing tests, product code, external oracle or preregistration. Measured code `74a9c5ce` then passed inherited targeted baseline: **2 passed, 20 deselected**, plus original and independent J24C16 result. Generic CI has separate inherited historical-evidence/fingerprint errors; **no claim of full green**. Engineering Evidence PR-body schema was initially incomplete; the PR body was amended with concrete accepted headings; a fresh exact-head run must confirm the updated event snapshot.

No merge, release, format change, HEAD library product mutation, public website claim, or shared Discovery state update.

## Handoff

1. Owner #662 retains implementation scope; preserve both the raw original and evaluator, no comparator or gate changes.
2. Reject any proposal that labels this mutable object test as on-disk authentication failure without the additional on-disk evidence.
3. Choose a private frozen descriptor ownership model with bounded indexed-memory delta and concrete delayed read invalidation tests; run against the same installed Reader and hostile/correctness controls.
4. Do not paper over the J24C15 early Q1 admission debt or release-floor semantics while fixing this separate integrity boundary.
