//! Native semantic kernel for ONE-G0.3 block Statistical Law research.
//!
//! This is not a product ABI. It must remain byte-identical to
//! `experiments/one/statistical_law_reference.py` before any performance
//! evidence is admitted. The adaptive KT model uses an implicit all-ones
//! Fenwick tree per previous-byte context; observations add two weight units,
//! exactly realizing weight = 2*n+1 without serializing learned state.

const ALPHABET: usize = 256;
const STRIDE: usize = ALPHABET + 1;
const MAX_BLOCK: usize = 65_536;
const TOP: u64 = (1u64 << 32) - 1;
const HALF: u64 = 1u64 << 31;
const FIRST_QTR: u64 = 1u64 << 30;
const THIRD_QTR: u64 = FIRST_QTR * 3;

#[derive(Debug, Clone, PartialEq, Eq)]
enum StatError {
    Length,
    MissingBootstrap,
    Arithmetic,
}

#[derive(Clone)]
struct Model {
    // 256 independent 1-indexed Fenwick trees, each holding integer KT
    // weights. Initial symbol weights are all 1; an observation adds 2.
    tree: Vec<u32>,
}

impl Model {
    fn new() -> Self {
        let mut tree = vec![0u32; ALPHABET * STRIDE];
        for context in 0..ALPHABET {
            let base = context * STRIDE;
            for i in 1..=ALPHABET {
                tree[base + i] = (i & i.wrapping_neg()) as u32;
            }
        }
        Self { tree }
    }

    fn prefix(&self, context: usize, mut count: usize) -> u64 {
        let base = context * STRIDE;
        let mut sum = 0u64;
        while count != 0 {
            sum += u64::from(self.tree[base + count]);
            count &= count - 1;
        }
        sum
    }

    fn total(&self, context: usize) -> u64 {
        // 256 is a power of two, so this Fenwick node covers the whole row.
        u64::from(self.tree[context * STRIDE + ALPHABET])
    }

    fn interval(&self, context: usize, symbol: usize) -> (u64, u64, u64) {
        let low = self.prefix(context, symbol);
        let high = self.prefix(context, symbol + 1);
        (low, high, self.total(context))
    }

    fn update(&mut self, context: usize, symbol: usize) {
        let base = context * STRIDE;
        let mut i = symbol + 1;
        while i <= ALPHABET {
            self.tree[base + i] += 2;
            i += i & i.wrapping_neg();
        }
    }

    fn locate(&self, context: usize, target: u64) -> Result<(usize, u64, u64, u64), StatError> {
        let total = self.total(context);
        if target >= total {
            return Err(StatError::Arithmetic);
        }
        let base = context * STRIDE;
        let mut idx = 0usize;
        let mut accumulated = 0u64;
        let mut bit = ALPHABET;
        while bit != 0 {
            let next = idx + bit;
            if next <= ALPHABET {
                let candidate = accumulated + u64::from(self.tree[base + next]);
                if candidate <= target {
                    idx = next;
                    accumulated = candidate;
                }
            }
            bit >>= 1;
        }
        if idx >= ALPHABET {
            return Err(StatError::Arithmetic);
        }
        let high = self.prefix(context, idx + 1);
        Ok((idx, accumulated, high, total))
    }
}

struct BitWriter {
    out: Vec<u8>,
    acc: u8,
    bits: u8,
}

impl BitWriter {
    fn new() -> Self {
        Self { out: Vec::new(), acc: 0, bits: 0 }
    }

    fn write(&mut self, bit: u8) {
        self.acc = (self.acc << 1) | (bit & 1);
        self.bits += 1;
        if self.bits == 8 {
            self.out.push(self.acc);
            self.acc = 0;
            self.bits = 0;
        }
    }

    fn finish(mut self) -> Vec<u8> {
        if self.bits != 0 {
            self.acc <<= 8 - self.bits;
            self.out.push(self.acc);
        }
        self.out
    }
}

struct BitReader<'a> {
    data: &'a [u8],
    byte: usize,
    bit: u8,
}

impl<'a> BitReader<'a> {
    fn new(data: &'a [u8]) -> Self {
        Self { data, byte: 0, bit: 0 }
    }

    fn read(&mut self) -> u8 {
        if self.byte >= self.data.len() {
            return 0;
        }
        let value = (self.data[self.byte] >> (7 - self.bit)) & 1;
        self.bit += 1;
        if self.bit == 8 {
            self.byte += 1;
            self.bit = 0;
        }
        value
    }
}

fn validate_len(len: usize) -> Result<(), StatError> {
    if (1..=MAX_BLOCK).contains(&len) { Ok(()) } else { Err(StatError::Length) }
}

fn encode_block(block: &[u8]) -> Result<Vec<u8>, StatError> {
    validate_len(block.len())?;
    let first = block[0];
    if block.len() == 1 {
        return Ok(vec![first]);
    }

    let mut model = Model::new();
    let mut writer = BitWriter::new();
    let mut low = 0u64;
    let mut high = TOP;
    let mut pending = 0usize;
    let mut previous = usize::from(first);

    fn emit(writer: &mut BitWriter, pending: &mut usize, bit: u8) {
        writer.write(bit);
        let complement = 1 - bit;
        while *pending != 0 {
            writer.write(complement);
            *pending -= 1;
        }
    }

    for &byte in &block[1..] {
        let symbol = usize::from(byte);
        let (cum_low, cum_high, total) = model.interval(previous, symbol);
        let width = high - low + 1;
        high = low + (width * cum_high / total) - 1;
        low += width * cum_low / total;

        loop {
            if high < HALF {
                emit(&mut writer, &mut pending, 0);
            } else if low >= HALF {
                emit(&mut writer, &mut pending, 1);
                low -= HALF;
                high -= HALF;
            } else if low >= FIRST_QTR && high < THIRD_QTR {
                pending += 1;
                low -= FIRST_QTR;
                high -= FIRST_QTR;
            } else {
                break;
            }
            low = (low << 1) & TOP;
            high = ((high << 1) | 1) & TOP;
        }

        model.update(previous, symbol);
        previous = symbol;
    }

    pending += 1;
    emit(&mut writer, &mut pending, if low < FIRST_QTR { 0 } else { 1 });
    let mut out = Vec::with_capacity(1 + writer.out.len() + 1);
    out.push(first);
    out.extend(writer.finish());
    Ok(out)
}

fn decode_block(payload: &[u8], output_len: usize) -> Result<Vec<u8>, StatError> {
    validate_len(output_len)?;
    let (&first, coded) = payload.split_first().ok_or(StatError::MissingBootstrap)?;
    if output_len == 1 {
        return Ok(vec![first]);
    }

    let mut reader = BitReader::new(coded);
    let mut low = 0u64;
    let mut high = TOP;
    let mut code = 0u64;
    for _ in 0..32 {
        code = ((code << 1) | u64::from(reader.read())) & TOP;
    }

    let mut model = Model::new();
    let mut out = Vec::with_capacity(output_len);
    out.push(first);
    let mut previous = usize::from(first);

    for _ in 1..output_len {
        let total = model.total(previous);
        let width = high - low + 1;
        let scaled = ((code - low + 1) * total - 1) / width;
        let (symbol, cum_low, cum_high, located_total) = model.locate(previous, scaled)?;
        debug_assert_eq!(total, located_total);

        high = low + (width * cum_high / total) - 1;
        low += width * cum_low / total;
        loop {
            if high < HALF {
                // no offset
            } else if low >= HALF {
                code -= HALF;
                low -= HALF;
                high -= HALF;
            } else if low >= FIRST_QTR && high < THIRD_QTR {
                code -= FIRST_QTR;
                low -= FIRST_QTR;
                high -= FIRST_QTR;
            } else {
                break;
            }
            low = (low << 1) & TOP;
            high = ((high << 1) | 1) & TOP;
            code = ((code << 1) | u64::from(reader.read())) & TOP;
        }

        model.update(previous, symbol);
        out.push(symbol as u8);
        previous = symbol;
    }
    Ok(out)
}

fn main() {
    // Intentionally no production CLI yet. The first authority is unit-test
    // parity against Python semantic vectors; corpus timing comes only after
    // that gate is green.
}

#[cfg(test)]
mod tests {
    use super::*;

    fn hex(bytes: &[u8]) -> String {
        bytes.iter().map(|b| format!("{b:02x}")).collect()
    }

    #[test]
    fn python_semantic_vectors_are_byte_identical() {
        let vectors: Vec<(Vec<u8>, &str)> = vec![
            (b"a".to_vec(), "61"),
            (b"aa".to_vec(), "616140"),
            (b"ab".to_vec(), "616240"),
            (b"abc".to_vec(), "61626340"),
            (vec![0, 1, 0, 1, 0, 1], "00010000fe10"),
            (b"banana bandana".to_vec(), "62616e616e4550a13970932868"),
            ((0u8..16).collect(), "000102030405060708090a0b0c0d0e0f40"),
        ];
        for (source, expected) in vectors {
            let encoded = encode_block(&source).unwrap();
            assert_eq!(hex(&encoded), expected);
            assert_eq!(decode_block(&encoded, source.len()).unwrap(), source);
        }
    }

    #[test]
    fn full_block_is_bounded_and_exact() {
        let source = vec![0u8; MAX_BLOCK];
        let encoded = encode_block(&source).unwrap();
        assert_eq!(encoded.len(), 168);
        assert_eq!(decode_block(&encoded, source.len()).unwrap(), source);
    }

    #[test]
    fn resource_bounds_fail_closed() {
        assert_eq!(encode_block(&[]), Err(StatError::Length));
        assert_eq!(encode_block(&vec![0; MAX_BLOCK + 1]), Err(StatError::Length));
        assert_eq!(decode_block(&[0], 0), Err(StatError::Length));
        assert_eq!(decode_block(&[0], MAX_BLOCK + 1), Err(StatError::Length));
        assert_eq!(decode_block(&[], 1), Err(StatError::MissingBootstrap));
    }
}
