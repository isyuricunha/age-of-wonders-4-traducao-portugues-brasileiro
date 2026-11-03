"""Evidence-linked context, with explicit role separation. AGPL-3.0-only."""
import re
from storage import digest


class ContextIndex:
    def __init__(self, pairs, reference=None):
        self.source = dict(pairs)
        self.reference = reference or {}
        if self.reference and (self.reference.get('schema') != 1 or self.reference.get('source_file') != 'Language/EN/EN.MO'):
            raise ValueError('INVALID_CONTEXT_REFERENCE: unsupported schema/source mapping')
        self.characters = {}
        for item in self.reference.get('characters', []):
            if item['gender'] not in ('female', 'male', 'unknown', 'dynamic') or item['id'] in self.characters:
                raise ValueError('INVALID_CONTEXT_REFERENCE: gender domain or duplicate identity')
            key = item['biography_key']
            actual = digest(self.source[key].encode('utf-8')) if key in self.source else None
            valid = actual == item['EN_sha256']
            self.characters[item['id']] = {'identity': item['id'], 'evidence_key': key,
                'source_file': self.reference['source_file'], 'source_sha256': actual,
                'gender': item['gender'] if valid else 'unknown',
                'certainty': 'verified described person in biography' if valid else 'biography changed or missing; review evidence',
                'aliases': item.get('aliases', []), 'valid': valid}

    def enrich(self, key, text, base):
        if not self.characters:
            return base
        identifiers = {x.upper() for x in re.findall(r'[A-Za-z0-9]+', key)}
        identifiers.update(v.split('.')[0].upper() for v in base['variables'])
        related = []
        for character in self.characters.values():
            if key == character['evidence_key'] or any(alias.upper() in identifiers for alias in character['aliases']):
                record = {k: v for k, v in character.items() if k not in ('aliases', 'valid')}
                record['role'] = 'described referent' if key == character['evidence_key'] else 'identifier clue; role and identity not established'
                related.append(record)
                if key == character['evidence_key']:
                    base['referent'] = character['identity']
                    base['gender_evidence'].append({**record, 'role': 'referent'})
        # Bindings require separately recorded, hash-verified evidence; none is
        # invented from Script/character names. The real profile has no proven
        # dialogue bindings. Future verified evidence can be added explicitly.
        for binding in self.reference.get('bindings', []):
            if binding['key'] != key:
                continue
            role = binding['role']
            if role not in ('speaker', 'addressee', 'referent'):
                raise ValueError('INVALID_CONTEXT_ROLE')
            character = self.characters[binding['character']]
            proof = binding.get('evidence', [])
            confirmed = bool(proof) and all(p['key'] in self.source and digest(self.source[p['key']].encode('utf-8')) == p['EN_sha256'] for p in proof)
            base[role] = character['identity'] if confirmed else 'unknown'
            base['gender_evidence'].append({'role': role, 'identity': character['identity'],
                'gender': character['gender'] if confirmed else 'unknown', 'evidence': proof,
                'certainty': 'explicit verified role binding' if confirmed else 'role evidence changed or missing',
                'biography_sha256': character['source_sha256']})
        if related:
            base['related_characters'] = related
        return base
