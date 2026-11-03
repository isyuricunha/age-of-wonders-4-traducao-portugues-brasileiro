"""Installed-source refresh, dry runs, metadata discovery and recovery boundaries. AGPL-3.0-only."""
import contextlib
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native
from storage import Store, digest, json_bytes
from toolkit import Toolkit, SOURCE, RESOURCES
from test_toolkit import fixture, fill


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.repo = self.base / 'repository'
        fixture(self.repo)
        self.tool = Toolkit(self.repo)
        self.tool.extract()
        fill(self.tool)
        self.game = self.base / 'game with spaces'
        for relative in RESOURCES:
            target = self.game / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((self.repo / 'EN' / relative).read_bytes())
        (self.game / 'AOW4.exe').write_bytes(b'fixture identity, never executed')

    def tearDown(self):
        self.tmp.cleanup()

    def snapshot(self, root):
        return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file()}

    def test_update_sources_dryrun_import_and_game_readonly(self):
        path = self.game / SOURCE
        pairs = list(native.parse(path.read_bytes()).pairs)
        pairs[0] = (pairs[0][0], 'Updated {name}')
        path.write_bytes(native.encode(pairs))
        before_game, before_repo = self.snapshot(self.game), self.snapshot(self.repo)
        result = self.tool.update_sources(self.game, dry_run=True)
        self.assertEqual(result['counts']['modified'], 1)
        self.assertEqual(self.snapshot(self.game), before_game)
        self.assertEqual(self.snapshot(self.repo), before_repo)
        self.tool.update_sources(self.game)
        self.assertEqual(self.snapshot(self.game), before_game)
        self.assertEqual(self.tool.status()['pending'], 1)
        self.assertEqual(self.tool.status()['last_sync']['counts']['modified'], 1)
        self.assertFalse((self.repo / 'PTBR').exists())
        self.assertTrue(self.tool.update_sources(self.game)['unchanged'])
        (self.game / 'Language/EN/Unexpected.MO').write_bytes(native.encode([('unknown', 'new text')]))
        with self.assertRaisesRegex(ValueError, 'UNMANAGED_LOCALIZATION_RESOURCE'):
            self.tool.update_sources(self.game, dry_run=True)

    def test_missing_companion_wrong_level_invalid_english_and_original_file_input(self):
        for candidate in (self.repo, self.game / 'Language', self.game / 'Language/EN'):
            with self.assertRaises(ValueError):
                self.tool.update_sources(candidate)
        (self.game / 'Language/EN/Name.txt').write_bytes(b'Portuguese')
        with self.assertRaisesRegex(ValueError, 'NOT_ORIGINAL_ENGLISH'):
            self.tool.update_sources(self.game)
        (self.game / 'Language/EN/Name.txt').write_bytes(b'English')
        (self.game / 'Language/EN/Credits.txt').unlink()
        with self.assertRaisesRegex(ValueError, 'INCOMPLETE_SOURCE'):
            self.tool.update_sources(self.game)
        self.assertFalse(self.tool.sync(source_file=self.game / SOURCE, dry_run=True)['changed'])

    def test_bounded_steam_metadata_discovery(self):
        home = self.base / 'home'
        steam = home / '.local/share/Steam'
        metadata = steam / 'steamapps'
        metadata.mkdir(parents=True)
        library = self.base / 'library'
        (library / 'steamapps/common').mkdir(parents=True)
        installation = library / 'steamapps/common/Age of Wonders 4'
        shutil.copytree(self.game, installation)
        (metadata / 'libraryfolders.vdf').write_text('"path" "' + library.as_posix() + '"', encoding='utf-8')
        (library / 'steamapps/appmanifest_1669000.acf').write_text('"appid" "1669000"\n"installdir" "Age of Wonders 4"', encoding='utf-8')
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch('toolkit.Path.home', return_value=home))
            stack.enter_context(mock.patch.dict(os.environ, {'PROGRAMFILES(X86)': str(self.base / 'programs')}))
            if os.name == 'nt':
                stack.enter_context(mock.patch('winreg.OpenKey', side_effect=OSError('fixture: no registry candidate')))
            self.assertEqual(self.tool.discover(), installation.resolve())
            (library / 'steamapps/appmanifest_1669000.acf').unlink()
            with self.assertRaisesRegex(ValueError, 'GAME_NOT_UNIQUE'):
                self.tool.discover()

    def test_configurable_storage_gc_readonly_and_lock(self):
        self.tool.configure_storage(3, 16)
        again = Toolkit(self.repo)
        self.assertEqual((again.store.count, again.store.budget), (3, 16 * 1024 * 1024))
        before = self.snapshot(self.repo)
        again.store.gc(dry_run=True)
        self.assertEqual(before, self.snapshot(self.repo))
        with again.store.lock():
            with self.assertRaisesRegex(ValueError, 'LOCKED'):
                with Store(self.repo).lock():
                    pass
        with self.assertRaisesRegex(ValueError, 'INVALID_RETENTION'):
            self.tool.configure_storage(0, 1)

    def test_gc_refuses_unowned_files_and_corrupt_blobs(self):
        directory, receipt, _ = self.tool.store.inventory()[-1]
        unexpected = directory / 'personal-note.txt'
        unexpected.write_bytes(b'do not delete')
        with self.assertRaisesRegex(ValueError, 'UNOWNED_JOURNAL_FILE'):
            self.tool.store.gc()
        self.assertEqual(unexpected.read_bytes(), b'do not delete')
        unexpected.unlink()
        blob = next((directory / 'new').iterdir())
        blob.write_bytes(b'bad receipt data')
        with self.assertRaisesRegex(ValueError, 'CHECKSUM_MISMATCH'):
            self.tool.store.gc()

    def test_context_changed_invalidates_only_affected_entry(self):
        _, _, rows = self.tool.read()
        original = next(r for r in rows.values() if r['key'].startswith('STORY_EVENT@'))
        candidate = self.game / SOURCE
        pairs = [(k, v.replace('{hero}', '{Player.Name}') if k == original['key'] else v)
                 for k, v in native.parse(candidate.read_bytes()).pairs]
        candidate.write_bytes(native.encode(pairs))
        self.tool.sync(source_file=candidate)
        _, _, updated = self.tool.read()
        self.assertNotEqual(updated[original['id']]['context'], original['context'])
        self.assertEqual(updated[original['id']]['PTBR'], '')
        self.assertEqual(self.tool.status()['pending'], 1)


if __name__ == '__main__':
    unittest.main()
