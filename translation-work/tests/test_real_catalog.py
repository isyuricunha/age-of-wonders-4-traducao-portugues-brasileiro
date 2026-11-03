"""Read-only checks against the actual migrated corpus. AGPL-3.0-only."""
import gettext
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import native
import syntax
from storage import digest
from toolkit import Toolkit, SOURCE

ROOT = Path(__file__).resolve().parents[2]


class RealCatalogTests(unittest.TestCase):
    def test_source_roundtrip_complete_reconstruction_and_legacy_preservation(self):
        tool = Toolkit(ROOT)
        original = (ROOT / 'EN' / SOURCE).read_bytes()
        catalog = native.parse(original)
        self.assertEqual(native.encode(catalog.pairs, catalog), original)
        regenerated = native.encode(catalog.pairs)
        self.assertEqual(native.parse(regenerated).pairs, catalog.pairs)
        manifest, batches, rows = tool.read()
        self.assertEqual(len(rows), 52275)
        self.assertEqual(len(batches), 105)
        self.assertEqual(sum(r['passthrough'] for r in rows.values()), 32)
        historical = native.parse((ROOT / 'translation-work/legacy/output/PTBR.MO').read_bytes())
        legacy_texts = {k: v for k, v in historical.pairs if k and not native.passthrough(k, v)}
        imported = {r['key']: r['PTBR'] for r in rows.values() if not r['passthrough']}
        self.assertEqual(imported, legacy_texts)
        with (ROOT / 'PTBR/Language/PTBR/PTBR.MO').open('rb') as stream:
            independent = gettext.GNUTranslations(stream)
        self.assertTrue(all(independent.gettext(k) == v for k, v in imported.items()))
        actual = native.parse((ROOT / 'PTBR/Language/PTBR/PTBR.MO').read_bytes())
        self.assertEqual((ROOT / 'PTBR/Language/PTBR/Name.txt').read_bytes(),
                         (ROOT / 'translation-work/legacy/output/Name.txt').read_bytes())
        self.assertEqual(next(v for k, v in actual.pairs if not k), next(v for k, v in historical.pairs if not k))
        self.assertEqual([(k, v) for k, v in actual.pairs if native.passthrough(k, v)],
                         [(k, v) for k, v in catalog.pairs if native.passthrough(k, v)])

    def test_exact_legacy_policy_does_not_accept_new_source_or_token_change(self):
        tool = Toolkit(ROOT)
        _, _, rows = tool.read()
        policies = json.loads((ROOT / 'translation-work/legacy-rewrite-policy.json').read_bytes())
        for row in rows.values():
            if row['key'] not in policies:
                continue
            self.assertTrue(syntax.errors(row['EN'], row['PTBR']))
            self.assertFalse(tool.validation_errors(row))
            self.assertTrue(tool.validation_errors({**row, 'PTBR': row['PTBR'] + ' {invented}'}))
            self.assertTrue(tool.validation_errors({**row, 'EN': row['EN'] + ' {missing}'}))


if __name__ == '__main__':
    unittest.main()
