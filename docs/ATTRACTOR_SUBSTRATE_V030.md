# CMPCT v0.30 child research — Synthetic Attractor Substrate

Status: **DESIGN / CHILD RESEARCH — DO NOT MERGE — DO NOT VERSION-BUMP**  
Parent research head: `agent/lattice-v030-breakthrough` @ `0338527d3a9e4f12df20448c52665d1c93c8b937`  
Parent PR: #45  
Production remains CMPCT **v0.29.0 / canonical r24**.

This document defines a third research axis that is intentionally orthogonal to Geometry/latent types and
Bitplane Algebra. It exists because the accepted Mosaic engine still explains targets through a bounded set of
**existing direct root nodes**. A synthetic substrate asks whether CMPCT can instead manufacture a compact set
of shared phrase atoms that never existed as standalone input objects, while keeping reconstruction shallow and
recovery/accounting explicit.

---

## 1. Prior art / what is not novel

Do not claim the following ideas as CMPCT inventions.

- String attractors unify many repetitiveness measures and dictionary compressors and support compressed
  random-access constructions: <https://arxiv.org/abs/1709.05314>
- Prefix-free parsing creates a dictionary plus parse for huge repetitive collections:
  <https://arxiv.org/abs/1803.11245>
- Stable locally-consistent grammars can discover equivalent cores independently and merge them afterwards,
  enabling highly parallel repetitive-collection compression: <https://arxiv.org/abs/2411.12439>
- Bidirectional macro schemes can outperform one-directional LZ on repetitive sequences, although optimal
  schemes are computationally difficult: <https://arxiv.org/abs/2003.02336>

The proposed CMPCT contribution under test is the **representation boundary and promotion law**, not grammar
compression itself.

---

## 2. Observed Mosaic boundary

Accepted v0.29 attempt #5 inherits the Placement Compiler. Its multi-root mosaic candidate:

- nominates actual existing nodes;
- searches bounded subsets of 2–4 roots;
- requires roots to remain direct/materialized;
- keeps the logical DAG flat;
- prices the target recipe plus root placement/read amplification.

That is a deliberate and useful locality invariant. It also means a repeated phrase that appears inside many
otherwise-unrelated roots cannot become a shared basis unless an actual root happens to expose it economically.

The substrate hypothesis attacks that exact gap rather than replacing Mosaic indiscriminately.

---

## 3. Hypothesis — synthetic shared phrase atoms

Represent a file tree using a bounded set of **synthetic atoms** plus one-hop parses:

`file -> [atom | literal-run]*`

An atom is an exact byte string synthesized from repeated cores across the archive. It need not equal any input
file or inherited 128 KiB/512 KiB chunk. At promotion-quality locality, atoms are independently authenticated
physical objects; a file parse never recursively follows another file.

### Desired properties

- exact byte reconstruction;
- atoms are content-addressed and independently authenticated;
- file dependency depth <=1;
- atoms may be generated from stable local parsing rather than fixed offsets;
- atom admission uses complete net cost: atom bytes + descriptor/index bytes + file references + integrity;
- atoms with negative marginal value are absent;
- unmodelled material remains literal and can still use Geometry/GIR;
- per-file selective-read/recovery fan-out is measured explicitly.

---

## 4. Seed discovery algorithm — Stable Phrase Substrate

The first oracle should stay deliberately simpler than a full grammar compressor.

1. Run an O(n) locally-stable phrase boundary pass over every eligible logical byte stream. A practical seed may
   use content-defined/minimizer boundaries while the stable-local-grammar path is researched independently.
2. Content-address exact phrases across the entire workload.
3. Keep only repeated phrases whose conservative net saving is positive after one stored atom, per-reference
   identifiers, framing/integrity and parse metadata.
4. Inline unique/losing regions as literals rather than forcing a universal dictionary.
5. Encode file parses as compact symbol streams; repeated runs and local deltas in atom IDs may use existing
   bounded integer codelets.
6. Initially permit a **solid substrate seed** if it produces a dramatic size breakthrough, but record its
   selective-read debt explicitly. This is exploration debt, not promotion permission.
7. If the seed is real, rehabilitate locality by partitioning/materializing atoms into independently decodable
   packs selected under the existing per-member <=8x law.

The seed is intentionally analogous to `discover -> preserve breakthrough -> expose debt -> rehabilitate` from
`docs/BREAKTHROUGH_REHABILITATION.md`.

---

## 5. Novel refinement A — Attractor-weighted atom admission

Frequency alone is a poor dictionary objective. Prefer atoms that cover *distinct repeated contexts* and reduce
multiple otherwise-independent representations.

For a candidate atom `a`, estimate:

`gain(a) = displaced_stored_cost - atom_store_cost - reference_cost - recovery/locality_penalty`

Add a diminishing-return term when another selected atom already explains most occurrences. This is an
MDL-like set-cover objective over stored bytes rather than raw frequency.

The attractor literature motivates coverage as a unifying view of repetition, but CMPCT's score is archive-
engineering-specific: it prices physical framing, authenticated recovery and selective reads rather than only
text length/asymptotics.

---

## 6. Novel refinement B — one-hop grammar flattening

A conventional recursive grammar can achieve excellent compression while producing dependency chains that are
unattractive for an archive. CMPCT should test a different extraction boundary:

1. allow a bounded grammar/local-consistency pass to *discover* repeated nonterminals;
2. compute the fully expanded bytes of profitable nonterminals;
3. materialize only a selected frontier of those expansions as independent atoms;
4. rewrite file parses directly to that frontier + literals;
5. discard deeper grammar dependencies from the archive representation.

This deliberately spends some grammar compactness to buy depth-1 extraction, local integrity and simpler
recovery. The optimizer can search the **flattening frontier**: deeper discovery does not imply deeper decode.

---

## 7. Novel refinement C — Geometry inside atoms, atoms inside RSO

Synthetic atoms should not become a new silo.

- Text/structured atoms may themselves use G1–G4 or surviving Latent-Type codelets.
- Numeric/binary atoms may use a surviving Bitplane/ALP-like representation.
- Whole-file regions that Mosaic/PrefixGraph already explain more cheaply remain in those representations.
- The Representation Superoptimizer retains equivalent plans long enough to choose the cheapest legal one.

This creates a two-dimensional compiler:

**horizontal reuse** — repeated information shared across objects via atoms/reference edges;  
**vertical geometry** — compact physical view inside each stored object/atom.

The novelty target is the joint optimizer and shallow archive embodiment, not any one compression primitive.

---

## 8. Phase-ordering experiment

Before implementing a general e-graph/equality-saturation layer, construct three deterministic cases:

1. **reference-first wins:** two versions where a delta edge is much smaller than any independent Geometry view;
2. **geometry-first wins:** two superficially similar structured objects where independent latent/Geometry views
   beat storing a shared reference plus residual;
3. **substrate wins:** several objects share important phrases but no single object is a good central base.

A bounded equivalence-set extractor must choose the correct representation on all three using stored cost. If
such counterexamples cannot be produced without contrivance, the e-graph/superoptimizer complexity is not yet
justified.

---

## 9. First exact benchmark target

Use public, deterministic workloads where cross-object repetition is plausible but structurally different:

- `01_developer_repository` — repeated source/test/lockfile scaffolding;
- `02_office_workspace` — repeated embedded assets and package internals, with Preflate still allowed to win;
- `06_incremental_backups` — edited snapshot families;
- hostile shifted/boundary/version workloads already used by Mosaic research.

The first substrate oracle must compare **complete substrate representation cost** against accepted v0.29 on the
same live trees. A detached phrase-frequency number is insufficient because fine-grained dictionaries can hide
large parse/index overhead.

Suggested preregistration before code execution:

- >=256 KiB complete-artifact saving on at least one exact public workload;
- >=512 KiB aggregate across the focused set;
- zero data-integrity regressions;
- exact workload-level v0.29 fallback;
- synthetic atoms must actually be selected;
- report atom bytes, parse/index bytes, duplicated integrity/meta bytes, creation CPU and worst selective-read
  amplification separately;
- a solid-substrate seed may exceed the locality floor only while explicitly marked `BREAKTHROUGH_DEBT_OPEN`.

Do not lower these thresholds after observing the first result.

---

## 10. Rejection criteria

Reject or demote the mechanism if:

- gains vanish after parse/index/atom framing is charged;
- the only wins are exact duplicates already captured by coarse CDC/Mosaic;
- the synthetic-atom layer merely recreates solid Zstd with more metadata;
- locally-stable discovery consumes disproportionate CPU for negligible extra coverage;
- locality rehabilitation erases the seed's size advantage;
- atoms create recovery fan-out or parser complexity that cannot be bounded cleanly;
- complete-artifact gains are smaller than simpler Geometry/PrefixGraph integration work.

Negative evidence remains in the repo.

---

## 11. Merge lock

This branch is design research only.

**DO NOT MERGE TO MAIN.**  
**DO NOT VERSION-BUMP.**  
**DO NOT CALL THIS v0.30.**

If an Attractor/Substrate seed later wins, preserve its exact evidence and debt ledger first. Integration into
the parent Representation Superoptimizer happens only after the mechanism survives its own complete-artifact
falsification and the user explicitly allows a later integration/release phase.
