#[path = "logs.rs"]
pub(crate) mod logs;

#[derive(Debug, Clone, Copy, Eq, PartialEq)]
pub(crate) enum R25Identity {
    ResearchG04,
    ResearchPrefix,
    CanonicalG04,
    CanonicalPrefix,
}

impl R25Identity {
    pub(crate) const fn magic(self) -> &'static [u8; 8] {
        match self {
            Self::ResearchG04 => b"CMPNXG4\0",
            Self::ResearchPrefix => b"CMPNXP1\0",
            Self::CanonicalG04 => b"CMP25G4\0",
            Self::CanonicalPrefix => b"CMP25PG\0",
        }
    }

    pub(crate) const fn tail(self) -> &'static [u8; 8] {
        match self {
            Self::ResearchG04 => b"CNG4T\0\0\0",
            Self::ResearchPrefix => b"CMPNXP1T",
            Self::CanonicalG04 => b"C25G4TL\0",
            Self::CanonicalPrefix => b"C25PGTL\0",
        }
    }

    pub(crate) const fn is_canonical(self) -> bool {
        matches!(self, Self::CanonicalG04 | Self::CanonicalPrefix)
    }

    pub(crate) const fn profile_name(self) -> &'static str {
        match self {
            Self::ResearchG04 => "research-g04",
            Self::ResearchPrefix => "research-prefixgraph",
            Self::CanonicalG04 => "g04-r25",
            Self::CanonicalPrefix => "prefixgraph-r25",
        }
    }
}

pub(crate) fn classify(magic: &[u8; 8]) -> Option<R25Identity> {
    [
        R25Identity::CanonicalG04,
        R25Identity::CanonicalPrefix,
        R25Identity::ResearchG04,
        R25Identity::ResearchPrefix,
    ]
    .into_iter()
    .find(|identity| identity.magic() == magic)
}

// Footnote: profile identity is isolated from reconstruction semantics on purpose. T03's productization
// decision changed the canonical eight-byte framing while retaining the measured G0-G4/PrefixGraph grammars;
// keeping this table singular prevents research or pre-parity profile bytes from being silently described as
// supported canonical revision 25 before native/Android dispatch is complete. The hidden `logs` module above is
// compiled only to make preparity/parser tests executable; `classify` intentionally does not admit its magic.
