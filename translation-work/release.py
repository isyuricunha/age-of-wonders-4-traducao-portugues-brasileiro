"""Serialized, idempotent GitHub Release publisher. SPDX-License-Identifier: AGPL-3.0-only.

Only the CI workflow invokes publish. Offline tests exercise this actual client.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import native
from storage import digest, json_bytes
from toolkit import Toolkit, BUILD

REPOSITORY = 'isyuricunha/age-of-wonders-4-traducao-portugues-brasileiro'
REPO_URL = 'https://github.com/' + REPOSITORY
SEMVER = re.compile(r'^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$')


class ApiError(ValueError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ApiError('UNEXPECTED_REDIRECT: refusing to forward GitHub credentials')


def transport(method, url, headers, body):
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=45) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()
    except urllib.error.URLError as exc:
        raise ApiError(f'NETWORK_ERROR: {method} {url}; rerun to resume; {exc.reason}') from exc


class GitHub:
    def __init__(self, repository, token, send=transport, sleep=time.sleep):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
            raise ApiError('INVALID_REPOSITORY')
        if not token:
            raise ApiError('MISSING_TOKEN: workflow requires GITHUB_TOKEN and contents: write')
        self.repository, self.token, self.send, self.sleep = repository, token, send, sleep
        self.root = 'https://api.github.com/repos/' + repository

    def request(self, method, path='', value=None, *, optional=False, binary=False, upload=False):
        if upload:
            url = path
            parts = urllib.parse.urlsplit(url)
            required = '/repos/' + self.repository + '/releases/'
            if parts.scheme != 'https' or parts.netloc != 'uploads.github.com' or not parts.path.startswith(required) or not parts.path.endswith('/assets'):
                raise ApiError('UNSAFE_UPLOAD_ENDPOINT')
        else:
            if path and (not path.startswith('/') or '://' in path or '..' in path):
                raise ApiError('UNSAFE_API_PATH')
            url = self.root + path
        headers = {'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json',
                   'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'aow4-ptbr-release'}
        body = value if binary else (json_bytes(value) if value is not None else None)
        if body is not None:
            headers['Content-Type'] = 'application/zip' if binary else 'application/json'
        for attempt in range(4):
            status, response_headers, data = self.send(method, url, headers, body)
            rate_limited = status == 403 and response_headers.get('X-RateLimit-Remaining') == '0'
            if (status in (429, 500, 502, 503, 504) or rate_limited) and method in ('GET', 'PATCH') and attempt < 3:
                self.sleep(min(2 ** attempt, 8))
                continue
            if status == 404 and optional:
                return None
            if not 200 <= status < 300:
                raise ApiError(f'GITHUB_HTTP_{status}: {method} {url}; check endpoint, token permissions, rate limits and repository visibility; rerun to resume')
            return json.loads(data) if data else None
        raise ApiError('RETRY_EXHAUSTED')

    def pages(self, path):
        values = []
        for page in range(1, 101):
            result = self.request('GET', path + f'?per_page=100&page={page}')
            if not isinstance(result, list):
                raise ApiError('INVALID_API_RESPONSE: expected paginated list')
            values.extend(result)
            if len(result) < 100:
                return values
        raise ApiError('PAGINATION_LIMIT: refuse incomplete release/tag history')

    def tag_commit(self, tag):
        path = '/git/ref/tags/' + urllib.parse.quote(tag, safe='')
        ref = self.request('GET', path, optional=True)
        if not ref:
            return None
        obj = ref['object']
        for _ in range(8):
            if obj['type'] == 'commit':
                return obj['sha']
            if obj['type'] != 'tag' or not re.fullmatch('[a-f0-9]{40}', obj['sha']):
                raise ApiError('INVALID_TAG_OBJECT')
            obj = self.request('GET', '/git/tags/' + obj['sha'])['object']
        raise ApiError('TAG_DEPTH_EXCEEDED')


class Git:
    def __init__(self, root):
        self.root = root

    def run(self, *args, optional=False):
        result = subprocess.run(['git', '-C', str(self.root), *args], capture_output=True)
        if result.returncode:
            if optional:
                return None
            raise ValueError('GIT_FAILURE: ' + ' '.join(args) + ': ' + result.stderr.decode('utf-8', errors='replace'))
        return result.stdout

    def ancestor(self, previous, current):
        if self.run('merge-base', '--is-ancestor', previous, current, optional=True) is None:
            raise ValueError('NON_ANCESTOR_HISTORY: previous release/tag is not an ancestor of triggering commit')

    def baseline(self, revision):
        receipt = self.run('show', revision + ':' + BUILD, optional=True)
        if receipt is not None:
            data = json.loads(receipt)
            manifest = json.loads(self.run('show', revision + ':translation-work/translations/manifest.json'))
            rows = []
            for name in manifest['batches']:
                content = self.run('show', revision + ':translation-work/translations/' + name).decode('utf-8')
                rows.extend(json.loads(line) for line in content.splitlines())
            return {'output': data['output'], 'texts': {r['key']: r['PTBR'] for r in rows if not r['passthrough']}, 'legacy': False}
        # Explicit migration adapter for this repository's already-published flat layout.
        raw = self.run('show', revision + ':PTBR/PTBR.MO', optional=True)
        name = self.run('show', revision + ':PTBR/Name.txt', optional=True)
        if raw is None or name is None:
            raise ValueError('MISSING_RELEASE_BASELINE: previous release has neither build manifest nor verified legacy PTBR catalog')
        catalog = native.parse(raw)
        return {'output': {'Language/PTBR/PTBR.MO': digest(raw), 'Language/PTBR/Name.txt': digest(name)},
                'texts': {k: v for k, v in catalog.pairs if k and not native.passthrough(k, v)}, 'legacy': True}


def notes(tag, current, previous=None, previous_tag=None):
    texts, prior = current['texts'], previous['texts'] if previous else {}
    added = set(texts) - set(prior)
    removed = set(prior) - set(texts)
    changed = {k for k in set(texts) & set(prior) if texts[k] != prior[k]}
    retained = len(set(texts) & set(prior)) - len(changed)
    body = [f'# Age of Wonders 4 · PT-BR · {tag}', '', '## ⬇️ Download', '',
            'Baixe **PTBR.zip** nos arquivos desta Release. “Source code” é o repositório, não o pacote de instalação.', '',
            '## ✨ O que mudou', '']
    if previous is None:
        body.append('Pacote completo dos textos localizados: interface, descrições, eventos e conteúdo narrativo do catálogo de origem registrado nesta versão.')
    else:
        body.append(f'{len(added)} textos adicionados, {len(changed)} alterados, {len(removed)} removidos e {retained} preservados em relação à versão anterior.')
        labels = {'INTERFACE': 'Interface', 'STORY_EVENT': 'Eventos', 'CAMPAIGN': 'Campanha', 'DLC': 'Conteúdo de expansões'}
        categories = {}
        for key in sorted(added | changed | removed):
            category = labels.get(key.split('@')[0], 'Outros textos')
            categories[category] = categories.get(category, 0) + 1
        for category, count in sorted(categories.items()):
            body.append(f'- {category}: {count} textos afetados.')
        if not added and not changed and not removed:
            body.append('Os textos PT-BR permanecem iguais; esta versão altera a representação ou os arquivos nativos do pacote.')
        if previous.get('legacy'):
            body.append('O pacote passa a conter os caminhos completos de instalação; extraia o conteúdo na pasta principal do jogo.')
    body += ['', '## 📦 Instalação', '', '1. Faça backup da pasta `Language/PTBR` existente.',
             '2. Extraia o ZIP e copie a pasta `Language` para a pasta principal de Age of Wonders 4.',
             '3. Selecione Português Brasileiro nas opções de idioma e reinicie o jogo, se necessário.', '',
             '[Guia de instalação e restauração](' + REPO_URL + '#-instalação)', '', '## 🔎 Compatibilidade', '',
             'Consulte o catálogo/versão de origem e as limitações no guia do projeto. A validação estrutural não substitui teste dentro do jogo.', '',
             '## 💬 Comunidade e suporte', '', '[Vai Brasil — Discord](https://discord.gg/uFEwSMwUYb) · [Relatar problema](' + REPO_URL + '/issues) · [Portal](https://traducao.yuricunha.com/)', '',
             '## Créditos e licença', '', 'Manutenção: Yuri Cunha (isyuricunha) e colaboradores creditados nos respectivos PRs. Age of Wonders 4: Triumph Studios / Paradox Interactive.',
             '[CC BY-NC-SA 4.0](' + REPO_URL + '/blob/main/LICENSE) · [Permissão de integração oficial](' + REPO_URL + '/blob/main/GAME-DEVELOPER-PERMISSION.md) · [Contribuições](' + REPO_URL + '/blob/main/CONTRIBUTING.md)', '',
             'Apoio opcional via Pix: `pix@yuricunha.com`.']
    if previous_tag:
        body += ['', '[Comparar versões](' + REPO_URL + '/compare/' + urllib.parse.quote(previous_tag, safe='') + '...' + urllib.parse.quote(tag, safe='') + ')']
    return '\n'.join(body) + '\n'


def asset_matches(asset, data):
    return asset.get('name') == 'PTBR.zip' and asset.get('state') == 'uploaded' and asset.get('size') == len(data) and asset.get('digest') == 'sha256:' + digest(data)


def publish(toolkit, api, git, sha, archive):
    if not re.fullmatch('[a-f0-9]{40}', sha):
        raise ValueError('INVALID_TRIGGER_COMMIT')
    verified = toolkit.verify_output()  # fast gate; no native rebuild
    archive = Path(archive)
    if not archive.is_file() or archive.stat().st_size == 0:
        raise ValueError('MISSING_ZIP: workflow must package verified output first')
    import zipfile
    with zipfile.ZipFile(archive) as zf:
        if sorted(zf.namelist()) != sorted(verified['output']) or zf.testzip():
            raise ValueError('INVALID_ZIP: exact native member allowlist required')
        for member, checksum in verified['output'].items():
            if digest(zf.read(member)) != checksum:
                raise ValueError('ZIP_CHECKSUM_MISMATCH')
    data = archive.read_bytes()
    metadata = api.request('GET')  # intentionally NO trailing slash
    branch = metadata['default_branch']
    head_path = '/commits/' + urllib.parse.quote(branch, safe='')
    if api.request('GET', head_path)['sha'] != sha:
        raise ValueError('STALE_COMMIT: triggering commit is no longer default-branch HEAD')
    tags = api.pages('/tags')
    releases = api.pages('/releases')
    versions = {}
    for tag in tags:
        match = SEMVER.fullmatch(tag['name'])
        if not match:
            if tag['name'].startswith('v'):
                raise ValueError('AMBIGUOUS_VERSION_TAG: ' + tag['name'])
            continue
        version = tuple(map(int, match.groups()))
        if version in versions:
            raise ValueError('AMBIGUOUS_VERSION_TAG: duplicate semantic version')
        versions[version] = tag['name']
    published = [r for r in releases if not r['draft'] and not r.get('prerelease', False)]
    for release in published:
        if not SEMVER.fullmatch(release['tag_name']):
            raise ValueError('AMBIGUOUS_RELEASE_VERSION: migrate legacy non-SemVer release explicitly')
    published.sort(key=lambda r: tuple(map(int, SEMVER.fullmatch(r['tag_name']).groups())))
    previous_release = published[-1] if published else None
    previous_tag, previous = None, None
    if previous_release:
        previous_tag = previous_release['tag_name']
        previous_sha = api.tag_commit(previous_tag)
        if not previous_sha:
            raise ValueError('MISSING_PREVIOUS_TAG')
        git.ancestor(previous_sha, sha)
        previous = git.baseline(previous_sha)
        if not previous.get('legacy'):
            # Public assets are immutable here; report anomalies without deleting them.
            names = {a['name'] for a in previous_release.get('assets', [])}
            if names != {'PTBR.zip'} or len(previous_release['assets']) != 1:
                raise ValueError('UNEXPECTED_PUBLIC_ASSETS: request separately authorized correction')
        if previous['output'] == verified['output'] and not previous.get('legacy'):
            # Compare the uploaded asset with its original publishing receipt,
            # not a newly compressed ZIP (zlib/OS metadata may legitimately differ).
            markers = re.findall(r'<!-- aow4-ptbr-release: (\{[^\n]+\}) -->', previous_release.get('body') or '')
            if len(markers) != 1:
                raise ValueError('MISSING_RELEASE_RECEIPT: inspect prior publication; never invent its ZIP digest')
            published_receipt = json.loads(markers[0])
            asset = previous_release['assets'][0]
            if (published_receipt.get('schema') != 1 or published_receipt.get('commit') != previous_sha
                    or published_receipt.get('output_generation') != verified['generation']
                    or asset.get('state') != 'uploaded' or asset.get('size') != published_receipt.get('archive_size')
                    or asset.get('digest') != 'sha256:' + str(published_receipt.get('archive_sha256'))):
                raise ValueError('PUBLIC_ASSET_CHECKSUM: previous output matches but the published archive does not; inspect without modifying public assets')
            return {'unchanged': True, 'tag': previous_tag}
        version = tuple(map(int, SEMVER.fullmatch(previous_tag).groups()))
        tag = f'v{version[0]}.{version[1]}.{version[2] + 1}'
    else:
        tag = 'v1.0.0'
    for version, existing in versions.items():
        target = api.tag_commit(existing)
        if not target:
            raise ValueError('MISSING_TAG_REF: ' + existing)
        git.ancestor(target, sha)
        if existing != tag and (not previous_tag or version > tuple(map(int, SEMVER.fullmatch(previous_tag).groups()))):
            raise ValueError('ORPHAN_VERSION_TAG: resolve interrupted/ambiguous tag before publishing ' + existing)
    tag_sha = api.tag_commit(tag)
    if tag_sha and tag_sha != sha:
        raise ValueError('TAG_COMMIT_CONFLICT: never retag another commit')
    drafts = [r for r in releases if r['draft'] and r['tag_name'] == tag]
    if len(drafts) > 1:
        raise ValueError('AMBIGUOUS_DRAFTS')
    _, _, rows = toolkit.read()
    current = {'texts': {r['key']: r['PTBR'] for r in rows.values() if not r['passthrough']}}
    body = notes(tag, current, previous, previous_tag)
    published_receipt = {'schema': 1, 'commit': sha, 'output_generation': verified['generation'],
                         'archive_size': len(data), 'archive_sha256': digest(data)}
    body += '\n<!-- aow4-ptbr-release: ' + json.dumps(published_receipt, sort_keys=True, separators=(',', ':')) + ' -->\n'
    if api.request('GET', head_path)['sha'] != sha:
        raise ValueError('STALE_COMMIT: HEAD changed during planning')
    if drafts:
        release = drafts[0]
        if release.get('target_commitish') != sha:
            raise ValueError('DRAFT_COMMIT_CONFLICT')
        release = api.request('PATCH', '/releases/' + str(release['id']), {'name': 'Age of Wonders 4 · PT-BR · ' + tag, 'body': body})
    else:
        release = api.request('POST', '/releases', {'tag_name': tag, 'target_commitish': sha, 'name': 'Age of Wonders 4 · PT-BR · ' + tag,
                                                   'body': body, 'draft': True, 'prerelease': False})
    release_id = str(release['id'])
    assets = api.pages('/releases/' + release_id + '/assets')
    if any(a['name'] != 'PTBR.zip' for a in assets) or len(assets) > 1:
        raise ValueError('UNEXPECTED_DRAFT_ASSETS: review draft; refusing unexpected attachment')
    if assets and not asset_matches(assets[0], data):
        # Only an incomplete upload in this matching draft may be removed.
        api.request('DELETE', '/releases/assets/' + str(assets[0]['id']))
        assets = []
    if not assets:
        upload = release['upload_url'].split('{', 1)[0] + '?name=PTBR.zip'
        asset = api.request('POST', upload, data, binary=True, upload=True)
        if not asset_matches(asset, data):
            raise ValueError('ASSET_CONFIRMATION_FAILED: uploaded bytes/digest not confirmed')
    assets = api.pages('/releases/' + release_id + '/assets')
    if len(assets) != 1 or not asset_matches(assets[0], data):
        raise ValueError('ASSET_CONFIRMATION_FAILED: exact asset set required before publication')
    if api.request('GET', head_path)['sha'] != sha:
        raise ValueError('STALE_COMMIT: leave matching draft to review; no publication')
    api.request('PATCH', '/releases/' + release_id, {'draft': False})
    final = api.request('GET', '/releases/' + release_id)
    assets = api.pages('/releases/' + release_id + '/assets')
    if final['draft'] or final['tag_name'] != tag or len(assets) != 1 or not asset_matches(assets[0], data) or api.tag_commit(tag) != sha:
        raise ValueError('POST_PUBLISH_VERIFICATION_FAILED: inspect release; do not create a replacement')
    return {'published': True, 'tag': tag, 'sha': sha, 'assets': ['PTBR.zip'], 'archive_sha256': digest(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true', required=True)
    parser.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('GITHUB_REPOSITORY') != REPOSITORY:
        raise ValueError('CI_ONLY: publication requires the authorized repository workflow')
    toolkit = Toolkit()
    print(json.dumps(publish(toolkit, GitHub(REPOSITORY, os.environ.get('GITHUB_TOKEN')), Git(toolkit.root),
                             os.environ['GITHUB_SHA'], args.archive), ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
