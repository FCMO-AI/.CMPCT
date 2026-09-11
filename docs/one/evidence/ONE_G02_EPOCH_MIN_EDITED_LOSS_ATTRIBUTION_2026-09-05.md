# ONE-G0.2 — edited-version loss causal attribution

**Status:** missing relationship localized; repair direction may now be generated causally  
**Exact result-bearing source:** `811096b961ff3c272fea279e66ba0bae15d136da`  
**Workflow:** `33948078207`  
**Job:** `101257667199`  
**Artifact:** `9963959542`  
**Artifact digest:** `sha256:157ba3c9eb47fd3347c03746c11e846b695934f180eb067036823b0769343244`  
**Experiment:** `ONE-G0.2`

## Referee question

The frozen 64-row internally edited-version transfer found one strict replacement failure: on the 262,144-byte base #1 with 16 byte substitutions, the mature rolling minimizer found 1,008 marginal exact bytes beyond fixed observation while scalar epoch-min found none. This diagnostic was frozen before execution and changed **no** selector parameter. It reproduced the row and instrumented mature and candidate successful nominations plus edit coordinates.

## Exact result

All **50 ONE semantic tests** passed. The attribution decision is:

`missing_mature_nomination_localized`

The mature-only successful relation is exactly:

- accepted target interval: **[289,466, 290,797)**;
- exact bytes in that mature region: **1,331 B**;
- source nomination start: **28,157**;
- target nomination start: **290,301**;
- source→target translation delta: **262,144 B**;
- mature minimizer nomination position: **290,364**;
- left exact extension: 835 B;
- right exact extension: 496 B.

The two adjacent substitutions in the second version occur at absolute offsets:

- **289,465** (`second-version offset 27,321`), immediately before the mature-only exact island;
- **290,797** (`second-version offset 28,653`), immediately after it.

Therefore the mature-only 1,331-byte region is precisely the unchanged island **between two Surprise bytes**. The fixed observer recovers part of that island, which is why the frozen aggregate replacement deficit is 1,008 B rather than the full 1,331 B.

The nearest epoch nomination before the mature-only island is at position **289,064** (start 289,001); the next epoch nomination is at **292,978** (start 292,915). The scalar non-overlapping starvation cadence simply emits no reusable nomination inside the 1,331-byte island. Sparse nominations nearby also miss it.

## Stronger causal observation

This mature-only relation does **not** establish a new source/target mapping. Its translation delta is exactly **262,144 B**, the same version-to-version offset already proved by the candidate's surrounding successful exact relations. For example, the immediately preceding candidate relation covers `[278,635, 289,465)` and the immediately following epoch relation covers `[290,798, 309,040)` under the same version alignment.

The rolling minimizer's extra value here is therefore not discovery of a different Law. It is **re-nomination of an already-known translation Law after a local substitution**.

That changes the research question materially. Rebuilding a 4,096-position rolling-minimum structure to recover this island would be paying a large discovery tax for information the encoder already possesses: the source→target translation relation survives, while individual bytes violate it sparsely.

## ONE interpretation

The natural ONE hypothesis is **Law persistence across Surprise**, not a second selector:

- **Law:** target bytes predict from source bytes at the already-proven translation delta;
- **Surprise:** sparse substituted bytes where that prediction is false;
- **Crystallization:** only if the Law stops predicting well enough to justify preserving it.

This is architecturally cleaner than treating every edit-delimited exact island as a fresh reuse-discovery problem. It also aligns directly with the canonical Law + Surprise representation principle: the reader would reconstruct from an explicit Law and explicit Surprise bytes; it performs no discovery.

No implementation is promoted by this attribution alone. The next experiment must first establish honest headroom: after a candidate exact relation seeds a translation Law, can explicit Surprise-charged continuation subsume the mature edited-version opportunity without gifting representation bytes or reconstruction work?

## Scoped decision

**Retain the negative against scalar epoch-min as a complete selector replacement, but redirect repair from “more minimizer state” to “persist the already-proven translation Law across sparse Surprise.”**

Do not tune epoch size/masks or reinstate the mature deque unless this Law-persistence hypothesis is falsified.
