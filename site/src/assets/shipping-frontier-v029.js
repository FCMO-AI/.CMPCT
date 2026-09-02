/* Render the committed v0.29 shipping-versus-frontier stored-byte record. */
const $ = (selector, root = document) => root.querySelector(selector);

function number(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatBytes(value) {
  const bytes = number(value);
  if (bytes === null) return "—";
  if (bytes < 1024) return `${Math.round(bytes).toLocaleString()} B`;
  const units = ["KiB", "MiB", "GiB", "TiB"];
  let scaled = bytes / 1024;
  let index = 0;
  while (scaled >= 1024 && index < units.length - 1) {
    scaled /= 1024;
    index += 1;
  }
  return `${scaled.toFixed(scaled >= 100 ? 0 : scaled >= 10 ? 1 : 2)} ${units[index]}`;
}

function render(record) {
  if (record?.schema !== "cmpct-v029-shipping-vs-frontier-v1") return;
  const totals = record.totals || {};
  const shipping = number(totals.shipping_bytes);
  const frontier = number(totals.frontier_bytes);
  const workloads = number(totals.workloads);
  if (shipping === null || frontier === null || workloads === null || shipping <= 0 || frontier <= 0) return;

  const lead = (shipping - frontier) / shipping * 100;
  const cards = document.querySelectorAll(".authority-map article");
  if (cards.length < 3) return;

  const shippingNote = $("small", cards[0]);
  if (shippingNote) shippingNote.textContent = `${Math.round(workloads)}-workload aggregate · ${formatBytes(shipping)}`;

  const frontierNote = $("small", cards[1]);
  if (frontierNote) frontierNote.textContent = `${Math.round(workloads)}-workload aggregate · ${formatBytes(frontier)}`;

  const evidenceValue = $("strong", cards[2]);
  if (evidenceValue) evidenceValue.textContent = `${lead >= 0 ? "−" : "+"}${Math.abs(lead).toFixed(2)}%`;
  const evidenceNote = $("small", cards[2]);
  if (evidenceNote) evidenceNote.textContent = `frontier vs shipping · same-tree · ${totals.frontier_wins ?? "—"}/${Math.round(workloads)} frontier wins`;
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
    const response = await fetch("assets/shipping-vs-frontier-v029.json", { cache: "no-store" });
    if (!response.ok) return;
    renderAfterProof(await response.json());
  } catch (_) {
    // Additive evidence layer: failure leaves the existing proof surface intact.
  }
}

boot();
