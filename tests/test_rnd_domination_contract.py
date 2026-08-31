from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "docs" / "RND_DOMINATION_RUBRIC.md"
HOURLY = ROOT / "docs" / "HOURLY_RUN_DURATION_CONTRACT.md"


def test_rnd_domination_rubric_is_normative_and_strict() -> None:
    text = RUBRIC.read_text(encoding="utf-8")

    required = (
        "normative for material CMPCT R&D",
        "True domination means every frozen workload is strictly smaller AND strictly faster to create",
        "Ties fail",
        "D0 — Evidence / harness red",
        "D5 — Productization / platform red",
        "R0 — Measurement / disproof only",
        "R4 — Representation / physical semantics",
        "S1 — Proven floor trigger",
        "S6 — Proven-win productization trigger",
        "Research Priority Score (RPS)",
        "Micro-optimization admissibility test",
        "Mandatory hypothesis portfolio",
        "Mandatory self-critique loop for every material R&D iteration",
        "Exact futility is a first-class research target",
        "Representation invention contract",
        "PROMOTE_NEXT_PREREQUISITE",
        "ESCALATE_RADICALITY",
        "RETIRE_FAMILY",
        "Iteration 0",
        "Iteration 1",
        "Iteration 2",
    )
    missing = [needle for needle in required if needle not in text]
    assert not missing, f"R&D domination contract lost required law: {missing}"


def test_hourly_contract_binds_domination_rubric() -> None:
    text = HOURLY.read_text(encoding="utf-8")

    required = (
        "docs/RND_DOMINATION_RUBRIC.md",
        "Mandatory R&D selection checkpoint",
        "classify the active red(s) D0–D5",
        "apply saturation triggers S1–S6",
        "minimum admissible radicality R0–R4",
        "frontier queue",
        "convergence queue",
        "STRUCTURAL_RED",
        "never confuse activity with progress toward strict 15/15 domination",
    )
    missing = [needle for needle in required if needle not in text]
    assert not missing, f"hourly contract no longer enforces R&D domination rubric: {missing}"


def test_rubric_preserves_release_firewall() -> None:
    text = RUBRIC.read_text(encoding="utf-8")

    assert "This rubric selects and evaluates research. It **does not grant release credit**." in text
    assert "benchmark-identity dependent — **automatic rejection**" in text
    assert "zero-byte no-regression law" in text
    assert "locality <=8x" in text
    assert "decode unit <=8 MiB" in text
    assert "exact common-fingerprint 15-workload authority" in text
