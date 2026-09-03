/* Render the committed v0.29 shipping-versus-frontier stored-byte record.
   Visible benchmark text reuses the site's already-curated i18n vocabulary and translation patterns while
   measured percentages and byte totals come only from committed evidence. */
const $ = (selector, root = document) => root.querySelector(selector);

function number(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatMiB(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(2)} MiB`;
}

function kpi(label, value, note) {
  const cell = document.createElement("div");
  const labelNode = document.createElement("span");
  const valueNode = document.createElement("strong");
  const noteNode = document.createElement("small");
  labelNode.textContent = label;
  valueNode.textContent = value;
  noteNode.textContent = note;
  cell.append(labelNode, valueNode, noteNode);
  return cell;
}

function matchesCurrentRelease(record, projectData) {
  const project = projectData?.project || {};
  const evidence = projectData?.public_evidence || {};
  const recordVersion = String(record?.project_version || "");
  const shippingRevision = number(record?.shipping?.format_revision);
  const projectRevision = number(project?.format_revision);
  const evidenceRevision = number(evidence?.canonical_format_revision);

  return Boolean(
    recordVersion &&
    shippingRevision !== null &&
    project?.project_version === recordVersion &&
    projectRevision === shippingRevision &&
    evidence?.schema === "cmpct-public-evidence-v1" &&
    evidence?.project_version === recordVersion &&
    evidenceRevision === shippingRevision
  );
}

function ensureZipSectionPanel() {
  const parity = $(".parity-section");
  const anchor = parity ? $("#benchmark-headline", parity) : null;
  if (!parity || !anchor) return null;

  let panel = $("#shipping-frontier-zip-panel", parity);
  if (!panel) {
    panel = document.createElement("article");
    panel.id = "shipping-frontier-zip-panel";
    panel.className = "shipping-frontier-zip-panel";
    panel.setAttribute("aria-label", "PUBLIC EVIDENCE");

    const note = document.createElement("div");
    note.className = "benchmark-notes";
    const heading = document.createElement("div");
    const shippingHeading = document.createElement("strong");
    const frontierHeading = document.createElement("strong");
    shippingHeading.textContent = "SHIPPING / CANONICAL";
    frontierHeading.textContent = "RESEARCH FRONTIER";
    heading.append(shippingHeading, document.createTextNode(" ↔ "), frontierHeading);

    const qualification = document.createElement("p");
    const shippingMeaning = document.createElement("span");
    const frontierMeaning = document.createElement("span");
    shippingMeaning.textContent = "reader / writer contract";
    frontierMeaning.textContent = "benchmark candidate";
    qualification.append(shippingMeaning, document.createTextNode(" ↔ "), frontierMeaning);
    note.append(heading, qualification);

    const grid = document.createElement("div");
    grid.className = "parity-kpis";
    grid.id = "shipping-frontier-zip-kpis";
    grid.setAttribute("aria-live", "polite");

    const raw = document.createElement("div");
    raw.className = "benchmark-notes";
    const rawLink = document.createElement("a");
    rawLink.href = "assets/shipping-vs-frontier-v029.json";
    rawLink.textContent = "shipping-vs-frontier-v029.json";
    raw.append(rawLink);

    panel.append(note, grid, raw);
    anchor.before(panel);
  }
  return $("#shipping-frontier-zip-kpis", panel);
}

function render(record) {
  if (record?.schema !== "cmpct-v029-shipping-vs-frontier-v1") return;
  const totals = record.totals || {};
  const shipping = number(totals.shipping_bytes);
  const frontier = number(totals.frontier_bytes);
  const workloads = number(totals.workloads);
  const frontierWins = number(totals.frontier_wins);
  if (
    shipping === null || frontier === null || workloads !== 15 || frontierWins === null ||
    shipping <= 0 || frontier <= 0
  ) return;

  const lead = (shipping - frontier) / shipping * 100;
  const saved = shipping - frontier;

  const cards = document.querySelectorAll(".authority-map article");
  if (cards.length >= 3) {
    const evidenceValue = $("strong", cards[2]);
    if (evidenceValue) evidenceValue.textContent = `${lead >= 0 ? "−" : "+"}${Math.abs(lead).toFixed(2)}%`;

    const evidenceNote = $("small", cards[2]);
    if (evidenceNote) {
      // Keep the visible receipt compact while splitting it into data-only text nodes. The existing i18n
      // classifier recognizes each measurement/ratio independently, so localized surfaces preserve the
      // exact benchmark values without a translation-specific exception.
      evidenceNote.replaceChildren(
        document.createTextNode(formatMiB(shipping)),
        document.createTextNode(" → "),
        document.createTextNode(formatMiB(frontier)),
        document.createTextNode(" · "),
        document.createTextNode(`${Math.trunc(frontierWins)}/${Math.trunc(workloads)}`),
      );
    }

    cards[2].dataset.shippingBytes = String(Math.trunc(shipping));
    cards[2].dataset.frontierBytes = String(Math.trunc(frontier));
    cards[2].dataset.workloads = String(Math.trunc(workloads));
    cards[2].dataset.frontierWins = String(Math.trunc(frontierWins));
  }

  // The ZIP/parity chapter is where readers already go to compare shipping CMPCT with the familiar ZIP
  // baseline. Keep the same-tree Shipping-vs-Frontier result visible there as explicit context rather than
  // forcing readers to infer it from the separate authority band above.
  const zipGrid = ensureZipSectionPanel();
  if (zipGrid) {
    zipGrid.replaceChildren(
      kpi("SHIPPING / CANONICAL", formatMiB(shipping), "reader / writer contract"),
      kpi("RESEARCH FRONTIER", formatMiB(frontier), "benchmark candidate"),
      kpi("PUBLIC EVIDENCE", `${lead >= 0 ? "−" : "+"}${Math.abs(lead).toFixed(2)}%`, `${formatMiB(Math.abs(saved))} smaller`),
      kpi("RESEARCH FRONTIER", `${Math.trunc(frontierWins)}/${Math.trunc(workloads)}`, `${Math.trunc(frontierWins)}/${Math.trunc(workloads)} wins vs r24`),
    );
    zipGrid.dataset.shippingBytes = String(Math.trunc(shipping));
    zipGrid.dataset.frontierBytes = String(Math.trunc(frontier));
    zipGrid.dataset.workloads = String(Math.trunc(workloads));
    zipGrid.dataset.frontierWins = String(Math.trunc(frontierWins));
  }
}

function renderAfterProof(record, attempt = 0) {
  const expected = String(record.project_version || "");
  const ready = expected && $("#frontier-version")?.textContent?.includes(expected);
  if (ready || attempt >= 180) {
    requestAnimationFrame(() => render(record));
    return;
  }
  requestAnimationFrame(() => renderAfterProof(record, attempt + 1));
}

async function boot() {
  try {
    const [recordResponse, projectResponse] = await Promise.all([
      fetch("assets/shipping-vs-frontier-v029.json", { cache: "no-store" }),
      fetch("project-data.json", { cache: "no-store" }),
    ]);
    if (!recordResponse.ok || !projectResponse.ok) return;
    const [record, projectData] = await Promise.all([recordResponse.json(), projectResponse.json()]);

    // A release-specific evidence mirror is safe only on the release it actually measured. The stable
    // project-data public_evidence contract is the release authority: future project/format revisions suppress
    // this v0.29 panel instead of inheriting a stale headline above a newer canonical ZIP table.
    if (!matchesCurrentRelease(record, projectData)) return;
    renderAfterProof(record);
  } catch (_) {
    // Additive evidence layer: failure leaves the existing proof surface intact.
  }
}

boot();
