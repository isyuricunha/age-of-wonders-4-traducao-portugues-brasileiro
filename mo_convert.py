"""Compatibility for the preserved legacy PO/MO utility (AGPL-3.0)."""
import importlib.util
import sys
from pathlib import Path
_impl = Path(__file__).resolve().parent / "translation-work/legacy/scripts/mo_convert.py"
_spec = importlib.util.spec_from_file_location("aow4_legacy_mo_convert", _impl)
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
for _name in dir(_module):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_module, _name)
def main():
    # Standalone legacy exports must never bypass the canonical build/source gates.
    parser = _module.argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('to-po', 'to-mo'):
        child = sub.add_parser(command)
        child.add_argument('input', type=Path)
        child.add_argument('output', type=Path)
    args = parser.parse_args()
    target = args.output.resolve()
    root = Path(__file__).resolve().parent
    protected = [root / 'EN', root / 'PTBR', root / '.git']
    if any(target.is_relative_to(path.resolve()) for path in protected) or (
        target.is_relative_to((root / 'translation-work').resolve())
        and not target.is_relative_to((root / 'translation-work/reports').resolve())
    ):
        raise SystemExit('Managed resources are protected: use translation-work/toolkit.py build, sync or update-sources. Export standalone files elsewhere.')
    if args.command == 'to-po':
        _, entries = _module.read_mo(args.input)
        _module.write_po(args.output, entries)
    else:
        charset, entries = _module.read_po(args.input)
        _module.write_mo(args.output, entries, charset)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
