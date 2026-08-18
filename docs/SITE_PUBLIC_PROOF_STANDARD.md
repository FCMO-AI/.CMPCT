# CMPCT Public Proof Surface Standard

Status: **normative for the CMPCT website and its generated machine-readable public evidence.**

The website is not a marketing mirror of the repository. It is CMPCT's public proof surface: a human
should understand why the project matters in seconds, while a skeptical engineer or agent must be able
to trace every important claim back to committed evidence without trusting the page's rhetoric.

## 1. Audience contract

One page must serve three reading depths without switching modes:

1. **Uninformed viewer** — understand that CMPCT is a lossless archive project and why smaller archives,
   selective access, integrity and recovery matter.
2. **Computer-literate user** — understand where CMPCT sits relative to ZIP and serious compressors,
   what the Browser Lab can do, and why the project is more than a compression-ratio demo.
3. **Engineer / AI agent** — inspect benchmark scope, comparator identity, canonical-vs-research authority,
   losses, provenance, raw records and machine-readable state.

Progressive disclosure is preferred over separate beginner/expert pages. Each major claim should have a
plain-English meaning, a scoped technical statement and a path to raw evidence.

## 2. The evidence ladder

Public claims follow this order:

**headline → plain-English meaning → scope → comparator → methodology/provenance → caveat/loss**.

A large number without the rest of the ladder is incomplete. The page may be visually aggressive; it may
not be evidentially vague.

## 3. Stable public evidence contract

`site/enhance_site.py` emits `project-data.json.public_evidence` with schema
`cmpct-public-evidence-v1`.

Frontend code consumes that stable contract rather than adding release-specific renderers. Historical
`frontier-v028.js` / `frontier-v029.js` files may remain as compatibility shims, but new releases should
not create `frontier-v030.js`, `frontier-v031.js`, etc. unless a temporary emergency compatibility bridge
is unavoidable. The durable fix is always to normalize the new benchmark schema into the stable public
evidence contract.

Required conceptual groups are:

- project and canonical format identity;
- research-frontier name/status;
- matched structural comparison and competitors;
- serious size comparator;
- category/workload frontier when available;
- scoped scheduler/performance evidence when available;
- direct-base release delta;
- known losses/limitations;
- capability authority labels;
- provenance and benchmark contract;
- claim policy.

Missing evidence must render as unavailable or suppress the affected claim. Never reuse an old headline
number merely to avoid an empty card.

## 4. Visual semantics

Color has meaning:

- **green** — measured favorable result or passing gate;
- **red** — measured unfavorable result / open loss;
- **orange** — CMPCT identity, research emphasis or active mechanism; orange is not an automatic win;
- **ivory/neutral** — canonical authority and ordinary content;
- **steel/blue-gray** — provenance, links and contextual information.

A CMPCT result that loses stays red. Do not recolor it as brand orange to soften the loss.

## 5. Required homepage surfaces

Every current homepage must contain:

- a plain-English definition of CMPCT before deep jargon;
- one derived headline benchmark with scope attached;
- a metric wall showing at least one familiar baseline and one serious compressor when evidence exists;
- an explicit release-performance law / promotion gate;
- a simple explanation of CMPCT's relationship-oriented archive model;
- capability/strength surfaces beyond raw compression ratio;
- a matched competitor arena;
- workload/category evidence when available;
- a **Red Team Board** containing relevant current losses/qualifications;
- an explicit canonical-vs-research authority map;
- canonical execution-parity evidence;
- Browser Lab creation/inspection tools when compatible;
- raw evidence and machine-view links;
- release/frontier history.

## 6. Benchmark honesty rules

1. Headline percentages are derived from committed records, never typed into HTML.
2. A competitor win remains visible if it is relevant to the claim being made.
3. Raw size comparisons do not imply equivalent random-access, integrity, recovery or durability semantics.
4. Whole-suite structural, independent-workload category, canonical execution-parity and direct-base
   release-delta questions remain distinct.
5. Research representations never borrow canonical reader/writer authority.
6. Timing claims keep their runner, workload and boundary scope. A fixed scheduler benchmark is not a
   global “CMPCT is X% faster” claim.
7. A fair loss is an engineering target, not a copywriting problem.

## 7. Future-release update protocol

For a new material CMPCT version:

1. commit the durable public benchmark record(s);
2. normalize the new record into the existing frontier model or directly into `cmpct-public-evidence-v1`;
3. build the site;
4. confirm the hero, serious comparator, Red Team Board and evidence receipt are populated from the new
   record;
5. run `site/tests/proof_surface_contract.py`;
6. run `site/tests/release_evidence_contract.py`;
7. run Browser Lab compatibility and canonical reader checks;
8. verify mobile and reduced-motion behavior;
9. advance the numeric core version only if CMPCT itself earned it; presentation-only changes advance
   `SURFACE_REVISION`;
10. promote the validated generated tree to `gh-pages` and verify its `deployment.json` receipt.

If a new benchmark cannot satisfy the stable public contract, fix the normalization boundary rather than
hard-coding the new release into the browser.

## 8. Completion tests

A website milestone is incomplete unless it passes all five:

- **Three-second test:** a new visitor can tell what CMPCT is and why it matters.
- **Power-user test:** a ZIP/7z user can understand the practical difference and try CMPCT.
- **Skeptic test:** a hostile engineer can find the loss, scope and raw evidence without repository archaeology.
- **Agent test:** machine-readable state exposes the same current claim boundaries as the human page.
- **Next-release test:** a new benchmark record can update the major surfaces without redesigning the page
  or adding a release-specific frontend renderer.

The target feeling is a scientific instrument with editorial clarity: visually memorable, technically
calm, and unusually easy to audit.

## 9. Static publication architecture

The proof surface has two deliberately different Git authorities:

- **`main` is canonical source authority.** Site source, benchmark history, normalizers, tests and policy live there.
- **`gh-pages` is serving authority only.** It contains a generated static tree and must never become an editable
  parallel implementation of the site.

GitHub Actions keeps the jobs it is good at: disclosure scanning, deterministic site generation, evidence
arithmetic, JavaScript syntax checks, Browser Lab smoke tests and canonical-reader compatibility. Those jobs
validate what may be promoted. They do not own the public serving path.

Every static promotion must include `.nojekyll` so GitHub Pages can treat the branch as already-built output,
and `deployment.json` so a human or agent can prove which `main` source commit, surface revision, canonical
format revision and evidence schema the live tree represents.

The repository Pages setting is **Deploy from a branch → `gh-pages` → `/ (root)`**. See
`docs/GH_PAGES_DEPLOYMENT.md` for promotion and rollback procedure.

Footnote: branch-backed Pages still uses GitHub's internal Pages deployment infrastructure. The architectural
gain is not pretending GitHub disappears; it is removing CMPCT's custom build/test workflow from the critical
path between an already-validated static tree and public serving.
