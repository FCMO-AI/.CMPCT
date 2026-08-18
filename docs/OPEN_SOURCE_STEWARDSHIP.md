# FCMO Open-Source Stewardship Standard

Status: **public identity / attribution doctrine**.

## The principle: quiet provenance

An FCMO open-source project should earn attention through the quality of the thing itself. Organizational credit is present, durable, and easy to discover, but it does not compete with the project for attention.

The intended sequence is:

> **This is useful. → This is unusually well made. → Who built it? → FCMO AI.**

That is stronger than turning a useful project into an advertisement. The project creates the reputation; the credit merely preserves where that reputation belongs.

For CMPCT the canonical public wording is:

- **CMPCT by FCMO AI**
- **From the FCMO group**

For future FCMO open-source projects, replace the project name in the first line and preserve the second line as the quiet umbrella attribution.

> Footnote: “FCMO AI” is the technical stewardship identity used on project surfaces. “From the FCMO group” is the umbrella maker line. Neither phrase is a benchmark claim, a license restriction, or a substitute for contributor credit.

## Project first. Maker's mark second.

The project's own name, purpose, evidence, interface, and community always own the primary hierarchy. FCMO attribution belongs where provenance naturally belongs: the repository facade, package metadata, citation metadata, an About surface, a website footer, and machine-readable project state.

Do **not** turn attribution into wallpaper. In particular:

- do not prepend FCMO to every heading or command;
- do not insert corporate copy into algorithms or source-file headers;
- do not make FCMO branding larger than the project identity;
- do not add promotional interstitials, modal ads, or product-exit CTAs;
- do not repeat the maker line in every section of a README or website;
- do not imply that organizational stewardship erases individual contributors;
- do not use open-source documentation to advertise unrelated private systems or internal architecture.

The strongest nudge is craftsmanship with traceable provenance.

## Natural attribution surfaces

| Surface | Required treatment | Why |
|---|---|---|
| Repository landing view | One quiet maker line in the hero or immediately adjacent project byline | First-contact provenance without displacing the project |
| README | Credit visible through the landing composition; dedicated prose only when it adds useful stewardship context | Avoid repeated corporate copy |
| Package metadata | Standards-native author/steward and project URLs | Package indexes and tools can preserve provenance automatically |
| Citation metadata | Organizational author/steward in `CITATION.cff` | Academic/technical reuse retains attribution |
| Project website | Low-contrast footer/micro-credit with a single FCMO link | Discoverable without interrupting the experience |
| Machine-readable public state | Stable project/steward/organization fields | Agents and downstream tooling should not infer provenance from branding |
| About / credits screen, when one exists | One concise maker line plus contributor/license links | Provenance belongs naturally here |
| Source algorithms | **No repetitive corporate headers** | Keeps code readable and contributor-friendly |
| Benchmark results | Project name and evidence only; no extra promotional treatment | Measurement must not become marketing theater |
| CLI normal output | Project behavior first; no recurring ad line | Tool usage should remain frictionless |

> Footnote: a single natural surface can satisfy several visibility needs. More repetitions do not create more trust once provenance is already obvious.

## Exact language and links

Use the public GitHub organization as the default attribution target until another canonical public FCMO destination is explicitly adopted:

`https://github.com/FCMO-AI`

The preferred visible forms are exactly:

`<PROJECT> by FCMO AI`

`From the FCMO group`

Avoid inflated alternatives such as “Powered by,” “Presented by,” “An FCMO revolution,” or other sponsorship language. FCMO should read as the maker, not as an advertiser renting space inside the project.

## Visual behavior

Attribution should usually be one or two hierarchy levels below the project's primary signal:

- small mono or metadata typography is preferred;
- use existing project neutrals before inventing a new corporate accent;
- provide enough contrast for accessibility, but do not use a glow, badge, or attention animation;
- a thin rule, small gap, or peripheral placement may separate stewardship from product information;
- on hover/focus, a linked `FCMO AI` may become clearer, but the interaction should remain calm;
- mobile layouts may stack the two credit lines rather than shrink them into illegibility.

CMPCT therefore keeps its own visual language and treats FCMO as a maker's signature rather than importing a second full brand system into the page.

## Contributor and community integrity

Organizational stewardship and human contribution are different layers. FCMO attribution must coexist with commit authorship, contributor lists, third-party notices, acknowledgements, and upstream license obligations.

Never use the maker line to imply that FCMO authored third-party code it did not author. Never remove an upstream notice to make the project appear more internally originated. Where a contributor deserves explicit project credit, give it.

A good open-source reputation comes partly from how generously and accurately the project handles other people's work.

## Evidence before halo

The desired reputation transfer must be earned by observable behavior:

- useful software;
- honest benchmarks;
- visible losses and limitations;
- good documentation;
- stable interfaces;
- responsive issue handling;
- clean security and disclosure practice;
- graceful contributor treatment;
- releases that improve the product rather than merely generate activity.

Organizational credit should never be used to make weak evidence look stronger. The causal direction is the reverse: **the evidence should make the organization look stronger**.

## Organization-level implementation

Each public project should implement the same quiet-provenance contract locally. At the organization level, FCMO AI should also maintain a public GitHub organization profile that explains what FCMO AI builds and highlights the strongest public projects. That is the correct place for portfolio-level discovery; individual repositories should not become catalog pages.

GitHub's native organization-profile mechanism is a public `.github` repository containing `profile/README.md`, with selected public projects pinned on the organization profile.

> Footnote: organization-level discovery is intentionally separated from repository-level attribution. A visitor should be able to enjoy and adopt a project without being pushed through an FCMO marketing funnel.

## Machine-readable contract

When a public site or project exposes machine-readable metadata, prefer fields with explicit semantics rather than forcing agents to parse prose:

```json
{
  "project": "CMPCT",
  "credit": "CMPCT by FCMO AI",
  "group_credit": "From the FCMO group",
  "steward": "FCMO AI",
  "steward_url": "https://github.com/FCMO-AI"
}
```

The exact schema may evolve, but those meanings should remain separable from project version, benchmark authority, license state, and contributor identity.

## Review gate for future public projects

Before publication or a major public-surface redesign, verify all of the following:

1. The project is understandable without private organizational context.
2. The project name remains the dominant identity.
3. The maker line appears on at least one repository-facing surface and one durable metadata surface.
4. A website or application has a quiet provenance location if it has a persistent footer/About surface.
5. Package/citation metadata uses ecosystem-native fields where available.
6. No repetitive FCMO advertising was inserted into source code or normal tool output.
7. Contributor and upstream attribution remains intact.
8. FCMO credit does not imply benchmark authority, licensing terms, or capabilities unsupported by the project.
9. Private project names, internal architecture, client context, and unrelated organizational lore remain outside the public surface.
10. The final rendered experience is inspected: subtle attribution must remain legible, and legible attribution must remain subtle.

## The standard in one sentence

**Build something people would recommend even if they never noticed the maker line; make the maker line good enough that, when they do notice it, they remember FCMO.**
