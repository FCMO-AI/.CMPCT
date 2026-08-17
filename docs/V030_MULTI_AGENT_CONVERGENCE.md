# v0.30 multi-agent convergence protocol

The repository is actively modified by multiple agents. Authoritative integration therefore follows a conflict-avoidant protocol rather than assuming branch heads are static.

1. Resolve the source branch head immediately before import.
2. Compare that head against the last reviewed head in `V030_INTEGRATION_IMPORTS.md`.
3. If the head moved, inspect only the delta first; do not blindly replace integration files.
4. Merge orthogonal files where possible. For overlapping implementations, assign one owner and port only the missing behavior/tests.
5. Do not weaken a source branch's frozen gate to make integration pass.
6. Preserve provenance in commit messages and evidence JSON; integration commits are not evidence substitutes.
7. Do not merge this branch to `main` while any normative release gate remains open.

### Current overlap decisions

- Generic same-filesystem winner publication is owned by the inherited v0.29 scheduler (PR #54 lineage). CMPNX14-specific code may use the same primitive but must not maintain a competing generic implementation.
- Hierarchical Geometry nomination/transform semantics are owned by the CMPNX14 Geometry reactor. Overlay integration should call/reuse that implementation rather than fork its separator heuristics.
- PrefixGraph's oracle grammar remains evidence scaffolding. The promoted feature must be represented inside the owning v0.30 graph/compiler with depth <=1 and exact complete-artifact pricing.
- GIR hardening semantics (bounded admission, streamed verification/extraction, recovery, rollback) are reader requirements for any promoted new grammar, regardless of which writer architecture wins.

Footnote: this protocol deliberately optimizes for semantic convergence, not minimum Git commit count. Duplicate research branches are acceptable; duplicate promoted implementations are not.
