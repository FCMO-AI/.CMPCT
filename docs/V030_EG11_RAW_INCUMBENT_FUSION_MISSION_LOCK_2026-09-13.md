# v0.30 EG11 raw-incumbent fusion repair Mission Lock — 2026-09-13

Status: **preregistered Builder contract; research only**

## Entering evidence

EG10 attempted to reproduce EG08 exactly while fusing EG08's `(3, 6, 12, 19)` effort ladder into first-pass ordinary final-pack creation and post-rewriting only cold stream packs. Hosted run `34764259533` preserved strong verification, recovery, locality geometry and zero positive RSS delta, and reduced aggregate creation CPU/wall to about `0.966x` EG08, but it failed exact identity on Office only:

- EG08 Office: `5,954,128 B`
- EG10 Office: `6,083,910 B`
- delta: **+129,782 B**
- all other eight frozen surfaces: exact archive identity and zero byte delta.

The same receipt reports one changed cold stream pack saving `2,419 B`, so the Office mismatch is not explained by failure to recover the cold-stream effort class.

## Code-level causal discrepancy

EG08 starts every non-hot pack from the *actual EG07 stored representation*. If EG07 stored a pack RAW because level-1 Zstd failed the `compressed + 8 < raw` admission law, EG08 still auditions levels 3/6/12/19. A later effort may cross the same admission law and legitimately promote that previously-RAW pack to compressed storage.

EG09/EG10 currently return immediately for requested-level-19 ordinary packs whenever the level-1 incumbent does not satisfy the admission law:

`if requested != 19 or len(incumbent) + 8 >= len(raw): return incumbent`

The second predicate is therefore stronger than EG08 and is not representation-equivalent. It can suppress exactly the class `EG07 RAW -> EG08 compressed at higher effort`.

## Falsifiable hypothesis

The entire Office identity failure is caused by that suppressed raw-incumbent promotion class.

A first-pass fused implementation that applies the *same EG08 storage economics* to requested-level-19 calls — using RAW as the incumbent storage choice when level 1 fails admission, continuing through ties, and stopping on the first strictly worse storage choice — followed by the unchanged EG10 cold-stream rewrite will reproduce EG08 byte-for-byte on all nine frozen surfaces.

## Disproof

The hypothesis is false if any of the following occurs:

- any of the nine complete archives differs byte-for-byte from EG08;
- any stored-byte delta remains;
- strong verification, tail recovery or locality geometry differs;
- the corrected fusion changes a surface that EG10 already matched;
- Office has no raw-incumbent promotion events yet identity still differs.

A mismatch is preserved as negative evidence; do not tune levels, thresholds, workload rules or pack geometry after seeing it.

## Frozen mechanism

For requested-level-19 final ordinary pack calls only:

1. compute the inherited capped level-1 compression exactly as EG07;
2. define the incumbent *stored* size as level-1 compressed bytes only when `len(level1)+8 < len(raw)`, otherwise RAW bytes;
3. audition levels `(3, 6, 12, 19)` exactly as EG08;
4. for each rung, define candidate storage as compressed only under the unchanged `+8` admission law, otherwise RAW;
5. continue on strict win or tie; stop at first strictly worse candidate;
6. return the selected compressed frame when compressed wins; otherwise return a non-admitted frame so the unchanged V25 caller stores RAW;
7. retain EG10's post-pass cold-stream-only rewrite unchanged.

No path, extension, corpus identity or learned threshold enters the decision.

## Required measurements

Same generated input per row, EG08 vs EG11 on the frozen eligible-nine surfaces:

- complete archive SHA-256 and byte identity;
- stored bytes and byte delta;
- fresh-process creation CPU/wall;
- peak RSS;
- strong verification;
- tail recovery;
- locality geometry, maximum decode unit and `<=8x` amplification;
- requested-level-19 call count;
- raw-incumbent call count;
- raw-incumbent promotion count.

## Success

`EG11_RAW_INCUMBENT_FUSION_PASSES` requires:

- 9/9 complete archive identity to EG08;
- zero byte delta on all nine;
- 9/9 strong verification and tail recovery;
- identical locality geometry;
- at least one raw-incumbent promotion event on Office;
- aggregate creation CPU and wall strictly below EG08;
- no confirmed per-workload creation regression under the inherited `+5% and +3 ms` timing rule.

Passing EG11 does not itself promote EG08. The eligible-nine low-yield export gate and the separate strong-verification read-cost debt remain required.

No numeric version, Genesis score, comparator, locality, integrity/recovery or ONE status changes in this Builder.
