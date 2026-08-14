import { writeFile } from "node:fs/promises";
import { buildCmpctFromEntries, inspectCmpctHeader } from "../src/assets/cmpct-browser-writer.js";

const repeated = new TextEncoder().encode("CMPCT browser writer smoke test. ".repeat(300));
const duplicate = new Uint8Array(repeated);
const unique = new TextEncoder().encode("small independent file\n");

const built = await buildCmpctFromEntries([
  { path: "docs/repeated.txt", bytes: repeated, lastModified: 1_700_000_000_000 },
  { path: "copy/repeated.txt", bytes: duplicate, lastModified: 1_700_000_000_001 },
  { path: "unique.txt", bytes: unique, lastModified: 1_700_000_000_002 },
], { formatRevision: 24 });

if (built.stats.logicalFiles !== 3) throw new Error("logical file count drift");
if (built.stats.uniqueBlobs !== 2) throw new Error("deduplication did not collapse duplicate content");
if (built.stats.deflateBlobs < 1) throw new Error("expected at least one compressible Deflate blob");
const header = inspectCmpctHeader(built.bytes);
if (!header.recognized || header.versionField !== 24) throw new Error("header inspection mismatch");

await writeFile(process.argv[2] || "browser-writer-smoke.cmpct", built.bytes);
console.log(JSON.stringify(built.stats));
