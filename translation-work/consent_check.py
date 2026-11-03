"""Check affirmative PR permission without writing a consent. AGPL-3.0-only."""
import json
import os
from pathlib import Path
import sys


def check(event, template):
    pr = event.get('pull_request', {})
    body = pr.get('body') or ''
    declarations = [line[6:] for line in template.splitlines() if line.startswith('- [ ] ')]
    if len(declarations) != 3 or any('- [x] ' + text not in body and '- [X] ' + text not in body for text in declarations):
        raise ValueError('CONSENT_REQUIRED: contributor must personally affirm all three declarations; never infer consent')
    if not pr.get('user', {}).get('login') or not pr.get('html_url') or not pr.get('head', {}).get('sha'):
        raise ValueError('CONSENT_SCOPE_REQUIRED: missing contributor, PR URL or revision')
    return {'contributor': pr['user']['login'], 'scope': pr['head']['sha'], 'evidence': pr['html_url'],
            'affirmative': True, 'review_required': 'Verify authorship, requested credit and scope before merging.'}


if __name__ == '__main__':
    try:
        root = Path(__file__).resolve().parent.parent
        print(json.dumps(check(json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_bytes()),
                               (root / '.github/pull_request_template.md').read_text(encoding='utf-8'))))
    except (ValueError, KeyError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
