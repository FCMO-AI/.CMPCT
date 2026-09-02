/* Render the committed v0.29 shipping-versus-frontier stored-byte record.
   Only the language-neutral percentage is replaced here; surrounding labels remain under the site's
   curated i18n system instead of being overwritten with English after localization. */
const $ = (selector, root = document) => root.querySelector(selector);

function number(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function render(record) {
  if (record?.schema !== "cmpct-v029-shipping-vs-frontier-v1") return;
  const totals = record.totals || {};
  const shipping = number(totals.shipping_bytes);
  const frontier = number(totals.frontier_bytes);
  const workloads = number(totals.workloads);
  if (shipping === null || frontier === null || workloads !== 15 || shipping <= 0 || frontier <= 0) return;

  const lead = (shipping - frontier) / shipping * 100;
  const cards = document.querySelectorAll(".authority-map article");
  if (cards.length < 3) return;

  const evidenceValue = $("strong", cards[2]);
  if (evidenceValue) evidenceValue.textContent = `${lead >= 0 ? "−" : "+"}${Math.abs(lead).toFixed(2)}%`;

  // Preserve inspectable raw values without introducing non-localized prose into the visible surface.
  cards[2].dataset.shippingBytes = String(Math.trunc(shipping));
  cards[2].dataset.frontierBytes = String(Math.trunc(frontier));
  cards[2].dataset.workloads = String(Math.trunc(workloads));
  cards[2].dataset.frontierWins = String(Math.trunc(number(totals.frontier_wins) ?? 0));
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
