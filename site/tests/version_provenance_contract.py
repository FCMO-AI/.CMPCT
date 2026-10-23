#!/usr/bin/env python3
from __future__ import annotations

"""Independent publication/source identity falsifier for the stable public evidence adapter.

An old (or future) research record is not evidence that the currently installed CMPCT
release or canonical reader has that research record's version/format. No archive
benchmark, comparator or threshold is changed by these controls.
"""

import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "site"))

from enhance_site import build_public_evidence  # noqa: E402


def main() -> None:
    cases = (
        ("historical", "0.29.0", 23),
        ("same-release", "0.30.0", 24),
        ("future-research-only", "0.31.0", 25),
        ("unknown-history", None, None),
    )
    for name, research_version, research_format in cases:
        payload = {
            "project": {"project_version": "0.30.0", "format_revision": 24},
            "frontier": {
                "project_version": research_version,
                "canonical_format_revision": research_format,
                "file": "",
                "kind": "research-frontier",
                "known_losses": ["unmeasured product portability"],
            },
        }
        pristine = copy.deepcopy(payload)
        evidence = build_public_evidence(payload)
        assert payload == pristine, name
        # These are shipping claims, not aliases of a chosen research record.
        assert evidence["project_version"] == "0.30.0", name
        assert evidence["canonical_format_revision"] == 24, name
        provenance = evidence["provenance"]
        # These are the true measured source identifiers, even when old or future.
        assert provenance["source_project_version"] == research_version, name
        assert provenance["source_format_revision"] == research_format, name
        assert evidence["known_losses"] == ["unmeasured product portability"], name

    print("CMPCT publication/source identity court: 4/4 PASS")


if __name__ == "__main__":
    main()
