# J24G01b — guard mixed GitHub PR metadata/file snapshots

Date: 2026-10-27 UTC. Immutable J24G01 original prereg at `9009eec01a46c568fbbd3febc4082177de4457ef`, source-based first tool at `d574448f95b6f05f286ca3ac0e180afe6b3e8fd8`; hosted initial exact-head live/offline court [Actions #40570768059](https://github.com/FCMO-AI/.CMPCT/actions/runs/40570768059) SUCCESS. This is an additive **measurement-custody** follow-up, not a retroactive change to the previous prediction.

## New limitation isolated after the first hosted live pass

Initial `live_snapshot` fetches PR metadata (including `head.sha`) and changed-file lists in distinct GitHub REST requests. Another cooperative activation can push during that interval. The output might then bind new file changes to the old PR head SHA, creating an inauthentic exact-source integration witness even if its pure graph classification is correct.

## Prospective repair and falsifier

After all changed-file lists have returned, re-fetch each selected PR metadata and assert the **head SHA, base SHA, head/base branch names and head/base repository names** are unchanged across the two observations. On mismatch **fail closed** with a bounded request rather than silently report an inconsistent source witness. No retry loop that hides the race and no claim of atomic GitHub snapshot: head/base could theoretically ABA-change between observations or changed-file API could have independent consistency delays; this is a stronger **two-boundary stability witness**, not an atomic snapshot.

Test negative by injecting one changed `head.sha` and one changed `base.ref` in a mocked second observation after file listings, with a positive unchanged mock control. No product, release, version, format, PR ownership, external workflow gate or `STATE.json` change. The first hosted PASS and Engineering Evidence FAILURE (missing required PR dossier headings) remain preserved separately.
