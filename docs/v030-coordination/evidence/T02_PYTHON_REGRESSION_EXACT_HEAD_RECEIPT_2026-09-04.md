# v0.30 exact-head Python regression custody receipt — 2026-09-04

Status: **CORRECTNESS / REGRESSION CUSTODY ONLY — not a substitute for T02 performance/frontier gates**

This record persists a substantive exact-head Python regression result that was otherwise present only in transient Actions logs. It advances the repository's completion evidence for exact-candidate Python correctness while granting no compression-generalization, runtime/RSS/selective-read, shared-build, external-competitor, topology, platform, or strict-release authority.

## Exact source and run

- PR: `#56`
- branch: `agent/v030-authoritative-integration`
- source commit: `83673bcab08b80d7146151f4a16c49206bade507`
- workflow run: `33877773523` (`CMPCT tests`)
- result-bearing job: `101038763406` (`test`)
- Python: `3.11.16`
- exact-head binding: passed
- public disclosure guard: clean (`1,547` tracked text files checked)
- full regression suite: **721 passed in 265.34 s**
- CLI smoke test: passed
- artifact: `pytest-83673bcab08b80d7146151f4a16c49206bade507`
- artifact id: `9938834615`
- artifact ZIP SHA-256: `af8247d011a3d3aec259e6df902971904b773145af80761187b1b21aece92284`

## Interpretation boundary

The result proves that the complete Python regression suite collected and passed on this exact repository head and that the public CLI surface still starts successfully. Because the T02 release-critical fingerprint deliberately excludes later coordination/evidence/receipt-only commits, this receipt may support exact-candidate correctness custody without claiming that skipped result-bearing performance/frontier jobs ran.

In particular, this receipt **does not** satisfy any of the following frozen T02 obligations:

- 15-workload compression generalization and <=8x locality;
- shared-build >=20% and >=5 s rehabilitation;
- create/extract/selective-read/peak-RSS ratios;
- strict ZIP and Zstd-19 per-workload size/create domination;
- full active-workflow topology authority;
- final strict release lock.

Green workflow shells whose substantive jobs were skipped remain non-authoritative.
