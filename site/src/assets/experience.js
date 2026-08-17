/* CMPCT Public Proof Surface renderer.
   Footnote: this renderer consumes a stable evidence contract instead of release-specific DOM patches.
   Historical adapters may change upstream, but presentation vocabulary stays anchored to measured claim,
   comparator, scope, provenance and authority. */
const $ = (selector, root = document) => root.querySelector(selector);

function esc(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[char]);
}

function num(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function pct(value, digits = 1) {
  const n = num(value);
  return n === null ? "—" : `${Math.abs(n).toFixed(digits)}%`;
}

function signedStorage(value, digits = 2) {
  const n = num(value);
  if (n === null) return "—";
  if (Math.abs(n) < 1e-12) return `0.${"0".repeat(digits)}%`;
  // Footnote: positive lead means CMPCT stores fewer bytes, therefore the archive-size delta is negative.
  return `${n > 0 ? "−" : "+"}${Math.abs(n).toFixed(digits)}%`;
}

function relation(value, comparator) {
  const n = num(value);
  if (n === null) return `vs ${comparator}`;
  if (Math.abs(n) < 1e-12) return `same stored bytes as ${comparator}`;
  return `${Math.abs(n).toFixed(Math.abs(n) < 1 ? 2 : 1)}% ${n > 0 ? "smaller" : "larger"} than ${comparator}`;
}

function formatBytes(value) {
  const n = num(value);
  if (n === null) return "—";
  if (n < 1024) return `${Math.round(n).toLocaleString()} B`;
  const units = ["KiB", "MiB", "GiB", "TiB"];
  let v = n / 1024;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i += 1; }
  return `${v.toFixed(v >= 100 ? 0 : v >= 10 ? 1 : 2)} ${units[i]}`;
}

function shortWorkload(name) {
  return String(name || "").replace(/^\d+_/, "").replaceAll("_", " ");
}

function byShort(rows, short) {
  return (rows || []).find((row) => row.short === short) || null;
}

function normalizeLegacy(data) {
  const f = data?.frontier || {};
  const overall = f.overall_comparison || {};
  const category = f.category_comparison || {};
  const competitors = overall.competitors || f.competitors || [];
  const seriousShort = overall.serious_comparator_short || "tar / Zstd solid";
  return {
    schema: "cmpct-public-evidence-v1",
    project_version: f.project_version || data?.project?.project_version,
    canonical_format_revision: f.canonical_format_revision ?? data?.project?.format_revision,
    frontier_status: f.candidate?.status || "research frontier",
    frontier_name: f.candidate?.name || "CMPCT research frontier",
    structural: {
      candidate_bytes: overall.candidate_bytes ?? f.archive_bytes,
      logical_bytes: overall.logical_bytes ?? f.logical_bytes,
      files: overall.files ?? f.files,
      competitors,
      headline_comparator_short: overall.headline_comparator_short || "ZIP / Deflate",
      serious_comparator_short: seriousShort,
      method: overall.method || f.structural_competitor_contract || {},
    },
    category: {
      baseline_short: category.baseline_short || seriousShort,
      workloads: category.workloads || f.workload_count || 0,
      wins: category.wins_vs_zstd,
      losses: category.losses_vs_zstd,
      ties: category.ties_vs_zstd,
      lead_pct: category.lead_vs_zstd_pct,
      rows: category.rows || [],
      contract: category.contract || {},
    },
    scheduler: f.scheduler || {},
    release_delta: f.release_delta || {},
    known_losses: f.known_losses || [],
    provenance: {
      record: f.file || "—",
      date: f.date || "—",
      tree_sha256: overall.method?.tree_sha256 || f.structural_competitor_contract?.tree_sha256 || null,
      method: overall.method || {},
      contract: f.contract || {},
    },
  };
}

function evidenceFrom(data) {
  return data?.public_evidence?.schema === "cmpct-public-evidence-v1"
    ? data.public_evidence
    : normalizeLegacy(data);
}

function renderHero(e) {
  const competitors = e.structural?.competitors || [];
  const headlineShort = e.structural?.headline_comparator_short || "ZIP / Deflate";
  const headline = byShort(competitors, headlineShort) || byShort(competitors, "ZIP / Deflate") || {};
  const lead = num(headline.lead_pct);
  const heroGain = $("#hero-gain");
  if (heroGain) heroGain.textContent = lead === null ? "—" : pct(lead, 1);

  const unit = $(".score-unit");
  if (unit) unit.textContent = lead !== null && lead < 0 ? `larger than ${headline.short || headlineShort}` : `smaller than ${headline.short || headlineShort}`;

  const translation = $("#hero-translation");
  if (translation && lead !== null) {
    const normalized = 100 * (1 - lead / 100);
    translation.textContent = lead >= 0
      ? `If ${headline.short || headlineShort} stores 100 MB on this matched test, CMPCT needs about ${normalized.toFixed(1)} MB.`
      : `CMPCT currently needs about ${normalized.toFixed(1)} MB for every 100 MB stored by ${headline.short || headlineShort} on this matched test.`;
  }

  const serious = byShort(competitors, e.structural?.serious_comparator_short || "tar / Zstd solid");
  const files = Number(e.structural?.files || 0).toLocaleString();
  const speed = num(e.scheduler?.wallclock_improvement_pct);
  const qualification = $("#hero-qualification");
  if (qualification) {
    const seriousText = serious ? ` Serious size baseline: ${relation(serious.lead_pct, serious.short)}.` : "";
    const speedText = speed === null ? "" : ` Scoped scheduler result: ${speed.toFixed(1)}% lower wall time on its fixed gate.`;
    qualification.textContent = `${e.frontier_name || "CMPCT research frontier"} · ${files} files on the matched structural tree.${seriousText}${speedText} Canonical format remains r${e.canonical_format_revision ?? "—"}.`;
  }
}

function metricCard(label, value, note, state = "context") {
  return `<article class="${esc(state)}"><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></article>`;
}

function renderMetricWall(e) {
  const rows = e.structural?.competitors || [];
  const zip = byShort(rows, "ZIP / Deflate") || byShort(rows, e.structural?.headline_comparator_short);
  const seven = byShort(rows, "7z / LZMA2");
  const serious = byShort(rows, e.structural?.serious_comparator_short || "tar / Zstd solid");
  const speed = num(e.scheduler?.wallclock_improvement_pct);
  const cards = [];

  for (const [label, row] of [["ZIP / DEFLATE", zip], ["7Z / LZMA2", seven], ["SOLID ZSTD-19", serious]]) {
    const lead = num(row?.lead_pct);
    const state = lead === null ? "context" : lead > 0 ? "win" : lead < 0 ? "loss" : "context";
    const note = lead === null ? "matched stored bytes unavailable" : lead > 0 ? "CMPCT smaller · matched stored bytes" : lead < 0 ? "CMPCT larger · matched stored bytes" : "same stored bytes";
    cards.push(metricCard(label, signedStorage(lead), note, state));
  }
  cards.push(metricCard("CREATE WALL TIME", speed === null ? "—" : `−${speed.toFixed(1)}%`, "fixed hostile scheduler gate · not a global speed claim", speed !== null && speed > 0 ? "win" : "context"));
  const wall = $("#hero-metrics");
  if (wall) wall.innerHTML = cards.join("");
}

function renderArena(e) {
  const rows = e.structural?.competitors || [];
  const candidateBytes = num(e.structural?.candidate_bytes);
  const max = Math.max(...rows.map((r) => Number(r.bytes) || 0), 1);
  const logical = $("#arena-logical");
  if (logical) logical.textContent = `${formatBytes(e.structural?.logical_bytes)} logical input · ${Number(e.structural?.files || 0).toLocaleString()} files`;

  const ladder = $("#competitor-ladder");
  if (ladder) {
    ladder.innerHTML = [...rows].sort((a, b) => Number(a.bytes || 0) - Number(b.bytes || 0)).map((row) => {
      const isCandidate = row.role === "candidate";
      const lead = isCandidate ? null : num(row.lead_pct);
      const state = isCandidate ? "candidate" : lead !== null && lead > 0 ? "win" : lead !== null && lead < 0 ? "loss" : "";
      const width = Math.max(2, Number(row.bytes || 0) / max * 100);
      const detail = isCandidate
        ? "current CMPCT research frontier"
        : relation(lead, row.short || row.name || "competitor");
      return `<div class="ladder-row ${state}">
        <div class="ladder-label"><strong>${esc(row.short || row.name)}</strong><small>${esc(row.name || row.short)}</small></div>
        <div class="bar-track"><div class="bar-fill" style="width:${width.toFixed(2)}%"></div></div>
        <div class="ladder-value"><strong>${esc(formatBytes(row.bytes))}</strong><small>${esc(detail)}</small></div>
      </div>`;
    }).join("");
  }

  // Footnote: candidateBytes is read even though row bytes currently carry the same value. Keeping the
  // explicit field makes it possible for validation to reject a malformed contract rather than trusting
  // whichever candidate-looking row happened to be rendered.
  void candidateBytes;
}

function renderCategory(e) {
  const rows = e.category?.rows || [];
  const score = $("#workload-score");
  if (score) {
    score.textContent = rows.length
      ? `${e.category?.wins ?? "—"}/${e.category?.workloads ?? rows.length} smaller · ${e.category?.losses ?? "—"} larger`
      : "category evidence unavailable";
  }
  const matrix = $("#workload-matrix");
  if (!matrix) return;
  if (!rows.length) {
    matrix.innerHTML = '<div class="loss-item">Fresh exact-tree category evidence is not available for this frontier.</div>';
    return;
  }
  matrix.innerHTML = rows.map((row) => {
    const lead = num(row.cmpct_vs_zstd_pct ?? row.lead_pct);
    const state = lead === null ? "" : lead > 1e-12 ? "win" : lead < -1e-12 ? "loss" : "";
    const note = lead === null ? "comparison unavailable" : relation(lead, e.category?.baseline_short || "solid Zstd");
    return `<div class="workload-cell ${state}"><span>${esc(shortWorkload(row.name))}</span><strong>${esc(signedStorage(lead))}</strong><small>${esc(note)}</small></div>`;
  }).join("");
}

function renderLosses(e) {
  const target = $("#known-losses");
  if (!target) return;
  const losses = e.known_losses || [];
  target.innerHTML = losses.length
    ? losses.map((item) => `<div class="loss-item">${esc(item)}</div>`).join("")
    : '<div class="loss-item">No benchmark qualification is recorded for this public frontier.</div>';
}

function renderAuthority(e) {
  const version = $("#frontier-version");
  if (version) version.textContent = `v${e.project_version || "—"}`;
  const label = $("#frontier-label");
  if (label) label.textContent = e.frontier_status || "research frontier";
}

function shortenHash(value) {
  const s = String(value || "");
  return s.length > 16 ? `${s.slice(0, 12)}…${s.slice(-6)}` : s || "—";
}

function renderReceipt(e) {
  const grid = $("#evidence-receipt-grid");
  if (!grid) return;
  const method = e.structural?.method || e.provenance?.method || {};
  const tree = e.provenance?.tree_sha256 || method.tree_sha256 || "—";
  const contract = e.provenance?.contract || {};
  const contractLabel = contract.structural_aggregate || contract.portable_frontier || "matched committed benchmark";
  const cells = [
    ["Project", `v${e.project_version || "—"}`],
    ["Format", `r${e.canonical_format_revision ?? "—"}`],
    ["Tree", shortenHash(tree)],
    ["Files", Number(e.structural?.files || 0).toLocaleString()],
    ["Record", e.provenance?.record || "—"],
    ["Contract", contractLabel],
  ];
  grid.innerHTML = cells.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd title="${esc(v)}">${esc(v)}</dd></div>`).join("");
}

function render(e) {
  renderHero(e);
  renderMetricWall(e);
  renderArena(e);
  renderCategory(e);
  renderLosses(e);
  renderAuthority(e);
  renderReceipt(e);
}

async function boot() {
  try {
    const response = await fetch("project-data.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`Unable to load project data (${response.status})`);
    const data = await response.json();
    const evidence = evidenceFrom(data);
    render(evidence);
  } catch (error) {
    // Footnote: app.js owns Browser Lab compatibility and the generic site-data error state. This layer
    // fails soft so a presentation enhancement can never disable the archive tool or canonical reader UI.
    const qualification = $("#hero-qualification");
    if (qualification && qualification.textContent.includes("Loading")) {
      qualification.textContent = `Public evidence unavailable: ${error?.message || error}`;
    }
  }
}

boot();
