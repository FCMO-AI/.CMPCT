#!/usr/bin/env python3
"""O211: source-exact authentic mixed sparse+Deflate ZIP64 export CPU attribution.
Preregistered in docs/v031-research/2026-10-26-o211-mixed-zip64-cost-prereg.md.
No production Reader patch; stdlib writer timing is research instrumentation only.
"""
from __future__ import annotations
import argparse, hashlib, json, os, platform, statistics, subprocess, sys, time
import traceback, zipfile
from pathlib import Path

MiB = 1 << 20
GiB = 1 << 30
TOTAL = 4 * GiB
N = 48
SRC_TIME_NS = 946684800000000000

def digest_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(4 * MiB), b''):
            h.update(block)
    return h.hexdigest()

def custody():
    root = Path(os.environ['GITHUB_WORKSPACE']).resolve()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    assert head == os.environ['EVIDENCE_HEAD'], (head, os.environ['EVIDENCE_HEAD'])
    import cmpct.reader, cmpct.builder
    found = {}
    for label, mod in (('reader', cmpct.reader), ('builder', cmpct.builder)):
        src = root / 'src' / 'cmpct' / (label + '.py')
        active = Path(mod.__file__).resolve()
        clean = lambda b: b.replace(b'\r\n', b'\n')
        assert active != src.resolve() and clean(active.read_bytes()) == clean(src.read_bytes()), label
        found[label] = hashlib.sha256(clean(active.read_bytes())).hexdigest()
    return {'git_head': head, 'installed_module_sha256': found}

def make_sparse(path):
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.ftruncate(fd, TOTAL)
        for i in range(4096):
            mark = hashlib.blake2s(i.to_bytes(4,'little')).digest() * 128
            assert os.pwrite(fd, mark, i * MiB) == 4096
    finally:
        os.close(fd)
    st = path.stat()
    assert st.st_size == TOTAL and st.st_blocks * 512 <= 64 * MiB
    fd = os.open(path, os.O_RDONLY)
    count, pos = 0, 0
    try:
        while pos < TOTAL:
            try:
                begin = os.lseek(fd, pos, os.SEEK_DATA)
            except OSError as e:
                if e.errno == 6:
                    break
                raise
            end = os.lseek(fd, begin, os.SEEK_HOLE)
            assert pos <= begin < end <= TOTAL
            count += 1
            pos = end
    finally:
        os.close(fd)
    assert count >= 2048, count
    return {'physical_extents': count, 'allocated_bytes': st.st_blocks * 512}

def data_for(i):
    # Two independent deterministic structural regimes, not a benchmark identity detector.
    seed = hashlib.sha256(b'cmpct-o211-' + i.to_bytes(4,'little')).digest()
    if i % 3:
        return hashlib.shake_256(seed).digest(MiB)
    tile = hashlib.shake_256(seed).digest(8192)
    return (tile * 128)[:MiB]

def create(workdir, receipt):
    from cmpct.builder import Builder
    from cmpct.reader import CMPCT
    from cmpct.codec import S_SPARSE, S_BLOB, CODEC_DEFLATE
    root = workdir / 'input'; root.mkdir(parents=True, exist_ok=True)
    sparse = root / 'sparse.bin'
    receipt['sparse_physical'] = make_sparse(sparse)
    source_sha = digest_file(sparse)
    provenance_zip = root / 'deflate-provenance.zip'
    small = {}
    with zipfile.ZipFile(provenance_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as z:
        for i in range(N):
            name = f'member-{i:03d}.bin'
            data = data_for(i)
            (root / name).write_bytes(data)
            z.writestr(name, data)
            small[name] = hashlib.sha256(data).hexdigest()
    archive = workdir / 'mixed.cmpct'
    t, cpu = time.perf_counter(), time.process_time()
    Builder(root, workers=1).build(archive)
    receipt['create_wall_s'] = time.perf_counter() - t
    receipt['create_cpu_s'] = time.process_time() - cpu
    selected = []
    with CMPCT(archive) as reader:
        s = reader.by['sparse.bin']
        assert s[4] == TOTAL and s[6][0] == S_SPARSE and len(s[6][1]) >= 2048
        for name in small:
            row = reader.by[name]
            if row[6][0] == S_BLOB and reader.blobs[row[6][1]][3] == CODEC_DEFLATE:
                selected.append(name)
        assert len(selected) >= 16, ('insufficient inherited Deflate', len(selected))
        assert reader.read_range('sparse.bin', 0, 4096) == sparse.open('rb').read(4096)
        for name in selected[:4]:
            assert hashlib.sha256(reader.read(name)).hexdigest() == small[name]
    manifest = {
        'archive_sha256': digest_file(archive),
        'archive_bytes': archive.stat().st_size,
        'sparse_sha256': source_sha,
        'sparse_size': TOTAL, 'small_sha256': small,
        'inherited_deflate': selected,
        'source_zip_bytes': provenance_zip.stat().st_size,
        'builder': receipt['source'],
        'representation': {'sparse_extents': len(s[6][1]), 'deflate_members': len(selected)}
    }
    (workdir / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    receipt['manifest'] = {k: manifest[k] for k in ('archive_sha256','archive_bytes','source_zip_bytes','representation')}
    receipt['verdict'] = 'GENUINE_BUILDER_MIXED_R24_SOURCE_CREATED'

def peak_rss():
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024

def consume(workdir, receipt):
    from cmpct.reader import CMPCT
    from cmpct.codec import S_BLOB, CODEC_DEFLATE
    manifest = json.loads((workdir / 'manifest.json').read_text())
    assert manifest['builder']['git_head'] == receipt['source']['git_head']
    archive = workdir / 'mixed.cmpct'
    assert digest_file(archive) == manifest['archive_sha256']
    selected = set(manifest['inherited_deflate'])
    wall_samples, cpu_samples, timed_records = [], [], []
    zip_hashes = []
    # One uninstrumented and three measured exports. Same input and stdout clock boundaries.
    for trial in range(4):
        profile = trial != 0
        writer_cpu = {}
        original = zipfile._ZipWriteFile.write
        def timed_write(self, data):
            t = time.process_time_ns()
            try:
                return original(self, data)
            finally:
                key = self._zinfo.filename
                writer_cpu[key] = writer_cpu.get(key, 0) + time.process_time_ns() - t
        out = workdir / ('export-%d.zip' % trial)
        try:
            if profile:
                zipfile._ZipWriteFile.write = timed_write
            t, cpu = time.perf_counter(), time.process_time()
            with CMPCT(archive) as reader:
                for name in selected:
                    row = reader.by[name]
                    assert row[6][0] == S_BLOB and reader.blobs[row[6][1]][3] == CODEC_DEFLATE
                reader.export_zip(out, level=6)
            wall, elapsed_cpu = time.perf_counter() - t, time.process_time() - cpu
        finally:
            zipfile._ZipWriteFile.write = original
        wall_samples.append(wall)
        cpu_samples.append(elapsed_cpu)
        zip_hashes.append(digest_file(out))
        stat = {'trial':trial, 'instrumented':profile, 'export_wall_s':wall,
                'export_cpu_s':elapsed_cpu, 'zip_bytes':out.stat().st_size,
                'zip_sha256':zip_hashes[-1], 'peak_rss_bytes':peak_rss()}
        if profile:
            small_cpu = sum(writer_cpu.get(name,0) for name in selected) / 1e9
            all_cpu = sum(writer_cpu.values()) / 1e9
            stat.update({'selected_writer_cpu_s': small_cpu,
                'all_member_write_cpu_s': all_cpu,
                'selected_writer_fraction_total_cpu': small_cpu / elapsed_cpu,
                'selected_member_count':len(selected),
                'write_call_member_count':len(writer_cpu)})
            assert 0 <= small_cpu <= all_cpu <= elapsed_cpu * 1.02
            timed_records.append(stat)
        receipt.setdefault('trials',[]).append(stat)
    assert len(set(zip_hashes)) == 1, 'zip output differs across runs'
    out = workdir / 'export-3.zip'
    with zipfile.ZipFile(out) as z:
        assert len(z.namelist()) == N + 2, (len(z.namelist()), N + 2)
        assert z.getinfo('sparse.bin').file_size == TOTAL
        h = hashlib.sha256(); logical = 0
        with z.open('sparse.bin') as f:
            for block in iter(lambda:f.read(4*MiB),b''):
                h.update(block); logical += len(block)
        assert logical == TOTAL and h.hexdigest() == manifest['sparse_sha256']
        for name, expected in manifest['small_sha256'].items():
            with z.open(name) as f:
                assert hashlib.sha256(f.read()).hexdigest() == expected
    fractions = [x['selected_writer_fraction_total_cpu'] for x in timed_records]
    receipt['decision'] = (
        'MIXED_64MIB_REGIME_OPTIMISTIC_WRITE_CPU_CEILING_BELOW_5_PERCENT'
        if max(fractions) < .05 else
        'MIXED_64MIB_REGIME_ELIGIBLE_FOR_OWNER_CONTROLLED_SAME_ARCHIVE_AB')
    receipt['median_selected_cpu_fraction'] = statistics.median(fractions)
    receipt['all_profiled_selected_cpu_fractions'] = fractions
    receipt['independent_zip_readback'] = {'sparse_4gib_sha_pass':True,
        'all_small_sha_pass':True, 'full_zip_crc_pass':True,
        'cross_export_binary_identity':True}
    receipt['verdict'] = 'AUTHENTIC_MIXED_ZIP64_COST_ATTRIBUTION_COMPLETE'
    # Not a product win or a proved full CPU saving; the write timing is an optimistic bound.

def main():
    a = argparse.ArgumentParser()
    a.add_argument('--mode', choices=['build','consume'], required=True)
    a.add_argument('--workdir',type=Path,required=True)
    a.add_argument('--out',type=Path,required=True)
    args = a.parse_args()
    record = {'schema':'O211-mixed-zip64-attribution-v1','mode':args.mode,
              'host':platform.platform(), 'python':sys.version,
              'github_event_sha':os.environ.get('GITHUB_SHA'),
              'verdict':'INCOMPLETE'}
    code = 0
    try:
        args.workdir.mkdir(parents=True, exist_ok=True)
        record['source'] = custody()
        if args.mode == 'build': create(args.workdir,record)
        else: consume(args.workdir,record)
    except BaseException as exc:
        code = 1
        record['verdict'] = 'FAILED_OR_INCONCLUSIVE_NO_SCIENTIFIC_CREDIT'
        record['exception'] = type(exc).__name__+': '+str(exc)
        record['traceback'] = traceback.format_exc(limit=12)
    finally:
        record['peak_rss_bytes'] = peak_rss()
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
        print('O211_VERDICT', record['verdict'],'O211_DECISION',record.get('decision'))
    return code

if __name__ == '__main__':
    raise SystemExit(main())
