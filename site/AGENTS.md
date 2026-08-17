# Site agent instructions

This subtree is CMPCT's public proof surface. Before modifying it, read:

1. `../docs/SITE_PUBLIC_PROOF_STANDARD.md`;
2. `README.md`;
3. `../docs/PUBLIC_SURFACE.md`;
4. `../docs/BENCHMARKS.md`;
5. the current public benchmark record(s) under `../benchmarks/history/`.

## Non-negotiables

- Do not type benchmark headline percentages into HTML or CSS.
- Consume `project-data.json.public_evidence` for release-independent performance presentation.
- Do not add a new `frontier-vXYZ.js` renderer for each release. Normalize the new benchmark schema into
  `cmpct-public-evidence-v1` instead.
- Keep at least one familiar baseline and the strongest relevant serious compressor visible when evidence exists.
- Preserve relevant losses on the Red Team Board. Green means measured favorable evidence, not “CMPCT.”
- Keep research-frontier authority visually and textually separate from canonical format/reader authority.
- Raw stored-byte comparison does not imply equivalent access, recovery, integrity or durability semantics.
- Browser Lab compatibility is a release-sensitive feature; do not weaken its revision gate.
- Preserve accessibility, mobile reading order and `prefers-reduced-motion` behavior.
- Presentation-only work advances `SURFACE_REVISION`, not the numeric core version.
- Run `python site/tests/proof_surface_contract.py _site` after building the site.

A future agent should be able to replace the current benchmark record with the next release's evidence and
see the hero, arena, loss board and receipt update without rewriting the page.
