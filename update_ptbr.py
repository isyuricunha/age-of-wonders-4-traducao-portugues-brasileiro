import argparse
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import mo_convert

def _entry_key(entry: mo_convert.PoEntry) -> Tuple[Optional[str], str, Optional[str]]:
    return (entry.msgctxt, entry.msgid, entry.msgid_plural)

def main() -> int:
    parser = argparse.ArgumentParser(description="Update PTBR.po with missing strings from EN.po")
    parser.add_argument("--en", type=Path, default=Path("EN") / "EN.po", help="Path to EN.po")
    parser.add_argument("--pt", type=Path, default=Path("PTBR") / "PTBR.po", help="Path to PTBR.po")
    parser.add_argument("--out", type=Path, default=Path("PTBR") / "PTBR_updated.po", help="Path to output updated PTBR.po")

    args = parser.parse_args()

    print(f"Loading {args.en}...")
    en_charset, en_entries = mo_convert.read_po(args.en)
    
    print(f"Loading {args.pt}...")
    pt_charset, pt_entries = mo_convert.read_po(args.pt)

    pt_by_key: Dict[Tuple[Optional[str], str, Optional[str]], mo_convert.PoEntry] = {
        _entry_key(e): e for e in pt_entries
    }

    updated_entries = []
    added_count = 0

    for en_entry in en_entries:
        key = _entry_key(en_entry)
        pt_entry = pt_by_key.get(key)

        if pt_entry is not None:
            updated_entries.append(pt_entry)
        else:
            # We must create a new entry with the same msgid as EN.
            # Here we just use the entire EN entry (so msgstr is initially in English).
            # This matches "tambem nao vai ter msgstr" (so we provide the default EN msgstr).
            # Wait, if we use empty string for msgstr it might be better, but we will use the original msgstr from EN to guarantee it works.
            # I will create a copy here to avoid object reference issues.
            new_entry = mo_convert.PoEntry(
                msgctxt=en_entry.msgctxt,
                msgid=en_entry.msgid,
                msgid_plural=en_entry.msgid_plural,
                msgstr=list(en_entry.msgstr)
            )
            updated_entries.append(new_entry)
            added_count += 1

    print(f"Writing {args.out}...")
    mo_convert.write_po(args.out, updated_entries)
    print(f"Added {added_count} missing entries from EN.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
