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

function signedStorageDelta(value, digits = 2) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  if (Math.abs(n) < 1e-12) return `0.${"0".repeat(digits)}%`;
  // Positive lead means CMPCT uses fewer bytes; the displayed archive-size delta is therefore negative.
  return `${n > 0 ? "−" : "+"}${Math.abs(n).toFixed(digits)}%`;
}

function relation(value, comparator) {
  const n = Number(value);
  if (!Number.isFinite(n)) return `vs ${comparator}`;
  if (Math.abs(n) < 1e-12) return `same size as ${comparator}`;
  return `${Math.abs(n).toFixed(2)}% ${n > 0 ? "smaller" : "larger"} than ${comparator}`;
}

function render(frontier) {
  if (!frontier || frontier.render_contract !== "mosaic-v029") return;

  const overall = frontier.overall_comparison || {};
  const category = frontier.category_comparison || {};
  const release = frontier.release_delta || {};
  const scheduler = frontier.scheduler || {};
  const headlineShort = overall.headline_comparator_short || "ZIP / Deflate";
  const headline = competitor(frontier, headlineShort) || {};
  const zipDeflate = competitor(frontier, "ZIP / Deflate");
  const solid = competitor(frontier, "tar / Zstd solid");
  const sevenZip = competitor(frontier, "7z / LZMA2");

  // Footnote: ZIP is the familiar adoption headline, but solid Zstd is deliberately placed beside it
  // as the serious compression-size baseline. A negative Zstd result stays negative; the page earns
  // credibility by showing that current v0.29 is slightly larger on its matched hostile structural tree.
  $("#hero-gain").textContent = pct(headline.lead_pct);
  const scoreUnit = document.querySelector(".score-unit");
  if (scoreUnit) {
    const zipText = relation(zipDeflate?.lead_pct, "ZIP / Deflate");
    const zstdText = relation(solid?.lead_pct, "solid Zstd-19");
    scoreUnit.textContent = `${zipText} · ${zstdText}`;
  }

  const speed = Number(scheduler.wallclock_improvement_pct);
  const speedClause = Number.isFinite(speed)
    ? ` Accepted-engine scheduling: ${speed.toFixed(1)}% lower median creation wall time on its fixed hostile ABBA gate, byte-identical to sequential attempt #5.`
    : "";
  const categoryClause = category.workloads
    ? ` Category frontier: ${category.wins_vs_zstd}/${category.workloads} workloads smaller than solid Zstd-19, ${category.losses_vs_zstd} larger; independent-workload aggregate ${relation(category.lead_vs_zstd_pct, "solid Zstd-19")}.`
    : " Fresh exact-tree category evidence is unavailable for this frontier.";
  $("#hero-qualification").textContent = `Mosaic / Residual Program Packing v${frontier.project_version} · matched hostile whole-suite comparison across ${Number(overall.files || frontier.files || 0).toLocaleString()} files.${categoryClause} Release causality stays separate: ${pct(release.lead_pct, 4)} smaller than ${release.baseline_short || "v0.28"}, ${release.workloads_improved || 0} improved / ${release.workloads_regressed || 0} regressed across ${release.workloads || frontier.workload_count || 0} inherited-frontier workloads.${speedClause} Canonical format remains r${frontier.canonical_format_revision}.`;
  $("#frontier-version").textContent = `v${frontier.project_version || "—"}`;
  $("#frontier-label").textContent = frontier.candidate?.status || "accepted research milestone";

  const speedValue = Number.isFinite(speed) ? `${speed.toFixed(1)}%` : "—";
  const metrics = [
    ["ZIP / DEFLATE", signedStorageDelta(zipDeflate?.lead_pct), "matched hostile size delta"],
    ["SOLID ZSTD-19", signedStorageDelta(solid?.lead_pct), Number(solid?.lead_pct) >= 0 ? "CMPCT smaller · serious baseline" : "CMPCT larger · serious baseline"],
    ["CATEGORY WINS VS ZSTD", `${category.wins_vs_zstd ?? "—"}/${category.workloads ?? "—"}`, "exact-tree workload frontier"],
    ["CREATE WALL TIME", speedValue, "ABBA scheduler improvement"],
  ];
  $("#hero-metrics").innerHTML = metrics.map(([label, value, note]) => `<article><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></article>`).join("");

  // Footnote: the tiles now answer a competitive category question, not the release-delta question.
  // Each cell is current CMPCT vs solid tar+Zstd-19 on one exact same-lifetime workload tree. The lower
  // canonical table keeps a different job: executable CMPCT-vs-ZIP size plus create/extract timing.
  const matrixCard = $(".matrix-card .card-head span");
  if (matrixCard) matrixCard.textContent = "CATEGORY FRONTIER · SOLID ZSTD-19";
  const rows = category.rows || [];
  if (rows.length) {
    $("#workload-score").textContent = `${category.wins_vs_zstd}/${category.workloads} smaller · ${category.losses_vs_zstd} larger`;
    $("#workload-matrix").innerHTML = rows.map((row) => {
      const lead = Number(row.cmpct_vs_zstd_pct);
      const win = Number.isFinite(lead) && lead > 1e-12;
      const loss = Number.isFinite(lead) && lead < -1e-12;
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

  // The arena itself remains rendered by app.js from `frontier.competitors`; keeping 7z/ZPAQ/Borg there
  // prevents the hero focus on ZIP+Zstd from erasing stronger or differently scoped competitors.
  void sevenZip;
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
    // Browser Lab, canonical ZIP parity, navigation and accessibility behavior remain shared.
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
