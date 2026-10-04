# v0.30 G04 delimiter A/B custody correction — 2026-09-15

The earlier exact-ML A/B preserved at `docs/v030-coordination/evidence/g04-delimiter-inverse-negative-20260915.md` remains historical evidence of what that harness measured, but it is **not sufficient to adjudicate the shipping reader implementation**.

Root cause: canonical r25 Geometry is loaded through `entropygraph_v030_profile_isolation` into the private module `experiments._v030_canonical_g04`. The earlier A/B imported the public historical `entropygraph_v030_geometry_overlay_g04` module and assigned `G04.O.delimiter_inverse` while timing `entropygraph_v030_release_product.extract`. That public research module is intentionally distinct from the isolated canonical Geometry object used by the release product. The repository's profile-isolation contract exists specifically so research-module mutation cannot silently rewrite canonical execution.

The earlier result therefore cannot be promoted into a causal claim that replacing the shipping inverse made complete ML extraction ~50% slower. Its exact-tree checks still establish that both timed extractions reconstructed the tree, but the intervention boundary was not proven to be the product reader boundary. Treat the ~1.50x result as **custody-confounded** until reproduced with the canonical private reader object explicitly patched.

`experiments/v030_g04_delimiter_inverse_ab.py` is now corrected to:

- obtain the currently installed shipping inverse from `PRODUCT.C.SHARED.G.O.delimiter_inverse`;
- patch `PRODUCT.C.SHARED.G.O` and the canonical policy reader's G04 object together;
- use the reviewed bulk-v1 inverse as the control;
- preserve exact source-tree identity after every alternating extraction;
- report the patched reader scope in the artifact.

This correction changes no product code, archive bytes, threshold, format, release fingerprint input, or public claim. It repairs the causal instrument only. Do not delete the old negative; retain it as an example of why module-identity/custody must be proven when the product deliberately isolates mutable research globals.

Separately, the current guarded-banded implementation's operation-count guard is deterministically unable to select its banded arm on the already-recorded dominant ML shape; see `g04-guard-selection-derived-bound-20260915.md`. That is a code/evidence derivation, not a substitute for the corrected shipping-reader A/B.
