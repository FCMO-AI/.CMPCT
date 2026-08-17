const $ = (selector) => document.querySelector(selector);

function esc(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[char]);
}

function pct(value, digits = 1) {
  const n = Number(value);
  return Number.isFinite(n) ? `${n.toFixed(digits)}%` : "—";
}

function shortWorkload(name) {
  return String(name || "").replace(/^\d+_/, "").replaceAll("_", " ");
}

function competitor(frontier, short) {
  return (frontier.overall_comparison?.competitors || frontier.competitors || [])
    .find((row) => row.short === short);
}

function render(frontier) {
  if (!frontier || frontier.render_contract !== "entropygraph-v028") return;

  const overall = frontier.overall_comparison || {};
  const release = frontier.release_delta || {};
  const headlineShort = overall.headline_comparator_short || "ZIP / Deflate";
  const headline = competitor(frontier, headlineShort) || {};

  // Footnote: the homepage answers the enduring product question (current CMPCT vs external formats).
  // The direct-base v0.25→v0.28 delta remains visible as release evidence, but it no longer overwrites
  // the cross-format headline merely because that delta was the latest release's falsification target.
  $("#hero-gain").textContent = pct(headline.lead_pct);
  const scoreUnit = document.querySelector(".score-unit");
  if (scoreUnit) scoreUnit.textContent = `smaller than ${headline.short || "matched archive comparator"}`;
  $("#hero-qualification").textContent = `EntropyGraph II v${frontier.project_version} matched whole-suite frontier · ${Number(overall.files || frontier.files || 0).toLocaleString()} files across ${overall.suite_count || 0} deterministic aggregate suites. Release delta: ${pct(release.lead_pct)} smaller than ${release.baseline_short || "v0.25"}, ${release.workloads_improved || 0} improved / ${release.workloads_regressed || 0} regressed across ${release.workloads || frontier.workload_count || 0} fixed workloads. Canonical format remains r${frontier.canonical_format_revision}.`;
  $("#frontier-version").textContent = `v${frontier.project_version || "—"}`;
  $("#frontier-label").textContent = frontier.candidate?.status || "research benchmark candidate";

  const zipDeflate = competitor(frontier, "ZIP / Deflate");
  const sevenZip = competitor(frontier, "7z / LZMA2");
  const zpaq = competitor(frontier, "ZPAQ m5");
  const solid = competitor(frontier, "tar / Zstd solid");
  const metrics = [
    ["ZIP / DEFLATE", pct(zipDeflate?.lead_pct), "matched whole-suite lead"],
    ["7Z / LZMA2", pct(sevenZip?.lead_pct), "matched whole-suite lead"],
    ["ZPAQ M5", pct(zpaq?.lead_pct), "matched whole-suite lead"],
    ["SOLID TAR / ZSTD", pct(solid?.lead_pct), "matched diagnostic lead"],
  ];
  $("#hero-metrics").innerHTML = metrics.map(([label, value, note]) => `<article><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></article>`).join("");

  // Footnote: per-workload external-tool data was not re-measured in the public v0.28 record. Rather
  // than backfill stale v0.25 ZIP/Zstd numbers onto changed trees, keep this matrix explicitly scoped
  // to the v0.28 release delta while the arena above carries the current cross-format comparison.
  const matrixCard = $(".matrix-card .card-head span");
  if (matrixCard) matrixCard.textContent = "v0.28 RELEASE DELTA";
  const workloads = frontier.workloads || [];
  $("#workload-score").textContent = `${release.workloads_improved ?? frontier.wins_primary ?? 0}/${release.workloads || frontier.workload_count || workloads.length} improved · ${release.workloads_regressed ?? frontier.regressions_primary ?? 0} regressed`;
  $("#workload-matrix").innerHTML = workloads.map((row) => {
    const delta = Number(row.cmpct_vs_primary_pct);
    const improved = Boolean(row.improved);
    const unchanged = Number.isFinite(delta) && Math.abs(delta) < 1e-9;
    const className = improved ? "win" : unchanged ? "" : "loss";
    const value = Number.isFinite(delta)
      ? (unchanged ? "0.00%" : `${delta > 0 ? "−" : "+"}${Math.abs(delta).toFixed(2)}%`)
      : "—";
    const note = improved
      ? `smaller than ${release.baseline_short || "inherited v0.25"}`
      : unchanged
        ? "exact inherited fallback"
        : `larger than ${release.baseline_short || "inherited v0.25"}`;
    return `<div class="workload-cell ${className}"><span>${esc(shortWorkload(row.name))}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></div>`;
  }).join("");

  $("#known-losses").innerHTML = (frontier.known_losses || []).map((item) => `<div class="loss-item">${esc(item)}</div>`).join("") || "<div class='loss-item'>No recorded qualification.</div>";
}

async function boot() {
  let response;
  try {
    response = await fetch("project-data.json", { cache: "no-store" });
    if (!response.ok) return;
    const data = await response.json();
    const frontier = data.frontier;
    if (!frontier || frontier.render_contract !== "entropygraph-v028") return;

    // Wait until app.js has performed its normal first render, then apply the schema-specific view.
    // This keeps Browser Lab and parity rendering shared while the frontier gets its evidence-aware UI.
    let attempts = 0;
    const settle = () => {
      const ready = $("#frontier-version")?.textContent?.includes(String(frontier.project_version));
      if (ready || attempts++ > 120) render(frontier);
      else requestAnimationFrame(settle);
    };
    settle();
  } catch (_) {
    // app.js owns the canonical site-data error state; this optional adapter fails soft.
  }
}

boot();
