/*
 * CMPCT portable browser writer — revision 24, regular files only.
 *
 * Footnote: this is deliberately a small writer, not a second CMPCT reader/engine. The canonical
 * parser remains the Python/Rust implementation in the repository. The browser writer emits a
 * conservative subset (direct RAW or raw-DEFLATE blobs + dual indexes) that CI verifies with the
 * canonical reader. When the repository format revision moves past 24, the UI refuses conversion
 * until this module is consciously updated and re-gated instead of guessing new on-disk semantics.
 */

export const SUPPORTED_FORMAT_REVISION = 24;
export const BROWSER_WRITER_LIMIT_BYTES = 256 * 1024 * 1024;

const textEncoder = new TextEncoder();
const MAGIC = textEncoder.encode("CMPCT24\0");
const FOOTER_MAGIC = textEncoder.encode("CMPTF24\0");
const BLOB_MAGIC = textEncoder.encode("CMA4");
const CODEC_RAW = 0;
const CODEC_DEFLATE = 4;
const K_FILE = 0;
const S_BLOB = 0;

function concatBytes(parts) {
  const size = parts.reduce((sum, part) => sum + part.length, 0);
  const out = new Uint8Array(size);
  let offset = 0;
  for (const part of parts) {
    out.set(part, offset);
    offset += part.length;
  }
  return out;
}

function u16le(value) {
  const out = new Uint8Array(2);
  new DataView(out.buffer).setUint16(0, Number(value), true);
  return out;
}

function u32le(value) {
  const out = new Uint8Array(4);
  new DataView(out.buffer).setUint32(0, Number(value) >>> 0, true);
  return out;
}

function u64le(value) {
  const out = new Uint8Array(8);
  new DataView(out.buffer).setBigUint64(0, BigInt(value), true);
  return out;
}

function hex(bytes) {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function sha256(bytes) {
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return new Uint8Array(digest);
}

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) crc = CRC_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function normalizeLogicalPath(input) {
  const path = String(input || "").replaceAll("\\", "/");
  if (!path || path.startsWith("/") || path.includes("\0")) throw new Error(`Unsafe CMPCT path: ${input}`);
  const parts = path.split("/");
  if (parts.some((part) => !part || part === "." || part === "..")) throw new Error(`Unsafe CMPCT path: ${input}`);
  return parts.join("/");
}

async function deflateRaw(bytes) {
  if (typeof CompressionStream === "undefined") return null;
  try {
    const stream = new Blob([bytes]).stream().pipeThrough(new CompressionStream("deflate-raw"));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  } catch {
    // Unsupported browsers still produce a correct archive by storing the exact bytes RAW.
    return null;
  }
}

/* Minimal MessagePack encoder for the exact value classes used by revision-24 indexes. */
function msgpack(value) {
  if (value === null || value === undefined) return Uint8Array.of(0xc0);
  if (value instanceof Uint8Array) {
    const n = value.length;
    if (n <= 0xff) return concatBytes([Uint8Array.of(0xc4, n), value]);
    if (n <= 0xffff) return concatBytes([Uint8Array.of(0xc5), be16(n), value]);
    return concatBytes([Uint8Array.of(0xc6), be32(n), value]);
  }
  if (typeof value === "string") {
    const data = textEncoder.encode(value);
    const n = data.length;
    if (n <= 31) return concatBytes([Uint8Array.of(0xa0 | n), data]);
    if (n <= 0xff) return concatBytes([Uint8Array.of(0xd9, n), data]);
    if (n <= 0xffff) return concatBytes([Uint8Array.of(0xda), be16(n), data]);
    return concatBytes([Uint8Array.of(0xdb), be32(n), data]);
  }
  if (typeof value === "number" || typeof value === "bigint") return msgpackUnsigned(value);
  if (Array.isArray(value)) {
    const body = value.map(msgpack);
    const n = value.length;
    const head = n <= 15 ? Uint8Array.of(0x90 | n) : n <= 0xffff ? concatBytes([Uint8Array.of(0xdc), be16(n)]) : concatBytes([Uint8Array.of(0xdd), be32(n)]);
    return concatBytes([head, ...body]);
  }
  if (typeof value === "object") {
    const entries = Object.entries(value);
    const n = entries.length;
    const head = n <= 15 ? Uint8Array.of(0x80 | n) : n <= 0xffff ? concatBytes([Uint8Array.of(0xde), be16(n)]) : concatBytes([Uint8Array.of(0xdf), be32(n)]);
    const body = [];
    for (const [key, item] of entries) body.push(msgpack(key), msgpack(item));
    return concatBytes([head, ...body]);
  }
  throw new TypeError(`Unsupported MessagePack value: ${typeof value}`);
}

function be16(value) {
  const out = new Uint8Array(2);
  new DataView(out.buffer).setUint16(0, Number(value), false);
  return out;
}

function be32(value) {
  const out = new Uint8Array(4);
  new DataView(out.buffer).setUint32(0, Number(value), false);
  return out;
}

function be64(value) {
  const out = new Uint8Array(8);
  new DataView(out.buffer).setBigUint64(0, BigInt(value), false);
  return out;
}

function msgpackUnsigned(input) {
  const value = BigInt(input);
  if (value < 0n) throw new RangeError("CMPCT browser index does not require signed integers");
  if (value <= 0x7fn) return Uint8Array.of(Number(value));
  if (value <= 0xffn) return Uint8Array.of(0xcc, Number(value));
  if (value <= 0xffffn) return concatBytes([Uint8Array.of(0xcd), be16(value)]);
  if (value <= 0xffffffffn) return concatBytes([Uint8Array.of(0xce), be32(value)]);
  if (value <= 0xffffffffffffffffn) return concatBytes([Uint8Array.of(0xcf), be64(value)]);
  throw new RangeError("Integer exceeds MessagePack uint64");
}

/*
 * Emit a legal Zstandard frame made only of RAW blocks.
 *
 * Footnote: CMPCT revision 24 requires a Zstd-coded index, while browsers do not expose Zstd in the
 * CompressionStream API. A Zstd RAW block is still a standards-compliant Zstd block; using it here
 * avoids importing an unrelated JS parser/compressor and keeps the browser writer auditable. The
 * canonical libzstd reader is the compatibility gate in CI.
 */
function zstdRawFrame(bytes) {
  const size = bytes.length;
  let descriptor;
  let fcs;
  if (size <= 0xff) {
    descriptor = 0x20; // single-segment + 1-byte frame content size
    fcs = Uint8Array.of(size);
  } else if (size <= 65791) {
    descriptor = 0x60; // single-segment + 2-byte frame content size, encoded with +256 bias
    fcs = u16le(size - 256);
  } else if (size <= 0xffffffff) {
    descriptor = 0xa0; // single-segment + 4-byte frame content size
    fcs = u32le(size);
  } else {
    throw new RangeError("Browser-writer index exceeds Zstd 32-bit frame-content-size path");
  }

  const blocks = [];
  if (size === 0) {
    blocks.push(Uint8Array.of(1, 0, 0));
  } else {
    for (let offset = 0; offset < size; offset += 128 * 1024) {
      const block = bytes.subarray(offset, Math.min(size, offset + 128 * 1024));
      const last = offset + block.length >= size ? 1 : 0;
      const headerValue = (block.length << 3) | last; // block type 0 == RAW
      blocks.push(Uint8Array.of(headerValue & 0xff, (headerValue >>> 8) & 0xff, (headerValue >>> 16) & 0xff), block);
    }
  }
  return concatBytes([Uint8Array.of(0x28, 0xb5, 0x2f, 0xfd, descriptor), fcs, ...blocks]);
}

function blobRecord({ codec, raw, compressed, sha }) {
  const header = concatBytes([
    BLOB_MAGIC,
    Uint8Array.of(codec, 0),
    u16le(0),
    u64le(raw.length),
    u64le(compressed.length),
    u32le(0), // metadata length
    u32le(crc32(raw)),
    sha,
  ]);
  return concatBytes([header, compressed]);
}

function archiveHeader(indexCompressedLength, indexRawLength, dataLength, indexHash) {
  return concatBytes([
    MAGIC,
    u16le(SUPPORTED_FORMAT_REVISION),
    u16le(0),
    u64le(indexCompressedLength),
    u64le(indexRawLength),
    u64le(dataLength),
    indexHash,
  ]);
}

function archiveFooter(indexCompressedLength, indexRawLength, indexHash) {
  return concatBytes([
    FOOTER_MAGIC,
    Uint8Array.of(0, 1, 0, 0), // full index generation, Zstd codec, no flags
    u64le(indexCompressedLength),
    u64le(indexRawLength),
    u64le(0),
    indexHash,
  ]);
}

export async function buildCmpctFromEntries(entries, options = {}) {
  if (options.formatRevision !== undefined && Number(options.formatRevision) !== SUPPORTED_FORMAT_REVISION) {
    throw new Error(`Portable writer supports format revision ${SUPPORTED_FORMAT_REVISION}; repository is revision ${options.formatRevision}.`);
  }
  if (!Array.isArray(entries) || entries.length === 0) throw new Error("Choose at least one file.");

  const paths = new Set();
  let total = 0;
  const logical = [];
  const candidates = new Map();

  for (const entry of entries) {
    const path = normalizeLogicalPath(entry.path);
    if (paths.has(path)) throw new Error(`Duplicate logical path: ${path}`);
    paths.add(path);
    const raw = entry.bytes instanceof Uint8Array ? entry.bytes : new Uint8Array(entry.bytes);
    total += raw.length;
    if (total > BROWSER_WRITER_LIMIT_BYTES) throw new Error("Browser writer is capped at 256 MiB. Use the full CMPCT CLI for larger archives.");
    const digest = await sha256(raw);
    const key = hex(digest);
    if (!candidates.has(key)) candidates.set(key, { raw, sha: digest, key });
    logical.push({
      path,
      size: raw.length,
      shaKey: key,
      mtimeNs: BigInt(Math.max(0, Number(entry.lastModified || 0))) * 1000000n,
    });
  }

  const ordered = Array.from(candidates.values()).sort((a, b) => a.key.localeCompare(b.key));
  const blobIndex = new Map();
  const blobs = [];
  const records = [];
  let offset = 0;

  for (let index = 0; index < ordered.length; index += 1) {
    const candidate = ordered[index];
    let codec = CODEC_RAW;
    let payload = candidate.raw;
    const deflated = await deflateRaw(candidate.raw);
    // Match the reference encoder's spirit: compression must earn enough bytes to justify itself.
    if (deflated && deflated.length + 16 < candidate.raw.length) {
      codec = CODEC_DEFLATE;
      payload = deflated;
    }
    const record = blobRecord({ codec, raw: candidate.raw, compressed: payload, sha: candidate.sha });
    blobIndex.set(candidate.key, index);
    blobs.push([offset, candidate.raw.length, payload.length, codec, 0]);
    records.push(record);
    offset += record.length;
  }

  logical.sort((a, b) => a.path.localeCompare(b.path));
  const files = logical.map((file) => [
    file.path,
    K_FILE,
    0o644,
    file.mtimeNs,
    file.size,
    null, // direct blobs inherit their physical SHA-256 identity
    [S_BLOB, blobIndex.get(file.shaKey)],
  ]);

  const index = {
    v: SUPPORTED_FORMAT_REVISION,
    files,
    blobs,
    recipes: [],
    dict_blob: null,
    fsmeta: { owner: [0, 0], owner_overrides: [], xattrs: [] },
    features: ["dedup", "crc32-fastpath", "sha256", "dual-index"],
  };

  const indexRaw = msgpack(index);
  const indexCompressed = zstdRawFrame(indexRaw);
  const indexHash = await sha256(indexRaw);
  const data = concatBytes(records);
  const archive = concatBytes([
    archiveHeader(indexCompressed.length, indexRaw.length, data.length, indexHash),
    indexCompressed,
    data,
    indexCompressed,
    archiveFooter(indexCompressed.length, indexRaw.length, indexHash),
  ]);

  return {
    bytes: archive,
    stats: {
      inputBytes: total,
      archiveBytes: archive.length,
      logicalFiles: files.length,
      uniqueBlobs: blobs.length,
      deflateBlobs: blobs.filter((row) => row[3] === CODEC_DEFLATE).length,
      rawBlobs: blobs.filter((row) => row[3] === CODEC_RAW).length,
    },
    manifest: files.map((row) => ({ path: row[0], bytes: row[4] })),
  };
}

export async function fileObjectsToEntries(files) {
  const result = [];
  for (const file of Array.from(files || [])) {
    const path = normalizeLogicalPath(file.webkitRelativePath || file.name);
    result.push({ path, bytes: new Uint8Array(await file.arrayBuffer()), lastModified: file.lastModified || 0 });
  }
  return result;
}

export function inspectCmpctHeader(bytesLike) {
  const bytes = bytesLike instanceof Uint8Array ? bytesLike : new Uint8Array(bytesLike);
  if (bytes.length < 68) throw new Error("File is too small to contain a CMPCT header.");
  const magic = new TextDecoder().decode(bytes.subarray(0, 8));
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  return {
    magic: magic.replace(/\0/g, "\\0"),
    recognized: magic.startsWith("CMPCT") && magic.endsWith("\0"),
    versionField: view.getUint16(8, true),
    flags: view.getUint16(10, true),
    primaryIndexCompressedBytes: Number(view.getBigUint64(12, true)),
    primaryIndexRawBytes: Number(view.getBigUint64(20, true)),
    dataSpanBytes: Number(view.getBigUint64(28, true)),
    fileBytes: bytes.length,
  };
}
