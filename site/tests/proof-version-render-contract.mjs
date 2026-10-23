#!/usr/bin/env node
/* Independent DOM-level provenance test: source benchmark and shipping project versions
   must not become aliases, including through the historical adapter or async render order. */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import vm from "node:vm";

const js = await readFile(new URL("../src/assets/proof-renderer.js", import.meta.url), "utf8");

async function runCase({ legacy, research = "0.29.0", researchFormat = 23 }) {
  const marker = { textContent: `v${research}` };
  const receipt = { innerHTML: "" };
  const nodes = new Map([["#frontier-version", marker], ["#evidence-receipt-grid", receipt]]);
  let frames = 0;
  const data = {
    project: { project_version: "0.30.0", format_revision: 24 },
    frontier: {
      project_version: research,
      canonical_format_revision: researchFormat,
      kind: "research-frontier",
      candidate: { status: "research-only" },
      file: "historical-research-record.json",
    },
  };
  if (!legacy) {
    data.public_evidence = {
      schema: "cmpct-public-evidence-v1",
      project_version: "0.30.0",
      canonical_format_revision: 24,
      frontier_status: "research-only",
      provenance: {
        source_project_version: research,
        source_format_revision: researchFormat,
        record: "historical-research-record.json",
      },
      structural: { competitors: [] },
    };
  }
  const context = {
    document: { querySelector: (selector) => nodes.get(selector) || null },
    fetch: async () => ({ ok: true, json: async () => data }),
    requestAnimationFrame: (callback) => {
      frames += 1;
      if (frames > 2) throw new Error("historical frontier version caused render delay");
      callback();
    },
  };
  vm.runInNewContext(js, context, { filename: "proof-renderer.js" });
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(frames, 0, "source-ready DOM must not wait on a different shipping version");
  assert.equal(marker.textContent, `v${research}`, "research label must show source version");
  assert.ok(receipt.innerHTML.includes("v0.30.0"), "receipt must show shipping project version");
  assert.ok(receipt.innerHTML.includes(`v${research} · r${researchFormat}`),
    "receipt must independently expose research source version and format");
}

await runCase({ legacy: false });
await runCase({ legacy: true });
await runCase({ legacy: false, research: "0.31.0", researchFormat: 25 });
console.log("CMPCT source/publication DOM provenance: 3/3 PASS");
