"""Strict, dependency-free AoW4 gettext catalog adapter. SPDX-License-Identifier: AGPL-3.0-only."""
from __future__ import annotations

import re
import struct
from dataclasses import dataclass


class FormatError(ValueError):
    pass


@dataclass(frozen=True)
class Catalog:
    pairs: tuple[tuple[str, str], ...]
    raw: bytes


def parse(data: bytes) -> Catalog:
    if len(data) < 28:
        raise FormatError("MALFORMED_INPUT: MO header is truncated")
    magic = data[:4]
    endian = {b'\xde\x12\x04\x95': '<', b'\x95\x04\x12\xde': '>'}.get(magic)
    if endian is None:
        raise FormatError("MALFORMED_INPUT: invalid gettext MO magic")
    _, revision, count, original, translated, hsize, hoff = struct.unpack(endian + '7I', data[:28])
    if revision != 0:
        raise FormatError(f"UNSUPPORTED_FORMAT: MO revision {revision}")
    for offset, size in ((original, count * 8), (translated, count * 8), (hoff, hsize * 4)):
        if offset + size > len(data) or (size and offset < 28):
            raise FormatError("MALFORMED_INPUT: table outside catalog")
    tables = []
    for table in (original, translated):
        strings = []
        for i in range(count):
            size, offset = struct.unpack_from(endian + '2I', data, table + 8 * i)
            if offset < 28 or offset + size >= len(data) or data[offset + size] != 0:
                raise FormatError("MALFORMED_INPUT: string outside catalog or missing NUL")
            try:
                text = data[offset:offset + size].decode('utf-8', errors='strict')
            except UnicodeDecodeError as exc:
                raise FormatError("UNSUPPORTED_ENCODING: this AoW4 adapter requires UTF-8") from exc
            if '\x00' in text or '\x04' in text:
                raise FormatError("UNSUPPORTED_FORMAT: context/plural catalogs are not this game's verified profile")
            strings.append(text)
        tables.append(strings)
    pairs = tuple(zip(*tables))
    seen = {}
    for key, value in pairs:
        opaque = bool(key and value and set(key) == set(value) == {'@'})
        if key in seen and not (opaque and seen[key]):
            raise FormatError(f"AMBIGUOUS_ID: duplicate non-obfuscated key {key!r}")
        seen[key] = opaque
    return Catalog(pairs, data)


def encode(pairs, original: Catalog | None = None) -> bytes:
    pairs = tuple(pairs)
    if original is not None and pairs == original.pairs:
        return original.raw
    count = len(pairs)
    pool_offset = 28 + 16 * count
    pool = bytearray()
    tables = []
    for column in (0, 1):
        table = bytearray()
        for pair in pairs:
            raw = pair[column].encode('utf-8', errors='strict')
            if b'\x00' in raw or b'\x04' in raw:
                raise FormatError('UNSUPPORTED_FORMAT: embedded native separators')
            padding = (-(pool_offset + len(pool))) % 4
            pool.extend(b'\0' * padding)
            table.extend(struct.pack('<2I', len(raw), pool_offset + len(pool)))
            pool.extend(raw + b'\0')
        tables.append(table)
    data = struct.pack('<7I', 0x950412DE, 0, count, 28, 28 + count * 8, 0, 0)
    data += bytes(tables[0] + tables[1] + pool)
    if parse(data).pairs != pairs:
        raise FormatError('ROUNDTRIP_FAILED: reconstructed catalog differs')
    return data


def passthrough(key: str, value: str) -> bool:
    return bool(key and value and set(key) == set(value) == {'@'})


def context(key: str, text: str) -> dict:
    """Expose evidence, never infer agreement from a name or a speaker alone."""
    scope = key.split('@')
    evidence = []
    for marker in ('FEMALE', 'MALE'):
        if re.search(r'(?:^|_)' + marker + r'(?:_|$)', key):
            evidence.append({'source': 'native key', 'value': marker, 'certainty': 'explicit name-bank classification',
                             'role': 'generated name category; not proof of dialogue speaker/addressee/referent'})
    if 'Speaker_' in key or key.startswith('Script'):
        evidence.append({'source': 'native key', 'value': key, 'certainty': 'identifier clue only',
                         'role': 'unverified speaker association; name alone does not prove gender'})
    variables = sorted(set(re.findall(r'\{([^{}]+)\}', text)))
    return {'scope': scope[:-1], 'category': scope[0], 'variables': variables,
            'speaker': 'unknown', 'addressee': 'unknown', 'referent': 'dynamic or unknown' if variables else 'unknown',
            'gender_evidence': evidence, 'limitation': 'Catalog has no authoritative dialogue speaker mapping; inspect related native keys and gameplay.'}
