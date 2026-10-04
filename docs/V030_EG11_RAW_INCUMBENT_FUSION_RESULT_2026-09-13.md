# v0.30 EG11 raw-incumbent fusion result — 2026-09-13

Status: **PASS for exact EG08-equivalent fused creation; research evidence only, no release credit**

Candidate SHA: `8a6e3aa7b99487d915b9eba2f860b4b4410604b8`

Hosted run: `34764741529`

Job: `103743598114`

Artifact: `10319694556`

Artifact digest: `sha256:88459718ada5bf796b6166fd5bdbefb473cf544cda14124caaa114b5e270c9f7`

Scientific verdict: `EG11_RAW_INCUMBENT_FUSION_PASSES`

## Entering negative

EG10 attempted to reproduce EG08 while fusing ordinary final-pack effort into the first pass and retaining only a cold-stream post-pass rewrite. Its hosted referee was faster in aggregate but failed exact identity on Office:

- EG08 Office: `5,954,128 B`
- EG10 Office: `6,083,910 B`
- delta: **+129,782 B**

The other eight frozen surfaces were byte-identical. Code review found that EG09/EG10 returned immediately when EG07's level-1 candidate failed the `compressed + 8 < raw` admission law, even though EG08 re-audits every non-hot pack and can promote a level-1 RAW incumbent at a higher effort.

EG11 preregistered that discrepancy as the sole causal hypothesis before changing the implementation.

## Exact result

All nine frozen eligible surfaces are complete-archive byte-identical to EG08:

- `9/9` complete archive identity;
- aggregate byte delta: **0 B**;
- aggregate absolute byte delta: **0 B**;
- `9/9` strong verification;
- `9/9` tail recovery;
- identical locality geometry on every row;
- no confirmed per-workload CPU regression;
- no confirmed per-workload wall regression;
- maximum positive RSS delta: **0 KiB**.

Aggregate creation measurements:

- EG08 CPU: `32.306359501 s`
- EG11 CPU: `31.878808183 s`
- CPU ratio: **0.9867657x**
- EG08 wall: `32.320286395 s`
- EG11 wall: `31.894695450 s`
- wall ratio: **0.9868321x**

Thus the exact-equivalent fused path is about **1.32% lower CPU** and **1.32% lower wall** than EG08 on this hosted same-runner matrix while producing exactly the same complete bytes.

## Causal confirmation

Across all nine workloads:

- requested-level-19 final-pack calls: measured by the receipt per row;
- raw-incumbent calls: **132**;
- raw-incumbent promotions: **1**;
- raw-incumbent saved bytes: **129,782 B**.

The single promotion occurred on Office and recovered exactly the byte deficit seen in EG10:

- Office raw-incumbent calls: `1`;
- Office raw-incumbent promotions: `1`;
- Office raw-incumbent saved bytes: **129,782 B**;
- EG11 Office: **5,954,128 B**, byte-identical to EG08.

This strongly confirms the preregistered causal explanation rather than merely finding another configuration that happens to match the total.

## Representative access/resource state

Office remains at:

- max read amplification: `4.0011285266x`;
- max decode unit: `524,288 B`;
- strong verification: PASS;
- tail recovery: PASS;
- RSS delta vs EG08: `0 KiB`.

Every other row also preserved EG08 locality geometry. No locality, integrity, recovery, filesystem, comparator or workload rule was weakened.

## Interpretation

EG11 supersedes EG10 as the strongest known exact-EG08 creation path. The key result is not a new density win: it is that EG08's already-earned bytes can be produced with less duplicate effort **without changing a byte of the artifact**.

The experiment also retires the incorrect assumption that a pack stored RAW after EG07 level-1 admission can be skipped during higher-effort fusion. A RAW incumbent is an economic storage choice, not proof that higher effort cannot later cross the same admission law.

## What this does not prove

This PASS does **not** promote EG08/EG11 to canonical v0.30 and does not change Genesis or R4 scores. EG11 reproduces EG08 exactly, so all remaining EG08 debts remain:

- eligible-nine low-yield/export justification;
- strong-verification/read-cost accounting;
- transfer beyond the frozen eligible surfaces where required;
- exact-candidate native/platform/release receipts;
- final composition against the direct v0.29 product floor.

No numeric version, format revision, release claim or ONE status changes from this result.

## Next decisive question

With creation duplication materially reduced while preserving exact bytes, the next decision should be based on EG08's remaining **reader/exported-cost** debt rather than another encoder micro-optimization. In particular, measure whether the stronger stored-byte result exports unacceptable work into strong verification, selective reads, or native reader complexity. If the read-cost referee is already durable and negative, attack that specific mechanism; if it is green, proceed to the eligible-nine/composition gate without reopening the fused encoder.
