import {
  BROWSER_WRITER_LIMIT_BYTES,
  SUPPORTED_FORMAT_REVISION,
  buildCmpctFromEntries,
  fileObjectsToEntries,
  inspectCmpctHeader,
} from "./cmpct-browser-writer.js";

const state = {
  projectData: null,
  selectedFiles: [],
  resultUrl: null,
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

function formatBytes(value) {
  const n = Number(value || 0);
  if (!Number.isFinite(n)) return "—";
  if (n < 1024) return `${n.toLocaleString()} B`;
  const units = ["KiB", "MiB", "GiB", "TiB"];
  let v = n / 1024;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i += 1; }
  return `${v.toFixed(v >= 100 ? 0 : v >= 10 ? 1 : 2)} ${units[i]}`;
}

function formatMs(seconds) {
  const n = Number(seconds);
  if (!Number.isFinite(n)) return "—";
  const ms = n * 1000;
  return `${ms.toFixed(ms >= 100 ? 1 : ms >= 10 ? 2 : 3)} ms`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[char]);
}

async function loadProjectData() {
  const response = await fetch("project-data.json", { cache: "no-store" });
  if (!response.ok) throw new Error(`Unable to load project data (${response.status})`);
  state.projectData = await response.json();
  configureWriterCompatibility();
  populateBenchmarks();
}

function configureWriterCompatibility() {
  const status = $("#writer-status");
  const button = $("#build-archive");
  const revision = Number(state.projectData?.project?.format_revision);
  if (revision === SUPPORTED_FORMAT_REVISION) {
    status.classList.add("ready");
    status.classList.remove("blocked");
    status.innerHTML = `<span class="status-dot"></span><div><strong>Portable writer is gated for format revision ${revision}.</strong><small>Regular-file subset only; full filesystem semantics remain CLI territory.</small></div>`;
    button.disabled = state.selectedFiles.length === 0;
  } else {
    status.classList.add("blocked");
    status.classList.remove("ready");
    status.innerHTML = `<span class="status-dot"></span><div><strong>Browser conversion paused: repository moved to revision ${escapeHtml(revision)}.</strong><small>This writer is verified for revision ${SUPPORTED_FORMAT_REVISION} and will not guess a newer on-disk contract.</small></div>`;
    button.disabled = true;
  }
}

function setSelectedFiles(files) {
  state.selectedFiles = Array.from(files || []).filter((file) => file && typeof file.arrayBuffer === "function");
  const total = state.selectedFiles.reduce((sum, file) => sum + Number(file.size || 0), 0);
  const summary = $("#selection-summary");
  if (!state.selectedFiles.length) {
    summary.innerHTML = "<span>No files selected.</span>";
  } else {
    summary.innerHTML = `<span><strong>${state.selectedFiles.length.toLocaleString()} file${state.selectedFiles.length === 1 ? "" : "s"}</strong><br>${formatBytes(total)} input</span><span>${total > BROWSER_WRITER_LIMIT_BYTES ? "Use CLI: over browser limit" : "Ready locally"}</span>`;
  }
  configureWriterCompatibility();
}

function initFilePicker() {
  const fileInput = $("#file-input");
  const folderInput = $("#folder-input");
  const dropZone = $("#drop-zone");
  $("#choose-files").addEventListener("click", () => fileInput.click());
  $("#choose-folder").addEventListener("click", () => folderInput.click());
  dropZone.addEventListener("click", () => fileInput.click());
  dropZone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); fileInput.click(); }
  });
  fileInput.addEventListener("change", () => setSelectedFiles(fileInput.files));
  folderInput.addEventListener("change", () => setSelectedFiles(folderInput.files));

  for (const name of ["dragenter", "dragover"]) {
    dropZone.addEventListener(name, (event) => { event.preventDefault(); dropZone.classList.add("dragging"); });
  }
  for (const name of ["dragleave", "drop"]) {
    dropZone.addEventListener(name, (event) => { event.preventDefault(); dropZone.classList.remove("dragging"); });
  }
  dropZone.addEventListener("drop", (event) => setSelectedFiles(event.dataTransfer?.files));
}

async function buildArchive() {
  const button = $("#build-archive");
  const result = $("#build-result");
  const revision = Number(state.projectData?.project?.format_revision);
  button.disabled = true;
  button.textContent = "Building locally…";
  result.hidden = true;

  try {
    const entries = await fileObjectsToEntries(state.selectedFiles);
    const built = await buildCmpctFromEntries(entries, { formatRevision: revision });
    if (state.resultUrl) URL.revokeObjectURL(state.resultUrl);
    const blob = new Blob([built.bytes], { type: "application/vnd.fcmo.cmpct" });
    state.resultUrl = URL.createObjectURL(blob);
    const ratio = built.stats.inputBytes ? built.stats.archiveBytes / built.stats.inputBytes : 0;
    const delta = built.stats.inputBytes - built.stats.archiveBytes;
    const deltaLabel = delta >= 0 ? `${formatBytes(delta)} smaller` : `${formatBytes(Math.abs(delta))} overhead`;
    const projectVersion = state.projectData?.project?.project_version || "current";
    result.innerHTML = `
      <strong>Archive built on this device.</strong>
      <p>${built.stats.logicalFiles.toLocaleString()} logical files → ${built.stats.uniqueBlobs.toLocaleString()} unique blobs · ${built.stats.deflateBlobs.toLocaleString()} Deflate / ${built.stats.rawBlobs.toLocaleString()} RAW.</p>
      <div class="result-mini-grid">
        <div><span>Input</span><b>${formatBytes(built.stats.inputBytes)}</b></div>
        <div><span>Archive</span><b>${formatBytes(built.stats.archiveBytes)}</b></div>
        <div><span>Delta</span><b>${deltaLabel}${ratio ? ` · ${(ratio * 100).toFixed(1)}%` : ""}</b></div>
      </div>
      <a class="button button-primary" href="${state.resultUrl}" download="archive-v${escapeHtml(projectVersion)}.cmpct"><span aria-hidden="true">^</span> Save .cmpct</a>`;
    result.hidden = false;
  } catch (error) {
    result.innerHTML = `<strong>Could not build the archive.</strong><p>${escapeHtml(error?.message || error)}</p>`;
    result.hidden = false;
  } finally {
    button.innerHTML = '<span aria-hidden="true">^</span> Build .cmpct';
    configureWriterCompatibility();
  }
}

function initInspector() {
  const input = $("#inspect-input");
  const output = $("#inspect-output");
  input.addEventListener("change", async () => {
    const file = input.files?.[0];
    if (!file) return;
    try {
      // The fixed header is 68 bytes. Reading only that slice keeps even multi-gigabyte archives local
      // and cheap; full structural validation belongs to `cmpct preflight` and the native core.
      const head = new Uint8Array(await file.slice(0, 68).arrayBuffer());
      const info = inspectCmpctHeader(head);
      info.fileBytes = file.size;
      output.innerHTML = `
        <div><dt>Magic</dt><dd>${escapeHtml(info.magic)}</dd></div>
        <div><dt>Version field</dt><dd>${info.versionField}</dd></div>
        <div><dt>Primary index</dt><dd>${formatBytes(info.primaryIndexCompressedBytes)} → ${formatBytes(info.primaryIndexRawBytes)}</dd></div>
        <div><dt>Data span</dt><dd>${formatBytes(info.dataSpanBytes)}</dd></div>
        <div><dt>Archive size</dt><dd>${formatBytes(info.fileBytes)}</dd></div>`;
      if (!info.recognized) throw new Error("The fixed magic does not look like CMPCT.");
    } catch (error) {
      output.innerHTML = `<div><dt>Inspection</dt><dd>${escapeHtml(error?.message || error)}</dd></div>`;
    }
  });
}

function metricPair(cmpct, zip, formatter) {
  const c = Number(cmpct);
  const z = Number(zip);
  const cmpctWin = Number.isFinite(c) && Number.isFinite(z) && c < z;
  const zipWin = Number.isFinite(c) && Number.isFinite(z) && z < c;
  return `<div class="metric-pair"><span class="${cmpctWin ? "winner" : ""}"><i>CMPCT</i><b>${formatter(c)}</b></span><span class="${zipWin ? "winner" : ""}"><i>ZIP</i><b>${formatter(z)}</b></span></div>`;
}

function renderBenchmark(record) {
  const headline = $("#benchmark-headline");
  const env = record.environment || {};
  const runner = env.cpu_model || env.uname || "Recorded environment";
  headline.innerHTML = `
    <div><span>Format</span><strong>r${escapeHtml(record.format_revision ?? "—")}</strong></div>
    <div><span>Repetitions</span><strong>${escapeHtml(record.repetitions ?? "—")}</strong></div>
    <div><span>Statistic</span><strong>${escapeHtml(record.timing_statistic ?? "—")}</strong></div>
    <div><span>Runner</span><strong title="${escapeHtml(runner)}">${escapeHtml(String(runner).replace(/\s+Processor$/i, "").slice(0, 32))}</strong></div>`;

  const body = $("#benchmark-body");
  body.innerHTML = Object.entries(record.corpora || {}).map(([name, corpus]) => {
    const lib = corpus.library || {};
    const cli = corpus.cli || {};
    return `<tr>
      <td><strong>${escapeHtml(name)}</strong><br><small>${formatBytes(corpus.logical_bytes)} logical</small></td>
      <td>${metricPair(lib.cmpct?.bytes, lib.zip?.bytes, formatBytes)}</td>
      <td>${metricPair(lib.cmpct?.create_s_median, lib.zip?.create_s_median, formatMs)}</td>
      <td>${metricPair(lib.cmpct?.extract_s_median, lib.zip?.extract_s_median, formatMs)}</td>
      <td>${metricPair(cli.cmpct?.create_s_median, cli.zip?.create_s_median, formatMs)}</td>
      <td>${metricPair(cli.cmpct?.extract_s_median, cli.zip?.extract_s_median, formatMs)}</td>
    </tr>`;
  }).join("");

  const notes = $("#benchmark-notes");
  const interpretation = record.interpretation || {};
  const noteText = typeof interpretation.note === "string" ? interpretation.note : "";
  notes.innerHTML = [
    record.filesystem_semantic_mismatch ? `<p><strong>Semantic qualification:</strong> ${escapeHtml(record.filesystem_semantic_mismatch)}</p>` : "",
    noteText ? `<p><strong>Record interpretation:</strong> ${escapeHtml(noteText)}</p>` : "",
    record.source_commit ? `<p><strong>Source commit:</strong> <code>${escapeHtml(String(record.source_commit).slice(0, 12))}</code> · <strong>Harness:</strong> <code>${escapeHtml(record.harness || "—")}</code> · <strong>Record:</strong> <code>${escapeHtml(record.file)}</code></p>` : "",
  ].join("");
}

function populateBenchmarks() {
  const records = state.projectData?.benchmark_records || [];
  const select = $("#benchmark-record");
  if (!records.length) {
    select.innerHTML = '<option value="">No durable parity record found</option>';
    return;
  }
  select.innerHTML = records.map((record, index) => `<option value="${index}">${escapeHtml(record.date)} · ${escapeHtml(record.file.replace(/^\d{4}-\d{2}-\d{2}-/, ""))} · ${escapeHtml(record.repetitions)}×</option>`).join("");
  select.addEventListener("change", () => renderBenchmark(records[Number(select.value) || 0]));
  renderBenchmark(records[0]);
}

function initCopyActions() {
  $$("[data-copy-target]").forEach((button) => {
    button.addEventListener("click", async () => {
      const target = document.getElementById(button.dataset.copyTarget);
      await navigator.clipboard.writeText(target?.innerText || "");
      const before = button.textContent;
      button.textContent = "Copied";
      setTimeout(() => { button.textContent = before; }, 1200);
    });
  });

  const agentButton = $("[data-copy-agent]");
  agentButton?.addEventListener("click", async () => {
    const version = state.projectData?.project?.project_version || "current";
    const revision = state.projectData?.project?.format_revision || "current";
    const prompt = `You are entering the canonical FCMO-AI/.CMPCT repository at project v${version}, format revision ${revision}. Read README.md, AGENTS.md, docs/CURRENT_STATE.md, docs/HARDENING.md, docs/PORTABILITY.md, docs/NATIVE_CORE.md, docs/FORMAT.md, docs/HISTORY.md, docs/RESEARCH_LOG.md, docs/BENCHMARKS.md, and docs/ROADMAP.md before changing format or encoder policy. Treat committed repository evidence as authoritative; preserve losing benchmarks and code design footnotes; do not infer project-critical facts from chat history.`;
    await navigator.clipboard.writeText(prompt);
    const before = agentButton.textContent;
    agentButton.textContent = "Bootstrap prompt copied";
    setTimeout(() => { agentButton.textContent = before; }, 1400);
  });
}

function initHeader() {
  const header = $("[data-header]");
  const update = () => header.classList.toggle("scrolled", window.scrollY > 12);
  update();
  window.addEventListener("scroll", update, { passive: true });
}

async function init() {
  initHeader();
  initFilePicker();
  initInspector();
  initCopyActions();
  $("#build-archive").addEventListener("click", buildArchive);
  try {
    await loadProjectData();
  } catch (error) {
    const status = $("#writer-status");
    status.classList.add("blocked");
    status.innerHTML = `<span class="status-dot"></span><div><strong>Canonical site data did not load.</strong><small>${escapeHtml(error?.message || error)}</small></div>`;
  }
}

init();
