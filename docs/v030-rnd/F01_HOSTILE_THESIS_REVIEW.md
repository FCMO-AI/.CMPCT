# F-01 hostile thesis review

Status: **completed — retire F-01 as the active primary thesis; no superseding freeze authorized**.

Authority:

- doctrine: `docs/FUNDAMENTAL_RESEARCH_DOCTRINE.md`;
- active thesis entering review: `docs/ACTIVE_RESEARCH_THESIS.md` at `TRANSFER_FAIL / HOSTILE_REVIEW_REQUIRED`;
- accepted O0.1 result: `docs/v030-rnd/F01_O01_RESULT.md`;
- accepted causal result: `docs/v030-rnd/F01_CAUSAL_RESULT.md`;
- accepted transfer/AOM result: `docs/v030-rnd/F01_TRANSFER_AOM_RESULT.md`;
- assumption input: `docs/ASSUMPTION_LEDGER.md` A04/A05 and adjacent A01/A02/A03/A06 opportunities.

This review changes thesis state only. It does not edit or reinterpret any frozen F-01 preregistration, grammar, threshold, corpus label, comparator or result.

## Question under hostile review

F-01 proposed that a bounded exact compiler over a small reversible grammar could discover materially smaller exact descriptions and that the resulting mechanism could advance toward a trustworthy general structural opportunity class.

The first clause survived strongly. The stronger causal/generalization clause did not.

## Immutable evidence

### What survived

The compiler produced exact fully charged composition wins in O0.1 and transfer. Accepted O0.1 material wins included 552 B / 26.41%, 561 B / 18.18% and a post-freeze transfer win of 427 B / 23.17%. Causal ablation showed SPLIT was necessary for those composition wins; removing it restored the one-stage control. LANE[8]/LANE[16] were causally active on the seed.

The frozen structural-transfer run then found six material positive-family winners across `lane+record` and `lane+lane`, spanning 32–128 KiB, with 11,378 B total saving on the synthetic winner set and ~23.05% conditional saving inside material winners.

Therefore the one-stage representation assumption remains falsified: exact composition is real headroom, not measurement noise or uncharged metadata.

### What failed

The preregistered hostile `offgrid-lane-record` case also received a material composition win: 6,991 -> 3,091 B, saving 3,900 B / 55.79%. Under the frozen interpretation this is a hostile material false win and forces `TRANSFER_FAIL`.

The seed-derived `{8,16}` grammar-pruning claim also failed exact transfer. Removing widths 2/4 reduced generated/costed states by ~36.48%, but did not preserve every exact optimum because LANE[4], inactive on the causal seed, became useful on transfer cases.

These are two independent anti-overfit constraints:

1. the human structural labels used by F-01 do not define a trustworthy admission boundary for what the compiler can exploit;
2. seed-local operator inactivity is not sufficient evidence for global grammar pruning.

## Candidate rescue claims considered

### 1. Relabel the hostile winner as a positive

Rejected. That would change the frozen interpretation after seeing the result. More importantly, it would not supply a predictive causal predicate; it would merely declare every profitable exact composition to be intended after the fact.

### 2. Move or densify the split grid

Rejected. The hostile failure was not a missed opportunity caused by insufficient search reach; the grammar already found the hostile win. Grid expansion would increase carrying cost without explaining generality.

### 3. Add operators so the positive labels become more distinctive

Rejected under F-01. Operator expansion changes the mechanism but does not explain why a pre-result observable property should separate intended structure from opportunistic compressibility. It also violates the old freeze as a rescue move.

### 4. Use compression gain itself as the admission predicate

Not sufficient for a new Foundry thesis yet. Exact measured gain can be a correct encoder tournament rule, but using expensive synthesized size as the sole predicate moves the unresolved question into O1 discovery economics and global carrying cost. It does not provide the missing causal account required to reopen F-01, and it risks reducing the thesis to “search more compositions and keep winners.” That is useful research tooling, not yet a new information-model claim.

### 5. Predict profitable composition from a pre-search structural statistic

Potentially valid, but not yet charterable. A reopening would need a pre-result observable such as independently measurable field/lane heterogeneity, residual mutual information, boundary-conditioned entropy reduction, or another structural statistic that predicts composition headroom across positives and hostile negatives before exhaustive synthesis. No such predictor is presently established by repository evidence.

## Thesis Initiation Gate review

A direct F-01 continuation does not clear the finalized doctrine's initiation gate:

- **Worldview delta:** already established; composition can beat one-stage transforms.
- **Capability delta:** established at O0, but not tied to a trustworthy opportunity predicate.
- **Non-triviality:** passes.
- **Prior-art boundary:** adequate for the old thesis.
- **Plausible headroom:** passes strongly.
- **AOM hypothesis:** synthetic headroom exists, but real addressable opportunity is unsupported because the structural label boundary failed.
- **Cheap decisive oracle:** a new oracle is only justified after a new causal predictor is specified; otherwise it repeats the same search with new labels.
- **Disproof rule:** can be written, but without a new predictor it would be ceremonial.
- **Product survival sketch:** unresolved discovery/carrying cost remains material.
- **Complexity/carrying cost:** full grammar required 2,064 generated/costed states and 2,752 nominations per logical MiB; the attempted ~36.48% simplification did not preserve optima.

Result: **no superseding primary thesis is authorized from the current evidence.**

## Scoped negative constraint

Within the tested F-01 grammar and transfer regime, material exact composition gain is broader than the human `lane+record` / `lane+lane` labels used for structural admission. Those labels cannot be used as a generality proof or product admission predicate. Seed-local operator inactivity likewise cannot justify global pruning without held-out optimum-preservation evidence.

This is not a universal claim that reversible program synthesis is unhelpful. Reopen only if new causal evidence supplies a pre-result, content-derived predictor of composition headroom that can be preregistered and challenged against generator-distinct hostile cases without benchmark identity.

## Relationship to the Assumption Ledger

A04/A05 remain open scientific territories: logical byte order and handcrafted transform vocabulary are still questionable assumptions. F-01's failure narrows how they may be attacked. Future work should not begin from “add more DSL operators.” It should begin from a new causal observable explaining when/why a reversible composition creates description-length headroom.

A01/A02/A03/A06 remain separate candidate worldview questions and are not promoted merely because F-01 retired.

## Decision

**F-01 -> `FAMILY_RETIRED` as the active primary thesis.**

Preserve the compiler and all evidence as a reusable research instrument/constraint. Do not productize F-01, extend its old grammar, or continue its old structural-transfer claim. The Foundry returns to **no active primary thesis** until a candidate independently clears the Thesis Initiation Gate.

The next Foundry heartbeat should inspect the Assumption Ledger and newly exposed residual costs, but Forge D5 convergence may proceed without waiting for a replacement thesis.

## Reopening predicate

F-01's research family may be reconsidered only when all of the following are true before result-bearing execution:

1. a new observable, content-derived causal predictor of composition headroom is stated;
2. the predictor is computable without benchmark identity and without gifting decoder semantics;
3. a frozen generator-distinct transfer challenge contains both predicted-positive and predicted-negative structures;
4. exact representation bytes and reconstruction remain fully charged;
5. the experiment has an explicit hostile false-positive threshold and a global carrying-cost account;
6. the new claim is recorded as a superseding thesis/freeze rather than an edit to F-01 evidence.
