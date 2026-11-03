"""Role evidence and downstream context invalidation, using synthetic casting data. AGPL-3.0-only."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native
from storage import digest, json_bytes
from toolkit import Toolkit, SOURCE
from test_toolkit import fixture, fill


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.pairs = fixture(self.root)
        self.pairs += [('Speaker_Jessica', 'Jessica'), ('Speaker_Daniel', 'Daniel'),
                       ('CHARACTER@JESSICA@BIO', 'Jessica is a woman. She is the speaker in this fixture.'),
                       ('CHARACTER@DANIEL@BIO', 'Daniel is a man. He is described by Jessica.'),
                       ('CAST@SCENE_1', 'ScriptJessica: speaker Jessica; line 2 describes Daniel.'),
                       ('ScriptJessica@LINE_1', 'I am tired.'), ('ScriptJessica@LINE_2', 'He is tired.'),
                       ('Speaker_Alex', 'Alex'), ('STORY_EVENT@PLAYER@TEXT', '{Player.Name} is tired.')]
        (self.root / 'EN' / SOURCE).write_bytes(native.encode(self.pairs))
        texts = dict(self.pairs)
        chars = [{'id': name, 'aliases': [name], 'biography_key': key, 'gender': gender, 'EN_sha256': digest(texts[key].encode())}
                 for name, key, gender in [('Jessica', 'CHARACTER@JESSICA@BIO', 'female'), ('Daniel', 'CHARACTER@DANIEL@BIO', 'male')]]
        proof = [{'key': 'CAST@SCENE_1', 'EN_sha256': digest(texts['CAST@SCENE_1'].encode())}]
        bindings = [{'key': key, 'role': role, 'character': person, 'evidence': proof}
                    for key, role, person in [('ScriptJessica@LINE_1', 'speaker', 'Jessica'),
                                              ('ScriptJessica@LINE_2', 'speaker', 'Jessica'),
                                              ('ScriptJessica@LINE_2', 'referent', 'Daniel')]]
        (self.root / 'translation-work').mkdir(exist_ok=True)
        (self.root / 'translation-work/context-reference.json').write_bytes(json_bytes({'schema': 1, 'source_file': SOURCE, 'characters': chars, 'bindings': bindings}))
        self.tool = Toolkit(self.root)
        self.tool.extract()

    def tearDown(self):
        self.tmp.cleanup()

    def by_key(self):
        return {r['key']: r for r in self.tool.read()[2].values()}

    def test_verified_female_speaker_male_referent_unknown_name_and_dynamic_player(self):
        rows = self.by_key()
        first = rows['ScriptJessica@LINE_1']
        self.assertEqual(first['context']['speaker'], 'Jessica')
        self.assertEqual(next(e['gender'] for e in first['context']['gender_evidence'] if e.get('role') == 'speaker'), 'female')
        second = rows['ScriptJessica@LINE_2']['context']
        self.assertEqual((second['speaker'], second['referent']), ('Jessica', 'Daniel'))
        self.assertEqual({e['role']: e['gender'] for e in second['gender_evidence'] if 'gender' in e}, {'speaker': 'female', 'referent': 'male'})
        self.assertEqual(rows['Speaker_Alex']['context']['speaker'], 'unknown')
        self.assertEqual(rows['STORY_EVENT@PLAYER@TEXT']['context']['referent'], 'dynamic or unknown')
        self.assertTrue(all(not row['PTBR'] for row in rows.values()))
        self.assertTrue(self.tool.migrate_context()['unchanged'])

    def test_biography_change_invalidates_dependent_context_without_losing_other_progress(self):
        fill(self.tool)
        before = self.by_key()
        reference = self.root / 'translation-work/context-reference.json'
        accepted_reference = reference.read_bytes()
        candidate = json.loads(accepted_reference)
        candidate['characters'][0]['EN_sha256'] = '0' * 64
        reference.write_bytes(json_bytes(candidate))
        with self.assertRaisesRegex(ValueError, 'CONTEXT_ALREADY_MIGRATED'):
            self.tool.migrate_context()
        reference.write_bytes(accepted_reference)
        changed = [(k, 'The biography was changed; the former gender evidence needs review.' if k == 'CHARACTER@JESSICA@BIO' else v) for k, v in self.pairs]
        (self.root / 'EN' / SOURCE).write_bytes(native.encode(changed))
        with self.assertRaisesRegex(ValueError, 'SOURCE_CHANGED'):
            self.tool.migrate_context()
        self.tool.sync()
        after = self.by_key()
        for key in ('ScriptJessica@LINE_1', 'ScriptJessica@LINE_2'):
            self.assertEqual(after[key]['PTBR'], '')
            self.assertEqual(after[key]['history'][-1]['PTBR'], before[key]['PTBR'])
        self.assertEqual(after['INTERFACE@TITLE@NAME']['PTBR'], before['INTERFACE@TITLE@NAME']['PTBR'])
        self.assertEqual(next(e['gender'] for e in after['ScriptJessica@LINE_2']['context']['gender_evidence'] if e.get('role') == 'speaker'), 'unknown')


if __name__ == '__main__':
    unittest.main()
