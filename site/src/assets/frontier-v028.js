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

function render(frontier) {
  if (!frontier || frontier.render_contract !== "entropygraph-v028") return;
  const primary = frontier.primary_comparator || {};

  // Footnote: v0.28's primary falsification target is its inherited EntropyGraph frontier, not an
  // invented ZIP/Zstd aggregate. The old site renderer assumed one fixed comparator; this additive
  // renderer changes the labels and percentages to match the benchmark's actual declared contract.
  $("#hero-gain").textContent = pct(primary.lead_pct);
  const scoreUnit = document.querySelector(".score-unit");
  if (scoreUnit) scoreUnit.textContent = `smaller than ${primary.short || "inherited frontier"}`;
  $("#hero-qualification").textContent = `EntropyGraph II v${frontier.project_version} research frontier · ${Number(frontier.files || 0).toLocaleString()} files · ${frontier.workload_count || 0} fixed workloads · ${frontier.regressions_primary || 0} size regressions. Canonical format remains r${frontier.canonical_format_revision}.`;
  $("#frontier-version").textContent = `v${frontier.project_version || "—"}`;
  $("#frontier-label").textContent = frontier.candidate?.status || "research benchmark candidate";

  const competitors = frontier.competitors || [];
  const zipDeflate = competitors.find((row) => row.short === "ZIP / Deflate");
  const solid = competitors.find((row) => row.short === "tar / Zstd solid");
  const sevenZip = competitors.find((row) => row.short === "7z / LZMA2");
  const metrics = [
    [String(primary.short || "BASELINE").toUpperCase(), pct(primary.lead_pct), "measured portfolio lead"],
    ["ZIP / DEFLATE", pct(zipDeflate?.lead_pct), "structural aggregate lead"],
    ["7Z / LZMA2", pct(sevenZip?.lead_pct), "structural aggregate lead"],
    ["SOLID TAR / ZSTD", pct(solid?.lead_pct), "structural diagnostic lead"],
  ];
  $("#hero-metrics").innerHTML = metrics.map(([label, value, note]) => `<article><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></article>`).join("");

  const workloads = frontier.workloads || [];
  $("#workload-score").textContent = `${frontier.wins_primary || 0}/${frontier.workload_count || workloads.length} improved · ${frontier.regressions_primary || 0} regressed`;
  $("#workload-matrix").innerHTML = workloads.map((row) => {
    const delta = Number(row.cmpct_vs_primary_pct);
    const improved = Boolean(row.improved);
    const unchanged = Number.isFinite(delta) && Math.abs(delta) < 1e-9;
    const className = improved ? "win" : unchanged ? "" : "loss";
    const value = Number.isFinite(delta) ? (unchanged ? "0.00%" : `−${Math.abs(delta).toFixed(2)}%`) : "—";
    const note = improved ? "smaller than inherited v0.25" : unchanged ? "exact inherited fallback" : "larger than inherited v0.25";
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
    // This keeps the patch additive and avoids forking the Browser Lab / parity-rendering code.
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
