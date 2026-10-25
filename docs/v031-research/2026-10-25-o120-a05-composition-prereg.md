# O120 A05 prospective research preregistration

Date: 2026-10-25.
Base: agent/v031-development@4545d7d5b2a0b712b4b00f5a9c291d4a3a9e169b.

Question: Does a charged two-step reversible byte-transform program improve complete Zstd-19 storage beyond the best zero-step or one-step transform?

Freeze operations: byte shuffle with record widths 2/4/8/16; modulo-256 lag differences and lag XOR with distances 1/2/4/8/16. Search depth 0, 1, 2 exhaustively and identically on every dataset. Serialize operator count (one byte), type and parameter (two bytes each), original length (eight bytes), original SHA-256 (32 bytes), four-byte magic, plus complete Zstd-19 frame. Byte-exact inverse and hash checks required. Research-model bytes, never CMPCT product bytes.

Five fixed independent dataset families: 4096 rows of four smooth 16-bit numeric lanes; 3072 rows of four independently generated 32-bit numeric lanes (held-out geometry); 4096 event records of eight bytes each with sparse shocks; variable-length UTF-8 log-style records; and 32768 deterministic pseudo-random bytes. Seeds and construction must remain fixed before seeing results. Same shared grammar for all inputs.

Prediction: two-step composition might beat best zero/one-step complete bytes by >=1% and >=64 bytes on both structured cohorts. If neither passes, narrow/retire this small grammar, not A05 broadly. If exactly one passes, preserve as regime-limited seed. If both pass, retain research headroom only pending fully integrated product and selective-work evaluation. Baseline may win. Search CPU, temporary-memory and decoded work are costs, not gifted product credit.

Controls: complete source Zstd-19, best single transform, byte-exact reconstruction, strongest charged total. Kill on any changed comparator, altered data after outcomes, missing descriptor cost, or inverse failure. No version/format/release or benchmark modification. No shared-state mutation; PR #440 currently owns discovery state reconciliation. No parallel identical A05 branch identified at start.
