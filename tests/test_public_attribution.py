from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


CANONICAL_CREDIT = "CMPCT by FCMO AI"
GROUP_CREDIT = "From the FCMO group"
FCMO_URL = "https://github.com/FCMO-AI"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_surface_revision_records_attribution_campaign() -> None:
    assert read("SURFACE_REVISION").strip() == "0.29.k"


def test_repository_facade_preserves_quiet_maker_credit() -> None:
    hero = read(".github/assets/repository-hero.svg")
    assert CANONICAL_CREDIT in hero
    assert GROUP_CREDIT in hero
    # Footnote: the maker line may be subtle, but it must not gain benchmark/release payload that can go stale.
    assert "CMPCT by <tspan" in hero


def test_python_package_metadata_carries_stewardship_natively() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]
    assert project["authors"] == [{"name": "FCMO AI"}]
    assert project["urls"]["Repository"] == "https://github.com/FCMO-AI/.CMPCT"
    assert project["urls"]["FCMO AI"] == FCMO_URL


def test_native_package_uses_modern_metadata_not_deprecated_authors() -> None:
    cargo = read("native/cmpct-core/Cargo.toml")
    assert 'repository = "https://github.com/FCMO-AI/.CMPCT"' in cargo
    assert f'steward-url = "{FCMO_URL}"' in cargo
    assert f'project-credit = "{CANONICAL_CREDIT}"' in cargo
    assert f'group-credit = "{GROUP_CREDIT}"' in cargo
    # Footnote: Cargo authors is deprecated; provenance lives in durable URLs/namespaced metadata instead.
    assert "\nauthors =" not in cargo


def test_citation_and_machine_receipt_preserve_same_identity() -> None:
    citation = read("CITATION.cff")
    assert 'name: "FCMO AI"' in citation
    assert 'title: "CMPCT"' in citation

    receipt = json.loads(read("site/src/project-attribution.json"))
    assert receipt["credit"] == CANONICAL_CREDIT
    assert receipt["group_credit"] == GROUP_CREDIT
    assert receipt["steward"] == "FCMO AI"
    assert receipt["steward_url"] == FCMO_URL


def test_website_attribution_is_additive_and_outside_proof_renderer() -> None:
    assembly_js = read("site/src/assets/experience.js")
    assembly_css = read("site/src/assets/experience.css")
    attribution_js = read("site/src/assets/fcmo-attribution.js")
    attribution_css = read("site/src/assets/fcmo-attribution.css")
    proof_renderer = read("site/src/assets/proof-renderer.js")

    assert 'import "./fcmo-attribution.js";' in assembly_js
    assert '@import url("./fcmo-attribution.css");' in assembly_css
    assert assembly_css.index('fcmo-attribution.css') < assembly_css.index('responsive.css')
    assert CANONICAL_CREDIT.split(" FCMO AI")[0] in attribution_js
    assert "FCMO AI" in attribution_js
    assert GROUP_CREDIT in attribution_js
    assert "fcmo-attribution" in attribution_css

    # Footnote: the serving receipt prevents a stale visible surface label after a safe partial promotion.
    assert "fetch('surface-revision.txt'" in attribution_js
    assert "surface\\s+\\d+\\.\\d+\\.[a-z]+" in attribution_js

    # Footnote: evidence truth must remain independent from organizational provenance.
    assert "FCMO AI" not in proof_renderer
    assert GROUP_CREDIT not in proof_renderer


def test_public_stewardship_doctrine_is_project_first() -> None:
    doctrine = read("docs/OPEN_SOURCE_STEWARDSHIP.md")
    assert "quiet provenance" in doctrine.lower()
    assert "Project first. Maker's mark second." in doctrine
    assert CANONICAL_CREDIT in doctrine
    assert GROUP_CREDIT in doctrine
    assert "do not insert corporate copy into algorithms or source-file headers" in doctrine
