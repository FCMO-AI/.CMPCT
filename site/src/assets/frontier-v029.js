const $ = (selector) => document.querySelector(selector);

function esc(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[char]);
}

function pct(value, digits = 2) {
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

function signedLead(value, digits = 2) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  if (Math.abs(n) < 1e-12) return `0.${"0".repeat(digits)}%`;
  return `${n > 0 ? "−" : "+"}${Math.abs(n).toFixed(digits)}%`;
}

function render(frontier) {
  if (!frontier || frontier.render_contract !== "mosaic-v029") return;

  const overall = frontier.overall_comparison || {};
  const release = frontier.release_delta || {};
  const scheduler = frontier.scheduler || {};
  const headlineShort = overall.headline_comparator_short || "7z / LZMA2";
  const headline = competitor(frontier, headlineShort) || {};

  // Footnote: the v0.29 hero is cross-format and same-tree. The portable v0.28→v0.29 release delta is
  // intentionally reported separately because summing fifteen independently archived workloads answers
  // a different benchmark question than archiving the hostile suite as one complete recursive tree.
  $("#hero-gain").textContent = pct(headline.lead_pct);
  const scoreUnit = document.querySelector(".score-unit");
  if (scoreUnit) {
    const relation = Number(headline.lead_pct) >= 0 ? "smaller than" : "larger than";
    scoreUnit.textContent = `${relation} ${headline.short || "matched archive comparator"}`;
  }

  const speed = Number(scheduler.wallclock_improvement_pct);
  const speedClause = Number.isFinite(speed)
    ? ` Accepted-engine parallel scheduling: ${speed.toFixed(1)}% lower median creation wall time on its fixed hostile ABBA gate, byte-identical to the sequential attempt-5 portfolio.`
    : "";
  $("#hero-qualification").textContent = `Mosaic / Residual Program Packing v${frontier.project_version} · matched hostile whole-suite comparison across ${Number(overall.files || frontier.files || 0).toLocaleString()} files. Portable release delta: ${pct(release.lead_pct, 4)} smaller than ${release.baseline_short || "v0.28"}, ${release.workloads_improved || 0} improved / ${release.workloads_regressed || 0} regressed across ${release.workloads || frontier.workload_count || 0} inherited-frontier workloads.${speedClause} Canonical format remains r${frontier.canonical_format_revision}.`;
  $("#frontier-version").textContent = `v${frontier.project_version || "—"}`;
  $("#frontier-label").textContent = frontier.candidate?.status || "accepted research milestone";

  const sevenZip = competitor(frontier, "7z / LZMA2");
  const zpaq = competitor(frontier, "ZPAQ m5");
  const solid = competitor(frontier, "tar / Zstd solid");
  const speedValue = Number.isFinite(speed) ? `${speed.toFixed(1)}%` : "—";
  const metrics = [
    ["7Z / LZMA2", signedLead(sevenZip?.lead_pct), "matched hostile size delta"],
    ["ZPAQ M5", signedLead(zpaq?.lead_pct), "matched hostile size delta"],
    ["SOLID TAR / ZSTD", signedLead(solid?.lead_pct), "matched hostile size delta"],
    ["CREATE WALL TIME", speedValue, "ABBA scheduler improvement"],
  ];
  $("#hero-metrics").innerHTML = metrics.map(([label, value, note]) => `<article><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></article>`).join("");

  const matrixCard = $(".matrix-card .card-head span");
  if (matrixCard) matrixCard.textContent = "v0.29 RELEASE DELTA";
  const workloads = frontier.workloads || [];
  $("#workload-score").textContent = `${release.workloads_improved ?? frontier.wins_primary ?? 0}/${release.workloads || frontier.workload_count || workloads.length} improved · ${release.workloads_regressed ?? frontier.regressions_primary ?? 0} regressed`;
  $("#workload-matrix").innerHTML = workloads.map((row) => {
    const delta = Number(row.cmpct_vs_primary_pct);
    const improved = Boolean(row.improved);
    const unchanged = Number.isFinite(delta) && Math.abs(delta) < 1e-12;
    const className = improved ? "win" : unchanged ? "" : "loss";
    const value = Number.isFinite(delta) ? signedLead(delta) : "—";
    const note = improved
      ? `smaller than ${release.baseline_short || "v0.28"}`
      : unchanged
        ? "exact v0.28 fallback"
        : `larger than ${release.baseline_short || "v0.28"}`;
    return `<div class="workload-cell ${className}"><span>${esc(shortWorkload(row.name))}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></div>`;
  }).join("");

  $("#known-losses").innerHTML = (frontier.known_losses || []).map((item) => `<div class="loss-item">${esc(item)}</div>`).join("") || "<div class='loss-item'>No recorded qualification.</div>";
}

async function boot() {
  try {
    const response = await fetch("project-data.json", { cache: "no-store" });
    if (!response.ok) return;
    const data = await response.json();
    const frontier = data.frontier;
    if (!frontier || frontier.render_contract !== "mosaic-v029") return;

    // Wait until app.js establishes the common DOM, then overwrite only evidence-sensitive labels.
    // This keeps Browser Lab, parity rendering, navigation and accessibility behavior shared with v0.28.
    let attempts = 0;
    const settle = () => {
      const ready = $("#frontier-version")?.textContent?.includes(String(frontier.project_version));
      if (ready || attempts++ > 120) render(frontier);
      else requestAnimationFrame(settle);
    };
    settle();
  } catch (_) {
    // app.js owns the canonical site-data error state; the release adapter fails soft.
  }
}

boot();
