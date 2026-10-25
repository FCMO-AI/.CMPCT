# O130 result — prospective candidate fingerprint is not injective over Git execution semantics

**Status:** DECISIVE NEGATIVE FOR STANDALONE DIGEST COMPLETENESS; EXACT-GIT-HEAD-BOUND RECEIPT NOT FALSIFIED; NO PRODUCT/RELEASE CREDIT.

Date: 2026-10-25 UTC. PR: [#478](https://github.com/FCMO-AI/.CMPCT/pull/478), stacked on #476 original exact `55fa9584ac118194cdf4fe2210c977d93f644735`. Preregistered *before implementation* at `30ef67abb8cb96820e3a743e911f142f58463cae` in `2026-10-25-o130-fingerprint-semantic-custody-prereg.md`. Frozen v0.30/r24 and public lock unchanged. Investigation does not edit #266/#473/#476 parent code, candidate manifest or checker.

## Result-bearing exact source and genuine GitHub Actions evidence

**Source HEAD:** `bcc6422ae8bdf39740c7cf64d6ee6ed41d5728e1`.

Hosted run: [40245329755](https://github.com/FCMO-AI/.CMPCT/actions/runs/40245329755), **SUCCESS on Ubuntu 24.04 and macOS 14**.

| Platform | Job ID | Court | Raw artifact ID | Artifact SHA-256 |
| --- | --- | --- | --- | --- |
| Ubuntu 24.04 | `121325566231` | exact-Git oracle + independently coded JSON audit: PASS | `12618860805` | `3f835e35a4b1cdeddb8747f42f1be4249169c9d4f106255728cb713e92aee461` |
| macOS 14 | `121325566425` | exact-Git oracle + independently coded JSON audit: PASS | `12618028381` | `001279bcfb9668659aa87068e804ef14d36f05911bfb4176ac42b3c687966477` |

[Ubuntu raw JSON](https://github.com/FCMO-AI/.CMPCT/actions/runs/40245329755/artifacts/12618860805) · [macOS raw JSON](https://github.com/FCMO-AI/.CMPCT/actions/runs/40245329755/artifacts/12618028381).

Both jobs reported the identical source fingerprint manifest SHA-256 `f1df4c9699569478b3304c8879ad01ee4f556d86732fefd3a8024c4aecde7f74` and imported checker source SHA-256 `a87b0b9bc04aaa692e763ca891b49bf21e8fb8678469cff839d9d3974f8aa2c0`. The actual O129 manifest Git blob is `f806d96dba4750dead6746e078e596e848e6f201` and original checker blob is `4a8c0748b03f621add78810057d9f708f8050e06`.

The fixture materialized every required path declared by the **original** manifest as deterministic synthetic input, and created four **real Git commits**. The oracle imported the actual unchanged `fingerprint()` implementation. No external corpora or mocked hashing code was used.

## All preregistered predictions tested

| Case | Actual Git tree | Standalone candidate digest | Decision |
| --- | --- | --- | --- |
| baseline | `06e07410e03e26a3da47ec075006d8ba6caf5e4c` | `d1d62be1d34179d3ac485b5dc9748d2fd00b1244e1d15ba19e04afb95999448a` | Control |
| commit new tracked `.github/workflows/new-execution.yaml` | `6116f5b81842e1b1514a9411711c12e5ea5b3f4c` | **same digest** | **P1 CONFIRMED** |
| commit included script Git mode `100644→100755` with same bytes | `1f62abd8ad52a1c83902b360d92c65cbeae81d49` | **same digest** | **P2 CONFIRMED** |
| commit changed included script bytes | `f7e0fc80813bc8a7fe19074825971e1720cb4e31` | `48f978cc9c8ef415276abeff792c1769fe1514be85fff8230aed9b0b6eb56c82` | **P3 POSITIVE CONTROL PASS** |

P4: the source checker, manifest and required-path admission were unchanged; both platforms independently confirmed the same outcomes.

In both negative rows, the committed Git tree SHA **changed** while the standalone candidate digest stayed identical. It is therefore **not a complete representation of Git source execution semantics**. However, the actual `source_sha` that #266/#476 record **also changes** across these commits: a downstream verifier that insists on exact Git HEAD is **not bypassed by this result**.

## Earlier failures / evidence ethics

First hosted run [40245066345](https://github.com/FCMO-AI/.CMPCT/actions/runs/40245066345) on `be6fcab2` failed on both hosts before scientific execution because the direct `python research/...` invocation did not place the repo root on `sys.path` (`ModuleNotFoundError: tools`); this is a **failed instrument, not a product observation**. The workflow was changed to `PYTHONPATH="$PWD"`, with no checker or oracle prediction alteration.

Second hosted run [40245156463](https://github.com/FCMO-AI/.CMPCT/actions/runs/40245156463) on `24d19b99` executed the real Git cases but failed on an instrument-only assumption: staging a later byte edit resets a previously staged executable mode unless it is restaged; the fourth row's mode assertion failed. Neither P1 nor P2 was thereby disproved. The oracle now explicitly reapplies the Git +x mode for that fourth control; every initial collision/equality condition remains unchanged. CI topology also exposed the missing `ci-lane` marker/concurrency policy and was repaired in the dedicated workflow; the existing topology validator was **not changed**.

The final result-bearing HEAD `bcc6422a` passes both scientific and independent audit jobs. All negative run identities remain visible; no cherry-picked replacement of failed tests or weakened source gates.

## Mechanism and scope

The current checker uses `glob.glob()` and hashes included relative path bytes + a SHA-256 of file content. It does **not** hash Git file modes. The original manifest matches `.github/workflows/*.yml`, not `.github/workflows/*.yaml`. GitHub Actions supports both extensions. In current CMPCT Git history, `native/build.sh` already has mode `100755`, demonstrating executable-mode provenance can be relevant to an actual included path; this experiment itself used a small synthetic committed `tools/sample.py` rather than modifying that source file.

**Strongest counterclaim:** `source_sha` is retained in O129's candidate receipt and exact-head binding is an inherited explicit gate. For consumers that use both `source_sha` and fingerprint and demand exact SHA, there is no demonstrated authorization or safety failure here. The unsupported claim is only that the digest **alone** captures the complete semantic Git tree. O129's 854 PASS / 7 SKIP / 0 FAIL inherited compatibility remains a separate positive.

Other untested surfaces: newly added out-of-scope file extensions, untracked workspace files, symlinks/Git submodules, true Windows mode semantics, CI permissions, real product behavior, package-build determinism, filesystem reconstruction, performance and native ABI. No general source-integrity or security guarantee follows from these four cases.

## Decision, alternatives and counterfactual

**DECISION:** FALSIFY standalone fingerprint-completeness claim under original manifest. Preserve exact-head receipt as valid within its proven scope. Do not change O129 owner branch or merge this science experiment.

Cheapest prospective discriminator: before describing any path+bytes digest as complete source identity, compare it against the full set of **tracked Git tree semantics**—paths (including both Actions workflow extensions), modes/types, and content—using paired mode-only and newly-added-path witnesses. Future remediation may (a) explicitly declare a limited scope and always require Git HEAD, (b) expand the audited manifest to include all active execution source extensions and Git mode, or (c) derive the identity from tracked Git tree records with deterministic byte and metadata accounting. Option (c) is conceptually strongest but requires independent evidence against unwanted repository/mode noise, symlink/submodule semantics and resource cost. A unilateral patch is not justified here.

No evidence-backed general Discovery Engine policy change was earned. `docs/discovery/STATE.json` is a staleable cache under PR #440 ownership and remains untouched. No concurrency collision or branch overwrite.

## Head CI/economic truth and next owner action

At result-bearing HEAD `bcc6422a`: scientific dedicated workflow **2/2 SUCCESS**; Engineering Evidence **SUCCESS**; Version Discipline **SUCCESS**; R36 Attribution **SUCCESS**. The generic CMPCT tests and CI Topology were **PENDING** on the last result-bearing poll; do not claim them green without exact-run confirmation. The scientific workflow costs two short hosted stdlib jobs; no product bytes, wall/CPU, RSS, I/O, decode/recovery, benchmark or release metrics were measured. Future report-document HEAD needs its own CI and is not automatically covered by this source receipt.

**Next:** notify owners #266/#476 with results, emphasizing that exact-Git-HEAD custody is already the strongest defense and this negative affects only using the SHA-256 digest in isolation. Owner should decide between contract-narrowing and a bounded semantic-tree fingerprint patch; run an independent exact-head negative suite before promoting any changed checker.

**Research credit:** decisive scientific falsification. **Product credit:** 0. **Format change:** 0. **Merge:** NO. **Release:** NO.
