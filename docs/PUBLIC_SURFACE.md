# CMPCT public-surface policy

Status: **release/publication gate**.

CMPCT must be understandable, testable and presentable as its own project. The repository and website
must not rely on unrelated private context, and publishing CMPCT must not accidentally publish that
context with it.

## What belongs in the public project surface

- CMPCT source code, format specifications, conformance vectors and generic engineering notes;
- reproducible synthetic/public benchmark corpora and machine-readable results;
- generalized lessons learned from private development experiments when the private provenance is not
  needed to understand or reproduce the engineering conclusion;
- project-specific branding, repository identifiers and technical MIME/type identifiers;
- public issue/PR history that discusses CMPCT itself;
- third-party attribution required by applicable licenses;
- deliberately published project legal attribution recorded by the canonical `COPYRIGHT.md` / `LICENSING.md`
  policy, limited to the exact ownership/scope statements those files intentionally expose.

## What must not be copied into the public surface

- customer/client files or identifiers;
- personal information not intentionally published for the project;
- unrelated internal agent/project names, prompts, memory, conversations or system architecture;
- private corpus names when those names reveal unrelated internal systems;
- private artifact filenames, internal bundle layouts or private source-tree names;
- private URLs, tokens, credentials, API keys, secrets or machine-specific access paths;
- private benchmark input bytes or hashes that identify internal artifacts;
- claims whose only evidence is an unavailable private corpus.

A technical lesson learned from private data may be retained in generalized form. The private identity
or operational context that produced the lesson should not be retained merely for historical color.
Deliberately public legal attribution is not a license to spread the same names into research, benchmark,
workflow, site or operational prose: only the canonical legal-attribution statements are exempt.

## Benchmark rule

Private development corpora may still be useful locally. Their results are **internal regression
signals**, not public proof. Public performance claims should be reproduced on public or deterministic
synthetic workloads with enough environment/semantic metadata for an independent rerun.

If a private result materially changed architecture, `docs/HISTORY.md` or `docs/RESEARCH_LOG.md` may
say that an early mixed-workload corpus exposed the issue, but should not identify the unrelated
system, people or private artifact names.

## Website rule

The website build may consume only deliberately public project inputs. In particular:

- benchmark UI data comes from public durable benchmark schemas, not arbitrary history files;
- Browser Lab file conversion/inspection stays local to the browser and does not upload selected
  files;
- generated agent orientation must point to CMPCT repository sources rather than private context;
- visual rules may be implemented directly without publishing private design-source documents or
  unrelated organizational lore.

## Public stewardship rule

Public organizational provenance is intentional and is not treated as unrelated private context.
CMPCT uses the quiet maker lines **“CMPCT by FCMO AI”** and **“From the FCMO group”** according to
`docs/OPEN_SOURCE_STEWARDSHIP.md`.

The attribution boundary is strict:

- CMPCT remains the dominant project identity;
- FCMO credit appears where provenance naturally belongs: repository facade, ecosystem metadata,
  citation metadata, machine-readable project state and a quiet website footer/About surface;
- attribution must not be inserted repeatedly into algorithms, benchmark results or normal CLI output;
- FCMO provenance must not imply benchmark authority, license terms, archive capability or ownership of
  third-party/contributor work;
- unrelated private project names, internal architecture and organizational lore remain prohibited.

# Footnote: public stewardship is a deliberately published identity fact. It does not create an exception
# for leaking private FCMO systems; the organization name is public, the unrelated internal context is not.

## Git-history rule

Removing a file or name from the current tree does not remove it from older Git objects. Before the
repository itself is made public, perform a dedicated full-history audit for private artifacts,
private corpus records, credentials, personal data and unrelated internal provenance.

If that audit finds publish-prohibited material in reachable history, the public-release procedure must
rewrite/purge the affected history or publish from a sanitized repository lineage **before** changing
repository visibility. Do not rewrite active private development history casually: coordinate the
rewrite because branches, pull requests, tags and clones may need to be rebased or recreated.

# Footnote: the website can safely be reviewed before the repository is public because its build is
# generated only from the sanitized current tree. That does not make old Git objects safe to publish.

## Licensing rule

While `LICENSING.md` says the Apache-2.0 proposal is non-final, public pages and package metadata must
say **proposed**, not **licensed under**. Final adoption requires the explicit checklist in that file.

Canonical copyright attribution is a separate ownership/provenance statement, not evidence that the
Apache-2.0 proposal has been adopted and not a grant of license by itself.

## Automated guard

`tools/check_public_surface.py` checks release-facing documentation, site source and public benchmark
history for known internal-provenance markers and private-path patterns. CI must run it before normal
tests and before any site publication.

The guard permits person markers only on the exact canonical legal-attribution lines in `COPYRIGHT.md`
and `LICENSING.md`; the same markers anywhere else still fail closed. This is a narrow reconciliation
with deliberately published legal metadata, not a path-wide or person-wide allowlist.

The guard is a tripwire, not a substitute for review. A new sensitive term that is not in the pattern
list is still prohibited by this policy, and the current-tree guard cannot substitute for the full
Git-history audit required before making the repository public.
