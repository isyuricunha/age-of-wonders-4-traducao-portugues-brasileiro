#!/usr/bin/env python3
"""Sync translation-work.json with a freshly regenerated EN.po.

- Regenerate EN/EN.po from EN/EN.MO (mo_convert to-po).
- Keys 1:1 with EN.po msgids (no msgctxt/plural in this game).
- New keys: en from new po, pt_old = "", pt = "" (needs translation).
- Removed keys: dropped from the work file.
- Changed en text: en updated, pt_old = old pt, pt cleared (needs re-translation).
- Unchanged keys: untouched (pt kept).
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import mo_convert

WORK = REPO / "translation-work.json"


def main() -> int:
    en_po = REPO / "EN" / "EN.po"
    en_mo = REPO / "EN" / "EN.MO"

    subprocess.run(
        [sys.executable, str(REPO / "mo_convert.py"), "to-po", str(en_mo), str(en_po)],
        cwd=REPO, check=True,
    )
    _charset, entries = mo_convert.read_po(en_po)
    new_map = {e.msgid: e.msgstr[0] if e.msgstr else "" for e in entries if e.msgid != ""}

    work = json.loads(WORK.read_text(encoding="utf-8"))

    added, removed, changed, kept = 0, 0, 0, 0
    out = {}
    for msgid, en_text in new_map.items():
        old = work.get(msgid)
        if old is None:
            out[msgid] = {"en": en_text, "pt_old": "", "pt": ""}
            added += 1
        else:
            if old["en"] != en_text:
                out[msgid] = {"en": en_text, "pt_old": old.get("pt") or old.get("pt_old") or "", "pt": ""}
                changed += 1
            else:
                out[msgid] = old
                kept += 1
    for msgid in work:
        if msgid not in new_map:
            removed += 1

    tmp = WORK.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    tmp.replace(WORK)
    print(f"sync done: added={added} changed={changed} removed={removed} kept={kept} total={len(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
