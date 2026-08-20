import {
  BROWSER_WRITER_LIMIT_BYTES,
  SUPPORTED_FORMAT_REVISION,
  buildCmpctFromEntries,
  fileObjectsToEntries,
  inspectCmpctHeader,
} from "./cmpct-browser-writer.js";

const state = { projectData: null, selectedFiles: [], resultUrl: null };
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[char]);
}

function formatBytes(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  if (n < 1024) return `${n.toLocaleString()} B`;
  const units = ["KiB", "MiB", "GiB", "TiB"];
  let v = n / 1024; let i = 0;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i += 1; }
  return `${v.toFixed(v >= 100 ? 0 : v >= 10 ? 1 : 2)} ${units[i]}`;
}

function formatMs(seconds) {
  const n = Number(seconds);
  if (!Number.isFinite(n)) return "—";
  const ms = n * 1000;
  return `${ms.toFixed(ms >= 100 ? 1 : ms >= 10 ? 2 : 3)} ms`;
}

function pct(value, digits = 1) {
  const n = Number(value);
  return Number.isFinite(n) ? `${n.toFixed(digits)}%` : "—";
}

function shortWorkload(name) {
  return String(name || "").replace(/^\d+_/, "").replaceAll("_", " ");
}

async function loadProjectData() {
  const response = await fetch("project-data.json", { cache: "no-store" });
  if (!response.ok) throw new Error(`Unable to load project data (${response.status})`);
  state.projectData = await response.json();
  renderFrontier();
  populateBenchmarks();
  renderReleaseRail();
  configureWriterCompatibility();
}

function renderFrontier() {
  const f = state.projectData?.frontier;
  if (!f) {
    $("#hero-qualification").textContent = "No committed research-frontier benchmark is available.";
    return;
  }

  const competitors = f.competitors || [];
  const zipZstd = competitors.find((x) => x.short === "ZIP / Zstd");
  const zipDeflate = competitors.find((x) => x.short === "ZIP / Deflate");
  const solid = competitors.find((x) => x.short === "tar / Zstd solid");
  $("#hero-gain").textContent = pct(zipZstd?.lead_pct);
  $("#hero-qualification").textContent = `EntropyGraph v${f.project_version} research frontier · ${Number(f.files || 0).toLocaleString()} files · ${f.workload_count || 0} hostile/neutral workloads. Canonical format remains r${state.projectData.project.format_revision}.`;
  $("#frontier-version").textContent = `v${f.project_version || "—"}`;
  $("#frontier-label").textContent = f.candidate?.status || "research benchmark candidate";

  const metrics = [
    ["ZIP / ZSTD", pct(zipZstd?.lead_pct), "verified aggregate lead"],
    ["ZIP / DEFLATE", pct(zipDeflate?.lead_pct), "verified aggregate lead"],
    ["SOLID TAR / ZSTD", pct(solid?.lead_pct), "diagnostic aggregate lead"],
    ["WORKLOAD WINS", `${f.wins_zip_zstd || 0}/${f.workload_count || 0}`, "against ZIP / Zstd"],
  ];
  $("#hero-metrics").innerHTML = metrics.map(([label, value, note]) => `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></article>`).join("");
  $("#arena-logical").textContent = `${formatBytes(f.logical_bytes)} logical input`;

  const max = Math.max(...competitors.map((x) => Number(x.bytes) || 0), 1);
  $("#competitor-ladder").innerHTML = competitors.map((row) => {
    const width = Math.max(2, (Number(row.bytes || 0) / max) * 100);
    const candidate = row.role === "candidate";
    const detail = candidate
      ? `${pct(f.saved_pct)} smaller than logical input`
      : `${pct(row.lead_pct)} CMPCT lead`;
    return `<div class="ladder-row ${candidate ? "candidate" : ""}">
      <div class="ladder-label"><strong>${escapeHtml(row.short)}</strong><small>${escapeHtml(row.name)}</small></div>
      <div class="bar-track"><div class="bar-fill" style="width:${width.toFixed(2)}%"></div></div>
      <div class="ladder-value"><strong>${formatBytes(row.bytes)}</strong><small>${escapeHtml(detail)}</small></div>
    </div>`;
  }).join("");

  const workloads = f.workloads || [];
  $("#workload-score").textContent = `${f.wins_zip_zstd || 0}/${f.workload_count || workloads.length} wins vs ZIP/Zstd`;
  $("#workload-matrix").innerHTML = workloads.map((row) => {
    const delta = Number(row.cmpct_vs_zip93_pct);
    const win = Number.isFinite(delta) && delta >= 0;
    return `<div class="workload-cell ${win ? "win" : "loss"}">
      <span>${escapeHtml(shortWorkload(row.name))}</span>
      <strong>${Number.isFinite(delta) ? `${delta >= 0 ? "−" : "+"}${Math.abs(delta).toFixed(2)}%` : "—"}</strong>
      <small>${win ? "smaller than ZIP/Zstd" : "larger than ZIP/Zstd"}</small>
    </div>`;
  }).join("");

  $("#known-losses").innerHTML = (f.known_losses || []).map((item) => `<div class="loss-item">${escapeHtml(item)}</div>`).join("") || "<div class='loss-item'>No recorded losses in this frontier record.</div>";
}

function metricPair(cmpct, zip, formatter) {
  const c = Number(cmpct); const z = Number(zip);
  const cWin = Number.isFinite(c) && Number.isFinite(z) && c < z;
  const zWin = Number.isFinite(c) && Number.isFinite(z) && z < c;
  return `<div class="metric-pair"><span class="${cWin ? "winner" : ""}"><i>CMPCT</i><b>${formatter(c)}</b></span><span class="${zWin ? "winner" : ""}"><i>ZIP</i><b>${formatter(z)}</b></span></div>`;
}

function renderBenchmark(record) {
  const env = record.environment || {};
  const runner = env.cpu_model || env.uname || "Recorded environment";
  $("#benchmark-headline").innerHTML = [
    ["Project", record.project_version || env.version || "historical"],
    ["Format", `r${record.format_revision ?? "—"}`],
    ["Repetitions", `${record.repetitions ?? "—"}× median`],
    ["Runner", String(runner).replace(/\s+Processor$/i, "").slice(0, 34)],
  ].map(([k, v]) => `<div><span>${escapeHtml(k)}</span><strong title="${escapeHtml(v)}">${escapeHtml(v)}</strong></div>`).join("");

  $("#benchmark-body").innerHTML = Object.entries(record.corpora || {}).map(([name, corpus]) => {
    const lib = corpus.library || {}; const cli = corpus.cli || {};
    return `<tr>
      <td><strong>${escapeHtml(name)}</strong><br><small>${formatBytes(corpus.logical_bytes)} logical</small></td>
      <td>${metricPair(lib.cmpct?.bytes, lib.zip?.bytes, formatBytes)}</td>
      <td>${metricPair(lib.cmpct?.create_s_median, lib.zip?.create_s_median, formatMs)}</td>
      <td>${metricPair(lib.cmpct?.extract_s_median, lib.zip?.extract_s_median, formatMs)}</td>
      <td>${metricPair(cli.cmpct?.create_s_median, cli.zip?.create_s_median, formatMs)}</td>
      <td>${metricPair(cli.cmpct?.extract_s_median, cli.zip?.extract_s_median, formatMs)}</td>
    </tr>`;
  }).join("");

  const note = record.interpretation?.note || "";
  $("#benchmark-notes").innerHTML = [
    record.filesystem_semantic_mismatch ? `<p><strong>Semantic qualification:</strong> ${escapeHtml(record.filesystem_semantic_mismatch)}</p>` : "",
    note ? `<p><strong>Interpretation:</strong> ${escapeHtml(note)}</p>` : "",
    `<p><strong>Record:</strong> <code>${escapeHtml(record.file || "—")}</code>${record.source_commit ? ` · <strong>commit:</strong> <code>${escapeHtml(String(record.source_commit).slice(0, 12))}</code>` : ""}</p>`,
  ].join("");
}

function populateBenchmarks() {
  const records = state.projectData?.parity_records || [];
  const select = $("#benchmark-record");
  if (!records.length) {
    select.innerHTML = '<option value="">No committed parity record</option>';
    return;
  }
  select.innerHTML = records.map((record, index) => {
    const version = record.project_version || record.environment?.version || "historical";
    return `<option value="${index}">${escapeHtml(record.date || "undated")} · v${escapeHtml(version)} · ${escapeHtml(record.repetitions || "?")}×</option>`;
  }).join("");
  select.addEventListener("change", () => renderBenchmark(records[Number(select.value) || 0]));
  renderBenchmark(records[0]);
}

function renderReleaseRail() {
  const rows = state.projectData?.release_history || [];
  $("#release-rail").innerHTML = rows.map((row, index) => `<article class="release-node"><span>${escapeHtml(row.date || "RELEASE")}</span><strong>v${escapeHtml(row.version)}</strong><p>${escapeHtml(row.title.replace(/^CMPCT\s+v?\d+\.\d+\.\d+\s*[—-]?\s*/i, "") || (index === 0 ? "Current project release" : "Versioned milestone"))}</p></article>`).join("");
}

function configureWriterCompatibility() {
  const status = $("#writer-status"); const button = $("#build-archive");
  const revision = Number(state.projectData?.project?.format_revision);
  if (revision === SUPPORTED_FORMAT_REVISION) {
    status.classList.add("ready"); status.classList.remove("blocked");
    status.innerHTML = `<span class="status-dot"></span><div><strong>Portable writer verified for canonical format r${revision}.</strong><small>Regular-file subset only; full filesystem semantics remain CLI territory.</small></div>`;
    button.disabled = state.selectedFiles.length === 0;
  } else {
    status.classList.add("blocked"); status.classList.remove("ready");
    status.innerHTML = `<span class="status-dot"></span><div><strong>Browser writer paused after format revision ${escapeHtml(revision)}.</strong><small>This build is verified for r${SUPPORTED_FORMAT_REVISION}; it refuses to guess a newer grammar.</small></div>`;
    button.disabled = true;
  }
}

function setSelectedFiles(files) {
  state.selectedFiles = Array.from(files || []).filter((file) => file && typeof file.arrayBuffer === "function");
  const total = state.selectedFiles.reduce((sum, file) => sum + Number(file.size || 0), 0);
  $("#selection-summary").innerHTML = !state.selectedFiles.length
    ? "<span>No files selected.</span>"
    : `<span><strong>${state.selectedFiles.length.toLocaleString()} file${state.selectedFiles.length === 1 ? "" : "s"}</strong><br>${formatBytes(total)} input</span><span>${total > BROWSER_WRITER_LIMIT_BYTES ? "Use CLI: over browser limit" : "Ready locally"}</span>`;
  configureWriterCompatibility();
}

function initFilePicker() {
  const fileInput = $("#file-input"); const folderInput = $("#folder-input"); const drop = $("#drop-zone");
  $("#choose-files").addEventListener("click", () => fileInput.click());
  $("#choose-folder").addEventListener("click", () => folderInput.click());
  drop.addEventListener("click", () => fileInput.click());
  drop.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); fileInput.click(); } });
  fileInput.addEventListener("change", () => setSelectedFiles(fileInput.files));
  folderInput.addEventListener("change", () => setSelectedFiles(folderInput.files));
  for (const name of ["dragenter", "dragover"]) drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.add("dragging"); });
  for (const name of ["dragleave", "drop"]) drop.addEventListener(name, (event) => { event.preventDefault(); drop.classList.remove("dragging"); });
  drop.addEventListener("drop", (event) => setSelectedFiles(event.dataTransfer?.files));
}

async function buildArchive() {
  const button = $("#build-archive"); const result = $("#build-result");
  const revision = Number(state.projectData?.project?.format_revision);
  button.disabled = true; button.textContent = "Building locally…"; result.hidden = true;
  try {
    const entries = await fileObjectsToEntries(state.selectedFiles);
    const built = await buildCmpctFromEntries(entries, { formatRevision: revision });
    if (state.resultUrl) URL.revokeObjectURL(state.resultUrl);
    const blob = new Blob([built.bytes], { type: "application/x-cmpct" });
    state.resultUrl = URL.createObjectURL(blob);
    const ratio = built.stats.inputBytes ? built.stats.archiveBytes / built.stats.inputBytes : 0;
    const delta = built.stats.inputBytes - built.stats.archiveBytes;
    const deltaLabel = delta >= 0 ? `${formatBytes(delta)} smaller` : `${formatBytes(Math.abs(delta))} overhead`;
    const version = state.projectData?.project?.project_version || "current";
    result.innerHTML = `<strong>Archive built on this device.</strong><p>${built.stats.logicalFiles.toLocaleString()} logical files → ${built.stats.uniqueBlobs.toLocaleString()} unique blobs · ${built.stats.deflateBlobs.toLocaleString()} Deflate / ${built.stats.rawBlobs.toLocaleString()} RAW.</p><div class="result-mini-grid"><div><span>Input</span><b>${formatBytes(built.stats.inputBytes)}</b></div><div><span>Archive</span><b>${formatBytes(built.stats.archiveBytes)}</b></div><div><span>Delta</span><b>${deltaLabel}${ratio ? ` · ${(ratio * 100).toFixed(1)}%` : ""}</b></div></div><a class="button button-hot" href="${state.resultUrl}" download="archive-v${escapeHtml(version)}.cmpct">Save .cmpct</a>`;
    result.hidden = false;
  } catch (error) {
    result.innerHTML = `<strong>Could not build the archive.</strong><p>${escapeHtml(error?.message || error)}</p>`; result.hidden = false;
  } finally {
    button.textContent = "Build .cmpct"; configureWriterCompatibility();
  }
}

function initInspector() {
  $("#inspect-input").addEventListener("change", async (event) => {
    const file = event.target.files?.[0]; if (!file) return;
    const output = $("#inspect-output");
    try {
      // Footnote: inspect only the fixed header. Full archive parsing belongs to the shared canonical
      // reader rather than growing a second browser parser with divergent security semantics.
      const head = new Uint8Array(await file.slice(0, 68).arrayBuffer());
      const info = inspectCmpctHeader(head); info.fileBytes = file.size;
      if (!info.recognized) throw new Error("The fixed magic does not look like CMPCT.");
      output.innerHTML = `<div><dt>Magic</dt><dd>${escapeHtml(info.magic)}</dd></div><div><dt>Version field</dt><dd>${info.versionField}</dd></div><div><dt>Primary index</dt><dd>${formatBytes(info.primaryIndexCompressedBytes)} → ${formatBytes(info.primaryIndexRawBytes)}</dd></div><div><dt>Data span</dt><dd>${formatBytes(info.dataSpanBytes)}</dd></div><div><dt>Archive size</dt><dd>${formatBytes(info.fileBytes)}</dd></div>`;
    } catch (error) {
      output.innerHTML = `<div><dt>Inspection</dt><dd>${escapeHtml(error?.message || error)}</dd></div>`;
    }
  });
}

function initHeader() {
  const header = $("[data-header]");
  const update = () => header.classList.toggle("scrolled", window.scrollY > 10);
  update(); window.addEventListener("scroll", update, { passive: true });
}

async function init() {
  initHeader(); initFilePicker(); initInspector();
  $("#build-archive").addEventListener("click", buildArchive);
  try { await loadProjectData(); }
  catch (error) {
    $("#hero-qualification").textContent = `Benchmark data unavailable: ${error?.message || error}`;
    const status = $("#writer-status"); status.classList.add("blocked");
    status.innerHTML = `<span class="status-dot"></span><div><strong>Canonical site data did not load.</strong><small>${escapeHtml(error?.message || error)}</small></div>`;
  }
}

init();
