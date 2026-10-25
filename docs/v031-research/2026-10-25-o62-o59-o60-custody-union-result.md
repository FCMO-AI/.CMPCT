# O62 — O59 historical source custody composed with O60 VZIP product: hosted result

Date: 2026-10-25 UTC. **Result-bearing source HEAD: `d04ceaadce6672ac0204bc4cdf6cb8bac4755a1c`.** This is evidence/integration, not a compression or release result.

## Prospective claim and provenance

Preregistration committed at `76964f407f08381711d61bd3c8cf957fb7b1b642`, **before implementation**. Source parent: O60 #415 at `c88a6bc29b9ec8738e23aab788b7c09ab0390e79`. The unchanged O59 #414 test and historic O47 fixture blobs were transplanted by Git tree identity: `20faf26980693342439c7730f62bd0bab8daca0f` (test) and `6f60dfe63742ff4b777f959a15d6fb828ae29610` (fixture). O60 Builder `bda9d7f8005e276ba891aac75ae50eabe67bd431` and codec `dc3446b0eed82edfba9380e3885a20aa45577899` were *not* modified. The exact O60 adversarial test is `95740053ac9a3dd3335c10b63362eb0484722382`.

## Source-authentic hosted decision

**GitHub Actions run [40169200188](https://github.com/FCMO-AI/.CMPCT/actions/runs/40169200188): SUCCESS, 5/5 real installed Python 3.11 jobs.** Five independent fresh checkouts of exactly `d04ceaad`; each checks candidate Builder/codec and retained test/fixture blob IDs, installs CMPCT, proves all installed modules are outside checkout, performs original O59 full CMPCT-archive byte comparisons and the original O60 12-case source-coherence test suite.

| Hosted job | Real historical source | O59 tests | O60 tests | GitHub artifact / SHA-256 |
|---|---|---|---|---|
| Ubuntu 24.04 shallow | exact fixture Git blob | 3 PASS | 12 PASS | 12590016892 / `cb585c9dfc20402bd0c1fdd4ab815d3e3da0adf01623a9533bd4f7cf708d7985` |
| Ubuntu 24.04 full | historical parent commit | 3 PASS | 12 PASS | 12588907635 / `07640d01bb4d2502e2a18fa45c45408fca17a7e15f72dfa214c7ddff95015879` |
| macOS 14 shallow | exact fixture Git blob | 3 PASS | 12 PASS | 12589007185 / `d55225d4ab8a4cd057e3cc2662fd9bd89952b215d6aff457687780390b981763` |
| Windows 2025 shallow | exact fixture Git blob | 2 PASS, 1 POSIX-only SKIP | 12 PASS | 12589447946 / `116933fe1d2467615a5ced1e77e2369b49431c13ec66232fbbaa9210407a4b73` |
| Windows 2025 full | historical parent commit | 2 PASS, 1 POSIX-only SKIP | 12 PASS | 12589457918 / `ee275c27e7c5dd8f0211b2eb8f48daec0b9bf40a838867e914615af69a08c83d` |

**Aggregate: 73 PASS, 2 justified POSIX-only SKIP, 0 FAIL.** In every job, tiny and mixed **entire CMPCT archives** agreed byte-for-byte with the original O47 Builder *executed using the currently installed O60 codec*. Linux shallow and full produced identical tiny-case archive SHA-256 `af430fff...`; Windows full/shallow identical `9bd9b9c5...`. Cross-host physical archive hashes are **not** expected to match and were never used as comparators. The POSIX FIFO negative control passed; both source-custody paths selected the identical historical parent Git blob.

## Strongest scope limitation / alternative explanation

The historical O47 Builder is executed with the installed O60 codec in O59's comparison; this court establishes **Builder-admission compatibility on selected sources**, not independently reconstructed historical O47 all-dependency runtime. O60's original [run 40167592349](https://github.com/FCMO-AI/.CMPCT/actions/runs/40167592349) supplies the *separate* actual installed O50-old-engine vs candidate-complete-archive control and was preserved unchanged. Source mutation *during* initial capture remains unproven. NTFS named stream fidelity, arbitrary network filesystem semantics, unbounded file economics and official release ABBA remain unproven.

## CI / integration boundary and next

On O62 result HEAD, CI Topology, Version Discipline, Native Core, Fuzzing, and R36 attribution passed; O62 dedicated matrix passed. The original O50 workflow correctly rejects modified Builder/test blob source pins: **FAIL**, not reclassified. Initial Engineering Evidence was **FAIL** solely because the PR body lacked required evidence headings; owner corrected this metadata, not evaluator. Generic Tests and substantive r24/ZIP performance require independent exact-head adjudication; ZIP workflow administrative SUCCESS is not a benchmark pass. The inherited four v0.30 fingerprint/revision failures remain unresolved; no waiver or promotion. No project source/format change, merge, version change, or release credit.

**Primary question: PASSED within five-host source-bound scope. Decision changed:** O59's shallow historical-source test is compatible with O60's product safety fix. No concurrency collision; two source-owner branches untouched. Counterfactual: selecting the exact original historical Builder test source and original O60 hosted product court was cheaper and more decisive than a new comparator. No discovery-policy change earned. Next highest-leverage route: source-owner approval for the test-fixture integration; then valid prospective CI and economic release gates.
