from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "site" / "src" / "assets" / "shipping-frontier-v029.js"


def test_shipping_frontier_benchmark_is_published_inside_zip_chapter() -> None:
    text = RENDERER.read_text(encoding="utf-8")

    # The benchmark must be injected into the canonical ZIP/parity chapter, immediately before the
    # existing ZIP benchmark headline, rather than living only in the separate authority band.
    assert '$(".parity-section")' in text
    assert '$("#benchmark-headline", parity)' in text
    assert 'panel.id = "shipping-frontier-zip-panel"' in text
    assert 'grid.id = "shipping-frontier-zip-kpis"' in text
    assert 'anchor.before(panel)' in text

    # The visible numbers stay evidence-driven: the renderer reads the committed JSON mirror and computes
    # the percentage from byte totals instead of hard-coding the benchmark headline into presentation code.
    assert 'fetch("assets/shipping-vs-frontier-v029.json"' in text
    assert 'const lead = (shipping - frontier) / shipping * 100;' in text
    assert 'rawLink.textContent = "shipping-vs-frontier-v029.json"' in text
    assert "24.24%" not in text
    assert "181503126" not in text
    assert "137501815" not in text

    # Dynamic authored labels reuse the existing curated vocabulary/patterns so the new block cannot become
    # an English-only island on localized surfaces.
    assert '"SHIPPING / CANONICAL"' in text
    assert '"reader / writer contract"' in text
    assert '"RESEARCH FRONTIER"' in text
    assert '"benchmark candidate"' in text
    assert '"PUBLIC EVIDENCE"' in text
    assert 'wins vs r24`' in text
    assert 'fewer stored bytes' not in text
    assert 'same trees' not in text
