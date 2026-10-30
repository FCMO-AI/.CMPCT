#!/usr/bin/env python3
"""J24I47 research-only observational-integrity bound and charged digest-index oracle.

NOT a CMPCT codec or a drop-in read_range replacement. SHA-256 here is an
independent byte-array model; the theorem, not this witness, carries the claim.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import random
from pathlib import Path

REGIONS = (4096, 65536, 1048576)
REQUEST_BYTES = 4096
RECORD_BYTES = 32 + 8 + 8
ROOT_BYTES = 32

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def probe(original: bytes, chunk: int, mutant_position: int, request_start: int):
    # Entire commitment table derived from valid original; generous creator oracle.
    # The table's identity is unchanged after a payload flip.
    table = [hashlib.sha256(memoryview(original)[k:k+chunk]).digest()
             for k in range(0, len(original), chunk)]
    table_root = hashlib.sha256(b''.join(table)).hexdigest()
    selected = request_start // chunk
    begin = selected * chunk
    end = min(len(original), begin + chunk)
    assert begin <= request_start and request_start + REQUEST_BYTES <= end
    assert mutant_position < begin or mutant_position >= end
    assert sha256(original) != sha256(original[:mutant_position] +
            bytes([original[mutant_position] ^ 0x04]) + original[mutant_position+1:])
    late = bytearray(original)
    late[mutant_position] ^= 0x04
    late = bytes(late)
    local_target = bytearray(original)
    local_target[request_start] ^= 0x04
    local_target = bytes(local_target)
    def local_valid(payload):
        return hashlib.sha256(payload[begin:end]).digest() == table[selected]
    baseline_digest = sha256(original)
    assert local_valid(original)
    assert local_valid(late) and sha256(late) != baseline_digest
    assert not local_valid(local_target) and sha256(local_target) != baseline_digest
    assert late[request_start:request_start+REQUEST_BYTES] == original[request_start:request_start+REQUEST_BYTES]
    return {
        'chunk_logical_bytes': chunk, 'request_logical_bytes': REQUEST_BYTES,
        'member_logical_bytes': len(original), 'member_original_sha256': baseline_digest,
        'member_late_corrupt_sha256': sha256(late),
        'unchanged_authenticated_table_root': table_root,
        'observed_region': [begin, end], 'mutant_unobserved_byte_offset': mutant_position,
        'clean': {'local_digest': True, 'whole_member_sha256': True},
        'late_mutant': {'local_digest': local_valid(late), 'whole_member_sha256': False,
                       'requested_bytes_unchanged': True},
        'selected_mutant': {'local_digest': local_valid(local_target), 'whole_member_sha256': False},
        'member_bytes_not_observed_by_local_check': len(original) - (end - begin)
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    source = args.manifest.read_bytes()
    meta = json.loads(source)
    logical = meta['pcm_bytes_each']
    assert logical > 0 and logical % max(REGIONS) == 0
    assert set(meta['cases']) == {'mono', 'stereo'}
    for case in meta['cases'].values():
        assert case['wav_bytes'] == logical + 44
        assert case['flac_bytes'] > 0 and len(case['flac_sha256']) == 64
    # Two independent structures; toy buffers, not physical source FLAC.
    patterns = {
        'periodic': (b'PCM16-EXACT-ABCD' * (logical // 16 + 1))[:logical],
        'prng': random.Random(0xFC047).randbytes(logical)
    }
    experiments = []
    for pattern, data in patterns.items():
        assert len(data) == logical
        for chunk in REGIONS:
            x = probe(data, chunk, (logical * 85) // 100, logical // 4)
            x['pattern'] = pattern
            experiments.append(x)
    cost = []
    for size in REGIONS:
        n = (logical + size - 1) // size
        metadata = n * RECORD_BYTES + ROOT_BYTES
        for name, c in sorted(meta['cases'].items()):
            cost.append({
                'flac_case': name, 'source_flac_sha256': c['flac_sha256'],
                'source_flac_bytes': c['flac_bytes'], 'logical_pcm_bytes': logical,
                'region_bytes': size, 'region_count': n,
                'charged_digest_bytes': n * 32,
                'charged_offset_and_length_bytes': n * 16,
                'optimistic_root_bytes': ROOT_BYTES,
                'optimistic_total_stored_overhead_bytes': metadata,
                'optimistic_overhead_percent_of_existing_flac': round(metadata / c['flac_bytes'] * 100, 6),
                'excluded_unmeasured_costs': 'seek checkpoints; FLAC dependency; decoder CPU; authentication tree paths; cold-open; updates/recovery; source custody'
            })
    assert len(experiments) == 6 and len(cost) == 6
    assert all(x['late_mutant']['local_digest'] and not x['late_mutant']['whole_member_sha256']
               and not x['selected_mutant']['local_digest'] for x in experiments)
    assert all(x['optimistic_overhead_percent_of_existing_flac'] < 1
               for x in cost if x['region_bytes'] == 65536)
    assert all(x['optimistic_overhead_percent_of_existing_flac'] > 2
               for x in cost if x['region_bytes'] == 4096 and x['flac_case'] == 'stereo')
    record = {
        'schema': 'cmpct-j24i47-integrity-observation-bound-v1',
        'classification': 'research proof/witness and optimistic metadata cost ONLY',
        'source': {'j24i46_generation_manifest_sha256': sha256(source),
                   'source_reference': '#796 / 2026-10-30 / 32MiB mono and stereo, libsndfile 1.2.2'},
        'theorem_boundary': 'untrusted mutable same-source, no prior full validation or external trusted state; strict fail-on-any-member-physical-corruption',
        'local_integrity_not_global_integrity': experiments,
        'cost_lower_bounds': cost,
        'decision': 'Strict global-corruption equivalent sublinear selective read without an explicit new trust boundary is impossible; chunk digests can only support weaker local integrity',
        'product_evidence': False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'witnesses': len(experiments), 'metadata_cost_rows': len(cost),
                      '64KiB_overhead_percent': {x['flac_case']: x['optimistic_overhead_percent_of_existing_flac'] for x in cost if x['region_bytes'] == 65536},
                      'max_unobserved_bytes': max(x['member_bytes_not_observed_by_local_check'] for x in experiments),
                      'output_sha256': sha256(args.out.read_bytes())}, sort_keys=True))

if __name__ == '__main__':
    main()
