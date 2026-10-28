# CMPCT Site Visual Campaign — Surface 0.29.e

Status: implementation record for the 0.29.e public-site visual redesign.

## Mission

Upgrade the website without changing benchmark claims, release information, engineering authority, Browser Lab behavior, or the public evidence model.

The campaign executes three stages:

1. **Restore** the strong enhancement layer that existed before the public-proof rebuild and repair the publication regression that dropped it.
2. **Refine** the restored graphics into a more disciplined visual grammar rather than blindly reviving generic technical spectacle.
3. **Elevate** the whole site into one coherent, premium system whose graphics explain CMPCT instead of merely decorating it.

## What regressed

Historical comparison found that the richer stylesheet and motion machinery still existed in `main`; the major loss happened in publication. The serving `gh-pages` artifact contained raw source HTML rather than the fully enhanced build.

Observable symptoms included:

- `motion.css`, `polish.css`, and `motion.js` absent from served HTML;
- template markers such as `__CMPCT_VERSION__` remaining unexpanded;
- the proof-oriented information architecture therefore being served without its intended enhancement pass.

This campaign treats correct enhancement/publication as part of visual quality, not as an unrelated deployment detail.

## Visual doctrine

The new surface follows a small set of rules:

- **Formal facade, unusual system underneath.** From a distance the page is stable, sober and credible. Up close, data structure, evidence receipts, alignment and interaction reveal the deeper system.
- **Structure before effects.** Grid, proportion, spacing, boundaries and hierarchy do the work before animation or decoration enters.
- **Charcoal is structure.** The dark frame is the permanent system: boundaries, authority and continuity.
- **Orange is intervention.** `#FD5204` is reserved for the active caret, actions, entry marks, decisions and moments of change; it is not a generic success color.
- **One dominant signal per surface.** Empty space and restraint preserve the force of the active mark.
- **Technical without cosplay.** Real benchmark data, evidence, machine-readable state and interface behavior create the technical character. Particles, neon, fake terminals and decorative data streams do not.
- **Depth is discovered.** Contemporary sans leads; classical serif appears only in selected conceptual emphasis; monospace is used for real data, code, commands and machine state.

## Restore without erasing

The established proof-surface stylesheet is retained byte-for-byte as `site/src/assets/experience-base.css`.

`experience.css` is now a tiny assembly layer:

1. load the preserved proof baseline;
2. load `atelier.css` last as the current visual campaign.

Footnote: this split allows future visual work to be replaced or rolled back without reconstructing the evidence-oriented CSS that predates it.

## Major visual features

### Hero gateway

The hero becomes a large open charcoal frame crossed by an orange caret. The frame is deliberately stable and incomplete; the caret enters from outside and crosses the boundary. This is the primary graphic moment, so the headline itself returns to warm ivory instead of competing in orange.

The live benchmark proof card sits inside that language: open internal frame, oversized measured value, and a single caret crossing the top boundary.

### Evidence wall

Headline metrics become an architectural wall of large evidence typography and shared rules. One localized orange datum line establishes the active entry point; cells remain flat charcoal and only lift slightly on inspection.

### Mental model

Traditional archive and CMPCT relationship diagrams use frame grammar instead of decorative illustration. The CMPCT side receives the crossing caret and orange structural edge; logical objects and shared physical information remain the graphic subject.

### Arena

The comparison ladder is styled as a measurement instrument. Bars are taller, quarter-scale ticks improve visual comparison, and one orange datum line organizes the chart. Orange identifies CMPCT; green/red continue to encode measured favorable/unfavorable evidence only.

### Red-team board

Known losses use the same design care as wins. This prevents transparency from looking like an afterthought and reinforces that preserved failure is part of the proof system.

### Canonical / research authority

The shipping-versus-frontier band becomes the second open-frame moment. The caret crosses the band boundary while canonical and research cards remain unmistakably separate.

### Browser Lab

The Lab reads like an instrument rather than a SaaS widget: flat panels, precise borders, an activation line, strong selected/result states and no fake terminal decoration.

### Release rail and engineering handoff

Release history reads as a measured progression instead of a pile of cards. The final handoff gets generous space, one orange rule and restrained exit links into the engineering system.

## Motion law

Motion must do one of four jobs:

- **arrive** — introduce a signal or evidence once;
- **cross** — show entry through a boundary;
- **order** — reveal hierarchy or update measured data;
- **respond** — provide small pointer/hover feedback.

The older orbit/particle layer is suppressed. Useful pointer depth, staged reveals and data-value response remain. `prefers-reduced-motion` remains authoritative.

## Regression guard

`site/tests/proof_surface_contract.py` now rejects generated sites when:

- build/version placeholders remain unexpanded;
- motion, polish or stable experience assets are missing from generated HTML;
- the preserved baseline or current atelier stylesheet is missing from the generated artifact;
- existing proof/evidence surfaces disappear.

This turns the exact publication downgrade that motivated the campaign into a release-blocking test.

## Scope boundary

Surface 0.29.e changes presentation only. It does **not** change:

- archive bytes or canonical format revision;
- compression benchmark values;
- release claims;
- public-evidence semantics;
- Browser Lab archive behavior.

## Definition of done

The campaign is complete only when:

- source is merged to `main`;
- proof/evidence/JavaScript/Browser Lab gates pass;
- the enhanced static artifact is promoted to `gh-pages`;
- `deployment.json` names the exact merged source commit and surface `0.29.e`;
- the public URL is verified against that receipt.
