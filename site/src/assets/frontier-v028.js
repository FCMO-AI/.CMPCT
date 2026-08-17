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

function signedStorageDelta(lead) {
  const n = Number(lead);
  if (!Number.isFinite(n)) return "—";
  if (Math.abs(n) < 1e-9) return "0.00%";
  // Positive `lead` means CMPCT stores fewer bytes, so the visual delta is negative (smaller archive).
  return `${n > 0 ? "−" : "+"}${Math.abs(n).toFixed(2)}%`;
}

function render(frontier) {
  if (!frontier || frontier.render_contract !== "entropygraph-v028") return;

  const overall = frontier.overall_comparison || {};
  const category = frontier.category_comparison || {};
  const release = frontier.release_delta || {};
  const headlineShort = overall.headline_comparator_short || "ZIP / Deflate";
  const headline = competitor(frontier, headlineShort) || {};
  const zipDeflate = competitor(frontier, "ZIP / Deflate");
  const sevenZip = competitor(frontier, "7z / LZMA2");
  const solid = competitor(frontier, "tar / Zstd solid");

  // Footnote: the hero answers the broad adoption question with familiar ZIP as the headline, but it
  // places the stronger solid-Zstd size baseline beside it. The category matrix below then pivots fully
  // to Zstd so the page does not look impressive only because it chose an easy legacy comparator.
  $("#hero-gain").textContent = pct(headline.lead_pct);
  const scoreUnit = document.querySelector(".score-unit");
  if (scoreUnit) {
    const zstdPart = Number.isFinite(Number(solid?.lead_pct)) ? ` · ${pct(solid.lead_pct)} vs solid Zstd-19` : "";
    scoreUnit.textContent = `smaller than ${headline.short || "ZIP / Deflate"}${zstdPart}`;
  }
  $("#hero-qualification").textContent = `EntropyGraph II v${frontier.project_version} matched whole-suite frontier · ${Number(overall.files || frontier.files || 0).toLocaleString()} files across ${overall.suite_count || 0} aggregate suites. Category frontier: ${category.wins_vs_zstd ?? "—"}/${category.workloads ?? frontier.workload_count ?? "—"} workloads smaller than solid Zstd-19. Release causality remains separate: ${pct(release.lead_pct)} smaller than ${release.baseline_short || "v0.25"}, ${release.workloads_improved || 0} improved / ${release.workloads_regressed || 0} regressed. Canonical format remains r${frontier.canonical_format_revision}.`;
  $("#frontier-version").textContent = `v${frontier.project_version || "—"}`;
  $("#frontier-label").textContent = frontier.candidate?.status || "research benchmark candidate";

  const metrics = [
    ["ZIP / DEFLATE", pct(zipDeflate?.lead_pct), "matched whole-suite lead"],
    ["SOLID ZSTD-19", pct(solid?.lead_pct), "serious size baseline · matched suites"],
    ["7Z / LZMA2", pct(sevenZip?.lead_pct), "matched whole-suite lead"],
    ["CATEGORY WINS VS ZSTD", `${category.wins_vs_zstd ?? "—"}/${category.workloads ?? "—"}`, "exact-tree workload frontier"],
  ];
  $("#hero-metrics").innerHTML = metrics.map(([label, value, note]) => `<article><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></article>`).join("");

  // Footnote: these tiles are deliberately NOT the v0.28-vs-v0.25 release delta. Each tile compares
  // current CMPCT with solid tar+Zstd-19 on the exact same independently archived workload tree. The
  // release delta stays in qualification/evidence, while the lower canonical table keeps its own job:
  // executable CMPCT-vs-ZIP archive size plus create/extract latency.
  const matrixCard = $(".matrix-card .card-head span");
  if (matrixCard) matrixCard.textContent = "CATEGORY FRONTIER · SOLID ZSTD-19";
  const rows = category.rows || [];
  if (rows.length) {
    $("#workload-score").textContent = `${category.wins_vs_zstd}/${category.workloads} smaller · ${category.losses_vs_zstd} larger`;
    $("#workload-matrix").innerHTML = rows.map((row) => {
      const lead = Number(row.cmpct_vs_zstd_pct);
      const win = Number.isFinite(lead) && lead > 1e-9;
      const loss = Number.isFinite(lead) && lead < -1e-9;
      const className = win ? "win" : loss ? "loss" : "";
      const note = win
        ? "smaller than solid Zstd-19"
        : loss
          ? "larger than solid Zstd-19"
          : "size tie with solid Zstd-19";
      return `<div class="workload-cell ${className}"><span>${esc(shortWorkload(row.name))}</span><strong>${esc(signedStorageDelta(lead))}</strong><small>${esc(note)}</small></div>`;
    }).join("");
  } else {
    $("#workload-score").textContent = "category evidence unavailable";
    $("#workload-matrix").innerHTML = '<div class="loss-item">Fresh exact-tree Zstd category evidence has not been committed for this frontier.</div>';
  }

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
    // This keeps Browser Lab and canonical ZIP parity rendering shared while the frontier gets its
    // evidence-aware overall/category/release separation.
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
