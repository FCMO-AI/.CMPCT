//! Zero-allocation structural guard for archive-controlled MessagePack declarations.
//!
//! `rmpv` is used only after this scanner proves that every declared string/bin/container length and
//! aggregate nesting/node count stays inside explicit native parser ceilings. This closes the gap where
//! a small authenticated byte string could declare a multi-billion-element array and make a general
//! MessagePack decoder reserve memory before semantic validation ever sees the value.

use thiserror::Error;

#[derive(Debug, Clone, Copy)]
pub struct GuardLimits {
    pub max_string_bytes: u64,
    pub max_binary_bytes: u64,
    pub max_array_items: u64,
    pub max_map_items: u64,
    pub max_depth: usize,
    pub max_nodes: u64,
}

#[derive(Debug, Error, PartialEq, Eq)]
pub enum GuardError {
    #[error("MessagePack value is truncated")]
    Truncated,
    #[error("MessagePack declaration exceeds native parser resource limit")]
    Limit,
    #[error("MessagePack extension values are not part of revision-24 index grammar")]
    Extension,
    #[error("MessagePack payload has trailing values/bytes")]
    Trailing,
}

fn take<'a>(bytes: &'a [u8], cursor: &mut usize, length: usize) -> Result<&'a [u8], GuardError> {
    let end = cursor.checked_add(length).ok_or(GuardError::Limit)?;
    let slice = bytes.get(*cursor..end).ok_or(GuardError::Truncated)?;
    *cursor = end;
    Ok(slice)
}

fn u16_be(bytes: &[u8]) -> u64 {
    u16::from_be_bytes(bytes.try_into().expect("two-byte MessagePack width")) as u64
}

fn u32_be(bytes: &[u8]) -> u64 {
    u32::from_be_bytes(bytes.try_into().expect("four-byte MessagePack width")) as u64
}

fn declared_length(
    bytes: &[u8],
    cursor: &mut usize,
    width: usize,
) -> Result<u64, GuardError> {
    let raw = take(bytes, cursor, width)?;
    Ok(match width {
        1 => raw[0] as u64,
        2 => u16_be(raw),
        4 => u32_be(raw),
        _ => unreachable!("MessagePack declaration width is fixed"),
    })
}

fn skip_payload(
    bytes: &[u8],
    cursor: &mut usize,
    length: u64,
    limit: u64,
) -> Result<(), GuardError> {
    if length > limit {
        return Err(GuardError::Limit);
    }
    let length = usize::try_from(length).map_err(|_| GuardError::Limit)?;
    take(bytes, cursor, length)?;
    Ok(())
}

fn push_container(
    stack: &mut Vec<u64>,
    child_count: u64,
    item_limit: u64,
    max_depth: usize,
) -> Result<(), GuardError> {
    if child_count > item_limit || stack.len() >= max_depth {
        return Err(GuardError::Limit);
    }
    if child_count > 0 {
        stack.push(child_count);
    }
    Ok(())
}

/// Validate exactly one MessagePack value without allocating according to archive-declared lengths.
pub fn validate(bytes: &[u8], limits: GuardLimits) -> Result<(), GuardError> {
    if limits.max_depth == 0 || limits.max_nodes == 0 {
        return Err(GuardError::Limit);
    }
    let mut cursor = 0usize;
    let mut stack = vec![1u64];
    let mut nodes = 0u64;

    while !stack.is_empty() {
        while stack.last() == Some(&0) {
            stack.pop();
        }
        if stack.is_empty() {
            break;
        }
        let remaining = stack.last_mut().expect("non-empty stack");
        *remaining -= 1;
        nodes = nodes.checked_add(1).ok_or(GuardError::Limit)?;
        if nodes > limits.max_nodes {
            return Err(GuardError::Limit);
        }

        let tag = *take(bytes, &mut cursor, 1)?
            .first()
            .expect("one-byte MessagePack tag");
        match tag {
            // positive fixint / negative fixint / nil / bool
            0x00..=0x7f | 0xc0 | 0xc2 | 0xc3 | 0xe0..=0xff => {}

            // fixmap: low nibble is pair count, therefore 2 child values per pair.
            0x80..=0x8f => {
                let pairs = (tag & 0x0f) as u64;
                push_container(
                    &mut stack,
                    pairs.checked_mul(2).ok_or(GuardError::Limit)?,
                    limits.max_map_items.saturating_mul(2),
                    limits.max_depth,
                )?;
            }
            // fixarray
            0x90..=0x9f => push_container(
                &mut stack,
                (tag & 0x0f) as u64,
                limits.max_array_items,
                limits.max_depth,
            )?,
            // fixstr
            0xa0..=0xbf => skip_payload(
                bytes,
                &mut cursor,
                (tag & 0x1f) as u64,
                limits.max_string_bytes,
            )?,

            // binary
            0xc4 => {
                let length = declared_length(bytes, &mut cursor, 1)?;
                skip_payload(bytes, &mut cursor, length, limits.max_binary_bytes)?;
            }
            0xc5 => {
                let length = declared_length(bytes, &mut cursor, 2)?;
                skip_payload(bytes, &mut cursor, length, limits.max_binary_bytes)?;
            }
            0xc6 => {
                let length = declared_length(bytes, &mut cursor, 4)?;
                skip_payload(bytes, &mut cursor, length, limits.max_binary_bytes)?;
            }

            // extension values are intentionally excluded from the revision-24 index grammar.
            0xc7 | 0xc8 | 0xc9 | 0xd4 | 0xd5 | 0xd6 | 0xd7 | 0xd8 => {
                return Err(GuardError::Extension)
            }

            // floats
            0xca => {
                take(bytes, &mut cursor, 4)?;
            }
            0xcb => {
                take(bytes, &mut cursor, 8)?;
            }

            // unsigned/signed integers
            0xcc | 0xd0 => {
                take(bytes, &mut cursor, 1)?;
            }
            0xcd | 0xd1 => {
                take(bytes, &mut cursor, 2)?;
            }
            0xce | 0xd2 => {
                take(bytes, &mut cursor, 4)?;
            }
            0xcf | 0xd3 => {
                take(bytes, &mut cursor, 8)?;
            }

            // strings
            0xd9 => {
                let length = declared_length(bytes, &mut cursor, 1)?;
                skip_payload(bytes, &mut cursor, length, limits.max_string_bytes)?;
            }
            0xda => {
                let length = declared_length(bytes, &mut cursor, 2)?;
                skip_payload(bytes, &mut cursor, length, limits.max_string_bytes)?;
            }
            0xdb => {
                let length = declared_length(bytes, &mut cursor, 4)?;
                skip_payload(bytes, &mut cursor, length, limits.max_string_bytes)?;
            }

            // arrays
            0xdc => {
                let count = declared_length(bytes, &mut cursor, 2)?;
                push_container(
                    &mut stack,
                    count,
                    limits.max_array_items,
                    limits.max_depth,
                )?;
            }
            0xdd => {
                let count = declared_length(bytes, &mut cursor, 4)?;
                push_container(
                    &mut stack,
                    count,
                    limits.max_array_items,
                    limits.max_depth,
                )?;
            }

            // maps: encoded count is key/value pairs.
            0xde => {
                let pairs = declared_length(bytes, &mut cursor, 2)?;
                if pairs > limits.max_map_items {
                    return Err(GuardError::Limit);
                }
                push_container(
                    &mut stack,
                    pairs.checked_mul(2).ok_or(GuardError::Limit)?,
                    limits.max_map_items.saturating_mul(2),
                    limits.max_depth,
                )?;
            }
            0xdf => {
                let pairs = declared_length(bytes, &mut cursor, 4)?;
                if pairs > limits.max_map_items {
                    return Err(GuardError::Limit);
                }
                push_container(
                    &mut stack,
                    pairs.checked_mul(2).ok_or(GuardError::Limit)?,
                    limits.max_map_items.saturating_mul(2),
                    limits.max_depth,
                )?;
            }

            // 0xc1 is reserved and never a valid MessagePack value.
            0xc1 => return Err(GuardError::Trailing),
        }
    }

    if cursor != bytes.len() {
        return Err(GuardError::Trailing);
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn limits() -> GuardLimits {
        GuardLimits {
            max_string_bytes: 1024,
            max_binary_bytes: 4096,
            max_array_items: 32,
            max_map_items: 32,
            max_depth: 16,
            max_nodes: 256,
        }
    }

    #[test]
    fn accepts_nested_revision_style_value_without_allocating_from_declarations() {
        // {"files": [["a", 0]], "blobs": []}
        let bytes = [
            0x82, 0xa5, b'f', b'i', b'l', b'e', b's', 0x91, 0x92, 0xa1, b'a', 0x00, 0xa5,
            b'b', b'l', b'o', b'b', b's', 0x90,
        ];
        assert_eq!(validate(&bytes, limits()), Ok(()));
    }

    #[test]
    fn huge_declared_array_is_rejected_before_child_allocation_or_read() {
        let bytes = [0xdd, 0xff, 0xff, 0xff, 0xff];
        assert_eq!(validate(&bytes, limits()), Err(GuardError::Limit));
    }

    #[test]
    fn huge_declared_binary_is_rejected_before_payload_read() {
        let bytes = [0xc6, 0x00, 0x01, 0x00, 0x00];
        assert_eq!(validate(&bytes, limits()), Err(GuardError::Limit));
    }

    #[test]
    fn extensions_and_trailing_second_values_fail_closed() {
        assert_eq!(validate(&[0xd4, 0, 0], limits()), Err(GuardError::Extension));
        assert_eq!(validate(&[0xc0, 0xc0], limits()), Err(GuardError::Trailing));
    }
}
