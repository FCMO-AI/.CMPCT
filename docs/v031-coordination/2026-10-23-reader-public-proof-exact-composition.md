# Reader × prospective CI × public-proof source-composition preregistration

UTC 2026-10-23. **PREREGISTERED, before transplant; research/integration-only.**

Base: PR #268 `34ca9c34fd313fff21d92577d711f82a561f75a4`.
Disjoint owner: PR #248 `80ee6a1f22717d6b50c1c31eddc5389c2945a287`.

## Baseline and question
PR #268: installed full Tests 806 PASS (run 39978793839), genuine same-runner r24/ZIP ABBA PASS (run 39978794055), but Public Proof FAIL (run 39978794066). PR #248: genuine owner Public Proof PASS (run 39941151589), but old inherited CI failures before PR #266 were integrated. Does exact Git-blob composition remove Public Proof red without weakening Reader or historical scientific identity?

## Hypothesis and alternatives
Copy **exactly seven owner blobs** from PR #248; preserve all PR #268 source blobs. Alternative of changing v0.30 historical release-lock, relabeling v0.29 measured frontier as shipping v0.30, deleting release assertions or rebuilding the Reader is disallowed. Disjoint source transplant is simpler and independently falsifiable.

Owner blobs:
- `.github/workflows/site-proof-contract.yml` = `93c1652b0c89ee68c090c98da50ba218fadaac02`
- `docs/SITE_PUBLIC_PROOF_STANDARD.md` = `086a8ac848f72044bca4bc98f3eaba1afc92eb08`
- `site/enhance_site.py` = `cda7b8c2a37bef614a340f0ac80a671b70e5027f`
- `site/src/assets/proof-renderer.js` = `ed70fd99185a96e28c4ca551d9b5b877eb0b46fe`
- `site/tests/proof-version-render-contract.mjs` = `999e40af8d7a621574fadf765606099319b65245`
- `site/tests/release_evidence_contract.py` = `3904959bc18793c202fac170f0b0c06f47dbbda5`
- `site/tests/version_provenance_contract.py` = `37f0cfdd6107f1fa4c0ef688d9c0747972987c60`

## Falsification and scope
On the composed candidate demand seven source blob matches, unchanged PR #268 Reader/tests/CI blobs and historical lock blob `988a7b05ad4e0833fac0453de74133b38f890f87`; strict hosted Public Proof with shipping v0.30/r24 and historical research v0.29 provenance; full installed-package Tests; exact-head CI. Any mismatch/failure narrows or kills composition. A skipped performance job gives zero performance credit; previous ABBA cannot automatically be reused after fingerprint changes. Format r24, numeric release v0.30.0, comparators and promotion gates remain unchanged.

Concurrent #270 owns sparse/NAME_MAX Reader composition; this independent source-disjoint proof lane changes no Reader. Source ownership stays with #248 and #268. Draft only; no merge/release.
