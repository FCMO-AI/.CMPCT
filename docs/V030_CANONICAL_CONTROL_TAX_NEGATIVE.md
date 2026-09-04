# v0.30 canonical control-tax negative

Status: **exact-head scoped negative / Forge retirement evidence**

This note preserves the causal result from the exact canonical product-gap diagnostic on authoritative candidate `4c77fdde54b9c34968e462e847c8d25844db4631`. It grants no release credit and does not alter any frozen threshold.

## Question

Can Office and Analytics cross the accepted v0.29 complete-artifact floor by further shrinking, reframing, or eliminating only the canonical r25 filesystem-control representation, while leaving their selected content representation unchanged?

The test deliberately gives this family an optimistic advantage: the counterfactual deletes **all** filesystem-control physical bytes rather than merely finding a more compact legal encoding. Search/discovery cost is irrelevant to this lower-bound question. Content bytes, the accepted v0.29 floor, exact reconstruction requirements, and the strict-tie rule are not gifted.

## Exact evidence custody

- candidate: `4c77fdde54b9c34968e462e847c8d25844db4631`
- workflow run: `33509114566`
- proof job: `99860894595`
- result: success
- artifact: `v030-canonical-product-gap-4c77fdde54b9c34968e462e847c8d25844db4631`
- artifact id: `9801415681`
- artifact ZIP SHA-256: `d27e2acebbd868960c5f7947ecb7f293b4cec672632fb2c51487d94b517bcbc7`

The proof used the ordinary frozen benchmark fixtures and the same accepted-v0.29 identities used by the canonical product-gap diagnostic. It is evidence about physical byte capacity, not product creation speed or release readiness.

## Office

- accepted v0.29: **5,954,924 B**
- accepted artifact SHA-256: `d3c6029015cd590732eac245e54f62d6ac3c48103efba060b1d9a6749a60ce59`
- direct canonical r25: **5,955,232 B** (**+308 B**)
- selected implicit-v4 control payload: **223 B**
- explicit filesystem-v1 control payload: **1,798 B**
- implicit-v4 raw control saving: **1,575 B**
- effective complete-artifact control cost: **308 B**
- framing/physical overhead beyond selected raw control: **85 B**
- zero-control optimistic counterfactual: **5,954,924 B**
- zero-control delta versus accepted v0.29: **0 B**
- strict remaining control budget: **-1 B**
- minimum additional non-control saving required from the current direct representation: **309 B**
- genuine r24 fallback: **15,453,978 B**
- strong verification: true

Deleting every filesystem-control byte merely reaches an exact tie. The release/product law rejects ties.

## Analytics

- accepted v0.29: **6,135,172 B**
- accepted artifact SHA-256: `d3b2622c050d46157897323730efbda8120d472e18a71c8c7efd2c6c8d3ac0fb`
- direct canonical r25: **6,135,348 B** (**+176 B**)
- selected implicit-v4 control payload: **49 B**
- explicit filesystem-v1 control payload: **504 B**
- implicit-v4 raw control saving: **455 B**
- effective complete-artifact control cost: **176 B**
- framing/physical overhead beyond selected raw control: **127 B**
- zero-control optimistic counterfactual: **6,135,172 B**
- zero-control delta versus accepted v0.29: **0 B**
- strict remaining control budget: **-1 B**
- minimum additional non-control saving required from the current direct representation: **177 B**
- genuine r24 fallback: **10,392,498 B**
- strong verification: true

Again, removing the filesystem-control member entirely only ties the accepted floor.

## Causal interpretation

For these two rows, the current selected content representation already occupies exactly the accepted-v0.29 complete-artifact byte floor when filesystem control is removed. Therefore **no representation that changes only filesystem-control bytes can produce a strict v0.29 win** from this content representation. A legal control format cannot have negative physical size.

This closes a narrower family than “metadata optimization” in general. It specifically retires additional pure filesystem-control shaving/reframing/elision as the missing mechanism for Office and Analytics on the measured representation. Other mechanisms may still reduce bytes if they change the content representation, allow content and control to share physical structure, or otherwise invalidate the measured decomposition while preserving exact semantics and all product laws.

## Forge audit

- diagnosis: **D4 representation boundary**, after D5 control productization exposed the exact floor
- lowest sufficient next intervention: **R4** for the affected rows; further R0/R1 control shaving is proven futile
- saturation: **S1 + S3 + S4** — exact optimistic lower bound reached, remaining strict gap is outside the tested family, and another same-family sweep cannot change the decision
- Referee pre-mortem: if deleting all control still failed to become strictly smaller than v0.29, no legal positive-size control encoding could rescue the unchanged content representation
- Builder instrument: exact-head physical product-gap diagnostic plus a zero-control counterfactual that removes the entire filesystem-control cost
- Hostile Reviewer: the result does **not** prove that canonical r25 cannot win Office or Analytics; it proves only that the unchanged selected content representation cannot be rescued by filesystem-control-only work
- terminal decision for pure control-byte shaving: **RETIRE_FAMILY**
- next decision boundary: obtain at least **309 B Office** and **177 B Analytics** of additional content/combined-representation saving, then re-price the complete canonical artifact and all creation/verification/locality costs

## Reopening predicate

Reopen control-focused work only if new causal evidence changes the decomposition—for example, a representation in which filesystem semantics share already-required content bytes, or a new content encoding whose physical framing interacts with control so that the old zero-control lower bound no longer applies. Do not reopen because of another control codec, field packing, varint choice, or framing shave applied to the same content representation.

This negative is intentionally scoped. It is a constraint on search, not a universal statement about future r25 representations.