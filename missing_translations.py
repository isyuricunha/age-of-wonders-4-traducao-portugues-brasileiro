import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import mo_convert


def _entry_key(entry: mo_convert.PoEntry) -> Tuple[Optional[str], str, Optional[str]]:
    return (entry.msgctxt, entry.msgid, entry.msgid_plural)


def _normalize_msgstr(parts: Iterable[str]) -> List[str]:
    return [p or "" for p in parts]


def _is_missing_translation(
    en_entry: mo_convert.PoEntry, pt_entry: mo_convert.PoEntry
) -> bool:
    if pt_entry.msgid == "":
        return False

    en_msgstr = _normalize_msgstr(en_entry.msgstr)
    pt_msgstr = _normalize_msgstr(pt_entry.msgstr)

    if not pt_msgstr or all(s.strip() == "" for s in pt_msgstr):
        return True

    max_len = max(len(en_msgstr), len(pt_msgstr))
    en_msgstr += [""] * (max_len - len(en_msgstr))
    pt_msgstr += [""] * (max_len - len(pt_msgstr))

    return all(pt == en for pt, en in zip(pt_msgstr, en_msgstr))


def _format_missing(
    en_entry: mo_convert.PoEntry, pt_entry: mo_convert.PoEntry
) -> str:
    lines: List[str] = []
    lines.append(f"msgid: {en_entry.msgid}")

    if en_entry.msgctxt is not None:
        lines.append(f"msgctxt: {en_entry.msgctxt}")

    if en_entry.msgid_plural is not None:
        lines.append(f"msgid_plural: {en_entry.msgid_plural}")

    en_msgstr = _normalize_msgstr(en_entry.msgstr)
    pt_msgstr = _normalize_msgstr(pt_entry.msgstr)

    if en_entry.msgid_plural is not None:
        for i, (en_s, pt_s) in enumerate(zip(en_msgstr, pt_msgstr)):
            lines.append(f"en.msgstr[{i}]: {en_s}")
            lines.append(f"pt.msgstr[{i}]: {pt_s}")
    else:
        lines.append(f"en.msgstr: {en_msgstr[0] if en_msgstr else ''}")
        lines.append(f"pt.msgstr: {pt_msgstr[0] if pt_msgstr else ''}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Compare EN and PTBR .po files and list entries that are still identical (missing translation)."
        )
    )
    parser.add_argument(
        "--en",
        type=Path,
        default=Path("EN") / "EN.po",
        help="Path to EN.po (default: EN/EN.po)",
    )
    parser.add_argument(
        "--pt",
        type=Path,
        default=Path("PTBR") / "PTBR.po",
        help="Path to PTBR.po (default: PTBR/PTBR.po)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("falta-traduzir.txt"),
        help='Output TXT file (default: "falta-traduzir.txt")',
    )

    args = parser.parse_args()

    _en_charset, en_entries = mo_convert.read_po(args.en)
    _pt_charset, pt_entries = mo_convert.read_po(args.pt)

    en_by_key: Dict[Tuple[Optional[str], str, Optional[str]], mo_convert.PoEntry] = {
        _entry_key(e): e for e in en_entries if e.msgid != ""
    }

    missing_blocks: List[str] = []
    missing_count = 0

    for pt_entry in pt_entries:
        if pt_entry.msgid == "":
            continue

        key = _entry_key(pt_entry)
        en_entry = en_by_key.get(key)
        if en_entry is None:
            continue

        if _is_missing_translation(en_entry, pt_entry):
            missing_count += 1
            missing_blocks.append(_format_missing(en_entry, pt_entry))

    args.out.write_text("\n\n".join(missing_blocks) + ("\n" if missing_blocks else ""), encoding="utf-8")
    print(f"Missing translations: {missing_count}")
    print(f"Wrote: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
