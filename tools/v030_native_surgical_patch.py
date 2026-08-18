#!/usr/bin/env python3
from pathlib import Path

PATH = Path('native/cmpct-portable/src/g04.rs')
text = PATH.read_text()


def replace(old: str, new: str, *, count: int = 1) -> None:
    global text
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f'anchor mismatch: expected {count}, got {actual}: {old[:100]!r}')
    text = text.replace(old, new, count)


replace(
    '};\nuse crate::{MemberReadStats, PortableEntry, PortableError};',
    '};\nuse crate::identity::R25Identity;\nuse crate::{MemberReadStats, PortableEntry, PortableError};',
)
replace('const MAGIC: &[u8; 8] = b"CMPNXG4\\0";\nconst TAIL: &[u8; 8] = b"CNG4T\\0\\0\\0";\n', '')
replace(
    '''\n    fn logical_len(&self) -> usize {\n        match self {\n            Self::Direct { length, .. }\n            | Self::Delta { length, .. }\n            | Self::DeltaPack { length, .. }\n            | Self::Mosaic { length, .. }\n            | Self::PackMosaic { length, .. } => *length,\n        }\n    }\n''',
    '',
)
replace(
    'pub(crate) struct G04Archive {\n    entries: Vec<PortableEntry>,',
    'pub(crate) struct G04Archive {\n    identity: R25Identity,\n    entries: Vec<PortableEntry>,',
)
replace(
    '    pub(crate) fn open(path: &Path) -> Result<Self, PortableError> {\n        let mut file = File::open(path)?;',
    '''    pub(crate) fn open(path: &Path, identity: R25Identity) -> Result<Self, PortableError> {\n        if !matches!(identity, R25Identity::ResearchG04 | R25Identity::CanonicalG04) {\n            return Err(PortableError::Format(\n                "G0-G4 reader received a PrefixGraph profile identity".into(),\n            ));\n        }\n        let mut file = File::open(path)?;''',
)
replace('        let primary = read_primary(&mut file).ok();\n        let tail = read_tail(&mut file, file_len).ok();',
        '        let primary = read_primary(&mut file, identity).ok();\n        let tail = read_tail(&mut file, file_len, identity).ok();')
replace('        Ok(Self {\n            entries,', '        Ok(Self {\n            identity,\n            entries,')
replace(
    '''    pub(crate) fn entries(&self) -> &[PortableEntry] {\n        &self.entries\n    }\n\n    pub(crate) fn tail_authenticated(&self) -> bool {''',
    '''    pub(crate) fn entries(&self) -> &[PortableEntry] {\n        &self.entries\n    }\n\n    pub(crate) fn entry_identity(&self, index: usize) -> Result<(u64, [u8; 32]), PortableError> {\n        let (_, file) = self.file_at(index)?;\n        Ok(match file {\n            GFile::Preflate { size, sha, .. } | GFile::Nodes { size, sha, .. } => (*size, *sha),\n        })\n    }\n\n    pub(crate) fn tail_authenticated(&self) -> bool {''',
)
replace('            profile: "g04-r25",', '            profile: self.identity.profile_name(),')
replace('fn read_primary(file: &mut File) -> Result<AuthMeta, PortableError> {',
        'fn read_primary(file: &mut File, identity: R25Identity) -> Result<AuthMeta, PortableError> {')
replace('    if &header[0..8] != MAGIC {\n        return Err(PortableError::Format("not G0-G4 archive".into()));\n    }',
        '    if &header[0..8] != identity.magic() {\n        return Err(PortableError::Format("G0-G4 profile magic mismatch".into()));\n    }')
replace('fn read_tail(file: &mut File, file_len: u64) -> Result<AuthMeta, PortableError> {',
        'fn read_tail(file: &mut File, file_len: u64, identity: R25Identity) -> Result<AuthMeta, PortableError> {')
replace('    if &footer[0..8] != TAIL {', '    if &footer[0..8] != identity.tail() {')

PATH.write_text(text)
print('surgical G0-G4 identity patch applied')
