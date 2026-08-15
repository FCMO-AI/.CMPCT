//! Revision-24 virtual-ZIP recipe validation and range planning.
//!
//! ZIP_STORED plus all three revision-24 Deflate stream modes now have explicit source semantics:
//! logical blob bytes, authenticated physical codec-4 bytes, retained exact stream bytes, or
//! deterministic zlib regeneration from authenticated logical content. The planner never performs
//! archive I/O itself; it records *what kind of bytes* a projection segment needs so archive dispatch
//! can preserve the correct integrity boundary without guessing from a blob index.

use rmpv::Value;
use thiserror::Error;

const ZIP_STORED: u64 = 0;
const ZIP_DEFLATED: u64 = 8;
const STREAM_CANONICAL: u64 = 0;
const STREAM_RETAINED_EXACT: u64 = 1;
const STREAM_REGENERATED_ZLIB: u64 = 2;
const MAX_VZIP_PAYLOADS: usize = 1_000_000;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum VirtualZipError {
    #[error("invalid virtual-ZIP recipe: {0}")]
    Schema(String),
    #[error("virtual-ZIP payload method/stream mode is not supported by the native handler")]
    UnsupportedPayload,
    #[error("requested virtual-ZIP range is outside the logical file")]
    Range,
}

/// The byte source required by one virtual-ZIP projection segment.
///
/// Footnote: mode 0 and mode 2 deliberately cannot be represented as an ordinary logical blob read.
/// Mode 0 needs the *physical* RFC-1951 payload stored inside a codec-4 blob; mode 2 needs an exact
/// zlib-compatible RFC-1951 regeneration from authenticated logical content. The expected total
/// stream length is carried in the source itself so a selective read cannot accidentally accept an
/// authenticated but differently-sized stream and project only a matching prefix.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProjectionSource {
    LogicalBlob,
    PhysicalDeflate { expected_len: u64 },
    RegeneratedDeflate { level: u8, expected_len: u64 },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct StoredPayload {
    /// Blob associated with this payload source.
    ///
    /// - ZIP_STORED: raw-content blob;
    /// - mode 0: codec-4 content blob whose physical payload is projected;
    /// - mode 1: retained exact-stream blob;
    /// - mode 2: authenticated raw-content blob used as regeneration input.
    pub blob_index: usize,
    pub logical_len: u64,
    pub source: ProjectionSource,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ProjectionSegment {
    pub source: ProjectionSource,
    /// CMPCT blob associated with this segment's source.
    pub blob_index: usize,
    /// Offset inside the selected source byte stream.
    pub blob_offset: u64,
    /// Offset inside the caller's requested output range.
    pub output_offset: u64,
    pub length: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VirtualZipRecipe {
    pub skeleton_blob: usize,
    pub literal_lengths: Vec<u64>,
    pub payloads: Vec<StoredPayload>,
    pub logical_sha256: [u8; 32],
    pub logical_size: u64,
    pub logical_crc32: u32,
}

fn blob_index(value: &Value, blob_count: usize, label: &str) -> Result<usize, VirtualZipError> {
    let raw = value
        .as_u64()
        .ok_or_else(|| VirtualZipError::Schema(format!("{label} is not a blob index")))?;
    let index = usize::try_from(raw)
        .map_err(|_| VirtualZipError::Schema(format!("{label} exceeds native index width")))?;
    if index >= blob_count {
        return Err(VirtualZipError::Schema(format!(
            "{label} references a missing blob"
        )));
    }
    Ok(index)
}

fn deflate_level(value: &Value, payload_index: usize) -> Result<u8, VirtualZipError> {
    value
        .as_i64()
        .filter(|level| (0..=9).contains(level))
        .map(|level| level as u8)
        .ok_or_else(|| {
            VirtualZipError::Schema(format!(
                "payload descriptor {payload_index} has invalid zlib level"
            ))
        })
}

/// Parse and structurally validate revision-24 virtual-ZIP recipe shapes.
///
/// `blob_sizes` are authenticated logical blob lengths from the primary index. Physical codec/csize
/// checks intentionally remain in archive dispatch because mode 0's projected length is a physical
/// compressed length rather than the blob's logical length.
pub fn parse_recipe(
    value: &Value,
    blob_sizes: &[u64],
    entry_logical_size: u64,
) -> Result<VirtualZipRecipe, VirtualZipError> {
    let row = value
        .as_array()
        .ok_or_else(|| VirtualZipError::Schema("recipe is not an array".into()))?;
    if row.len() != 6 {
        return Err(VirtualZipError::Schema(
            "recipe must contain six revision-24 fields".into(),
        ));
    }

    let skeleton_blob = blob_index(&row[0], blob_sizes.len(), "skeleton blob")?;
    let literal_values = row[1]
        .as_array()
        .ok_or_else(|| VirtualZipError::Schema("literal lengths are not an array".into()))?;
    let payload_values = row[2]
        .as_array()
        .ok_or_else(|| VirtualZipError::Schema("payload descriptors are not an array".into()))?;
    if payload_values.len() > MAX_VZIP_PAYLOADS {
        return Err(VirtualZipError::Schema(
            "payload count exceeds native handler limit".into(),
        ));
    }
    if literal_values.len() != payload_values.len().saturating_add(1) {
        return Err(VirtualZipError::Schema(
            "virtual-ZIP literal/payload counts do not alternate exactly".into(),
        ));
    }

    let mut literal_lengths = Vec::with_capacity(literal_values.len());
    let mut skeleton_total = 0u64;
    for (index, value) in literal_values.iter().enumerate() {
        let length = value.as_u64().ok_or_else(|| {
            VirtualZipError::Schema(format!("literal length {index} is not unsigned"))
        })?;
        skeleton_total = skeleton_total.checked_add(length).ok_or_else(|| {
            VirtualZipError::Schema("virtual-ZIP skeleton length overflows".into())
        })?;
        literal_lengths.push(length);
    }
    if blob_sizes[skeleton_blob] != skeleton_total {
        return Err(VirtualZipError::Schema(
            "skeleton blob length disagrees with literal lengths".into(),
        ));
    }

    let mut payloads = Vec::with_capacity(payload_values.len());
    let mut payload_total = 0u64;
    for (index, value) in payload_values.iter().enumerate() {
        let payload = value.as_array().ok_or_else(|| {
            VirtualZipError::Schema(format!("payload descriptor {index} is not an array"))
        })?;
        if payload.len() != 6 {
            return Err(VirtualZipError::Schema(format!(
                "payload descriptor {index} must contain six fields"
            )));
        }
        let content_blob = blob_index(
            &payload[0],
            blob_sizes.len(),
            &format!("payload descriptor {index} content blob"),
        )?;
        let method = payload[1].as_u64().ok_or_else(|| {
            VirtualZipError::Schema(format!("payload descriptor {index} has invalid ZIP method"))
        })?;
        let stream_mode = payload[2].as_u64().ok_or_else(|| {
            VirtualZipError::Schema(format!("payload descriptor {index} has invalid stream mode"))
        })?;
        let stream_blob = blob_index(
            &payload[3],
            blob_sizes.len(),
            &format!("payload descriptor {index} stream blob"),
        )?;
        let compressed_len = payload[4].as_u64().ok_or_else(|| {
            VirtualZipError::Schema(format!(
                "payload descriptor {index} has invalid stored length"
            ))
        })?;

        let (projected_blob, source) = match (method, stream_mode) {
            (ZIP_STORED, STREAM_CANONICAL) => {
                if stream_blob != content_blob {
                    return Err(VirtualZipError::Schema(format!(
                        "payload descriptor {index} stored stream reference disagrees with content blob"
                    )));
                }
                if compressed_len != blob_sizes[content_blob] {
                    return Err(VirtualZipError::Schema(format!(
                        "payload descriptor {index} stored length disagrees with content blob"
                    )));
                }
                (content_blob, ProjectionSource::LogicalBlob)
            }
            (ZIP_DEFLATED, STREAM_CANONICAL) => {
                if stream_blob != content_blob {
                    return Err(VirtualZipError::Schema(format!(
                        "payload descriptor {index} canonical stream reference disagrees with content blob"
                    )));
                }
                // Level is not needed to *read* mode 0, but validating it preserves the exact
                // revision-24 descriptor contract and catches malformed archive-controlled metadata.
                let _ = deflate_level(&payload[5], index)?;
                (
                    content_blob,
                    ProjectionSource::PhysicalDeflate {
                        expected_len: compressed_len,
                    },
                )
            }
            (ZIP_DEFLATED, STREAM_RETAINED_EXACT) => {
                // Mode 1 stores the exact RFC-1951 stream as an ordinary logical CMPCT blob.
                let _ = deflate_level(&payload[5], index)?;
                if compressed_len != blob_sizes[stream_blob] {
                    return Err(VirtualZipError::Schema(format!(
                        "payload descriptor {index} compressed length disagrees with retained stream blob"
                    )));
                }
                (stream_blob, ProjectionSource::LogicalBlob)
            }
            (ZIP_DEFLATED, STREAM_REGENERATED_ZLIB) => {
                if stream_blob != content_blob {
                    return Err(VirtualZipError::Schema(format!(
                        "payload descriptor {index} regenerated stream reference disagrees with content blob"
                    )));
                }
                let level = deflate_level(&payload[5], index)?;
                (
                    content_blob,
                    ProjectionSource::RegeneratedDeflate {
                        level,
                        expected_len: compressed_len,
                    },
                )
            }
            _ => return Err(VirtualZipError::UnsupportedPayload),
        };

        payload_total = payload_total.checked_add(compressed_len).ok_or_else(|| {
            VirtualZipError::Schema("virtual-ZIP payload lengths overflow".into())
        })?;
        payloads.push(StoredPayload {
            blob_index: projected_blob,
            logical_len: compressed_len,
            source,
        });
    }

    let logical_size = row[4]
        .as_u64()
        .ok_or_else(|| VirtualZipError::Schema("recipe logical size is not unsigned".into()))?;
    if logical_size != entry_logical_size {
        return Err(VirtualZipError::Schema(
            "recipe logical size disagrees with file entry".into(),
        ));
    }
    let projected_size = skeleton_total.checked_add(payload_total).ok_or_else(|| {
        VirtualZipError::Schema("virtual-ZIP projected size overflows".into())
    })?;
    if projected_size != logical_size {
        return Err(VirtualZipError::Schema(
            "skeleton plus payload lengths do not equal logical size".into(),
        ));
    }

    let hash = match &row[3] {
        Value::Binary(bytes) if bytes.len() == 32 => bytes,
        _ => {
            return Err(VirtualZipError::Schema(
                "recipe logical SHA-256 must be 32 binary bytes".into(),
            ))
        }
    };
    let mut logical_sha256 = [0u8; 32];
    logical_sha256.copy_from_slice(hash);

    let logical_crc32 = row[5]
        .as_u64()
        .filter(|value| *value <= u32::MAX as u64)
        .ok_or_else(|| VirtualZipError::Schema("recipe CRC32 is outside uint32".into()))?
        as u32;

    Ok(VirtualZipRecipe {
        skeleton_blob,
        literal_lengths,
        payloads,
        logical_sha256,
        logical_size,
        logical_crc32,
    })
}

/// Compatibility name retained for older focused tests. All currently frozen revision-24 stream
/// modes are parsed by the same implementation; the wrapper no longer means "stored-only".
pub fn parse_stored_recipe(
    value: &Value,
    blob_sizes: &[u64],
    entry_logical_size: u64,
) -> Result<VirtualZipRecipe, VirtualZipError> {
    parse_recipe(value, blob_sizes, entry_logical_size)
}

impl VirtualZipRecipe {
    /// Plan only the source slices needed for one logical virtual-ZIP range.
    ///
    /// Skeleton bytes always come from decoded logical blob bytes. Payload segments retain their typed
    /// source so the executor can select logical, physical-Deflate, or regenerated-Deflate semantics.
    pub fn plan_range(
        &self,
        start: u64,
        length: u64,
    ) -> Result<Vec<ProjectionSegment>, VirtualZipError> {
        let request_end = start.checked_add(length).ok_or(VirtualZipError::Range)?;
        if request_end > self.logical_size {
            return Err(VirtualZipError::Range);
        }
        if length == 0 {
            return Ok(Vec::new());
        }

        let mut segments = Vec::new();
        let mut logical_cursor = 0u64;
        let mut skeleton_cursor = 0u64;

        let mut append_overlap = |source: ProjectionSource,
                                  blob_index: usize,
                                  blob_base: u64,
                                  segment_len: u64,
                                  logical_start: u64|
         -> Result<(), VirtualZipError> {
            let logical_end = logical_start
                .checked_add(segment_len)
                .ok_or_else(|| VirtualZipError::Schema("projection segment overflows".into()))?;
            let overlap_start = start.max(logical_start);
            let overlap_end = request_end.min(logical_end);
            if overlap_start < overlap_end {
                let source_offset = blob_base
                    .checked_add(overlap_start - logical_start)
                    .ok_or_else(|| VirtualZipError::Schema("projection source offset overflows".into()))?;
                segments.push(ProjectionSegment {
                    source,
                    blob_index,
                    blob_offset: source_offset,
                    output_offset: overlap_start - start,
                    length: overlap_end - overlap_start,
                });
            }
            Ok(())
        };

        for (index, payload) in self.payloads.iter().enumerate() {
            let literal_len = self.literal_lengths[index];
            append_overlap(
                ProjectionSource::LogicalBlob,
                self.skeleton_blob,
                skeleton_cursor,
                literal_len,
                logical_cursor,
            )?;
            logical_cursor = logical_cursor
                .checked_add(literal_len)
                .ok_or_else(|| VirtualZipError::Schema("logical projection overflows".into()))?;
            skeleton_cursor = skeleton_cursor
                .checked_add(literal_len)
                .ok_or_else(|| VirtualZipError::Schema("skeleton projection overflows".into()))?;

            append_overlap(
                payload.source,
                payload.blob_index,
                0,
                payload.logical_len,
                logical_cursor,
            )?;
            logical_cursor = logical_cursor
                .checked_add(payload.logical_len)
                .ok_or_else(|| VirtualZipError::Schema("logical projection overflows".into()))?;
        }

        let tail_len = *self.literal_lengths.last().ok_or_else(|| {
            VirtualZipError::Schema("virtual-ZIP recipe has no trailing literal".into())
        })?;
        append_overlap(
            ProjectionSource::LogicalBlob,
            self.skeleton_blob,
            skeleton_cursor,
            tail_len,
            logical_cursor,
        )?;
        logical_cursor = logical_cursor
            .checked_add(tail_len)
            .ok_or_else(|| VirtualZipError::Schema("logical projection overflows".into()))?;
        if logical_cursor != self.logical_size {
            return Err(VirtualZipError::Schema(
                "planned virtual-ZIP bytes do not equal logical size".into(),
            ));
        }
        Ok(segments)
    }
}
