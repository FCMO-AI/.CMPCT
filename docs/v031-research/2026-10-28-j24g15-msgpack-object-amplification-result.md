# J24G15 — authenticated MessagePack object-expansion memory falsifier

Status: **SCIENTIFIC RESULT CONFIRMED; NO PRODUCT PROMOTION**. Prediction locked in commit 3f6dcb04422af2090917f6d421f343b6d7d5656a before implementation. Independent child of parent PR #675 exact commit e5dc38006a49d38b4f68071c9afeed9db7366952. All experiments used unchanged installed revision-24 Reader Git blob f13c5492f5acfa1cfcfec97cdbe0da71e41e327b.

## Question, strong control, and direct observations

Does a one-megabyte raw-payload retention budget in J24G14 bound Python object allocations when an authenticated, syntactically valid MessagePack delta contains many small objects? A genuine first-party r24 Builder archive containing owner.bin received exactly one SHA-authenticated orphan delta footer with prev=0. Three cases: empty delta (13 payload bytes), opaque extension (800,028 payload bytes), and extension with 200,000 one-key maps (800,028 payload bytes). Both large archives occupied exactly 801,073 bytes, so file size cannot explain their memory difference. Eager (original installed CMPCT Reader), guarded (parse/discard), and adaptive (raw 1MiB retention with no switch) each received the same physical archive three times in fresh alternating subprocesses. Full read, range, strong verify and selection of the older checkpoint passed.

Corrected hosted court: GitHub Actions https://github.com/FCMO-AI/.CMPCT/actions/runs/40697542435 SUCCESS at **measured code HEAD 6621c707e0ac7a540a2febb88facadabc61940fb**, Ubuntu 24.04 / CPython 3.11. Original artifact ID 12819563461, ZIP sha256 595aadcf4b72aa706719688f63c6f67aa2414dee0dc2469a22d0ef3c279ebc50. Three-run medians:

| Case | Eager CPU / peak RSS | Guarded CPU / peak RSS | Adaptive CPU / peak RSS |
| --- | --- | --- | --- |
| Empty | 0.471 ms / 33,988 KiB | 0.462 ms / 33,988 KiB | 0.462 ms / 33,988 KiB |
| Opaque 800,028B | 2.729 ms / 34,668 KiB | 3.305 ms / 34,668 KiB | 2.730 ms / 34,668 KiB |
| Nested 200,000 maps, 800,028B | 50.546 ms / 69,044 KiB | 51.012 ms / 69,096 KiB | 50.899 ms / 69,016 KiB |

The nested-minus-opaque adaptive RSS difference is **+34,348 KiB (+33.54 MiB)** despite equal source payload bytes and raw retention below the 1MiB limit. Eager and guarded nested-case RSS differ from adaptive by at most 80KiB. Nested CPU versus opaque adaptive is approximately **18.64x**. The preregistered H1 discriminator therefore fired. The post-parse lifetime mechanism does not prevent initial parser-object allocation. This is a scoped hostile-input finding, **not a global bounded-memory proof, exploit claim, released-product improvement, natural-workload frequency or published benchmark win**.

## Critical first-run negative and corrected instrument

First code HEAD f7cd594f9ed1645eb7b91bdb5c3d71c88932a83d gave GitHub Actions https://github.com/FCMO-AI/.CMPCT/actions/runs/40697217059 technical SUCCESS but misleading H1_NOT_CONFIRMED: empty, opaque and nested all showed 73,204 KiB RSS. The experiment constructed and fully unpacked the hostile 200,000-map payload in the parent process *before spawning trial workers*, polluting the highwater inherited into the child. This was instrument contamination, not evidence the parsed object cost vanished. No original evidence was overwritten, no thresholds or comparator semantics were changed. Commit 6621c707 isolated payload creation in a short-lived process and removed parent unpacking. The unchanged Reader/control code and same-sized signed physical archive then revealed actual RSS differences. Never combine the first and corrected court medians.

Both dedicated workflows ran the unchanged stdlib-only independent receipt referee: corrected HEAD **316 raw consistency assertions, 5 forged receipt alterations rejected**. A separate external ZIP audit verified original ZIP SHA and CRC, source identities, all 27 raw Reader trial records, medians, physical archive hash/size, decision threshold and a separate falsified receipt: **183 additional checks**. Neither receipt referee includes or independently reconstructs the physical CMPCT archive bytes.

## Differently rooted detached control and semantic falsifier

An isolated, non-Reader MessagePack microprobe measured ~38,397,444 traced allocated bytes for the 200,000-map extension versus ~800,189 bytes for the equally encoded-size opaque extension. This corroborates parse-time object growth, but is micro evidence only. A speculative streaming projection using a MessagePack Unpacker to consume ops/blobs while skipping an unknown extension had ~841,521B traced allocation versus ~38,385,896B for full unpacking, and ~1.154ms versus ~146.656ms detached CPU, but **is NOT equivalent**. A nested extension with an unhashable map key raises ValueError during original full msgpack.unpackb, yet the naive skip silently accepts it. This hostile semantics counterexample forbids promoting naive skip/projection on these numbers.

## Convergence, limits and future question

One-MiB raw payload accounting does not bound decoded heap or peak process RSS; eager, guarded and adaptive all materially lose in the tested hostile nested case. This narrows, but does not retire, the demonstrated J24G14 improvements on long ordinary invalid ancestry. Any new candidate must preserve accepted/rejected MessagePack semantics including nested malformed structures, exact authenticated checkpoint selection, read/range/verify, recovery and all inherited source/format/release checks. The next cheapest decision-changing lane is to investigate a genuinely bounded parser/validated streaming projection against existing full-unpack semantics on authenticated malformed map keys, duplicate keys, excess nesting and schema variations. Rejecting data solely for crossing a new arbitrary object limit is a compatibility change and cannot be called an equivalent fix.

One host / Python 3.11, one signed delta shape, no physical archive contents in audit ZIP, no installed product change, no Windows/macOS, no updated release/format version, no exact-head final documentation CI attribution. Discovery STATE.json belongs to another owner (#574) and was not changed. No collision with parent PR #675. Counterfactual transferable lesson: isolate hostile fixture construction from subprocess RSS highwater measurements *before* treating a uniform peak as evidence; do not revise Discovery Engine policy from one episode.

**Conclusion: J24G15 H1 CONFIRMED as research. Source exact case: 200,000 small maps encoded in 800,028 bytes increase Reader peak RSS by 33.54 MiB versus same-size opaque control. Product source changes: 0. Merge: NO. Release credit: 0.**

## Cross-run independent receipt control (additional negative)

Both original GitHub-hosted ZIPs were independently downloaded and compared outside the candidate Reader. First confounded artifact ID **12818589898**, ZIP SHA-256 **0241492b3312484e6f2e67d5094159d6ac1d648e6b3830aaa6cae51c3ede72a1**; corrected artifact ID **12819563461**, ZIP SHA-256 **595aadcf4b72aa706719688f63c6f67aa2414dee0dc2469a22d0ef3c279ebc50**. Both have three equal-source Reader arms *within their respective run*. Their Builder-generated physical archives differ slightly **across runs**: original empty archive 1,056B and large archive 801,071B, corrected empty 1,058B and large 801,073B; cross-run archive SHA-256 differs. Thus the 73,204-to-69,016 KiB cross-run difference is **not itself** a same-file A/B estimate. The decisive inference uses **within the corrected run** matched nested vs opaque 801,073B archives, with their source object count and exact SHA recorded. Instrument correction is causal source-code diagnosis plus fresh within-run control, not averaging or cross-run identical-input inference. Both negative/positive original artifacts remain separate and retained.
