"""CI decision check for the frozen ONE-G0.2 shared authentication family experiment."""
from __future__ import annotations

import json
from benchmarks.one.one_g02_shared_vs_independent_auth_family_ab import run

EXPECTED = "advance_shared_authenticated_family_pareto"

result = run()
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if result.get("decision") == EXPECTED else 1)
