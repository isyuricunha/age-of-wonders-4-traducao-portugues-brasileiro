"""Actual HTTP-client publishing flow, using an offline GitHub fixture. AGPL-3.0-only."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from urllib.parse import urlsplit, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import release
from storage import digest
from toolkit import Toolkit
from test_toolkit import fixture, fill

SHA = 'a' * 40
OLD = 'b' * 40


class FakeGit:
    def __init__(self, baseline=None):
        self.previous = baseline
        self.nonancestor = False

    def ancestor(self, previous, current):
        if self.nonancestor:
            raise ValueError('NON_ANCESTOR_HISTORY')

    def baseline(self, revision):
        if not self.previous:
            raise ValueError('MISSING_RELEASE_BASELINE')
        return self.previous


class Server:
    def __init__(self):
        self.calls, self.refs, self.releases, self.assets = [], {}, [], []
        self.head = SHA
        self.fail_upload = False
        self.fail_status = None
        self.rate = 0

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, headers, body))
        self.assert_header(headers)
        if self.fail_status:
            return self.fail_status, {}, b'{}'
        if self.rate:
            self.rate -= 1
            return 503, {}, b'{}'
        parsed = urlsplit(url)
        prefix = '/repos/' + release.REPOSITORY
        path = parsed.path
        payload = json.loads(body) if body and headers['Content-Type'] == 'application/json' else None
        def ok(value, status=200):
            return status, {}, json.dumps(value).encode()
        if parsed.netloc == 'uploads.github.com':
            if self.fail_upload:
                self.fail_upload = False
                return 503, {}, b'{}'
            if path != prefix + '/releases/1/assets' or parse_qs(parsed.query) != {'name': ['PTBR.zip']}:
                raise AssertionError('wrong upload endpoint')
            asset = {'id': 10, 'name': 'PTBR.zip', 'size': len(body), 'state': 'uploaded', 'digest': 'sha256:' + digest(body)}
            self.assets.append(asset)
            return ok(asset, 201)
        if path == prefix:
            return ok({'default_branch': 'main'})
        if path == prefix + '/commits/main':
            return ok({'sha': self.head})
        if path == prefix + '/tags':
            return ok([{'name': name} for name in self.refs])
        if path.startswith(prefix + '/git/ref/tags/'):
            tag = path.rsplit('/', 1)[1]
            return ok({'object': {'type': 'commit', 'sha': self.refs[tag]}}) if tag in self.refs else (404, {}, b'{}')
        if path == prefix + '/releases':
            if method == 'GET':
                return ok([{**r, 'assets': self.assets} for r in self.releases])
            if method == 'POST':
                if payload['draft'] is not True or payload['target_commitish'] != SHA:
                    raise AssertionError('wrong draft creation payload')
                value = {**payload, 'id': 1, 'upload_url': 'https://uploads.github.com' + prefix + '/releases/1/assets{?name,label}'}
                self.releases.append(value)
                return ok(value, 201)
        if path == prefix + '/releases/1/assets':
            return ok(self.assets)
        if path == prefix + '/releases/assets/10' and method == 'DELETE':
            self.assets = []
            return 204, {}, b''
        if path == prefix + '/releases/1':
            if method == 'PATCH':
                self.releases[-1].update(payload)
                if payload.get('draft') is False:
                    self.refs[self.releases[-1]['tag_name']] = SHA
            return ok(self.releases[-1])
        raise AssertionError(f'unhandled request {method} {url}')

    @staticmethod
    def assert_header(headers):
        if headers['Authorization'] != 'Bearer fixture-token':
            raise AssertionError('incorrect auth header')


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        fixture(self.root)
        self.tool = Toolkit(self.root)
        self.tool.extract()
        fill(self.tool)
        self.tool.build()
        for name in ('LICENSE', 'GAME-DEVELOPER-PERMISSION.md', 'CONTRIBUTING.md', 'FONT-LICENSE.txt', 'changelog.md'):
            (self.root / name).write_text('Fixture: repository notice, never an extra Release attachment.', encoding='utf-8')
        self.archive = self.root / 'PTBR.zip'
        self.tool.package(self.archive)
        self.server = Server()
        self.api = release.GitHub(release.REPOSITORY, 'fixture-token', self.server, sleep=lambda _: None)
        self.git = FakeGit()

    def tearDown(self):
        self.tmp.cleanup()

    def baseline(self):
        return {'output': self.tool.verify_output()['output'], 'legacy': False,
                'texts': {r['key']: r['PTBR'] for r in self.tool.read()[2].values() if not r['passthrough']}}

    def test_first_publish_actual_http_and_identical_rerun_noop(self):
        result = release.publish(self.tool, self.api, self.git, SHA, self.archive)
        self.assertEqual(result['tag'], 'v1.0.0')
        self.assertEqual(result['assets'], ['PTBR.zip'])
        self.assertEqual(self.server.calls[0][1], self.api.root)
        self.assertFalse(self.server.calls[0][1].endswith('/'))
        self.assertTrue(any(m == 'POST' and '/releases/1/assets?name=PTBR.zip' in u for m, u, _, _ in self.server.calls))
        self.git.previous = self.baseline()
        calls = len(self.server.calls)
        self.assertTrue(release.publish(self.tool, self.api, self.git, SHA, self.archive)['unchanged'])
        self.assertFalse(any(m in ('POST', 'PATCH', 'DELETE') for m, *_ in self.server.calls[calls:]))
        # Native output unchanged: a different ZIP representation is still a no-op.
        with zipfile.ZipFile(self.archive, 'w', zipfile.ZIP_STORED) as zf:
            for name in sorted(self.baseline()['output']):
                zf.writestr(name, (self.root / 'PTBR' / name).read_bytes())
        self.assertTrue(release.publish(self.tool, self.api, self.git, SHA, self.archive)['unchanged'])
        self.server.assets[0]['digest'] = 'sha256:' + '0' * 64
        with self.assertRaisesRegex(ValueError, 'PUBLIC_ASSET_CHECKSUM'):
            release.publish(self.tool, self.api, self.git, SHA, self.archive)

    def test_patch_version_diff_and_legacy_transition(self):
        self.server.refs['v1.0.0'] = OLD
        self.server.releases.append({'id': 2, 'tag_name': 'v1.0.0', 'draft': False, 'prerelease': False})
        baseline = self.baseline()
        baseline['output'] = {'old': 'different'}
        baseline['texts']['INTERFACE@TITLE@NAME'] = 'previous {name}'
        baseline['legacy'] = True
        self.git.previous = baseline
        result = release.publish(self.tool, self.api, self.git, SHA, self.archive)
        self.assertEqual(result['tag'], 'v1.0.1')
        body = self.server.releases[-1]['body']
        self.assertIn('1 alterados', body)
        self.assertIn('Interface: 1', body)
        self.assertIn('caminhos completos', body)
        self.assertIn('/compare/v1.0.0...v1.0.1', body)

    def test_interrupted_upload_resumes_matching_draft(self):
        self.server.fail_upload = True
        with self.assertRaisesRegex(release.ApiError, 'GITHUB_HTTP_503'):
            release.publish(self.tool, self.api, self.git, SHA, self.archive)
        self.assertTrue(self.server.releases[0]['draft'])
        result = release.publish(self.tool, self.api, self.git, SHA, self.archive)
        self.assertTrue(result['published'])
        self.assertEqual(len(self.server.releases), 1)
        self.assertEqual(len(self.server.assets), 1)

    def test_stale_commit_or_history_and_asset_allowlist_fail(self):
        self.server.head = OLD
        with self.assertRaisesRegex(ValueError, 'STALE_COMMIT'):
            release.publish(self.tool, self.api, self.git, SHA, self.archive)
        self.server.head = SHA
        self.server.refs['v1.0.0'] = OLD
        self.server.releases.append({'id': 2, 'tag_name': 'v1.0.0', 'draft': False})
        self.git.previous = self.baseline()
        self.git.nonancestor = True
        with self.assertRaisesRegex(ValueError, 'NON_ANCESTOR'):
            release.publish(self.tool, self.api, self.git, SHA, self.archive)
        self.git.nonancestor = False
        self.server.assets = [{'name': 'LICENSE'}]
        with self.assertRaisesRegex(ValueError, 'UNEXPECTED_PUBLIC_ASSETS'):
            release.publish(self.tool, self.api, self.git, SHA, self.archive)

    def test_orphan_and_conflicting_tags_and_missing_zip(self):
        self.server.refs['v01.0.0'] = OLD
        with self.assertRaisesRegex(ValueError, 'AMBIGUOUS_VERSION_TAG'):
            release.publish(self.tool, self.api, self.git, SHA, self.archive)
        self.server.refs = {}
        self.server.refs['v2.0.0'] = OLD
        with self.assertRaisesRegex(ValueError, 'ORPHAN_VERSION_TAG'):
            release.publish(self.tool, self.api, self.git, SHA, self.archive)
        self.server.refs = {'v1.0.0': OLD}
        with self.assertRaisesRegex(ValueError, 'TAG_COMMIT_CONFLICT'):
            release.publish(self.tool, self.api, self.git, SHA, self.archive)
        self.archive.unlink()
        with self.assertRaisesRegex(ValueError, 'MISSING_ZIP'):
            release.publish(self.tool, self.api, self.git, SHA, self.archive)

    def test_api_auth_404_transient_and_upload_host(self):
        for status in (401, 403, 404):
            self.server.fail_status = status
            with self.assertRaisesRegex(release.ApiError, f'GITHUB_HTTP_{status}'):
                self.api.request('GET')
        self.server.fail_status = None
        self.server.rate = 2
        self.assertEqual(self.api.request('GET')['default_branch'], 'main')
        with self.assertRaisesRegex(release.ApiError, 'UNSAFE_UPLOAD_ENDPOINT'):
            self.api.request('POST', 'https://example.com/repos/a/b/releases/1/assets', b'zip', binary=True, upload=True)

    def test_readme_and_release_truthful_copy(self):
        current = {'texts': {'STORY_EVENT@1': 'same', 'UNKNOWN@A': 'new'}}
        previous = {'texts': {'STORY_EVENT@1': 'old'}, 'output': {}}
        body = release.notes('v1.0.1', current, previous, 'v1.0.0')
        for section in ('Download', 'O que mudou', 'Instalação', 'Compatibilidade', 'Comunidade e suporte', 'Créditos e licença'):
            self.assertIn(section, body)
        self.assertIn('Outros textos', body)
        self.assertLess(body.index('Download'), body.index('Pix'))
        native_only = release.notes('v1.0.2', current, {**previous, 'texts': current['texts']}, 'v1.0.1')
        self.assertIn('textos PT-BR permanecem iguais', native_only)
        self.assertIn('https://discord.gg/uFEwSMwUYb', body)
        self.assertNotIn('Commits desde', body)


if __name__ == '__main__':
    unittest.main()
