#!/usr/bin/env python3
"""J24P03: actual Linux anonymous-fd -> pathname replacement negative oracle.

This is a kernel-primitive experiment, not an implementation of CMPCT overwrite.
The exact base/intent was preregistered before this instrument existed.
"""
from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

GOOD = b'J24P03-authenticated-good-' * 113
BAD = b'J24P03-unverified-foreign-' * 107
OLD = b'J24P03-existing-old-target-' * 101
AT_EMPTY_PATH = 0x1000
AT_SYMLINK_FOLLOW = 0x400
RENAME_EXCHANGE = 0x2
AT_FDCWD = -100
LIBC = ctypes.CDLL(None, use_errno=True)
LINKAT = LIBC.linkat
LINKAT.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_int)
LINKAT.restype = ctypes.c_int
RENAMEX = getattr(LIBC, 'renameat2', None)
if RENAMEX is not None:
    RENAMEX.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    RENAMEX.restype = ctypes.c_int


def digest(x):
    return hashlib.sha256(x).hexdigest()


def identity(path):
    st = os.stat(path, follow_symlinks=False)
    return [st.st_dev, st.st_ino]


def _link(srcfd, destfd, leaf):
    """Use the real kernel fd->name link, with the documented procfd fallback."""
    name = os.fsencode(leaf)
    ctypes.set_errno(0)
    if LINKAT(srcfd, b'', destfd, name, AT_EMPTY_PATH) == 0:
        return 'AT_EMPTY_PATH'
    first = ctypes.get_errno()
    if first not in (errno.EPERM, errno.ENOENT, errno.EINVAL):
        raise OSError(first, os.strerror(first), leaf)
    ctypes.set_errno(0)
    if LINKAT(AT_FDCWD, os.fsencode(f'/proc/self/fd/{srcfd}'), destfd, name, AT_SYMLINK_FOLLOW) == 0:
        return 'PROC_SELF_FD_FOLLOW'
    failure = ctypes.get_errno()
    raise OSError(failure, os.strerror(failure), leaf)


def _rename_exchange(dirfd):
    if RENAMEX is None:
        raise OSError(errno.ENOSYS, 'renameat2 unavailable')
    ctypes.set_errno(0)
    if RENAMEX(dirfd, b'stage', dirfd, b'target', RENAME_EXCHANGE) != 0:
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e), 'stage')


def _anonymous(fd_parent):
    fd = os.open('.', os.O_TMPFILE | os.O_RDWR, 0o600, dir_fd=fd_parent)
    try:
        assert os.write(fd, GOOD) == len(GOOD)
        assert os.pread(fd, len(GOOD), 0) == GOOD
        return fd
    except BaseException:
        os.close(fd)
        raise


def _child_actor(args):
    stage, quarantine = (Path(p) for p in args.actor)
    os.rename(stage, quarantine)
    with stage.open('xb') as f:
        f.write(BAD)
    assert quarantine.read_bytes() == GOOD
    assert stage.read_bytes() == BAD
    print(json.dumps({'actor_pid': os.getpid(), 'uid': os.geteuid(), 'quarantine_inode': identity(quarantine), 'foreign_inode': identity(stage)}), flush=True)
    return 0


def run_trial(root, method, hostile):
    root.mkdir()
    dfd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    fd = -1
    try:
        fd = _anonymous(dfd)
        st = os.fstat(fd)
        source_id = [st.st_dev, st.st_ino]
        assert st.st_nlink == 0
        target = root / 'target'
        target.write_bytes(OLD)
        old_id = identity(target)
        how = _link(fd, dfd, 'stage')
        assert identity(root / 'stage') == source_id
        assert os.pread(fd, len(GOOD), 0) == GOOD
        actor = None
        foreign_id = None
        if hostile:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--actor', str(root / 'stage'), str(root / 'quarantine')],
                                    capture_output=True, text=True, timeout=10, check=True)
            actor = json.loads(result.stdout.strip())
            foreign_id = identity(root / 'stage')
            assert foreign_id != source_id
            assert identity(root / 'quarantine') == source_id
            assert actor['uid'] == os.geteuid()
        if method == 'os.replace':
            os.replace(root / 'stage', target)
        elif method == 'renameat2_exchange':
            _rename_exchange(dfd)
        else:
            raise AssertionError(method)
        observed = target.read_bytes()
        observed_id = identity(target)
        assert os.pread(fd, len(GOOD), 0) == GOOD
        assert observed == (BAD if hostile else GOOD)
        assert observed_id == (foreign_id if hostile else source_id)
        if hostile:
            assert identity(root / 'quarantine') == source_id
            assert (root / 'quarantine').read_bytes() == GOOD
        if method == 'renameat2_exchange':
            assert (root / 'stage').read_bytes() == OLD
            assert identity(root / 'stage') == old_id
        return {
            'method': method, 'hostile': hostile, 'original_target_sha256': digest(OLD),
            'original_fd_sha256': digest(os.pread(fd, len(GOOD), 0)),
            'published_sha256': digest(observed),
            'published_is_authenticated_inode': observed_id == source_id,
            'source_inode': source_id, 'published_inode': observed_id,
            'attacker_inode': foreign_id, 'stage_link_mode': how, 'actor': actor,
            'decision': 'FOREIGN_INODE_PUBLISHED' if hostile else 'AUTHENTIC_INODE_PUBLISHED'
        }
    finally:
        if fd >= 0: os.close(fd)
        os.close(dfd)


def run_noclobber(root, occupied):
    root.mkdir()
    dfd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    fd = _anonymous(dfd)
    try:
        st = os.fstat(fd)
        original_id = [st.st_dev, st.st_ino]
        target = root / 'target'
        if occupied:
            target.write_bytes(OLD)
            prior = identity(target)
            try:
                _link(fd, dfd, 'target')
            except OSError as exc:
                assert exc.errno == errno.EEXIST, exc
            else:
                raise AssertionError('occupied linkat unexpectedly succeeded')
            assert target.read_bytes() == OLD and identity(target) == prior
            return {'occupied': True, 'decision': 'EEXIST_PRESERVED', 'target_sha256': digest(target.read_bytes()), 'target_inode': prior}
        how = _link(fd, dfd, 'target')
        assert target.read_bytes() == GOOD and identity(target) == original_id
        return {'occupied': False, 'decision': 'AUTHENTIC_NO_CLOBBER', 'target_sha256': digest(target.read_bytes()), 'target_inode': original_id, 'link_mode': how}
    finally:
        os.close(fd)
        os.close(dfd)


def direct_fd_rename(root):
    root.mkdir()
    dfd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    fd = _anonymous(dfd)
    try:
        target = root / 'target'
        target.write_bytes(OLD)
        try:
            os.replace(f'/proc/self/fd/{fd}', target)
        except OSError as exc:
            assert target.read_bytes() == OLD
            return {'decision': 'DIRECT_PROC_RENAME_REJECTED', 'errno': exc.errno, 'errno_name': errno.errorcode.get(exc.errno, 'UNKNOWN')}
        return {'decision': 'DIRECT_PROC_RENAME_SUCCEEDED', 'published_is_authenticated_inode': identity(target) == [os.fstat(fd).st_dev, os.fstat(fd).st_ino]}
    finally:
        os.close(fd)
        os.close(dfd)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--actor', nargs=2, metavar=('STAGE','QUARANTINE'))
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    if args.actor:
        return _child_actor(args)
    if args.output is None: p.error('required --output')
    assert sys.platform.startswith('linux') and hasattr(os,'O_TMPFILE')
    assert os.geteuid() != 0, 'hosted court must use nonroot permissions'
    record={'schema': 'j24p03-linux-existing-replace-v1', 'source': {
        'euid': os.geteuid(), 'platform': platform.platform(), 'python': platform.python_version(),
        'git_head': os.environ.get('EVIDENCE_HEAD'),
    }, 'payload_sha256': {'good':digest(GOOD),'bad':digest(BAD),'old':digest(OLD)}, 'trials': []}
    with tempfile.TemporaryDirectory(prefix='cmpct-j24p03-') as td:
        root=Path(td)
        for method in ('os.replace', 'renameat2_exchange'):
            for attack in (False, True):
                item=run_trial(root / (method.replace('.','_')+'-'+str(int(attack))),method,attack)
                record['trials'].append(item)
                print('J24P03_TRIAL='+json.dumps(item,sort_keys=True),flush=True)
        for occupied in (False,True):
            item=run_noclobber(root / ('link-'+str(int(occupied))),occupied)
            record['trials'].append(item)
            print('J24P03_CONTROL='+json.dumps(item,sort_keys=True),flush=True)
        item=direct_fd_rename(root / 'direct-proc-rename')
        record['trials'].append(item)
        print('J24P03_DIRECT='+json.dumps(item,sort_keys=True),flush=True)
    observations=[x for x in record['trials'] if x.get('hostile') is True]
    controls=[x for x in record['trials'] if x.get('hostile') is False]
    assert len(observations)==2 and len(controls)==2
    assert all(x['decision']=='FOREIGN_INODE_PUBLISHED' for x in observations)
    assert all(x['decision']=='AUTHENTIC_INODE_PUBLISHED' for x in controls)
    assert [x['decision'] for x in record['trials'][4:6]]==['AUTHENTIC_NO_CLOBBER','EEXIST_PRESERVED']
    record['decision']='RETIRE_VISIBLE_STAGE_PLUS_RENAME_EXISTING_TARGET_UNDER_HOSTILE_SAME_UID_WRITER'
    record['nonclaims']=['no global impossibility theorem', 'not installed CMPCT Reader product',
                          'no cross-platform result', 'no proof against unobserved pathname mutations',
                          'no performance or release credit']
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('J24P03_DECISION='+record['decision'],flush=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
