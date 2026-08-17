"""Safety/correctness facade for the bounded v0.30 Representation Superoptimizer extractor.

The initial research draft used ``row.__dict__`` in ``Problem.baseline``. ``Extraction`` is a slotted frozen
dataclass and intentionally has no instance dictionary, so that convenience path was invalid.  The optimizer's
`evaluate`, exact extraction and beam extraction were not affected, but benchmark/test callers should not carry
a latent audit-surface failure.

Footnote: keeping this repair in a facade preserves the exact first draft for research history.  If the shared-
cost mechanism survives its phase-ordering falsifiers, the correction should be folded into the owning module
before any parent integration.
"""
from __future__ import annotations

from experiments import representation_superoptimizer_v030 as RSO


def _baseline(self: RSO.Problem) -> RSO.Extraction:
    row = self.evaluate(frozenset())
    return RSO.Extraction(
        total_bytes=row.total_bytes,
        facility_bytes=row.facility_bytes,
        private_bytes=row.private_bytes,
        opened=row.opened,
        selected=row.selected,
        method="baseline",
        states_evaluated=1,
    )


RSO.Problem.baseline = _baseline

Policy = RSO.Policy
Facility = RSO.Facility
Plan = RSO.Plan
Extraction = RSO.Extraction
Problem = RSO.Problem
exact_extract = RSO.exact_extract
beam_extract = RSO.beam_extract
explain = RSO.explain
