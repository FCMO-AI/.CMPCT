# O130 — Candidate-fingerprint semantic custody falsifier (preregistration)

Date: 2026-10-25 UTC. Status: **PREDICTION LOCKED BEFORE INSTRUMENT**. Owner: independent Phased2 source-evidence audit; stacked exactly on O129 PR #476 at `55fa9584ac118194cdf4fe2210c977d93f644735`. No edits to O129/#266/#473 owners. Released v0.30.0, revision 24, frozen gates and release lock unchanged.

## Baseline and narrow question

O129 just composed O127 authentic Git-history custody with #266's prospective `tools/check_v031_candidate_fingerprint.py`. Its hosted exact-head suite reports 854 PASS / 7 SKIP / 0 FAIL, an **important positive for inherited regression compatibility**, not a proof that its new source-identity digest covers every semantically consequential future Git change. In #266's original implementation, `fingerprint()` hashes *matched path spelling + content SHA-256*, not Git file modes; the current manifest lists `.github/workflows/*.yml` but not `.github/workflows/*.yaml`. GitHub Actions recognizes both extensions. All source-custody success and regression counts from O129 remain valid unless challenged by an actual same-source independent test.

**Question:** Can two different Git-controlled behavior-bearing source trees produce the same proposed `fingerprint` SHA-256 under the *unchanged current real manifest* and exact current helper, while ordinary included byte changes correctly invalidate it?

## Prospective, falsifiable predictions

P1 — **Tracked new workflow spelling:** introducing `.github/workflows/ignored-by-manifest.yaml` into an isolated real-Git fixture whose other contents satisfy *all unchanged required paths* will change Git HEAD/tree identity but leave `fingerprint()` output identical. This is not an untracked-file trick: make two actual local commits and assert tree/commit SHAs differ.

P2 — **Tracked mode-only mutation:** changing Git mode 100644 to 100755 for an already included, executable-source-named `tools/sample.py` using `git update-index --chmod=+x` (content identical) changes Git tree/HEAD identity but leaves the candidate fingerprint unchanged.

P3 — **Strong positive control:** changing contents of that matched `tools/sample.py` changes both Git identity and candidate fingerprint.

P4 — **Exact candidate control:** the instrument loads `docs/V031_CANDIDATE_FINGERPRINT.json` and `tools/check_v031_candidate_fingerprint.py` from the actual O129 source branch; it does not redefine globs, change the checker, skip required paths, alter the v0.30 lock, or use hypothetical standalone hash pseudocode. The fixture materializes all real `required_paths` and the two exact prospective deltas; archived original candidate manifest SHA is reported.

## Scientific design and decision law

Use a temporary, deterministic minimal **genuine Git repository** independent of CMPCT, populate each unchanged required path with fixed bytes and add one included `.github/workflows/known.yml`, one `tools/sample.py`. All `required_paths` from the *original manifest* remain present in every snapshot. Run `git init` and make four separate commits: baseline; added .yaml; chmod-only; included content mutation. Call original `fingerprint(manifest,root=fixture)` at each committed state. Compare exact Git `HEAD`, root tree SHA, digest, and listed matching paths. This is an **adversarial source-identity oracle only**, not a CMPCT product/format/release or CI official fingerprint repair.

Disproof/kill: if either P1 or P2 changes the candidate fingerprint, narrow/retire the blind-spot claim; if content positive control does not change fingerprint or genuine committed Git source identity is not different, the instrument itself is invalid. Do not mutate the original manifest to make a negative, weaken the criterion, or present success of a scientific reproduction as a security fix.

## Alternatives and BONK

- Recheck O129's ordinary pytest green: already answers compatibility, not semantic injectivity.
- Audit source strings only: predicts mechanism but cannot prove actual committed Git tree mutation; the four-commit oracle is cheap and stronger.
- Replace O129 fingerprint immediately: unsafe without a real disproof and owner coordination; outside this lane.
- Import *all Git tree entries and modes* as a product correction now: complexity and migration debt unjustified before confirming exploit class. Later compare extension whitelist versus semantic Git-tree custody as conservative alternatives.
- "Mode is irrelevant": false for future directly executed scripts, but this experiment **does not prove a current shipped command uses such a mode**. Scope is candidate digest collision under Git-semantic changes.
- Existing receipt carries `source_sha=git HEAD`, so a consumer that checks **exact HEAD** is still protected. The specific falsification targets **fingerprint digest reused alone as complete semantic identity** and incomplete `fingerprint_globs` coverage.

## Evidence and handoff

Execute as self-contained stdlib script on hosted Linux with raw JSON observations, exact source sha and an independent assertion reader; preserve original test and provenance outputs, no product code changes, and no modified O129 gate. Send precise scoped evidence to owners #266/#476 if decisive, distinguishing missing **standalone digest** coverage from already-safe **HEAD-bound receipt**. Use no new project version or surface revision. Do not edit `docs/discovery/STATE.json` (PR #440 owns stale cache). No promotion or merge authorization.
