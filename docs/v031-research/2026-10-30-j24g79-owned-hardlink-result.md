# J24G79 — physical signed hardlink/xattr ownership court: source-exact result

Date: 2026-10-30 UTC. **RESEARCH ONLY / NO PRODUCT CREDIT / NO RELEASE / NO MERGE.**

## Prospective question and ownership

The immutable [preregistration](2026-10-30-j24g79-owned-hardlink-prereg.md) was committed at `0fb19489013836e6be87fd95e0b1faf06576e810` **before** instrument/CI. It asks whether the no-copy private Reader decoder strategy from #820 (and scaled under #823) preserves *authentic POSIX hardlink inode + sparse signed xattr identities* through 63 mixed public Writer generations. #795/#817 retain product integration authority; #574 owns the shared Discovery state; #826 independently studies Writer economics. Main/release authority is v0.30.0 / revision 24.

Source-result SHA: `9a2718fb03f0f87866bb153c7da84550a38364a9`. The unchanged actual Reader blob is `29a8be64f3acfb027750351c6a567fd82cf7dc97`; experimental research source is identical to #820. Research test `research/j24g79_owned_hardlink_court.py` is not a production change.

## Decisive hosted physical evidence

The exact-head original [GitHub Actions #41048277198](https://github.com/FCMO-AI/.CMPCT/actions/runs/41048277198) completed **SUCCESS** on Ubuntu 24.04, macOS 14 and Windows 2022. Each host's log explicitly reported `J24G79_DECISION H1_PHYSICAL_PASS` at the same source SHA.

| Host | Original physical ZIP artifact | ZIP SHA-256 verified against provider | Actual archive bytes | Final index SHA-256 | Signed xattr paths |
|---|---|---|---:|---|---|
| Ubuntu | [#12972794195](https://github.com/FCMO-AI/.CMPCT/actions/runs/41048277198/artifacts/12972794195) | `51251a1b84ce5fdb673ae92c59c8abafc2bcb31ff8037134e726f3a2229e6673` | 29,253 | `8415e968b2d10e44bdfe76e74c79cb2a000937ab87110b1e21dd50c0a2126df8` | 3 |
| macOS | [#12974210008](https://github.com/FCMO-AI/.CMPCT/actions/runs/41048277198/artifacts/12974210008) | `37bf0ce74cc00bebe889df479c828330d556ab317f4afde7bc572615a6c2d1e0` | 29,369 | `5e41c9a971236c3af2940f4fac764b04c94257a86bc7f96f16b86d27562b99a9` | 3 |
| Windows | [#12972534976](https://github.com/FCMO-AI/.CMPCT/actions/runs/41048277198/artifacts/12972534976) | `2553a6d1e5a34369bb76b8a26d48536fe62358b781ad02fafd3b6ee9b003f252` | 28,147 | `b12d5dbaef1572c4097d4686d6428f66ba02b4ea8b230630a66f770e21a77759` | 0 |

All three originals were independently downloaded as ZIPs and compared bytewise to GitHub's published ZIP SHA-256. For each ZIP, an **off-Runner, no-CMPCT** physical interpreter written specifically for the result decoded raw footer struct, used system `libzstd` to decompress bounded payloads, interpreted MessagePack and SHA-256, replayed **21 renames, 21 deletes and 21 puts** into the final sorted index, and checked the complete MessagePack SHA against the original signed receipt. All 3 had 64 SHA-authenticated footers and **119 final members**. Each independently corrupted most recent footer SHA was refused. This detached cross-host audit is distinct from all Reader-class comparisons, even though it shares the documented revision-24 binary footer grammar.

In both actual POSIX cases, the no-CMPCT auditor located authenticated `z-alias.dat` as `K_HARDLINK=3` targeting `a-owner.dat`, and exactly three signed xattr paths `a-owner.dat`, `z-alias.dat`, `r000.dat`. The host-side extractor checked that owner and alias share **one physical inode** and that their native xattrs survived, along with a renamed xattr owner and no phantom xattrs on untagged members. Both research variants, plus unchanged installed Reader, produced identical full index/wire, verified all contents, passed strict preflight and recovered the same prior generation after corrupt/truncated latest footer. Post-open descriptor mutation remained possible on one instance but did not affect a newly opened Reader.

## Key negative and scope constraint

**Windows is not a physical hardlink fidelity pass.** Its original Builder represented `z-alias.dat` as a regular file (`K_FILE=0`) and recorded no xattrs. Windows passed only the *representable physical archive/logical equivalence/recovery* court. Do not count Windows as an independently verified same-inode/xattr reconstruction, nor infer cross-host archive byte identity: SHA and sizes differ.

This deliberately small realistic fixture cannot establish arbitrary hardlink owner renames/deletes, hardlink path cycles, conflicting inode xattrs, checkpoint transaction 64, large-N memory, native Rust ownership, or cold-cache / full-release economics. J24G73's inherited full-Reader acceleration measurements remain a separate research claim. The off-Runner auditor independently checks signed **index and operations**, not every CMA4 payload's decoded SHA; complete member payload validation was performed by inherited Reader `verify()` and byte comparisons, not a second independent blob codec implementation. Untrusted semantic errors beyond the two tail corruption shapes remain for the integration owner.

The private no-copy helper is unsafe on retained public input graphs: #820 has a positive alias-mutation counterexample, and this court demonstrated public post-open descriptors remain mutable. This positive result authorizes **no** generic public in-place no-copy API.

## Source custody and continuing proof

The branch added only `research/j24g79_owned_hardlink_court.py`, a dedicated three-host CI workflow, a no-CMPCT `research/j24g79_detached_wire.py`, and the preregistration/result notes. Independent on-Runner referee was added **after** the first three-host result, without touching inherited Reader/replay/test semantics; [subsequent exact-head run](https://github.com/FCMO-AI/.CMPCT/actions/workflows/v031-j24g79-owned-hardlink.yml) is separately tracked and must pass its own original-artifact audit before any claim about that new head. New referee also rejects forged archive/index receipts and deliberately corrupted signed footer SHA; older local off-Runner physical audit is already complete, but not a substitute for this subsequent CI.

The scientific decision is **H1 survives authentic POSIX hardlink + sparse xattr mixed-history control on Linux/macOS**, while Windows supports only logical Reader equivalence. It is a *scope extension* of the established private ownership seed, not a product performance/release win. No discovery-policy lesson beyond existing private-ownership qualification is earned; shared `STATE.json` remains untouched.

## Exact next bounded integration proof

Under #795/#817, test hardlink-owner rename/delete/recreate cases, same-inode conflicting xattrs, complete checkpoint-64 and fail-closed recovery, canonical source-hash ownership and independent parser hostility. Only then merge the single general replay into a private Decoder boundary, execute same-input official full product and native parity gates. Favor simple fallback whenever admission is not provable.

**Product credit 0. No merge. No version or format change.**

## Post-result falsifiability correction (same physical evidence, new HEAD)

The original three-host harness emitted the same string `H1_PHYSICAL_PASS` on all platforms even though Windows encoded `z-alias.dat` as `K_FILE=0` rather than a physical hardlink and captured no xattrs. **The string overstates the Windows claim.** No test was relaxed: the harness was corrected prospectively for *future executions* to issue `H1_PHYSICAL_POSIX_PASS` only on native POSIX hosts and `LOGICAL_PASS_NO_NATIVE_HARDLINK` on Windows. The no-CMPCT referee now separately rejects a receipt claiming physical Windows fidelity. Source repair commits `e3fcb7bc16f1af0c546e0548324da0428c3def67` and `70c208ac7054e733eba1ccbb2b3810e3323fa35d`. Earlier original source-head physical artifacts, independent reconstruction, and SHA results are unmodified; the refined evidence gate must pass at its **new exact head**. This is a narrow improvement in claim honesty rather than a change to physical semantics or a release win.
