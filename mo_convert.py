import argparse
import ast
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class PoEntry:
    msgctxt: Optional[str]
    msgid: str
    msgid_plural: Optional[str]
    msgstr: List[str]


def _detect_charset_from_header(header_msgstr: str) -> str:
    m = re.search(r"charset=([^\\s;]+)", header_msgstr, flags=re.IGNORECASE)
    if not m:
        return "utf-8"
    return m.group(1).strip().strip('"')


def _po_escape(s: str) -> str:
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("\t", "\\t")
    s = s.replace("\r", "\\r")
    s = s.replace("\n", "\\n")
    return s


def _po_quote(s: str) -> List[str]:
    if s == "":
        return ['""']

    parts = s.split("\n")
    lines: List[str] = []
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            lines.append('"' + _po_escape(part + "\n") + '"')
        else:
            lines.append('"' + _po_escape(part) + '"')
    return lines


def read_mo(path: Path) -> Tuple[str, List[PoEntry]]:
    data = path.read_bytes()
    if len(data) < 28:
        raise ValueError("Invalid .mo: too small")

    magic_le = struct.unpack("<I", data[0:4])[0]
    magic_be = struct.unpack(">I", data[0:4])[0]

    if magic_le == 0x950412DE:
        endian = "<"
    elif magic_be == 0x950412DE:
        endian = ">"
    else:
        raise ValueError("Invalid .mo: bad magic")

    (revision, n, off_orig, off_trans, _hash_size, _hash_off) = struct.unpack(
        endian + "6I", data[4:28]
    )

    if revision != 0:
        raise ValueError(f"Unsupported .mo revision: {revision}")

    def read_table(off: int) -> List[Tuple[int, int]]:
        out: List[Tuple[int, int]] = []
        for i in range(n):
            l, o = struct.unpack(endian + "2I", data[off + i * 8 : off + i * 8 + 8])
            out.append((l, o))
        return out

    orig_table = read_table(off_orig)
    trans_table = read_table(off_trans)

    raw_pairs: List[Tuple[bytes, bytes]] = []
    for (ol, oo), (tl, to) in zip(orig_table, trans_table):
        o = data[oo : oo + ol]
        t = data[to : to + tl]
        raw_pairs.append((o, t))

    header_msgstr_bytes = None
    for o, t in raw_pairs:
        if o == b"":
            header_msgstr_bytes = t
            break

    header_charset = "utf-8"
    header_msgstr = ""
    if header_msgstr_bytes is not None:
        header_msgstr = header_msgstr_bytes.decode("utf-8", errors="replace")
        header_charset = _detect_charset_from_header(header_msgstr)

    entries: List[PoEntry] = []

    def decode(b: bytes) -> str:
        try:
            return b.decode(header_charset)
        except Exception:
            return b.decode("utf-8", errors="replace")

    for o_b, t_b in raw_pairs:
        msgid_raw = decode(o_b)
        msgstr_raw = decode(t_b)

        msgctxt = None
        msgid = msgid_raw
        msgid_plural = None

        if "\x04" in msgid_raw:
            msgctxt, msgid = msgid_raw.split("\x04", 1)

        if "\x00" in msgid:
            msgid, msgid_plural = msgid.split("\x00", 1)

        msgstr_parts = msgstr_raw.split("\x00") if "\x00" in msgstr_raw else [msgstr_raw]

        entries.append(
            PoEntry(
                msgctxt=msgctxt,
                msgid=msgid,
                msgid_plural=msgid_plural,
                msgstr=msgstr_parts,
            )
        )

    return header_charset, entries


def write_po(path: Path, entries: List[PoEntry]) -> None:
    out_lines: List[str] = []

    for e in entries:
        if e.msgctxt is not None:
            out_lines.append("msgctxt " + _po_quote(e.msgctxt)[0])
            for cont in _po_quote(e.msgctxt)[1:]:
                out_lines.append(cont)

        out_lines.append("msgid " + _po_quote(e.msgid)[0])
        for cont in _po_quote(e.msgid)[1:]:
            out_lines.append(cont)

        if e.msgid_plural is not None:
            out_lines.append("msgid_plural " + _po_quote(e.msgid_plural)[0])
            for cont in _po_quote(e.msgid_plural)[1:]:
                out_lines.append(cont)

            for i, s in enumerate(e.msgstr):
                quoted = _po_quote(s)
                out_lines.append(f"msgstr[{i}] " + quoted[0])
                for cont in quoted[1:]:
                    out_lines.append(cont)
        else:
            quoted = _po_quote(e.msgstr[0] if e.msgstr else "")
            out_lines.append("msgstr " + quoted[0])
            for cont in quoted[1:]:
                out_lines.append(cont)

        out_lines.append("")

    path.write_text("\n".join(out_lines), encoding="utf-8", newline="\n")


def _parse_po_string_literal(s: str) -> str:
    s = s.strip()
    if not s.startswith('"'):
        return ""
    try:
        return ast.literal_eval(s)
    except Exception:
        return ""


def read_po(path: Path) -> Tuple[str, List[PoEntry]]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    entries: List[PoEntry] = []
    cur: Optional[PoEntry] = None
    active_key: Optional[Tuple[str, Optional[int]]] = None

    def flush() -> None:
        nonlocal cur
        if cur is None:
            return
        if cur.msgid == "" and cur.msgstr:
            charset = _detect_charset_from_header(cur.msgstr[0])
            nonlocal_header[0] = charset
        entries.append(cur)
        cur = None

    nonlocal_header = ["utf-8"]

    for raw in lines + [""]:
        line = raw.strip()

        if line == "":
            flush()
            active_key = None
            continue

        if line.startswith("#"):
            continue

        if line.startswith("msgctxt"):
            if cur is None:
                cur = PoEntry(None, "", None, [])
            cur.msgctxt = _parse_po_string_literal(line[len("msgctxt") :].strip())
            active_key = ("msgctxt", None)
            continue

        if line.startswith("msgid_plural"):
            if cur is None:
                cur = PoEntry(None, "", None, [])
            cur.msgid_plural = _parse_po_string_literal(line[len("msgid_plural") :].strip())
            active_key = ("msgid_plural", None)
            continue

        if line.startswith("msgid"):
            if cur is None:
                cur = PoEntry(None, "", None, [])
            cur.msgid = _parse_po_string_literal(line[len("msgid") :].strip())
            active_key = ("msgid", None)
            continue

        m = re.match(r"^msgstr\[(\d+)\]", line)
        if m:
            if cur is None:
                cur = PoEntry(None, "", None, [])
            idx = int(m.group(1))
            lit = line[m.end() :].strip()
            s = _parse_po_string_literal(lit)
            while len(cur.msgstr) <= idx:
                cur.msgstr.append("")
            cur.msgstr[idx] = s
            active_key = ("msgstr", idx)
            continue

        if line.startswith("msgstr"):
            if cur is None:
                cur = PoEntry(None, "", None, [])
            s = _parse_po_string_literal(line[len("msgstr") :].strip())
            if cur.msgstr:
                cur.msgstr[0] = s
            else:
                cur.msgstr = [s]
            active_key = ("msgstr", 0)
            continue

        if line.startswith('"') and active_key is not None and cur is not None:
            frag = _parse_po_string_literal(line)
            k, idx = active_key
            if k == "msgctxt":
                cur.msgctxt = (cur.msgctxt or "") + frag
            elif k == "msgid":
                cur.msgid = cur.msgid + frag
            elif k == "msgid_plural":
                cur.msgid_plural = (cur.msgid_plural or "") + frag
            elif k == "msgstr" and idx is not None:
                while len(cur.msgstr) <= idx:
                    cur.msgstr.append("")
                cur.msgstr[idx] = cur.msgstr[idx] + frag
            continue

    return nonlocal_header[0], entries


def write_mo(path: Path, entries: List[PoEntry], charset: str) -> None:
    by_key: Dict[bytes, bytes] = {}

    def enc(s: str) -> bytes:
        try:
            return s.encode(charset)
        except Exception:
            return s.encode("utf-8")

    header_present = any(e.msgid == "" for e in entries)
    if not header_present:
        header = "Content-Type: text/plain; charset=UTF-8\n"
        entries = [PoEntry(None, "", None, [header])] + entries

    for e in entries:
        if e.msgctxt is not None:
            key = f"{e.msgctxt}\x04{e.msgid}"
        else:
            key = e.msgid

        if e.msgid_plural is not None:
            key = key + "\x00" + (e.msgid_plural or "")
            val = "\x00".join(e.msgstr)
        else:
            val = e.msgstr[0] if e.msgstr else ""

        by_key[enc(key)] = enc(val)

    keys = sorted(by_key.keys())
    values = [by_key[k] for k in keys]

    n = len(keys)

    header_size = 28
    orig_table_off = header_size
    trans_table_off = orig_table_off + n * 8
    string_pool_off = trans_table_off + n * 8

    def align4(x: int) -> int:
        return (x + 3) & ~3

    offsets_o: List[Tuple[int, int]] = []
    offsets_t: List[Tuple[int, int]] = []

    pool = bytearray()
    cur_off = string_pool_off

    for k in keys:
        cur_off = align4(cur_off)
        if len(pool) < cur_off - string_pool_off:
            pool.extend(b"\x00" * (cur_off - string_pool_off - len(pool)))
        offsets_o.append((len(k), cur_off))
        pool.extend(k + b"\x00")
        cur_off += len(k) + 1

    for v in values:
        cur_off = align4(cur_off)
        if len(pool) < cur_off - string_pool_off:
            pool.extend(b"\x00" * (cur_off - string_pool_off - len(pool)))
        offsets_t.append((len(v), cur_off))
        pool.extend(v + b"\x00")
        cur_off += len(v) + 1

    out = bytearray()
    out.extend(struct.pack("<I", 0x950412DE))
    out.extend(struct.pack("<I", 0))
    out.extend(struct.pack("<I", n))
    out.extend(struct.pack("<I", orig_table_off))
    out.extend(struct.pack("<I", trans_table_off))
    out.extend(struct.pack("<I", 0))
    out.extend(struct.pack("<I", 0))

    for l, o in offsets_o:
        out.extend(struct.pack("<II", l, o))

    for l, o in offsets_t:
        out.extend(struct.pack("<II", l, o))

    out.extend(pool)

    path.write_bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("to-po")
    p1.add_argument("input_mo", type=Path)
    p1.add_argument("output_po", type=Path)

    p2 = sub.add_parser("to-mo")
    p2.add_argument("input_po", type=Path)
    p2.add_argument("output_mo", type=Path)

    args = parser.parse_args()

    if args.cmd == "to-po":
        _charset, entries = read_mo(args.input_mo)
        write_po(args.output_po, entries)
        return 0

    if args.cmd == "to-mo":
        charset, entries = read_po(args.input_po)
        write_mo(args.output_mo, entries, charset)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
