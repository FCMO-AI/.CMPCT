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
- third-party attribution required by applicable licenses.

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

## Licensing rule

While `LICENSING.md` says the Apache-2.0 proposal is non-final, public pages and package metadata must
say **proposed**, not **licensed under**. Final adoption requires the explicit checklist in that file.

## Automated guard

`tools/check_public_surface.py` checks release-facing documentation, site source and public benchmark
history for known internal-provenance markers and private-path patterns. CI must run it before normal
tests and before any site publication.

The guard is a tripwire, not a substitute for review. A new sensitive term that is not in the pattern
list is still prohibited by this policy.
