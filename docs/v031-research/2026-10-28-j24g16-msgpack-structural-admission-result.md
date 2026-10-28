# J24G16 — MessagePack structural node budget: decision and negative product verdict

Date: 2026-10-28 UTC. **DRAFT SCIENCE ONLY; no product, Reader, format, version, benchmark or release credit.**

## Source and measured head
- Preregistration: `2ecabb35f3d6e4897080bd4bc29f74119d202005`, preceding research code.
- Exact tested candidate source HEAD: `a0a3340a309b8dda3b6d4f60841c9ce876139433`; inherited Reader blob `f13c5492f5acfa1cfcfec97cdbe0da71e41e327b` is unchanged.
- Hosted Ubuntu 24.04 / Python **3.11.17** / msgpack **1.1.2**: [source-locked Actions #40708185923](https://github.com/FCMO-AI/.CMPCT/actions/runs/40708185923) **SUCCESS**; [original artifact #12824572663](https://github.com/FCMO-AI/.CMPCT/actions/runs/40708185923/artifacts/12824572663) with 72 raw matched observations, six original physical MessagePack vectors, source receipt and independent referee. The artifact name includes GitHub's PR event merge SHA; checkout and source receipt are bound to exact **head `a0a3340a`**, not to the artifact name.
- Independent standard-library-only referee: **681 checks PASS**, **6 forged receipts rejected**. The referee independently compares case/mode/repetition coverage, bytes, SHA-256, original decoder acceptance/refusal, CPU/wall/RSS and a measured minimum 12MiB RSS separation.

## Predictions versus observed
1. **P1 confirmed only in the microcourt:** 200,000 tiny maps in a physically matched 800KiB MessagePack payload yield an exact structural resource refusal before building the object tree at cap 65,536 nodes. Hosted matched fresh-process peak-RSS difference (original direct decode minus predecode gate) was **37,456 KiB = 36.58 MiB**. This is a *rejected input* improvement under a new experimental policy, **not** an accepted-payload memory optimization or a guaranteed whole-Reader memory cap.
2. **P2 held-out semantic boundary survived:** the scanner plus *unchanged canonical* `msgpack.unpackb(raw=False)` accepted 2,510 seeded valid MessagePack values and rejected six malformed controls. Critically, bare `Unpacker.skip()` accepted the nested unhashable map-key witness which original `unpackb` rejected; skip alone cannot be substituted for semantic decode. The scanner admits some malformed syntax for full decode to reject, which is intentional and safe. Resource refusals of otherwise valid but over-budget structures are a **deliberate acceptance-domain change**, not format compatibility.
3. **P3 falsified:** scanner + original decode is **6.3756× slower in process CPU** than original decode alone on the admitted 10,000-map metadata-like case, far above the preregistered **2.0× veto**. The pure-Python token scanner is **RETIRED as a default Reader product candidate** despite P1. Its safety/conservation result remains a research seed for native/token-aware admissibility APIs.

## Stronger controls and self-critique
Direct original `unpackb`, C-backed `Unpacker.skip` then original decode, and post-allocation `object_hook`/`list_hook` were run on identical bytes with three fresh subprocess repetitions per case. Flat scalar arrays bypass container-hook budgets; skip alone loses nested map-key semantic rejection. Scanner's extra traversal is expensive even without constructing objects, and cannot be hidden in an uncharged setup cost. No value was tuned after seeing results.

The first local Python 3.13 three-repeat court had **all arms reporting identical highwater RSS** because the controller generated the 200,000 objects before invoking measured workers; this was a **measurement-invalid artifact**, not a null memory result. J24G16b `7dfdd98a` moved generation to a separate short-lived process. Independent local corrected Python3.13 observations then reported 36,872 KiB matched RSS saving and 7.6446× ordinary CPU cost. These local numbers are not merged with the hosted result, and the shipped experiment is independently run from original GitHub source at `a0a3340a`.

The final head also added an exact node-cap boundary control: 65,536 tokens are admitted; 65,537 otherwise-valid tokens are rejected. That change is intentional in the research court and blocks direct product promotion under today's Reader acceptance/recovery contract.

## Safety and compatibility
No `src/`, `native/`, writer, builder, validation, CI gates, format, policy or version files modified. This run did not prove a safe policy for rejecting an over-budget *authentic signed tail* while recovering an earlier checkpoint; #658 already warns that a resource ceiling may abort all recovery instead of rejecting only a candidate. No process concurrent-modification guarantee, cross-platform result, full file-read test, realistic input-frequency model or complete product economics. Exact lossless reconstruction and portability retain full gates.

## Decision and next unclaimed action
**Stop implementing this pure-Python scanner into the Reader.** The narrow architecture question changed: can a native/extension-level token counter or schema-first decoder expose total object-count admission without second-pass Python traversal, while preserving the original decoding error semantics and the previous valid checkpoint on over-budget append? First use a charged component-level A/B with this direct-unpack control and skip-only negative, and require a meaningful ordinary-path CPU ceiling. Consider global memory-object caps and token counts a *new explicit product policy choice* not silently inferred from a positive research experiment.

There was no discovered concurrency claim or collision in this narrow implementation. No policy change to the Discovery Engine and no `docs/discovery/STATE.json` write; another owner is reconciling stale primary frontier state. Counterfactual discriminator: measure ordinary valid MessagePack decode first, not only the hostile map-heavy case. The 6.38× loss could have killed the pure-Python route before more expensive Reader integration.

## Engineering evidence / completion
- [x] authority, source parent, original blob, PR overlap checked
- [x] prospective prereg first, cheap falsifier before Reader changes
- [x] valid/malformed/boundary/held-out controls, 72 hosted case/mode/repetition observations
- [x] exact-source hosted judge, 681 independent checks, six forged negatives
- [x] RSS inherited-highwater defect diagnosed, corrected, and original negative retained
- [x] P1 narrow positive and P3 decisive product veto recorded
- [ ] general CI on this later documentation HEAD (separate from measured code HEAD)
- [ ] any product/parser/Reader/three-host memory/resource/recovery/benchmark/release credit (none earned)
