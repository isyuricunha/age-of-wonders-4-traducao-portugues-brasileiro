"""Git-byte handoff, read-only doctor, legal consent and public-copy regressions. AGPL-3.0-only."""
import copy
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import consent_check
import doctor
from storage import digest, json_bytes, normalized
from toolkit import Toolkit, SOURCE
from test_toolkit import fixture

ROOT = Path(__file__).resolve().parents[2]


def receipts(root):
    work = root / 'translation-work'
    work.mkdir(exist_ok=True)
    (root / '.gitattributes').write_bytes(b'* text eol=lf\n/EN/** -text\n*.MO -text\n')
    (work / 'adapter.json').write_bytes(b'{\r\n  "format": "MO revision 0"\r\n}\r\n')
    metadata = {'files': {'.gitattributes': digest((root / '.gitattributes').read_bytes()),
                           'translation-work/adapter.json': digest(normalized((work / 'adapter.json').read_bytes()))}}
    (work / 'toolchain.json').write_bytes(json_bytes(metadata).replace(b'\n', b'\r\n'))
    (work / 'runtime-support.json').write_bytes(json_bytes({'target': 'Ubuntu Server 24.04 LTS ARM64',
             'toolchain_sha256': digest(normalized((work / 'toolchain.json').read_bytes()))}))


class PortabilityTests(unittest.TestCase):
    def test_git_index_crlf_metadata_passes_normalized_receipts_and_tampering_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            tool = Toolkit(root)
            tool.extract()
            receipts(root)
            def git(*args):
                result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, check=True)
                return result.stdout
            git('init', '-q')
            git('-c', 'core.autocrlf=true', 'add', '.gitattributes', 'EN', 'translation-work/adapter.json', 'translation-work/toolchain.json', 'translation-work/runtime-support.json')
            for relative in ('translation-work/adapter.json', 'translation-work/toolchain.json'):
                blob = git('show', ':' + relative)
                self.assertNotIn(b'\r\n', blob)
                (root / relative).write_bytes(blob)
            native_bytes = git('show', ':EN/' + SOURCE)
            self.assertEqual(native_bytes, (root / 'EN' / SOURCE).read_bytes())
            before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob('*') if p.is_file() and '.git' not in p.parts}
            result = doctor.run(tool, require_arm64=False)
            self.assertTrue(result['valid'])
            for p, saved in before.items():
                self.assertEqual((p.read_bytes(), p.stat().st_mtime_ns), saved)
            path = root / 'translation-work/adapter.json'
            path.write_bytes(path.read_bytes().replace(b'revision 0', b'revision 1'))
            with self.assertRaisesRegex(ValueError, 'CHECKSUM_MISMATCH'):
                doctor.run(tool, require_arm64=False)
            path.write_bytes(git('show', ':translation-work/adapter.json'))
            source = root / 'EN' / SOURCE
            source.write_bytes(source.read_bytes() + b'tamper')
            with self.assertRaisesRegex(ValueError, 'CHECKSUM_MISMATCH'):
                doctor.run(tool, require_arm64=False)

    def test_architecture_and_missing_dependency_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            tool = Toolkit(root)
            tool.extract()
            receipts(root)
            with mock.patch.object(doctor.sys, 'version_info', (3, 9, 0)):
                with self.assertRaisesRegex(ValueError, 'MISSING_RUNTIME'):
                    doctor.run(tool, require_arm64=False)
            with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_ARCHITECTURE'):
                doctor.run(tool, system='Linux', machine='x86_64')
            self.assertTrue(doctor.run(tool, system='Linux', machine='aarch64')['valid'])
            # Simulated architecture is a fixture, never evidence of a live ARM64 run.
            path = root / 'translation-work/adapter.json'
            path.unlink()
            with self.assertRaisesRegex(ValueError, 'MISSING_DEPENDENCY'):
                doctor.run(tool, require_arm64=False)


class PublicDocsTests(unittest.TestCase):
    def test_compat_converter_cannot_write_managed_trees(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / 'translation-work/legacy/scripts'
            archive.mkdir(parents=True)
            shutil.copyfile(ROOT / 'mo_convert.py', root / 'mo_convert.py')
            shutil.copyfile(ROOT / 'translation-work/legacy/scripts/mo_convert.py', archive / 'mo_convert.py')
            source = root / 'input.po'
            source.write_text('msgid "key"\nmsgstr "value"\n', encoding='utf-8')
            for relative in ('EN/EN.MO', 'PTBR/PTBR.MO', 'translation-work/translations/partial.MO'):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                for mode in ('to-mo', 'to-po'):
                    for separator in ([], ['--']):
                        result = subprocess.run([sys.executable, '-B', str(root / 'mo_convert.py'), mode, *separator, str(source), str(target)], capture_output=True)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn(b'Managed resources are protected', result.stderr)
                        self.assertFalse(target.exists())

    def test_full_authentic_license_scope_and_consent(self):
        license_text = (ROOT / 'LICENSE').read_text(encoding='utf-8')
        self.assertTrue(license_text.startswith('Attribution-NonCommercial-ShareAlike 4.0 International'))
        self.assertGreater(len(license_text), 19000)
        for section in ('Section 1', 'Section 2', 'Section 3', 'Section 4', 'Section 5', 'Section 6', 'Section 7', 'Section 8'):
            self.assertIn(section, license_text)
        permission = (ROOT / 'GAME-DEVELOPER-PERMISSION.md').read_text(encoding='utf-8')
        self.assertIn('Age of Wonders 4', permission)
        self.assertNotIn('Soulash', permission)
        self.assertIn('Triumph Studios and Paradox Interactive', permission)
        self.assertIn('royalty-free', permission)
        self.assertIn('Unapproved submissions', permission)
        self.assertIn('AFFERO', (ROOT / 'translation-work/LICENSE-AGPL-3.0').read_text(encoding='utf-8'))
        template = (ROOT / '.github/pull_request_template.md').read_text(encoding='utf-8')
        event = {'pull_request': {'body': template, 'user': {'login': 'fixture'}, 'html_url': 'https://github.com/owner/repo/pull/1', 'head': {'sha': 'f' * 40}}}
        with self.assertRaisesRegex(ValueError, 'CONSENT_REQUIRED'):
            consent_check.check(event, template)
        event['pull_request']['body'] = template.replace('- [ ] ', '- [x] ')
        self.assertTrue(consent_check.check(event, template)['affirmative'])
        event['pull_request']['head'] = {}
        with self.assertRaisesRegex(ValueError, 'CONSENT_SCOPE_REQUIRED'):
            consent_check.check(event, template)

    def test_evergreen_readme_badges_content_boundaries(self):
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        self.assertIn('https://github.com/isyuricunha/age-of-wonders-4-traducao-portugues-brasileiro/releases)', readme)
        self.assertIn('quando disponível', readme)
        self.assertIn('https://discord.gg/uFEwSMwUYb', readme)
        self.assertIn('width="650"', readme)
        badges = re.findall(r'\[!\[([^\]]+)\]\((https://img.shields.io/[^)]+)\)\]\((https://[^)]+)\)', readme)
        self.assertTrue(2 <= len(badges) <= 5)
        self.assertTrue(all(alt and 'for-the-badge' in image for alt, image, _ in badges))
        for forbidden in ('100%', '52.275', 'JSONL', 'batch-', 'toolkit.py', 'build-manifest', 'ARM64', 'hash', 'ainda não publicada', 'release-state:'):
            self.assertNotIn(forbidden, readme)
        # Same exact document remains valid before and after any release.
        versions = (None, 'v1.0.0', 'v1.0.1', 'v1.0.99')
        self.assertEqual(len({digest(readme.encode()) for _ in versions}), 1)
        self.assertLess(readme.index('Baixar a tradução'), readme.index('Pix'))
        for link in ('(LICENSE)', '(GAME-DEVELOPER-PERMISSION.md)', '(CONTRIBUTING.md)'):
            self.assertIn(link, readme)

    def test_workflow_completion_boundary_and_no_unrelated_uploads(self):
        workflow = (ROOT / '.github/workflows/release.yml').read_text(encoding='utf-8')
        self.assertIn("- 'PTBR/**'", workflow)
        self.assertNotIn("- 'translation-work/**'", workflow)
        self.assertNotIn("- 'EN/**'", workflow)
        self.assertIn('verify-output', workflow)
        self.assertIn('release.py --publish', workflow)
        self.assertIn('contents: write', workflow)
        self.assertIn('cancel-in-progress: false', workflow)
        self.assertNotIn('toolkit.py build', workflow)
        for forbidden in ('NEXUSMODS_API_KEY', '*.zip', '*.7z', 'release upload', 'upload-artifact'):
            self.assertNotIn(forbidden, workflow)

    def test_public_attribution_negative_fixtures(self):
        def violations(text):
            return re.findall(r'(?i)Ella Mizuki|Sayuri Mizuki|Yue Mizuki|(?:Yuri|isyuricunha)\s+(?:traduziu|testou|revisou|traduz|testa)', text)
        self.assertTrue(violations('Ella Mizuki traduziu isto.'))
        self.assertTrue(violations('Yuri testou o jogo.'))
        self.assertFalse(violations('Manutenção: Yuri Cunha (isyuricunha).'))
        self.assertFalse(violations((ROOT / 'README.md').read_text(encoding='utf-8')))
        for name in ('README.md', 'docs/briefing-do-jogo.md', 'docs/fluxo-de-traducao.md'):
            self.assertFalse(violations((ROOT / 'translation-work' / name).read_text(encoding='utf-8')))


if __name__ == '__main__':
    unittest.main()
