from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "docs" / "RND_DOMINATION_RUBRIC.md"
HOURLY = ROOT / "docs" / "HOURLY_RUN_DURATION_CONTRACT.md"
DOCTRINE = ROOT / "docs" / "FUNDAMENTAL_RESEARCH_DOCTRINE.md"


def test_rnd_domination_rubric_is_normative_and_strict() -> None:
    text = RUBRIC.read_text(encoding="utf-8")

    required = (
        "normative for Forge convergence/productization work",
        "The Foundry may invent beyond the current benchmark matrix; the Forge must make the real product satisfy it.",
        "Every frozen workload is strictly smaller and strictly faster to create than both ordinary ZIP/Deflate and solid Zstd-19",
        "Ties fail.",
        "D0 — Evidence / custody red",
        "D5 — Productization / platform",
        "R0 — measurement/disproof",
        "R4 — representation/physical semantics",
        "S1 — Proven floor",
        "S6 — Proven-win productization",
        "Forge Research Priority Score (RPS)",
        "Micro-optimization admissibility",
        "Referee → Builder → Hostile Reviewer",
        "Proof that work cannot win is a first-class Forge optimization.",
        "Global carrying cost during Forge admission",
        "PROMOTE_NEXT_PREREQUISITE",
        "RETURN_TO_FOUNDRY",
        "RETIRE_FAMILY",
    )
    missing = [needle for needle in required if needle not in text]
    assert not missing, f"Forge domination contract lost required law: {missing}"


def test_foundry_forge_authority_split_is_explicit() -> None:
    rubric = RUBRIC.read_text(encoding="utf-8")
    doctrine = DOCTRINE.read_text(encoding="utf-8")

    assert "no longer the global CMPCT research-question generator" in rubric
    assert "R5 belongs to the Foundry" in rubric
    assert "Foundry" in doctrine and "Forge" in doctrine and "Custody" in doctrine


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

    assert "This objective is product/convergence truth." in text
    assert "Aggregate wins never erase a losing required row." in text
    assert "A strict local win does not automatically justify permanent portfolio entropy." in text
    assert "Do not skip a prerequisite because the research result is exciting." in text
    assert "Correctness, integrity/authentication, hostile-input/resource safety and truthful evidence are never debt." in text
    assert "do not call the product finished until every current promotion requirement is honestly satisfied." in text
