"""Dirty-file transactions with bounded local recovery. SPDX-License-Identifier: AGPL-3.0-only."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import time
import uuid

LIMIT_COUNT = 10
LIMIT_BYTES = 512 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def normalized(data: bytes) -> bytes:
    return data.replace(b'\r\n', b'\n')


def safe(root: Path, relative: str) -> Path:
    p = PurePosixPath(relative)
    if not relative or p.is_absolute() or any(s in ('..', '.', '') or ':' in s for s in p.parts) or '\\' in relative:
        raise ValueError(f'UNSAFE_PATH: {relative}')
    target = root.joinpath(*p.parts)
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'PATH_ESCAPE: {relative}')
    current = target
    while current != root:
        if current.is_symlink():
            raise ValueError(f'SYMLINK: {relative}')
        current = current.parent
    return target


def atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    try:
        with tmp.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        if os.name != 'nt':
            fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    finally:
        if tmp.exists():
            tmp.unlink()


class Store:
    def __init__(self, root: Path, count=LIMIT_COUNT, budget=LIMIT_BYTES):
        self.root = root.resolve()
        self.state = safe(self.root, 'translation-work/.state')
        self.transactions = self.state / 'transactions'
        self.count = count
        self.budget = budget
        self.locked = False

    @contextlib.contextmanager
    def lock(self):
        self.state.mkdir(parents=True, exist_ok=True)
        with (self.state / 'lock').open('a+b') as stream:
            try:
                if os.fstat(stream.fileno()).st_size == 0:
                    stream.write(b'0')
                    stream.flush()
                stream.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise ValueError('LOCKED: another toolkit operation is active') from exc
            self.locked = True
            try:
                yield
            finally:
                self.locked = False
                stream.seek(0)
                if os.name == 'nt':
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def inventory(self):
        out = []
        if not self.transactions.exists():
            return out
        for directory in sorted(self.transactions.iterdir()):
            safe(self.root, directory.relative_to(self.root).as_posix())
            initial_files = list(directory.iterdir()) if directory.is_dir() else []
            if directory.is_dir() and not (directory / 'receipt.json').exists() and re.fullmatch(r'\d{20}-[a-f0-9]{32}', directory.name) and all(re.fullmatch(r'receipt\.json\.tmp-[a-f0-9]{32}', p.name) and p.is_file() and not p.is_symlink() for p in initial_files):
                out.append((directory, {'id': directory.name, 'status': 'preparing', 'files': []}, 0))
                continue
            if not directory.is_dir() or not (directory / 'receipt.json').is_file():
                raise ValueError(f'CORRUPT_JOURNAL: {directory.name}; inspect before new writes')
            receipt = json.loads((directory / 'receipt.json').read_bytes())
            if receipt.get('id') != directory.name or receipt.get('status') not in ('preparing', 'pending', 'complete', 'rolled-back'):
                raise ValueError('CORRUPT_JOURNAL: invalid transaction ownership/status')
            owned = {'receipt.json'}
            for entry in receipt['files']:
                if not isinstance(entry.get('slot'), int) or not 0 <= entry['slot'] < len(receipt['files']):
                    raise ValueError('CORRUPT_JOURNAL: unsafe blob slot')
                safe(self.root, entry['path'])
                for side in ('old', 'new'):
                    expected = entry[side]
                    blob = directory / side / str(entry['slot'])
                    safe(self.root, blob.relative_to(self.root).as_posix())
                    if expected is not None and (not blob.is_file() or blob.is_symlink() or digest(blob.read_bytes()) != expected):
                        if receipt['status'] != 'preparing':
                            raise ValueError(f'CHECKSUM_MISMATCH: journal {directory.name}/{side}/{entry["slot"]}')
                    if expected is not None:
                        owned.add(side + '/' + str(entry['slot']))
            for item in directory.rglob('*'):
                safe(self.root, item.relative_to(self.root).as_posix())
                if item.is_file() and item.relative_to(directory).as_posix() not in owned:
                    relative = item.relative_to(directory).as_posix()
                    base = re.sub(r'\.tmp-[a-f0-9]{32}$', '', relative)
                    if base == relative or base not in owned:
                        raise ValueError('UNOWNED_JOURNAL_FILE: refusing to prune user-created or unrecorded files')
            size = sum(p.stat().st_size for p in directory.rglob('*') if p.is_file())
            out.append((directory, receipt, size))
        return out

    def ready(self):
        if any(r['status'] in ('pending', 'preparing') for _, r, _ in self.inventory()):
            raise ValueError('RECOVERY_REQUIRED: run toolkit.py recover before any other operation')

    def gc(self, dry_run=True):
        items = self.inventory()
        if any(r['status'] in ('pending', 'preparing') for _, r, _ in items):
            raise ValueError('RECOVERY_REQUIRED: gc cannot prune protected transactions')
        total = sum(s for _, _, s in items)
        selected = []
        for i, (directory, receipt, size) in enumerate(items):
            # Always preserve the newest completed snapshot.
            if len(items) - len(selected) <= self.count and total <= self.budget:
                break
            if i == len(items) - 1:
                raise ValueError('DISK_BUDGET: newest recovery snapshot exceeds retention budget')
            selected.append({'id': receipt['id'], 'bytes': size, 'status': receipt['status']})
            total -= size
        if not dry_run:
            if not self.locked:
                raise ValueError('LOCK_REQUIRED')
            for entry in selected:
                directory = safe(self.root, f'translation-work/.state/transactions/{entry["id"]}')
                shutil.rmtree(directory)
        return {'eligible': selected, 'bytes': sum(i['bytes'] for i in selected), 'dry_run': dry_run}

    def status(self):
        items = self.inventory()
        return {'transactions': len(items), 'protected': sum(r['status'] in ('pending', 'preparing') for _, r, _ in items),
                'bytes': sum(s for _, _, s in items), 'limit_count': self.count, 'limit_bytes': self.budget,
                'reclaimable': self.gc()['bytes'] if not any(r['status'] in ('pending', 'preparing') for _, r, _ in items) else 0}

    def commit(self, changes: dict[str, bytes | None], *, expected=None, label='operation', crash_after=None):
        if not self.locked:
            raise ValueError('LOCK_REQUIRED')
        self.ready()
        changes = {p: value for p, value in changes.items()
                   if (safe(self.root, p).read_bytes() if safe(self.root, p).is_file() else None) != value}
        if not changes:
            return {'unchanged': True, 'files': []}
        if expected:
            for path, checksum in expected.items():
                target = safe(self.root, path)
                got = digest(target.read_bytes()) if target.is_file() else None
                if got != checksum:
                    raise ValueError(f'CONCURRENT_CHANGE: {path}; no changes applied')
        size = sum(len(v or b'') + (safe(self.root, p).stat().st_size if safe(self.root, p).is_file() else 0) for p, v in changes.items())
        if size + 65536 + 1024 * len(changes) > self.budget:
            raise ValueError(f'DISK_BUDGET: transaction needs at least {size + 65536 + 1024 * len(changes)} bytes')
        if shutil.disk_usage(self.root).free < size + 64 * 1024 * 1024:
            raise ValueError('DISK_SPACE: insufficient staging/rollback headroom')
        self.gc(False)
        txid = f'{time.time_ns():020d}-{uuid.uuid4().hex}'
        directory = self.transactions / txid
        directory.mkdir(parents=True)
        receipt = {'id': txid, 'status': 'preparing', 'label': label, 'files': []}
        for slot, (path, value) in enumerate(sorted(changes.items())):
            old = safe(self.root, path).read_bytes() if safe(self.root, path).is_file() else None
            receipt['files'].append({'path': path, 'slot': slot, 'old': digest(old) if old is not None else None,
                                     'new': digest(value) if value is not None else None})
        atomic(directory / 'receipt.json', json_bytes(receipt))
        for entry in receipt['files']:
            path = safe(self.root, entry['path'])
            if entry['old'] is not None:
                atomic(directory / 'old' / str(entry['slot']), path.read_bytes())
            if changes[entry['path']] is not None:
                atomic(directory / 'new' / str(entry['slot']), changes[entry['path']])
        # A crash before this receipt does not mutate any accepted file.
        receipt['status'] = 'pending'
        atomic(directory / 'receipt.json', json_bytes(receipt))
        for n, entry in enumerate(receipt['files']):
            target = safe(self.root, entry['path'])
            current = digest(target.read_bytes()) if target.is_file() else None
            if current != entry['old']:
                raise ValueError('CONCURRENT_CHANGE: recover pending transaction before continuing')
            if entry['new'] is None:
                target.unlink()
            else:
                atomic(target, (directory / 'new' / str(entry['slot'])).read_bytes())
            if crash_after == n + 1:
                raise RuntimeError('SIMULATED_CRASH')
        receipt['status'] = 'complete'
        atomic(directory / 'receipt.json', json_bytes(receipt))
        self.gc(False)
        return {'transaction': txid, 'files': sorted(changes)}

    def recover(self):
        if not self.locked:
            raise ValueError('LOCK_REQUIRED')
        recovered = []
        for directory, receipt, _ in self.inventory():
            if receipt['status'] == 'preparing':
                # No live data was touched. Drop incomplete staging under lock.
                shutil.rmtree(directory)
                recovered.append(receipt['id'])
            elif receipt['status'] == 'pending':
                for entry in receipt['files']:
                    target = safe(self.root, entry['path'])
                    got = digest(target.read_bytes()) if target.is_file() else None
                    if got not in (entry['old'], entry['new']):
                        raise ValueError(f'CONCURRENT_CHANGE: {entry["path"]}; retain journal for manual review')
                for entry in receipt['files']:
                    target = safe(self.root, entry['path'])
                    # Reserved atomic-write names may remain after a process crash.
                    # Inspect only the recorded target's siblings, never a tree-wide cleanup.
                    for temporary in target.parent.glob(target.name + '.tmp-*'):
                        if re.fullmatch(re.escape(target.name) + r'\.tmp-[a-f0-9]{32}', temporary.name):
                            safe(self.root, temporary.relative_to(self.root).as_posix())
                            if temporary.is_file():
                                temporary.unlink()
                    if entry['old'] is None:
                        if target.exists():
                            target.unlink()
                    else:
                        atomic(target, (directory / 'old' / str(entry['slot'])).read_bytes())
                receipt['status'] = 'rolled-back'
                atomic(directory / 'receipt.json', json_bytes(receipt))
                recovered.append(receipt['id'])
        return {'recovered': recovered}

    def rollback(self):
        self.ready()
        items = [(d, r, s) for d, r, s in self.inventory() if r['status'] == 'complete']
        if not items:
            raise ValueError('NO_SNAPSHOT: no retained completed transaction')
        directory, receipt, _ = items[-1]
        changes, expected = {}, {}
        for entry in receipt['files']:
            expected[entry['path']] = entry['new']
            changes[entry['path']] = (directory / 'old' / str(entry['slot'])).read_bytes() if entry['old'] is not None else None
        return self.commit(changes, expected=expected, label='rollback:' + receipt['id'])
