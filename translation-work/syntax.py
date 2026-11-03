"""Structural checks; no linguistic decisions. SPDX-License-Identifier: AGPL-3.0-only."""
import re
from collections import Counter

TOKEN = re.compile(r'\{[^{}]*\}|\[[^\[\]]*\]|%[a-zA-Z@#0-9.]+')
HERO = re.compile(r'<<[A-Za-z]+\{[^{}]*\}>>')
GRAMMAR = re.compile(r'<<[Cc]?[Gg]e?:[^<>]*>>')
LINK = re.compile(r'<<[^<>]*>>')


def tokens(text):
    out = []
    for construct in HERO.findall(text):
        selector, body = re.fullmatch(r'<<([A-Za-z]+)\{([^{}]*)\}>>', construct).groups()
        # m{resource} is a malformed-but-native reference in the supplied catalog,
        # not a translatable choice. Preserve it exactly.
        out.append(construct if selector == 'm' else f'<<selector:{selector}:{body.count("/") + 1}>>')
    text = HERO.sub(' ', text)
    for construct in GRAMMAR.findall(text):
        out.append('<<G:' + construct.split(',')[-1])
    text = GRAMMAR.sub(' ', text)
    out += LINK.findall(text)
    text = LINK.sub(' ', text)
    out += TOKEN.findall(text)
    return Counter(out)


def errors(en, pt):
    if not isinstance(pt, str) or '\x00' in pt or '\x04' in pt:
        return ['PTBR must be a string without native separators']
    if not pt:
        return []
    problems = []
    markers = {'M', 'F', 'z', 'n', 'N', 'a', 'm', 'p', 'f', 'ns', 'x', 'P', 's', 'Ng'}
    source_markers = Counter(re.findall(r'\^([A-Za-z]+)', en))
    target_markers = Counter(re.findall(r'\^([A-Za-z]+)', pt))
    if set(target_markers) - markers:
        problems.append('unknown native name/composition marker')
    if any(source_markers[m] != target_markers[m] for m in ('M', 'F', 'N', 'P')):
        problems.append('native name/gender marker multiplicity differs')
    # The existing project's documented pronoun/possessive rewrites are retained.
    # Bare referenced variables remain mandatory; no prefix-based equivalence.
    pro = re.compile(r'<<\s*(?:C?[oPpr]|C?g|in)\s*:', re.I)
    pro_args = set(re.findall(r'<<\s*(?:C?[oPpr]|C?g|in)\s*:([A-Za-z0-9_.{}]+)>>', en, re.I))
    pro_args = {a.strip('{}') for a in pro_args}
    for body in re.findall(r'<<[Cc]?[Gg]e?:([^<>]*)>>', en):
        if ',' in body:
            word, arg = body.rsplit(',', 1)
            pro_args.add(arg.strip('{}'))
            pro_args.update(re.findall(r'\{([^{}]*)\}', word))
    grammatical = r"<<[A-Za-z]+\{(?:bows/curtsies|he's/she's)\}>>"
    want = Counter({t: c for t, c in tokens(re.sub(grammatical, '', en)).items() if not pro.match(t)})
    got = Counter({t: c for t, c in tokens(re.sub(grammatical, '', pt)).items() if not pro.match(t)})
    for token, count in (want - got).items():
        problems.append(f'missing {token} x{count}')
    for token, count in (got - want).items():
        mention = re.fullmatch(r'<<m:([A-Za-z0-9_.{}]+)>>|<<(\d+)>>', token)
        promoted = (mention.group(1) or mention.group(2)).strip('{}') if mention else token.strip('{}')
        if promoted not in pro_args:
            problems.append(f'extra {token} x{count}')
    if en.count('\\n') != pt.count('\\n'):
        problems.append('literal newline escape count differs')
    # Actual newline counts may legitimately differ in prose; control bytes may not.
    for control in ('\t', '\r'):
        if en.count(control) != pt.count(control):
            problems.append(f'control {control!r} count differs')
    def nesting(text):
        stack, faults = [], []
        for tag in re.findall(r'\[([^\[\]]+)\]', text):
            if tag.endswith('/') or tag.lower() in ('br', 'bullet'):
                continue
            name = re.split('[,= ]', tag.lstrip('/'))[0]
            if tag.startswith('/'):
                if not stack or stack[-1] != name:
                    faults.append(tag)
                else:
                    stack.pop()
            else:
                stack.append(name)
        return faults, stack
    if nesting(en) != nesting(pt):
        problems.append('rich-text nesting differs from source')
    return problems
