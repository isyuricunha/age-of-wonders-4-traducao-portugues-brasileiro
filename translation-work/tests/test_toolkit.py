"""Offline safety and native-format regression tests. AGPL-3.0-only."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import time
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native
import syntax
from storage import Store, digest, json_bytes, normalized
from toolkit import Toolkit, SOURCE, MANIFEST, RESOURCES, BUILD, lines


def fixture(root, count=4):
    pairs = [('INTERFACE@TITLE@NAME', 'Realm {name}'), ('STORY_EVENT@1@BODY', 'Welcome [b]{hero}[/b]')]
    pairs += [(f'TEST@{i:06d}@NAME', f'Word {i}') for i in range(count - 2)]
    pairs += [('@' * 20, '@' * 4), ('@' * 20, '@' * 6)]
    path = root / 'EN' / SOURCE
    path.parent.mkdir(parents=True)
    path.write_bytes(native.encode(pairs))
    (path.parent / 'Name.txt').write_bytes(b'English')
    (path.parent / 'Credits.txt').write_bytes(b'Original credits\r\n')
    mod = root / 'Português Brasileiro - PTBR'
    mod.mkdir()
    (mod / 'PTBR.acp').write_bytes(b'fixture publication identity')
    (mod / 'thumbnail.png').write_bytes(b'fixture thumbnail')
    return pairs


def fill(tool):
    manifest, _, rows = tool.read()
    return tool.apply({'source_generation': manifest['catalog_sha256'],
                       'updates': [{'id': r['id'], 'PTBR': r['EN']} for r in rows.values() if not r['passthrough']]})


class NativeTests(unittest.TestCase):
    def test_binary_roundtrip_preserves_opaque_duplicates(self):
        pairs = [('INTERFACE@A', 'Ação\n\t"á"'), ('@@', '@@@'), ('@@', '@@@@')]
        data = native.encode(pairs)
        catalog = native.parse(data)
        self.assertEqual(catalog.pairs, tuple(pairs))
        self.assertEqual(native.encode(pairs, catalog), data)
        self.assertEqual(native.parse(native.encode(catalog.pairs)).pairs, catalog.pairs)
        # Independent big-endian fixture: change numeric fields, retaining strings.
        fields = struct.unpack('<7I', data[:28])
        big = bytearray(data)
        struct.pack_into('>7I', big, 0, *fields)
        for table in (fields[3], fields[4]):
            for i in range(fields[2]):
                length, offset = struct.unpack_from('<2I', data, table + i * 8)
                struct.pack_into('>2I', big, table + i * 8, length, offset)
        parsed_big = native.parse(bytes(big))
        self.assertEqual(parsed_big.pairs, tuple(pairs))
        self.assertEqual(native.encode(pairs, parsed_big), bytes(big))

    def test_truncated_encoding_revision_and_duplicate_rejection(self):
        data = native.encode([('key', 'value')])
        bad = bytearray(data)
        struct.pack_into('<I', bad, 4, 1)
        fixtures = [data[:20], data[:-1], bytes(bad), data.replace(b'value', b'\xffalue')]
        for item in fixtures:
            with self.assertRaises(native.FormatError):
                native.parse(item)
        with self.assertRaises(native.FormatError):
            native.encode([('x', 'one'), ('x', 'two')])

    def test_context_is_evidence_not_gender_guess(self):
        c = native.context('Speaker_Jessica', 'I am tired.')
        self.assertEqual(c['speaker'], 'unknown')
        self.assertIn('name alone', c['gender_evidence'][0]['role'])
        for key in ('ScriptJessica@line', 'Speaker_Daniel'):
            self.assertTrue(native.context(key, 'He is tired')['gender_evidence'])
        c = native.context('AFFINITY@HERO_FEMALE_FIRSTNAME_01@NAME', 'Jessica')
        self.assertEqual(c['gender_evidence'][0]['value'], 'FEMALE')
        self.assertEqual(c['referent'], 'unknown')
        self.assertEqual(native.context('STORY@1', '{Player.Name} is tired')['referent'], 'dynamic or unknown')

    def test_protected_tokens_and_nesting(self):
        self.assertFalse(syntax.errors('[b]{x}[/b] {y}', '{y} [b]{x}[/b]'))
        for pt in ('[b]{x}[/b]', '[b]{x} {x}[/b] {y}', '[b]{x}[i]{y}[/b][/i]'):
            self.assertTrue(syntax.errors('[b]{x}[/b] {y}', pt))
        self.assertTrue(syntax.errors('{thing}', '{thingElse}'))
        self.assertFalse(syntax.errors('<<m:Entity>>', ''))  # pending allowed
        self.assertFalse(syntax.errors('<<o:Hero>> {Hero.Name}', '{Hero.Name}'))

    def test_selector_identity_arity_and_native_gender_markers(self):
        self.assertFalse(syntax.errors('<<EventHero{Brother/Sister}>>', '<<EventHero{Irmão/Irmã}>>'))
        self.assertTrue(syntax.errors('<<EventHero{Brother/Sister}>>', '<<PlayerLeader{Irmão/Irmã}>>'))
        self.assertTrue(syntax.errors('<<EventHero{Brother/Sister}>>', '<<EventHero{Irmão}>>'))
        self.assertFalse(syntax.errors('Name^F', 'Nome^F'))
        self.assertTrue(syntax.errors('Name^F', 'Nome^M'))
        self.assertTrue(syntax.errors('Name^F', 'Nome^unknown'))
        self.assertFalse(syntax.errors('Heavy^a', 'Pesado^z'))
        self.assertTrue(syntax.errors('<<m{GLOBAL.UnitConcept.Hyperlink}>>', '<<m{GLOBAL.Other.Hyperlink}>>'))


class ToolkitTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pairs = fixture(self.root)
        self.tool = Toolkit(self.root)
        self.tool.extract(batch_size=2)

    def tearDown(self):
        self.tmp.cleanup()

    def test_extraction_manifest_duplicates_and_refusal(self):
        manifest, batches, rows = self.tool.read()
        self.assertEqual(len(rows), len(self.pairs))
        self.assertEqual(len(batches), 3)
        self.assertTrue(all(len(b) == 2 for b in batches.values()))
        self.assertTrue(self.tool.check()['valid'])
        self.assertEqual(self.tool.status()['pending'], 4)
        with self.assertRaisesRegex(ValueError, 'EXISTING_PROGRESS'):
            self.tool.extract()

    def test_apply_dirty_files_only_idempotence_and_safety(self):
        manifest, batches, rows = self.tool.read()
        chosen = next(r for r in rows.values() if not r['passthrough'])
        before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in (self.root / 'translation-work/translations').iterdir()}
        payload = {'source_generation': manifest['catalog_sha256'], 'updates': [{'id': chosen['id'], 'PTBR': chosen['EN']}]}
        result = self.tool.apply(payload)
        self.assertEqual(len(result['files']), 1)
        for name, (raw, mtime) in before.items():
            path = self.root / 'translation-work/translations' / name
            if path.relative_to(self.root).as_posix() not in result['files']:
                self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), (raw, mtime))
        self.assertTrue(self.tool.apply(payload)['unchanged'])
        for mutate in (lambda p: p.update(source_generation='bad'),
                       lambda p: p['updates'].append(p['updates'][0]),
                       lambda p: p['updates'][0].update(EN='forged'),
                       lambda p: p['updates'][0].update(PTBR='Missing variable')):
            bad = copy.deepcopy(payload)
            mutate(bad)
            with self.assertRaises(ValueError):
                self.tool.apply(bad)

    def test_partial_progress_cannot_change_output_or_build(self):
        output = self.root / 'PTBR/old.MO'
        output.parent.mkdir()
        output.write_bytes(b'last valid output')
        with self.assertRaisesRegex(ValueError, 'BUILD_REFUSED'):
            self.tool.build()
        self.assertEqual(output.read_bytes(), b'last valid output')

    def test_complete_build_packaging_and_tampering(self):
        fill(self.tool)
        self.tool.build()
        self.assertTrue(self.tool.verify_output()['valid'])
        for destination in (self.root / 'README.md', self.root / 'translation-work/translations/overwrite.zip', self.root / 'EN/overwrite.zip'):
            with self.assertRaisesRegex(ValueError, 'UNSAFE_ARCHIVE_DESTINATION'):
                self.tool.package(destination)
        archive = self.root / 'PTBR.zip'
        self.tool.package(archive)
        with zipfile.ZipFile(archive) as zf:
            self.assertEqual(zf.namelist(), ['Language/PTBR/Name.txt', 'Language/PTBR/PTBR.MO'])
            self.assertTrue(all(member.create_system == 3 for member in zf.infolist()))
            actual = native.parse(zf.read('Language/PTBR/PTBR.MO'))
            self.assertEqual(actual.pairs[1:], tuple(self.pairs))
        path = self.root / 'PTBR/Language/PTBR/PTBR.MO'
        original = path.read_bytes()
        path.write_bytes(original + b'tamper')
        with self.assertRaisesRegex(ValueError, 'OUTPUT_CHECKSUM'):
            self.tool.verify_output()
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'OUTPUT_INVENTORY'):
            self.tool.verify_output()
        path.write_bytes(original)
        (path.parent / 'LICENSE').write_bytes(b'not a native game asset')
        with self.assertRaisesRegex(ValueError, 'OUTPUT_INVENTORY'):
            self.tool.package(self.root / 'refused.zip')
        self.assertFalse((self.root / 'refused.zip').exists())

    def test_build_updates_mod_languages_and_preserves_identity(self):
        fill(self.tool)
        self.tool.build()
        mod = self.root / 'Português Brasileiro - PTBR'
        metadata = {name: (mod / name).read_bytes() for name in ('PTBR.acp', 'thumbnail.png')}
        manifest, _, rows = self.tool.read()
        row = next(r for r in rows.values() if r['EN'] == 'Realm {name}')
        self.tool.apply({'source_generation': manifest['catalog_sha256'],
                         'updates': [{'id': row['id'], 'PTBR': 'Reino {name}'}]}, replace=True)
        old = (mod / 'Language/PTBR/PTBR.MO').read_bytes()
        self.tool.build()
        self.assertNotEqual(old, (mod / 'Language/PTBR/PTBR.MO').read_bytes())
        for name in ('PTBR.MO', 'Name.txt'):
            self.assertEqual((mod / 'Language/PTBR' / name).read_bytes(),
                             (self.root / 'PTBR/Language/PTBR' / name).read_bytes())
        for name, data in metadata.items():
            self.assertEqual((mod / name).read_bytes(), data)
        (mod / 'PTBR.acp').unlink()
        with self.assertRaisesRegex(ValueError, 'MOD_METADATA_MISSING'):
            self.tool.build()
        self.assertEqual((mod / 'Language/PTBR/PTBR.MO').read_bytes(),
                         (self.root / 'PTBR/Language/PTBR/PTBR.MO').read_bytes())

    def test_forged_complete_flag_and_stale_workspace(self):
        fill(self.tool)
        self.tool.build()
        manifest, batches, rows = self.tool.read()
        name = next(iter(batches))
        batches[name][0]['PTBR'] = ''
        (self.root / 'translation-work/translations' / name).write_bytes(lines(batches[name]))
        with self.assertRaisesRegex(ValueError, 'INVALID_BUILD'):
            self.tool.verify_output()

    def test_sync_diff_preserves_translations_batch_assignments_and_history(self):
        fill(self.tool)
        previous_manifest, previous_batches, old = self.tool.read()
        with tempfile.TemporaryDirectory() as tmp:
            external = Path(tmp)
            fixture(external)
            path = external / 'EN' / SOURCE
            changed = list(reversed(self.pairs))
            changed[0:0] = [('TEST@NEW@NAME', 'New')]
            changed = [(k, 'Changed {name}' if k.startswith('INTERFACE@') else v) for k, v in changed]
            path.write_bytes(native.encode(changed))
            output_before = list((self.root / 'PTBR').rglob('*')) if (self.root / 'PTBR').exists() else []
            readonly = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob('*') if p.is_file()}
            report = self.tool.sync(external / 'EN', dry_run=True)
            self.assertEqual(report['counts']['modified'], 3)  # changed interface + opaque occurrences reordered
            self.assertEqual(report['counts']['added'], 1)
            for p, state in readonly.items():
                self.assertEqual((p.read_bytes(), p.stat().st_mtime_ns), state)
            self.tool.sync(external / 'EN')
        manifest, batches, rows = self.tool.read()
        self.assertTrue(all(len(batch) <= 2 for batch in batches.values()))
        for name, batch in previous_batches.items():
            for r in batch:
                self.assertIn(r['id'], {r['id'] for r in batches[name]})
        modified = next(r for r in rows.values() if r['key'].startswith('INTERFACE@'))
        self.assertEqual(modified['PTBR'], '')
        self.assertEqual(modified['history'][-1]['PTBR'], old[modified['id']]['PTBR'])
        self.assertEqual(list((self.root / 'PTBR').rglob('*')) if (self.root / 'PTBR').exists() else [], output_before)
        self.assertTrue(self.tool.sync()['unchanged'])

    def test_removal_requires_review_and_keeps_durable_record(self):
        source = self.root / 'EN' / SOURCE
        source.write_bytes(native.encode(self.pairs[:-1]))
        with self.assertRaisesRegex(ValueError, 'REMOVALS_REQUIRE_REVIEW'):
            self.tool.sync()
        self.tool.sync(allow_removals=True)
        self.assertTrue(list((self.root / 'translation-work/history').glob('removed-*.jsonl')))

    def test_500_tiny_updates_over_100_batches_bounded_retention(self):
        started = time.monotonic()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root, 50500)
            tool = Toolkit(root)
            tool.extract(batch_size=500)
            manifest, batches, rows = tool.read()
            self.assertGreaterEqual(len(batches), 100)
            candidates = [r for r in rows.values() if not r['passthrough']]
            for i in range(500):
                row = candidates[(i % 101) * 500]
                value = row['EN'] + ('!' * (i // 101 + 1))
                result = tool.apply({'source_generation': manifest['catalog_sha256'], 'updates': [{'id': row['id'], 'PTBR': value}]}, replace=True)
                self.assertEqual(len(result['files']), 1)
            storage = tool.store.status()
            self.assertLessEqual(storage['transactions'], 10)
            self.assertLess(storage['bytes'], 16 * 1024 * 1024)
            self.assertTrue(tool.check()['valid'])
            print(json.dumps({'event': 'storage_stress', 'records': len(rows), 'batches': len(batches),
                              'updates': 500, 'retained_snapshots': storage['transactions'], 'retained_bytes': storage['bytes'],
                              'elapsed_seconds': round(time.monotonic() - started, 3)}), file=sys.stderr, flush=True)


class StorageTests(unittest.TestCase):
    def test_crash_recovery_and_gc_protect_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'one').write_bytes(b'old')
            store = Store(root)
            with store.lock():
                with self.assertRaisesRegex(RuntimeError, 'SIMULATED_CRASH'):
                    store.commit({'one': b'new', 'two': b'new'}, crash_after=1)
                with self.assertRaisesRegex(ValueError, 'RECOVERY_REQUIRED'):
                    store.gc(False)
                self.assertTrue(store.recover()['recovered'])
                self.assertEqual((root / 'one').read_bytes(), b'old')
                self.assertFalse((root / 'two').exists())
                store.commit({'one': b'final'})
                store.rollback()
                self.assertEqual((root / 'one').read_bytes(), b'old')

    def test_concurrency_paths_budget_and_corrupt_journal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = Store(root, budget=100000)
            with store.lock():
                with self.assertRaisesRegex(ValueError, 'UNSAFE_PATH'):
                    store.commit({'../escape': b'x'})
                with self.assertRaisesRegex(ValueError, 'DISK_BUDGET'):
                    store.commit({'huge': b'x' * 100000})
                with self.assertRaisesRegex(ValueError, 'CONCURRENT_CHANGE'):
                    store.commit({'one': b'x'}, expected={'one': 'wrong'})
                store.commit({'one': b'x'})
            receipt = next(store.transactions.glob('*/receipt.json'))
            data = json.loads(receipt.read_bytes())
            data['files'][0]['slot'] = '../escape'
            receipt.write_bytes(json_bytes(data))
            with self.assertRaisesRegex(ValueError, 'CORRUPT_JOURNAL'):
                store.inventory()


if __name__ == '__main__':
    unittest.main()
