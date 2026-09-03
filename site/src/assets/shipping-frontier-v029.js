/* Render the committed v0.29 shipping-versus-frontier stored-byte record.
   Visible benchmark text is intentionally language-neutral: curated locale labels remain owned by the
   site's i18n system while the measured percentage and byte totals come only from committed evidence. */
const $ = (selector, root = document) => root.querySelector(selector);

function number(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatMiB(bytes) {
  return `${(bytes / (1024 * 1024)).toFixed(2)} MiB`;
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
  const cards = document.querySelectorAll(".authority-map article");
  if (cards.length < 3) return;

  const evidenceValue = $("strong", cards[2]);
  if (evidenceValue) evidenceValue.textContent = `${lead >= 0 ? "−" : "+"}${Math.abs(lead).toFixed(2)}%`;

  const evidenceNote = $("small", cards[2]);
  if (evidenceNote) {
    // Keep the visible receipt compact while splitting it into data-only text nodes. The existing i18n
    // classifier recognizes each measurement/ratio independently, so localized surfaces preserve the
    // exact benchmark values without a special CSS class or a translation-specific exception.
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
