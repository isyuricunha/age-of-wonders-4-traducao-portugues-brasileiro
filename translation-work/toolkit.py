#!/usr/bin/env python3
"""AoW4 manual localization CLI. SPDX-License-Identifier: AGPL-3.0-only."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import platform
import re
import sys
import tempfile
import zipfile

try:
    import native
    import syntax
    from context import ContextIndex
    from storage import Store, digest, json_bytes, normalized, safe
except ImportError as exc:
    print(json.dumps({'error': 'MISSING_DEPENDENCY: restore complete translation-work checkout; ' + str(exc)}), file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parent.parent
SOURCE = 'Language/EN/EN.MO'
RESOURCES = (SOURCE, 'Language/EN/Name.txt', 'Language/EN/Credits.txt')
MANIFEST = 'translation-work/translations/manifest.json'
BUILD = 'translation-work/build-manifest.json'
REPORT = 'translation-work/reports/sync-latest.json'
OUTPUTS = ('Language/PTBR/PTBR.MO', 'Language/PTBR/Name.txt')
READONLY = ('id', 'row', 'source_file', 'key', 'occurrence', 'EN', 'context', 'passthrough')


def load(path):
    return json.loads(path.read_bytes())


def lines(records):
    return ''.join(json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n' for r in records).encode('utf-8')


def batch_catalog(rows):
    return digest(json_bytes([{k: r[k] for k in READONLY} for r in rows]))


def record_id(key, occurrence, duplicate):
    # JSON tuple avoids collisions between key text and occurrence delimiters.
    return SOURCE + '#' + json.dumps([key, occurrence if duplicate else None], ensure_ascii=False, separators=(',', ':'))


def records(catalog, reference=None):
    counts = Counter(k for k, _ in catalog.pairs if k)
    seen = Counter()
    result = []
    contexts = ContextIndex(catalog.pairs, reference)
    for row, (key, value) in enumerate(catalog.pairs):
        if not key:
            continue
        occurrence = seen[key]
        seen[key] += 1
        opaque = native.passthrough(key, value)
        result.append({'id': record_id(key, occurrence, counts[key] > 1), 'row': row, 'source_file': SOURCE,
                       'key': key, 'occurrence': occurrence, 'EN': value, 'PTBR': '',
                       'passthrough': opaque, 'context': contexts.enrich(key, value, native.context(key, value)), 'history': []})
    return result


class Toolkit:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        self.store = Store(self.root)
        retention = self.path('translation-work/.state/retention.json')
        if retention.is_file():
            config = load(retention)
            self.configure_limits(config['max_snapshots'], config['max_mib'])

    def configure_limits(self, count, mib):
        if type(count) is not int or type(mib) is not int or count < 1 or mib < 1:
            raise ValueError('INVALID_RETENTION: positive integer count and MiB required')
        self.store.count, self.store.budget = count, mib * 1024 * 1024

    def configure_storage(self, count, mib):
        self.configure_limits(count, mib)
        with self.store.lock():
            self.store.ready()
            return self.store.commit({'translation-work/.state/retention.json': json_bytes({'max_snapshots': count, 'max_mib': mib})}, label='configure-storage')

    def path(self, relative):
        return safe(self.root, relative)

    def records(self, catalog):
        reference = self.path('translation-work/context-reference.json')
        return records(catalog, load(reference) if reference.is_file() else None)

    def migrate_context(self):
        with self.store.lock():
            manifest, batches, old = self.read()
            expected = dict(self.observed)
            resources, catalog = self.source()
            if manifest['resources'] != {p: digest(v) for p, v in resources.items()}:
                raise ValueError('SOURCE_CHANGED: use sync; context-only migration requires identical original resources')
            expected.update({'EN/' + p: digest(v) for p, v in resources.items()})
            fresh = {r['id']: r for r in self.records(catalog)}
            already_enriched = any('related_characters' in row['context'] or any('identity' in e for e in row['context']['gender_evidence']) for row in old.values())
            if set(fresh) != set(old) or any(any(old[k][f] != fresh[k][f] for f in READONLY if f != 'context') for k in old):
                raise ValueError('SOURCE_CHANGED: context migration cannot alter original values or identity')
            affected = []
            changes = {}
            for name, batch in batches.items():
                dirty = False
                for row in batch:
                    if row['context'] != fresh[row['id']]['context']:
                        if already_enriched:
                            raise ValueError('CONTEXT_ALREADY_MIGRATED: use sync for later evidence changes; existing context cannot bypass review')
                        row['history'].append({'kind': 'context-enrichment', 'previous_context': row['context'],
                            'note': 'Original resources unchanged; legacy PTBR retained without new linguistic approval.'})
                        row['context'] = fresh[row['id']]['context']
                        affected.append(row['id'])
                        dirty = True
                if dirty:
                    changes['translation-work/translations/' + name] = lines(batch)
            if not affected:
                return {'unchanged': True}
            updated = [r for batch in batches.values() for r in batch]
            changes[MANIFEST] = json_bytes(self.make_manifest(resources, updated, batches, manifest['batch_size']))
            changes['translation-work/reports/context-migration.json'] = json_bytes({'source_resources_unchanged': True,
                'previous_generation': manifest['catalog_sha256'], 'affected_ids': affected,
                'translations_changed': 0, 'linguistic_approval': 'none; technical enrichment of already available evidence'})
            return self.store.commit(changes, expected=expected, label='context-migration')

    def read(self):
        self.store.ready()
        manifest_bytes = self.path(MANIFEST).read_bytes()
        manifest = json.loads(manifest_bytes)
        observed = {MANIFEST: digest(manifest_bytes)}
        if manifest.get('schema') != 1 or manifest.get('source_file') != SOURCE:
            raise ValueError('UNSUPPORTED_SCHEMA: source mapping or manifest schema differs')
        batches, all_records = {}, {}
        actual = {p.name for p in self.path('translation-work/translations').glob('batch-*.jsonl')}
        if actual != set(manifest['batches']):
            raise ValueError('BATCH_INVENTORY: missing or unexpected JSONL batch')
        for name, count in manifest['batches'].items():
            if not re.fullmatch(r'batch-\d{4,}\.jsonl', name):
                raise ValueError('UNSAFE_BATCH_NAME')
            relative = 'translation-work/translations/' + name
            raw = self.path(relative).read_bytes()
            observed[relative] = digest(raw)
            rows = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
            if len(rows) != count or count > manifest['batch_size']:
                raise ValueError(f'BATCH_COUNT: {name}')
            batches[name] = rows
            for row in rows:
                if not isinstance(row.get('PTBR'), str) or not isinstance(row.get('EN'), str) or row['id'] in all_records:
                    raise ValueError('INVALID_RECORD: types or duplicate ID')
                all_records[row['id']] = row
        if len(all_records) != manifest['records']:
            raise ValueError('RECORD_COUNT: manifest and batches differ')
        source_fingerprint = digest(json_bytes([{k: r[k] for k in READONLY} for r in sorted(all_records.values(), key=lambda r: r['row'])]))
        if source_fingerprint != manifest['catalog_sha256']:
            raise ValueError('SOURCE_METADATA_CHANGED: restore read-only JSONL fields or use sync')
        if 'index' in manifest:
            if manifest['index'] != {r['id']: name for name, batch in batches.items() for r in batch} or manifest.get('batch_catalog') != {name: batch_catalog(batch) for name, batch in batches.items()}:
                raise ValueError('SOURCE_INDEX_CHANGED: restore accepted manifest/batch membership')
        self.observed = observed
        return manifest, batches, all_records

    def validation_errors(self, row):
        errors = syntax.errors(row['EN'], row['PTBR'])
        if not errors:
            return []
        policy = self.path('translation-work/legacy-rewrite-policy.json')
        if not hasattr(self, '_rewrite_policy'):
            self._rewrite_policy = load(policy) if policy.is_file() else {}
        receipt = self._rewrite_policy.get(row['key'])
        if receipt and receipt['EN_sha256'] == digest(row['EN'].encode('utf-8')) and receipt['PTBR_sha256'] == digest(row['PTBR'].encode('utf-8')) and receipt['diagnostics'] == errors:
            return []
        return errors

    def source_inventory(self, base):
        directory = safe(base, 'Language/EN')
        for path in directory.rglob('*'):
            if path.suffix.lower() in ('.mo', '.txt', '.json', '.csv', '.xml', '.yaml', '.yml') and path.is_file():
                relative = path.relative_to(base).as_posix()
                safe(base, relative)
                if relative not in RESOURCES:
                    raise ValueError(f'UNMANAGED_LOCALIZATION_RESOURCE: {relative}; extend and test the game profile before importing or publishing')

    def source(self, source_root=None, source_file=None):
        base = Path(source_root).resolve() if source_root else self.path('EN')
        self.source_inventory(base)
        result = {}
        for relative in RESOURCES:
            if source_file is not None and relative == SOURCE:
                path = Path(source_file).absolute()
                if path.name != 'EN.MO' or path.is_symlink():
                    raise ValueError('INVALID_SOURCE_FILE: expected original EN.MO, not a symlink or translated catalog')
            else:
                path = safe(base, relative)
            if not path.is_file():
                raise ValueError(f'INCOMPLETE_SOURCE: missing {relative}; expected game root containing Language/EN')
            result[relative] = path.read_bytes()
        if result['Language/EN/Name.txt'].decode('utf-8-sig').strip() != 'English':
            raise ValueError('NOT_ORIGINAL_ENGLISH: unexpected Language/EN/Name.txt')
        catalog = native.parse(result[SOURCE])
        if not any(k.startswith('INTERFACE@') for k, _ in catalog.pairs) or not any(k.startswith('STORY_EVENT@') for k, _ in catalog.pairs):
            raise ValueError('WRONG_GAME: expected AoW4 INTERFACE and STORY_EVENT localization keys')
        return result, catalog

    def make_manifest(self, resources, rows, batches, batch_size=500):
        return {'schema': 1, 'game': 'Age of Wonders 4', 'steam_appid': '1669000', 'source_file': SOURCE,
                'resources': {p: digest(v) for p, v in sorted(resources.items())}, 'batch_size': batch_size,
                'records': len(rows), 'batches': {n: len(r) for n, r in sorted(batches.items())},
                'index': {r['id']: name for name, batch in batches.items() for r in batch},
                'batch_catalog': {name: batch_catalog(batch) for name, batch in batches.items()},
                'catalog_sha256': digest(json_bytes([{k: r[k] for k in READONLY} for r in sorted(rows, key=lambda r: r['row'])])),
                'deployment': {'source': SOURCE, 'output': OUTPUTS[0], 'companion': OUTPUTS[1]},
                'identity': 'native key; opaque duplicate keys additionally scoped by occurrence; no translation reuse for opaque rows',
                'provenance': 'source build 26274772 verified during migration; future source hashes define exact coverage'}

    def extract(self, *, migrate=False, batch_size=500):
        if self.path(MANIFEST).exists():
            raise ValueError('EXISTING_PROGRESS: extract/migrate refuses to overwrite; use sync')
        if not 1 <= batch_size <= 500:
            raise ValueError('BATCH_SIZE: expected 1..500')
        resources, catalog = self.source()
        rows = self.records(catalog)
        legacy = load(self.path('translation-work.json')) if migrate else {}
        imported = 0
        for row in rows:
            old = legacy.get(row['key'])
            if old and not row['passthrough']:
                if old['en'] != row['EN']:
                    raise ValueError(f'LEGACY_SOURCE_MISMATCH: {row["key"]}; migration does not guess')
                row['PTBR'] = old['pt']
                row['history'] = [{'kind': 'legacy-import', 'EN': old['en'], 'PTBR': old.get('pt_old', ''),
                                   'provenance': 'translation-work.json; existing texts retained without linguistic approval'}]
                imported += bool(row['PTBR'])
        batches = {f'batch-{i // batch_size + 1:04d}.jsonl': rows[i:i + batch_size] for i in range(0, len(rows), batch_size)}
        manifest = self.make_manifest(resources, rows, batches, batch_size)
        changes = {'translation-work/translations/' + n: lines(r) for n, r in batches.items()}
        changes[MANIFEST] = json_bytes(manifest)
        changes['translation-work/reports/migration.json'] = json_bytes({'records': len(rows), 'imported': imported,
                   'opaque_passthrough': sum(r['passthrough'] for r in rows), 'legacy_sha256': digest(self.path('translation-work.json').read_bytes()) if migrate else None})
        with self.store.lock():
            return self.store.commit(changes, label='migrate' if migrate else 'extract')

    def fingerprints(self, manifest=None, batches=None):
        if manifest is None:
            manifest, batches, _ = self.read()
        result = {'manifest': digest(normalized(self.path(MANIFEST).read_bytes())),
                'batches': {n: digest(normalized(self.path('translation-work/translations/' + n).read_bytes())) for n in batches},
                'sources': {p: digest(self.path('EN/' + p).read_bytes()) for p in RESOURCES}}
        for path in ('translation-work/toolchain.json', 'translation-work/runtime-support.json'):
            if self.path(path).is_file():
                result[path] = digest(normalized(self.path(path).read_bytes()))
        return result

    def check(self, *, complete=False, parse_source=True):
        self.source_inventory(self.path('EN'))
        if self.path('translation-work/runtime-support.json').is_file():
            from doctor import integrity
            integrity(self)
        manifest, batches, by_id = self.read()
        problems = []
        for path, checksum in manifest['resources'].items():
            if path not in RESOURCES or digest(self.path('EN/' + path).read_bytes()) != checksum:
                problems.append({'path': path, 'error': 'source checksum differs; run sync'})
        if set(manifest['resources']) != set(RESOURCES):
            problems.append({'error': 'source inventory differs'})
        if parse_source:
            _, catalog = self.source()
            source_rows = self.records(catalog)
            if [{k: r[k] for k in READONLY} for r in source_rows] != [{k: r[k] for k in READONLY} for r in sorted(by_id.values(), key=lambda r: r['row'])]:
                problems.append({'error': 'native mapping differs from JSONL'})
        pending = 0
        for row in by_id.values():
            if row['passthrough']:
                if row['PTBR'] or not native.passthrough(row['key'], row['EN']):
                    problems.append({'id': row['id'], 'error': 'opaque rows must remain unmodified passthroughs'})
                continue
            if not row['PTBR']:
                pending += 1
            for error in self.validation_errors(row):
                problems.append({'id': row['id'], 'error': error})
        if complete and pending:
            problems.append({'error': f'INCOMPLETE_TRANSLATION: {pending} pending'})
        return {'records': len(by_id), 'batches': len(batches), 'pending': pending,
                'filled': sum(bool(r['PTBR']) for r in by_id.values()), 'passthrough': sum(r['passthrough'] for r in by_id.values()),
                'errors': problems, 'valid': not problems}

    def status(self):
        manifest, batches, rows = self.read()
        result = {'records': len(rows), 'batches': len(batches), 'filled': sum(bool(r['PTBR']) for r in rows.values()),
                  'pending': sum(not r['PTBR'] and not r['passthrough'] for r in rows.values()),
                  'passthrough': sum(r['passthrough'] for r in rows.values()), 'source_generation': manifest['catalog_sha256'],
                  'storage': self.store.status()}
        if self.path(BUILD).is_file():
            result['output_stale'] = load(self.path(BUILD)).get('inputs') != self.fingerprints(manifest, batches)
        else:
            result['output_stale'] = 'legacy output; no verified build receipt'
        result['next'] = next(({'batch': n, 'id': r['id']} for n, rs in batches.items() for r in rs if not r['PTBR'] and not r['passthrough']), None)
        if self.path(REPORT).is_file():
            report = load(self.path(REPORT))
            result['last_sync'] = {'counts': report['counts'], 'generation': report['generation'],
                                   'stale': report['generation'] != manifest['catalog_sha256']}
        return result

    def apply(self, payload, replace=False):
        with self.store.lock():
            self.store.ready()
            raw = self.path(MANIFEST).read_bytes()
            manifest = json.loads(raw)
            if set(payload) != {'source_generation', 'updates'} or payload['source_generation'] != manifest['catalog_sha256']:
                raise ValueError('STALE_PAYLOAD: expected source_generation and updates from current status')
            if manifest.get('schema') != 1 or manifest.get('source_file') != SOURCE:
                raise ValueError('UNSUPPORTED_SCHEMA')
            expected = {MANIFEST: digest(raw)}
            if 'index' not in manifest:
                manifest, batches, rows = self.read()  # compatible upgrade path
                expected = dict(self.observed)
            else:
                names = set()
                for update in payload['updates']:
                    if not isinstance(update, dict) or set(update) != {'id', 'PTBR'} or update['id'] not in manifest['index']:
                        raise ValueError('INVALID_PAYLOAD: unknown ID or immutable fields')
                    names.add(manifest['index'][update['id']])
                batches, rows = {}, {}
                for name in sorted(names):
                    if not re.fullmatch(r'batch-\d{4,}\.jsonl', name) or name not in manifest['batches']:
                        raise ValueError('SOURCE_INDEX_CHANGED: unsafe or unknown batch')
                    relative = 'translation-work/translations/' + name
                    data = self.path(relative).read_bytes()
                    expected[relative] = digest(data)
                    batch = [json.loads(line) for line in data.decode('utf-8').splitlines()]
                    if len(batch) != manifest['batches'][name] or batch_catalog(batch) != manifest['batch_catalog'].get(name):
                        raise ValueError('SOURCE_METADATA_CHANGED: immutable data differs in affected batch')
                    for row in batch:
                        if manifest['index'].get(row['id']) != name or row['id'] in rows or not isinstance(row.get('PTBR'), str):
                            raise ValueError('SOURCE_INDEX_CHANGED: duplicate or misplaced entry')
                        rows[row['id']] = row
                    batches[name] = batch
            updates, seen = {}, set()
            for update in payload['updates']:
                if set(update) != {'id', 'PTBR'} or update['id'] in seen or update['id'] not in rows:
                    raise ValueError('INVALID_PAYLOAD: unknown/duplicate ID or immutable fields')
                seen.add(update['id'])
                row = rows[update['id']]
                if row['passthrough'] or not isinstance(update['PTBR'], str) or not update['PTBR']:
                    raise ValueError('INVALID_PTBR: opaque, empty or non-string value')
                if row['PTBR'] and row['PTBR'] != update['PTBR'] and not replace:
                    raise ValueError('OVERWRITE_REFUSED: explicit --replace is required')
                errors = self.validation_errors({**row, 'PTBR': update['PTBR']})
                if errors:
                    raise ValueError(f'STRUCTURE: {row["id"]}: {errors}')
                updates[row['id']] = update['PTBR']
            changes = {}
            for name, batch in batches.items():
                dirty = False
                for row in batch:
                    if row['id'] in updates and updates[row['id']] != row['PTBR']:
                        row['history'].append({'kind': 'replace', 'EN': row['EN'], 'PTBR': row['PTBR']})
                        row['PTBR'] = updates[row['id']]
                        dirty = True
                if dirty:
                    path = 'translation-work/translations/' + name
                    changes[path] = lines(batch)
            return self.store.commit(changes, expected=expected, label='apply')

    def plan_sync(self, source_root=None, allow_removals=False, source_file=None):
        manifest, batches, old = self.read()
        self.observed.update({'EN/' + path: digest(self.path('EN/' + path).read_bytes()) for path in RESOURCES})
        resources, catalog = self.source(source_root, source_file)
        candidates = self.records(catalog)
        differences = []
        assignments = {r['id']: name for name, batch in batches.items() for r in batch}
        new_batches = {name: [] for name in batches}
        # Reserve each surviving existing entry before assigning new entries.
        occupancy = Counter(assignments[r['id']] for r in candidates if r['id'] in assignments)
        for row in candidates:
            previous = old.get(row['id'])
            if previous:
                row['history'] = previous['history']
                equal = row['EN'] == previous['EN'] and row['context'] == previous['context'] and row['passthrough'] == previous['passthrough']
                kind = ('moved' if row['row'] != previous['row'] else 'unchanged') if equal else 'modified'
                if equal and not row['passthrough']:
                    row['PTBR'] = previous['PTBR']
                elif not equal:
                    row['history'] = row['history'] + [{'kind': 'source-change', 'EN': previous['EN'], 'PTBR': previous['PTBR'], 'context': previous['context']}]
                name = assignments[row['id']]
            else:
                kind = 'added'
                name = next(reversed(new_batches), 'batch-0001.jsonl')
                if occupancy[name] >= manifest['batch_size']:
                    name = f'batch-{max([int(n[6:-6]) for n in new_batches] or [0]) + 1:04d}.jsonl'
                new_batches.setdefault(name, [])
                occupancy[name] += 1
            new_batches[name].append(row)
            differences.append({'kind': kind, 'id': row['id'], 'batch': name, 'source_file': SOURCE,
                                'previous_EN': previous['EN'] if previous else None, 'EN': row['EN'],
                                'previous_PTBR': previous['PTBR'] if previous else '', 'PTBR': row['PTBR']})
        current_ids = {r['id'] for r in candidates}
        removed = [r for key, r in old.items() if key not in current_ids]
        if removed and not allow_removals:
            raise ValueError(f'REMOVALS_REQUIRE_REVIEW: {len(removed)} entries missing; inspect diff using --allow-removals --dry-run before accepting')
        for row in removed:
            differences.append({'kind': 'removed', 'id': row['id'], 'batch': assignments[row['id']],
                                'source_file': SOURCE, 'previous_EN': row['EN'], 'EN': None, 'previous_PTBR': row['PTBR'], 'PTBR': ''})
        next_manifest = self.make_manifest(resources, candidates, new_batches, manifest['batch_size'])
        report = {'previous_generation': manifest['catalog_sha256'], 'generation': next_manifest['catalog_sha256'],
                  'source_resources': [{'path': p, 'previous_sha256': manifest['resources'][p], 'sha256': digest(v)} for p, v in resources.items()],
                  'counts': dict(Counter(d['kind'] for d in differences)), 'entries': [d for d in differences if d['kind'] != 'unchanged'],
                  'pending_existing': sum(not r['PTBR'] and not r['passthrough'] for r in old.values()),
                  'pending': sum(not r['PTBR'] and not r['passthrough'] for r in candidates),
                  'preserved_translations': sum(d['kind'] in ('unchanged', 'moved') and bool(d['PTBR']) for d in differences),
                  'affected_batches': sorted({d['batch'] for d in differences if d['kind'] != 'unchanged'}),
                  'valid': True, 'next': 'Review changed/new entries and source history; build only when complete.'}
        changes = {'EN/' + p: v for p, v in resources.items()}
        changes.update({'translation-work/translations/' + name: lines(batch) for name, batch in new_batches.items()})
        changes[MANIFEST] = json_bytes(next_manifest)
        if removed:
            changes[f'translation-work/history/removed-{manifest["catalog_sha256"][:16]}-{next_manifest["catalog_sha256"][:16]}.jsonl'] = lines(removed)
        changed = any(self.path(p).read_bytes() != value if self.path(p).is_file() else True for p, value in changes.items())
        if changed:
            changes[REPORT] = json_bytes(report)
            summary = '# Source synchronization\n\n' + json.dumps(report['counts'], ensure_ascii=False) + '\n\n' + report['next'] + '\n'
            changes['translation-work/reports/sync-latest.md'] = summary.encode('utf-8')
        return changes, report, changed

    def sync(self, source_root=None, dry_run=False, allow_removals=False, source_file=None):
        # Lock planning as well as promotion. Read-only dry run creates no lock/state files.
        if dry_run:
            _, report, changed = self.plan_sync(source_root, allow_removals, source_file)
            return {**report, 'changed': changed, 'dry_run': True}
        with self.store.lock():
            changes, report, changed = self.plan_sync(source_root, allow_removals, source_file)
            tx = self.store.commit(changes, expected=self.observed, label='sync') if changed else {'unchanged': True}
            return {'counts': report['counts'], 'pending': report['pending'], **tx}

    def discover(self, explicit=None):
        if explicit:
            candidate = Path(explicit).resolve()
            if candidate == self.root or candidate.is_relative_to(self.root):
                raise ValueError('NOT_GAME_ROOT: expected external game installation root')
            self.source(candidate)
            if not (candidate / 'AOW4.exe').is_file() and not (candidate / 'AOW4').is_file():
                raise ValueError('WRONG_GAME_ROOT: missing AOW4 executable identity')
            return candidate
        candidates = []
        remembered = self.path('translation-work/.state/game-root.json')
        if remembered.is_file():
            candidates.append(Path(load(remembered)['path']))
        steam_roots = [Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)')) / 'Steam',
                       Path.home() / '.local/share/Steam', Path.home() / '.steam/steam']
        if os.name == 'nt':
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as key:
                    steam_roots.append(Path(winreg.QueryValueEx(key, 'SteamPath')[0]))
            except OSError:
                pass
        libraries = set(steam_roots)
        for root in steam_roots:
            vdf = root / 'steamapps/libraryfolders.vdf'
            if vdf.is_file():
                for value in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text(encoding='utf-8')):
                    libraries.add(Path(value.replace('\\\\', '\\')))
        for library in libraries:
            acf = library / 'steamapps/appmanifest_1669000.acf'
            if acf.is_file():
                text = acf.read_text(encoding='utf-8')
                directory = re.search(r'"installdir"\s+"([^"]+)"', text)
                if re.search(r'"appid"\s+"1669000"', text) and directory:
                    candidates.append(safe(library / 'steamapps/common', directory.group(1)))
        valid = set()
        for candidate in candidates:
            try:
                valid.add(self.discover(candidate))
            except (ValueError, OSError):
                continue
        if len(valid) != 1:
            raise ValueError('GAME_NOT_UNIQUE: use python translation-work/toolkit.py update-sources --game-root "/path/to/Age of Wonders 4"')
        return valid.pop()

    def update_sources(self, game_root=None, dry_run=False, allow_removals=False):
        candidate = self.discover(game_root)
        result = self.sync(candidate, dry_run, allow_removals)
        return {'game_root': str(candidate), **result}

    def build(self):
        with self.store.lock():
            result = self.check(complete=True)
            if not result['valid']:
                raise ValueError(f'BUILD_REFUSED: {len(result["errors"])} validation errors; run check')
            manifest, batches, by_id = self.read()
            expected = dict(self.observed)
            mod_root = 'Português Brasileiro - PTBR/'
            for name in ('PTBR.acp', 'thumbnail.png'):
                metadata = mod_root + name
                if not self.path(metadata).is_file():
                    raise ValueError(f'MOD_METADATA_MISSING: restore {metadata}; publication identity must be preserved')
                expected[metadata] = digest(self.path(metadata).read_bytes())
            resources, catalog = self.source()
            expected.update({'EN/' + p: digest(data) for p, data in resources.items()})
            by_row = {r['row']: r for r in by_id.values()}
            pairs = []
            for i, (key, text) in enumerate(catalog.pairs):
                if not key:
                    continue
                row = by_row[i]
                pairs.append((key, text if row['passthrough'] else row['PTBR']))
            # Existing original catalog has no gettext header; PT-BR requires UTF-8 for GNU tools.
            pairs = [('', 'Content-Type: text/plain; charset=UTF-8\n')] + pairs
            mo = native.encode(pairs)
            output = {OUTPUTS[0]: mo, OUTPUTS[1]: 'Português Brasileiro'.encode('utf-8')}
            receipt = {'schema': 1, 'complete': True, 'inputs': self.fingerprints(manifest, batches),
                       'output': {p: digest(v) for p, v in output.items()}, 'records': len(by_id),
                       'filled': result['filled'], 'passthrough': result['passthrough'], 'pending': 0,
                       'native_pairs': len(pairs), 'runtime_test': 'not performed', 'source_build': manifest['provenance']}
            changes = {'PTBR/' + p: v for p, v in output.items()}
            changes.update({mod_root + p: v for p, v in output.items()})
            # Only output files owned by the prior receipt may be removed automatically.
            actual = {p.relative_to(self.path('PTBR')).as_posix() for p in self.path('PTBR').rglob('*') if p.is_file()}
            if actual - set(output):
                raise ValueError('LEGACY_OUTPUT_LAYOUT: archive existing flat PTBR before first build; no automatic deletion')
            changes[BUILD] = json_bytes(receipt)
            return self.store.commit(changes, expected=expected, label='build')

    def verify_output(self):
        self.store.ready()
        receipt = load(self.path(BUILD))
        result = self.check(complete=True, parse_source=False)
        if not result['valid'] or receipt.get('schema') != 1 or receipt.get('complete') is not True:
            raise ValueError('INVALID_BUILD: incomplete or structurally invalid inputs')
        manifest, batches, rows = self.read()
        if receipt.get('inputs') != self.fingerprints(manifest, batches):
            raise ValueError('STALE_BUILD: source/JSONL differs; run explicit build')
        if receipt.get('records') != len(rows) or receipt.get('filled') != result['filled'] or receipt.get('pending') != 0 or receipt.get('passthrough') != result['passthrough']:
            raise ValueError('FORGED_BUILD: recorded counts differ from actual workspace')
        if set(receipt.get('output', {})) != set(OUTPUTS):
            raise ValueError('OUTPUT_INVENTORY: receipt contains unexpected native paths')
        actual = {p.relative_to(self.path('PTBR')).as_posix() for p in self.path('PTBR').rglob('*') if p.is_file()}
        if actual != set(OUTPUTS):
            raise ValueError('OUTPUT_INVENTORY: extra or missing deployable file')
        for path, checksum in receipt['output'].items():
            if digest(self.path('PTBR/' + path).read_bytes()) != checksum:
                raise ValueError(f'OUTPUT_CHECKSUM: {path}')
        return {'valid': True, 'records': len(rows), 'output': receipt['output'], 'generation': digest(json_bytes(receipt['output']))}

    def package(self, destination):
        with self.store.lock():
            return self._package_locked(destination)

    def _package_locked(self, destination):
        self.verify_output()
        destination = Path(destination).resolve()
        if destination.is_relative_to(self.path('PTBR')) or destination.is_relative_to(self.path('EN')):
            raise ValueError('UNSAFE_ARCHIVE_DESTINATION')
        if destination.suffix.lower() != '.zip' or (destination.is_relative_to(self.root) and destination.parent != self.root and not destination.is_relative_to(self.path('translation-work/reports'))):
            raise ValueError('UNSAFE_ARCHIVE_DESTINATION: use a ZIP in repository root, reports, or an explicit external destination')
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
            archive = Path(tmp) / 'PTBR.zip'
            with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                for path in sorted(OUTPUTS):
                    info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    zf.writestr(info, self.path('PTBR/' + path).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(archive) as zf:
                if zf.namelist() != sorted(OUTPUTS) or zf.testzip():
                    raise ValueError('INVALID_ZIP')
            os.replace(archive, destination)
        return {'archive': str(destination), 'sha256': digest(destination.read_bytes()), 'members': sorted(OUTPUTS)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true', help='Output is always JSON; flag retained for automation')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('status', 'resume', 'check', 'build', 'verify-output', 'recover', 'rollback', 'migrate-context'):
        sub.add_parser(name)
    p = sub.add_parser('doctor')
    p.add_argument('--developer', action='store_true', help='Run local Windows checks without claiming ARM64 execution')
    for name in ('extract', 'migrate'):
        p = sub.add_parser(name)
        p.add_argument('--batch-size', type=int, default=500)
    for name in ('sync', 'update-sources', 'diff'):
        p = sub.add_parser(name)
        p.add_argument('--source-root', type=Path)
        p.add_argument('--game-root', type=Path)
        p.add_argument('--source-file', type=Path)
        p.add_argument('--dry-run', action='store_true')
        p.add_argument('--allow-removals', action='store_true')
    p = sub.add_parser('apply')
    p.add_argument('payload', type=Path)
    p.add_argument('--replace', action='store_true')
    p = sub.add_parser('gc')
    p.add_argument('--dry-run', action='store_true')
    p = sub.add_parser('package')
    p.add_argument('--output', type=Path, default=ROOT / 'PTBR.zip')
    p = sub.add_parser('configure-storage')
    p.add_argument('--max-snapshots', type=int, required=True)
    p.add_argument('--max-mib', type=int, required=True)
    args = parser.parse_args(argv)
    try:
        toolkit = Toolkit()
        if args.command in ('status', 'resume'):
            result = toolkit.status()
        elif args.command in ('extract', 'migrate'):
            result = toolkit.extract(migrate=args.command == 'migrate', batch_size=args.batch_size)
        elif args.command == 'apply':
            result = toolkit.apply(load(args.payload), args.replace)
        elif args.command in ('sync', 'update-sources', 'diff'):
            if sum(x is not None for x in (args.source_root, args.game_root, args.source_file)) > 1:
                raise ValueError('Use exactly one source input option')
            if args.command == 'update-sources' and (args.source_root or args.source_file):
                raise ValueError('INVALID_INPUT_OPTION: update-sources takes --game-root; use sync for --source-file or --source-root')
            if args.command == 'update-sources' or args.game_root:
                result = toolkit.update_sources(args.game_root, args.dry_run or args.command == 'diff', args.allow_removals)
            elif args.command == 'diff' and not args.source_root and not args.source_file:
                result = load(toolkit.path(REPORT)) if toolkit.path(REPORT).exists() else {'unchanged': True, 'report': 'no accepted source update yet'}
                if 'generation' in result:
                    result['stale'] = result['generation'] != toolkit.read()[0]['catalog_sha256']
            else:
                result = toolkit.sync(args.source_root, args.dry_run or args.command == 'diff', args.allow_removals, args.source_file)
        elif args.command in ('recover', 'rollback', 'gc'):
            if args.command == 'gc' and args.dry_run:
                result = toolkit.store.gc(True)
            else:
                with toolkit.store.lock():
                    result = toolkit.store.gc(False) if args.command == 'gc' else getattr(toolkit.store, args.command)()
        elif args.command == 'package':
            result = toolkit.package(args.output)
        elif args.command == 'configure-storage':
            result = toolkit.configure_storage(args.max_snapshots, args.max_mib)
        elif args.command == 'doctor':
            from doctor import run
            result = run(toolkit, require_arm64=not args.developer)
        else:
            result = getattr(toolkit, args.command.replace('-', '_'))()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get('valid') is False else 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'error': str(exc), 'type': type(exc).__name__}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
