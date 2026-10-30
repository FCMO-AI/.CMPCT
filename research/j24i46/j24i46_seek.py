#!/usr/bin/env python3
"""J24I46 preregistered, research-only same-FLAC seek vs full-decode oracle.

No CMPCT import, no archive-layout claim, no native product performance credit.
Usage: python j24i46_seek.py generate --out DIR
       python j24i46_seek.py probe --out DIR --case stereo --position 75 --mode seek
       python j24i46_seek.py run --out DIR --cycles 12
"""
import argparse
import hashlib
import io
import json
import os
import platform
import resource
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

PCM_BYTES = 32 * 1024 * 1024
RANGE_BYTES = 4096
CASES = {'stereo': (2, 48_000), 'mono': (1, 44_100)}
POSITIONS = ('25', '75', 'tail')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def generate(out):
    out.mkdir(parents=True, exist_ok=True)
    summary = {'cases': {}, 'numpy': np.__version__, 'soundfile': sf.__version__,
               'libsndfile': sf.__libsndfile_version__, 'pcm_bytes_each': PCM_BYTES}
    for case, (channels, rate) in CASES.items():
        count = PCM_BYTES // (2 * channels)
        rng = np.random.default_rng(0xFC046 if case == 'stereo' else 0xFC146)
        t = np.arange(count, dtype=np.int32)
        if channels == 2:
            delta = rng.integers(-5, 6, size=count, dtype=np.int16)
            left = np.cumsum(delta, dtype=np.int32)
            left = np.clip(left, -20000, 20000).astype(np.int16)
            right = ((t * 23) % 2048 - 1024).astype(np.int16)
            frames = np.column_stack((left, right))
        else:
            delta = rng.integers(-50, 51, size=count, dtype=np.int16)
            walk = np.cumsum(delta, dtype=np.int32)
            frames = (np.mod(walk + 32768, 65536) - 32768).astype(np.int16)
        raw = frames.astype('<i2', copy=False).tobytes()
        assert len(raw) == PCM_BYTES
        wav = out / (case + '.wav')
        flac = out / (case + '.flac')
        with wave.open(str(wav), 'wb') as w:
            w.setparams((channels, 2, rate, 0, 'NONE', 'not compressed'))
            w.writeframesraw(raw)
        sf.write(flac, frames, rate, format='FLAC', subtype='PCM_16')
        with sf.SoundFile(str(flac)) as reader:
            assert reader.channels == channels and reader.frames == count
            actual = reader.buffer_read(count, dtype='int16')
        assert actual == raw, 'FLAC codec does not reconstruct original PCM bytes'
        summary['cases'][case] = {'frames': count, 'channels': channels, 'rate': rate,
             'wav_bytes': wav.stat().st_size, 'flac_bytes': flac.stat().st_size,
             'flac_over_pcm_ratio': flac.stat().st_size / len(raw),
             'wav_sha256': sha256(wav.read_bytes()), 'flac_sha256': sha256(flac.read_bytes()),
             'pcm_sha256': sha256(raw)}
        print('GENERATED', case, summary['cases'][case]['flac_bytes'], flush=True)
        del frames, raw
    (out / 'generation.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    return summary


class CountingReader:
    """Seekable file-like source: counts bytes actually returned to libsndfile."""
    def __init__(self, path):
        self.raw = open(path, 'rb', buffering=0)
        self.bytes_returned = 0
        self.read_calls = 0
        self.seek_calls = 0
    def read(self, n=-1):
        data = self.raw.read(n)
        self.bytes_returned += len(data)
        self.read_calls += 1
        return data
    def readinto(self, dst):
        n = self.raw.readinto(dst)
        self.bytes_returned += (n or 0)
        self.read_calls += 1
        return n
    def seek(self, offset, whence=io.SEEK_SET):
        self.seek_calls += 1
        return self.raw.seek(offset, whence)
    def tell(self):
        return self.raw.tell()
    def close(self):
        self.raw.close()


def probe(out, case, position, mode):
    channels, rate = CASES[case]
    frames_total = PCM_BYTES // (2 * channels)
    frames_selected = RANGE_BYTES // (2 * channels)
    start = {'25': frames_total // 4, '75': 3 * frames_total // 4,
             'tail': frames_total - frames_selected}[position]
    flac = out / (case + '.flac')
    wav = out / (case + '.wav')
    f = CountingReader(flac)
    before_cpu = time.process_time_ns()
    before_wall = time.perf_counter_ns()
    with sf.SoundFile(f) as src:
        assert (src.channels, src.frames, src.samplerate) == (channels, frames_total, rate)
        if mode == 'seek':
            pos = src.seek(start)
            assert pos == start
            got = src.buffer_read(frames_selected, dtype='int16')
            decoded_bytes = len(got)
        elif mode == 'full':
            complete = src.buffer_read(frames_total, dtype='int16')
            decoded_bytes = len(complete)
            lo = start * channels * 2
            got = complete[lo:lo + RANGE_BYTES]
        else:
            raise ValueError(mode)
    elapsed_wall_ns = time.perf_counter_ns() - before_wall
    elapsed_cpu_ns = time.process_time_ns() - before_cpu
    read_bytes = f.bytes_returned
    read_calls = f.read_calls
    seeks = f.seek_calls
    f.close()
    # Source validation deliberately excluded from measured region.
    with wave.open(str(wav), 'rb') as w:
        assert (w.getnchannels(), w.getframerate(), w.getsampwidth()) == (channels, rate, 2)
        w.setpos(start)
        expected = w.readframes(frames_selected)
    assert got == expected, 'range bytes differ from original PCM WAV'
    return {'case': case, 'position': position, 'mode': mode,
        'start_frame': start, 'logical_bytes': len(got), 'logical_sha256': sha256(got),
        'decoded_bytes_returned_to_python': decoded_bytes, 'wall_ns': elapsed_wall_ns,
        'cpu_ns': elapsed_cpu_ns, 'flac_read_bytes': read_bytes,
        'flac_read_calls': read_calls, 'flac_seek_calls': seeks,
        'maxrss_kib_process': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'pid': os.getpid()}


def run(out, cycles):
    summary = json.loads((out / 'generation.json').read_text())
    observations = []
    jsonl = out / "raw-observations.jsonl"
    jsonl.write_text("")  # exact new run; no silent reuse of prior data
    for case in CASES:
        for pos in POSITIONS:
            for cycle in range(cycles):
                # Reverse treatment order at each cycle: no fixed first-party advantage.
                schedule = ['full', 'seek', 'seek', 'full'] if cycle % 2 == 0 else ['seek', 'full', 'full', 'seek']
                for mode in schedule:
                    proc = subprocess.run([sys.executable, __file__, 'probe', '--out', str(out),
                        '--case', case, '--position', pos, '--mode', mode],
                        capture_output=True, text=True, check=True)
                    val = json.loads(proc.stdout.strip())
                    val['cycle'] = cycle
                    val['order_in_cycle'] = len(observations) % 4
                    observations.append(val)
                    with jsonl.open("a") as durable:
                        durable.write(json.dumps(val, sort_keys=True) + "\n")
                        durable.flush()
                print('CYCLE', case, pos, cycle+1, '/', cycles, flush=True)
    summary.update({'source_script_sha256': sha256(Path(__file__).read_bytes()),
         'platform': platform.platform(), 'python': platform.python_version(),
         'cycles': cycles, 'observations': observations})
    (out / 'raw.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n')
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['generate', 'probe', 'run'])
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case', choices=CASES)
    parser.add_argument('--position', choices=POSITIONS)
    parser.add_argument('--mode', choices=('seek','full'))
    parser.add_argument('--cycles', type=int, default=12)
    x = parser.parse_args()
    if x.action == 'generate': data=generate(x.out)
    elif x.action == 'probe': data=probe(x.out,x.case,x.position,x.mode)
    else: data=run(x.out,x.cycles)
    if x.action == 'probe': print(json.dumps(data, sort_keys=True))

if __name__ == '__main__':
    main()
