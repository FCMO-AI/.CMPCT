//! Revision-24 virtual-ZIP recipe validation and range planning.
//!
//! Stored ZIP payloads and retained-exact Deflate stream mode 1 are live in archive dispatch.
//! Canonical physical Deflate stream mode 0 has a builder-independent oracle and can now be planned
//! with an explicit physical source kind, but the default parser deliberately keeps it unsupported
//! until archive dispatch routes that source through the authenticated physical-Deflate reader.

use rmpv::Value;
use thiserror::Error;

const ZIP_STORED: u64 = 0;
const ZIP_DEFLATED: u64 = 8;
const STREAM_CANONICAL: u64 = 0;
const STREAM_RETAINED_EXACT: u64 = 1;
const MAX_VZIP_PAYLOADS: usize = 1_000_000;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum VirtualZipError {
    #[error("invalid virtual-ZIP recipe: {0}")]
    Schema(String),
    #[error("virtual-ZIP payload method/stream mode is not yet independently conformance-gated")]
    UnsupportedPayload,
    #[error("requested virtual-ZIP range is outside the logical file")]
    Range,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProjectionSource {
    LogicalBlob,
    PhysicalDeflate,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct StoredPayload {
    pub blob_index: usize,
    pub logical_len: u64,
    pub source: ProjectionSource,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ProjectionSegment {
    pub source: ProjectionSource,
    pub blob_index: usize,
    pub blob_offset: u64,
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
        return Err(VirtualZipError::Schema(format!("{label} references a missing blob")));
    }
    Ok(index)
}

fn parse_recipe_impl(
    value: &Value,
    blob_sizes: &[u64],
    entry_logical_size: u64,
    allow_physical_deflate: bool,
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
        let compressed_len = payload[4].as_u64().ok_or_else(|| {
            VirtualZipError::Schema(format!(
                "payload descriptor {index} has invalid stored length"
            ))
        })?;

        let (projected_blob, source) = match (method, stream_mode) {
            (ZIP_STORED, STREAM_CANONICAL) => {
                if compressed_len != blob_sizes[content_blob] {
                    return Err(VirtualZipError::Schema(format!(
                        "payload descriptor {index} stored length disagrees with content blob"
                    )));
                }
                (content_blob, ProjectionSource::LogicalBlob)
            }
            (ZIP_DEFLATED, STREAM_CANONICAL) if allow_physical_deflate => {
                // Footnote: mode 0 projects the physical RFC-1951 payload, not decoded member bytes.
                // Keeping this source kind explicit prevents an archive adapter from accidentally
                // decode/recompressing and changing the byte-exact nested ZIP identity.
                (content_blob, ProjectionSource::PhysicalDeflate)
            }
            (ZIP_DEFLATED, STREAM_CANONICAL) => return Err(VirtualZipError::UnsupportedPayload),
            (ZIP_DEFLATED, STREAM_RETAINED_EXACT) => {
                let stream_blob = blob_index(
                    &payload[3],
                    blob_sizes.len(),
                    &format!("payload descriptor {index} retained stream blob"),
                )?;
                if compressed_len != blob_sizes[stream_blob] {
                    return Err(VirtualZipError::Schema(format!(
                        "payload descriptor {index} compressed length disagrees with retained stream blob"
                    )));
                }
                (stream_blob, ProjectionSource::LogicalBlob)
            }
            (ZIP_DEFLATED, _) => return Err(VirtualZipError::UnsupportedPayload),
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

pub fn parse_recipe(
    value: &Value,
    blob_sizes: &[u64],
    entry_logical_size: u64,
) -> Result<VirtualZipRecipe, VirtualZipError> {
    parse_recipe_impl(value, blob_sizes, entry_logical_size, false)
}

/// Parse the independently frozen mode-0 form for planner/component tests.
/// Archive dispatch must not use this until it can route `PhysicalDeflate` segments correctly.
pub fn parse_recipe_with_physical_deflate(
    value: &Value,
    blob_sizes: &[u64],
    entry_logical_size: u64,
) -> Result<VirtualZipRecipe, VirtualZipError> {
    parse_recipe_impl(value, blob_sizes, entry_logical_size, true)
}

pub fn parse_stored_recipe(
    value: &Value,
    blob_sizes: &[u64],
    entry_logical_size: u64,
) -> Result<VirtualZipRecipe, VirtualZipError> {
    parse_recipe(value, blob_sizes, entry_logical_size)
}

impl VirtualZipRecipe {
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
                segments.push(ProjectionSegment {
                    source,
                    blob_index,
                    blob_offset: blob_base + (overlap_start - logical_start),
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
