"""Compatibility facade for the hardened v0.30 Representation Superoptimizer extractor.

The initial research draft used ``row.__dict__`` in ``Problem.baseline`` even though ``Extraction`` is a slotted
frozen dataclass.  That first repair lived here to preserve derivation history.  The owning module has now been
production-hardened: baseline construction is native, declared targets cannot disappear through policy filtering,
resource/cost declarations are canonical, and component-wise exact extraction can emit an explicit optimality
certificate.

Footnote: keeping this facade means existing benchmark/test imports do not fork merely because correctness moved
to its rightful owner.  There is no runtime monkeypatch now; all aliases point directly at the hardened module.
"""
from __future__ import annotations

from experiments import representation_superoptimizer_v030 as RSO

Policy = RSO.Policy
Facility = RSO.Facility
Plan = RSO.Plan
Extraction = RSO.Extraction
Problem = RSO.Problem
exact_extract = RSO.exact_extract
beam_extract = RSO.beam_extract
extract_with_certificate = RSO.extract_with_certificate
explain = RSO.explain
