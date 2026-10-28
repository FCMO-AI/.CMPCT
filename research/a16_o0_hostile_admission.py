#!/usr/bin/env python3
"""A16 science-only hostile-envelope refusal court (not CMPCT product parser)."""
import json
import struct
import subprocess
import a16_o0_sharing_run_court as m

def run():
    data,_,_=m.encode(m.source(20261028,'prefix12'),'segref')
    def change(offset,raw):
        b=bytearray(data)
        b[offset:offset+len(raw)]=raw
        return bytes(b)
    mutants={
        'magic':change(0,b'xxxx'),
        'physical_sha':change(m.H.size+8,bytes([data[m.H.size+8]^1])),
        'compressed_frame':change(m.H.size+m.VAR.size,bytes([data[m.H.size+m.VAR.size]^1])),
        'owner_size':change(m.H.size,b'\xff\xff\xff\x7f'),
        'truncate':data[:-1],
        'trailing':data+b'X',
    }
    decisions={}
    for label,b in mutants.items():
        try: m.independent_parse(b)
        except (ValueError,struct.error,subprocess.CalledProcessError):
            decisions[label]='REJECTED'
        else: decisions[label]='ACCEPTED'
    print(json.dumps(decisions,sort_keys=True))
    if any(x!='REJECTED' for x in decisions.values()):
        raise AssertionError('invalid envelope was accepted')
if __name__=='__main__':run()
