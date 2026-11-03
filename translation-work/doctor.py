"""Read-only Ubuntu 24.04 ARM64 preflight. SPDX-License-Identifier: AGPL-3.0-only."""
import json
import platform
import sys

import native
from storage import digest, json_bytes, normalized


def integrity(toolkit):
    def required(path):
        try:
            return toolkit.path(path).read_bytes()
        except FileNotFoundError as exc:
            raise ValueError(f'MISSING_DEPENDENCY: {path}; restore complete matching Git checkout') from exc
    runtime = json.loads(required('translation-work/runtime-support.json'))
    toolchain_path = 'translation-work/toolchain.json'
    if digest(normalized(required(toolchain_path))) != runtime['toolchain_sha256']:
        raise ValueError('CHECKSUM_MISMATCH: toolchain.json; restore correct Git checkout, do not regenerate hashes')
    toolchain = json.loads(required(toolchain_path))
    for path, checksum in toolchain['files'].items():
        data = required(path)
        if digest(normalized(data)) != checksum:
            raise ValueError(f'CHECKSUM_MISMATCH: {path}; restore matching version from Git')
    manifest, _, _ = toolkit.read()
    for path, checksum in manifest['resources'].items():
        if digest(toolkit.path('EN/' + path).read_bytes()) != checksum:
            raise ValueError(f'CHECKSUM_MISMATCH: EN/{path}; run authorized source synchronization')
    return runtime


def run(toolkit, *, require_arm64=True, system=None, machine=None):
    if sys.version_info < (3, 10):
        raise ValueError('MISSING_RUNTIME: Python >=3.10 required; Ubuntu 24.04 system Python is suitable')
    simulated = system is not None or machine is not None
    system, machine = system or platform.system(), machine or platform.machine()
    if require_arm64 and (system != 'Linux' or machine.lower() not in ('aarch64', 'arm64')):
        raise ValueError(f'UNSUPPORTED_ARCHITECTURE: expected Linux aarch64/arm64; got {system}/{machine}. On Windows use doctor --developer only for local checks.')
    if require_arm64 and not simulated:
        distribution = platform.freedesktop_os_release()
        if distribution.get('ID') != 'ubuntu' or distribution.get('VERSION_ID') != '24.04':
            raise ValueError('UNSUPPORTED_RUNTIME: expected Ubuntu Server 24.04 LTS; report actual /etc/os-release before proceeding')
    runtime = integrity(toolkit)
    # Real AoW4 shape: immutable IDs in msgid, English text in msgstr, opaque duplicates.
    pairs = [('INTERFACE@FIXTURE@NAME', 'ação {Player.Name} [b]x[/b]'),
             ('STORY_EVENT@FIXTURE@BODY', 'Line one\nLine two\t"quoted"'), ('@@', '@@@'), ('@@', '@@@@')]
    raw = native.encode(pairs)
    parsed = native.parse(raw)
    if parsed.pairs != tuple(pairs) or native.encode(parsed.pairs, parsed) != raw:
        raise ValueError('MALFORMED_TEST_DATA: synthetic native roundtrip failed')
    candidate = list(parsed.pairs)
    candidate[0] = (candidate[0][0], 'fixture {Player.Name} [b]safe[/b]')
    if native.parse(native.encode(candidate)).pairs != tuple(candidate):
        raise ValueError('PARSER_RECONSTRUCTION_FAILED: safe fixture rewrite differs')
    resources, actual = toolkit.source()
    if native.encode(actual.pairs, actual) != resources['Language/EN/EN.MO']:
        raise ValueError('PARSER_RECONSTRUCTION_FAILED: actual source no-op differs')
    return {'valid': True, 'system': system, 'machine': machine, 'python': platform.python_version(),
            'read_only': True, 'dependencies': 'Python standard library only; no Mono, DLL, .NET or downloaded helper',
            'fixture_roundtrip': 'passed', 'source_noop': 'byte-identical',
            'target': runtime['target'], 'target_execution': 'simulated fixture' if simulated else ('passed on this host' if require_arm64 else 'not verified; local developer preflight only')}
