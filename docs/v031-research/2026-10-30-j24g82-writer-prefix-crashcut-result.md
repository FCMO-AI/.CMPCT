# J24G82 — physical every-prefix crash-cut result (research only)

**Decision 2026-10-30 UTC: NARROW HYPOTHESIS SURVIVES, 3/3 HOSTS. No Writer/product/release/promotion credit.** [Draft PR #830](https://github.com/FCMO-AI/.CMPCT/pull/830). Base [#829](https://github.com/FCMO-AI/.CMPCT/pull/829) exact parent `d29c8b6b64017ab912cfd219d598501e00b62a72`; frozen-before-code prereg `767c8ba713b5826de1028fa71f0f644c3148b88c`. Authoritative published product remains v0.30.0, physical format revision 24; the files `src/`, `native/`, original Writer and Reader are unchanged.

## Primary question / experimental scope

Can every one of 64 authentic signed public and private session Writer mutations recover its most recent **previous committed** generation if the attempted new generation is physically interrupted at six distinct cut/corruption conditions, while retaining exactly the same fully committed archive bytes and semantic state?

J24G80 #829 already established that a *quiescent* retained-index Writer can create the **same 64 intermediate physical SHA256 and byte lengths** as the normal public Writer, with original payload/footer fsyncs. Its larger-scale Ubuntu A/B/B/A experiment reported 29.381× for 8,192 and 32.167× for 32,768 in 63 consecutive deletes, but proved neither external concurrency safety nor per-prefix torn-tail recovery. Our narrow court uses 192 members to make an exhaustive per-prefix adversarial check affordable. It is **not** a new Writer optimization or a product benchmark.

## Evidence and provenance

The first test-only HEAD `00d35197962ec88775206c7202e6482e78d22e10` had [hosted run #41055588299](https://github.com/FCMO-AI/.CMPCT/actions/runs/41055588299) **SUCCESS 3/3** on Ubuntu 24.04, macOS 14 and Windows 2022. All three original artifacts were retrieved and verified against GitHub's exact uploaded ZIP SHA-256; an independent *container-side* wire decoder rebuilt all 65 authenticated linked footers, exact each-generation opcode/previous pointer, the 64th full checkpoint, 64 per-generation byte prefix hashes, and all recorded 896 recovery-state checks/host without importing CMPCT. The container-side audit also confirmed same-platform physical public/private identity.

An additional separate GitHub Actions implementation of the signed-wire referee, `research/j24g82_wire_referee.py`, was then bound to the actual executing HEAD and made a **required** step, including four distinct forged-receipt rejections per host. That stronger measured code/workflow HEAD was **`3daff73707906cd9b89be014a1f19afd446b43de`**. Its [exact-head specialized run #41056131954](https://github.com/FCMO-AI/.CMPCT/actions/runs/41056131954) finished **SUCCESS 3/3**, and the three *new original artifacts* were downloaded, checked against GitHub's ZIP digests and independently re-parsed again outside CMPCT.

| Host | Final-source exact run artifact | Provider ZIP SHA-256 | Detached reconstructed physical archive SHA-256 |
| --- | --- | --- | --- |
| Ubuntu 24.04 | [#12977356305](https://github.com/FCMO-AI/.CMPCT/actions/runs/41056131954/artifacts/12977356305) | `608e9bd50e4885b744d958c8c6a91f7b39db5b1558ba6f034fec99484c579cb6` | `5b6aeace4859947ed0a681877552e025632d063ed318383fc4bf48706dd75cb9` |
| macOS 14 | [#12976334499](https://github.com/FCMO-AI/.CMPCT/actions/runs/41056131954/artifacts/12976334499) | `6fb55180707b1472f003fcc00816db8b7914f414c56143fd4b59aef611ccd8d2` | `6f85fcf18373579081e19531d61abb799b717d6e74f2ef94bc8605e3e8d78673` |
| Windows 2022 | [#12977655025](https://github.com/FCMO-AI/.CMPCT/actions/runs/41056131954/artifacts/12977655025) | `ffe08510062fad35bb063eadb12e286cfcd6be3de484ac50cb10c9dce33e5af7` | `21f8bc6342bd470e7e5e5b3be27e2a26e281be5f6826c5ac05a553f244c76048` |

The synthetic Builder baseline and physical archives naturally differ *between* operating systems because filesystem modes/metadata differ. All A/B physical bytes and 64 intermediate SHA/length witnesses match **within** each host.

Each platform used 192 deterministic source files, 64 actual public deletes and 64 source-exact private session deletes, 65 total authenticated footer positions, and checked **448 states for public plus 448 for private**. Each generation was tested as fully committed and at five distinct partial write lengths plus a fully written footer with flipped final SHA byte: **896 checks/host, 2,688 across three hosts**, each opening original CMPCT Reader, running strong full-member verification, checking exact membership and strict preflight state. Final valid generation 64 is a full checkpoint; its damaged boundary must recover generation 63. The source-exported physical archive is also independently parsed as a signed linked chain.

All 12 forged receipts (4/host) were correctly rejected by the hosted standalone referee. The local independent original-artifact verifier *separately* recalculated the provider digests, footer grammar, opcode identities, SHA, physical cut-position claims and per-recovery logical name-hashes.

## What the result changes — and what it does not

**Survived:** the existing private quiescent Writer's same-byte signed stream is not merely eventually correct; it admits correct rollback of each possible truncated final-generation boundary under the tested physical cut model, with Reader and preflight agreeing, including the 64th checkpoint. No additional archive bytes are introduced by this *test*.

**Counterfactual insight:** since #829 had already proved byte-exact per-generation identity, deterministic Reader/preflight behavior is necessarily identical for the same physical prefix; executing two full original Readers per cut was **not** necessary to distinguish the Writer variants. The genuinely missing decisive observation was whether **every intermediate torn prefix actually recovers safely**, not whether equal bytes are parsed differently. Future repetitions should test one common physical byte stream with independent wire admission and only repeat across variants if the physical byte identity premise itself becomes questionable. This is a prospective experiment-design lesson, **not** sufficient evidence for a Discovery Engine policy edit.

**Strongest negative / bounds:** this is deterministic **fault injection into stored bytes**, not true process kill, power loss, journal/drive flush reorder, cross-process Writer lock, archive inode replacement/ABA, opportunistic uncooperative appends, races involving source data, signed native xattrs, hardlink owner changes, sparse/CDC payloads, external network filesystems or native Rust Reader equivalence. The fixture is only 192 regular members. An archive SHA and independent metadata referee are not an independent decoder of every compressed member; full-content checks were performed by the original product Reader. Neither reader memory/RSS nor entire product size/create/extract was measured for this experiment.

**Infrastructure note:** the original material-PR Engineering Evidence job initially failed because PR description had noncanonical headings and missing explicit `disproof` / `quality-ratchet` marker strings. The PR description was corrected **without changing the evaluator, code, baseline, thresholds, or measurement**. A run reporting CI success is considered separate from product/science correctness; exact-head latest status must be checked after this documentation commit.

## Decision and next executable priority

Keep #829's original private Writer-session candidate protected as a large **research-only** speedup and preserve the independent recovery result here. Do **not** integrate an implicit global cache or claim safe concurrent updates. Independent [issue #290](https://github.com/FCMO-AI/.CMPCT/issues/290) and [PR #289](https://github.com/FCMO-AI/.CMPCT/pull/289) already proved silent lost updates even with serialized physical appends if the predecessor snapshot isn't exclusively owned. #295/#304/#409 own the cross-process / Windows / source admission lease architectures.

The strongest *simpler* next product control (raised in #829 comments) is to test the already proven private-owned Reader reconstruction (#820/#823) **inside the ordinary public Writer**, retaining separate transaction ownership per append. If it reaches comparable whole-Writer benefit, a long-lived session lease may not justify its complexity. Otherwise combine retained index and Writer session **only** under an explicit locked inode/lease from predecessor snapshot through signed final fsync, with independent processes and replacement/ABA/recovery hard negatives. Bring signed xattrs/hardlinks (#795/#817/#828) into the same product proof. This is a new bounded productization question, not a reason to spin another duplicate implementation.

**Discovery/coordination:** no concurrency implementation collision, no changes to #829/#795/#817/#828 ownership surfaces, and no edits to `docs/discovery/STATE.json` (owner #574). Primary discovery outcome is a narrow safety hypothesis **advanced**, not a generic release capability; no evidence-backed policy amendment earned.

**Credit:** research/physical recovery evidence YES; new shipping Writer implementation NO; product performance credit 0; merge 0; release 0.
