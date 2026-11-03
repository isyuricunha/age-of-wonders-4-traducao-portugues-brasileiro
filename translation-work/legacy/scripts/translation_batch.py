#!/usr/bin/env python3
"""Batch tooling for the Age of Wonders 4 PT-BR translation overhaul.

Workflow per batch:
  python3 translation_batch.py extract N   -> writes batches/batch-NNN.json and prints it
  (translate by hand: write batches/batch-NNN.pt.json as a positional list)
  python3 translation_batch.py merge N     -> validates and applies into translation-work.json
  python3 translation_batch.py validate    -> full pass over the work file
  python3 translation_batch.py build-po    -> regenerate PTBR/PTBR.po from the JSON
  python3 translation_batch.py build-mo    -> compile .MO via mo_convert.py
"""

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
WORK = REPO / "translation-work.json"
BATCH_DIR = REPO / "batches"
BATCH_SIZE = 500

# Inline markup, icons and format variables: {x}, [tag], [/tag], [icon/], %s...
TOKEN_RE = re.compile(r"\{[^{}]*\}|\[[^\[\]]*\]|%[a-zA-Z@#0-9.]+")
# Gender-switch construct: article may live inside, content translates freely
HERO_RE = re.compile(r"<<[A-Za-z]+\{[^{}]*\}>>")
# Grammar-switch construct (<<G:word^flags,Token>> family: G, ge, Cge):
# token part is fixed, the display word translates freely
G_RE = re.compile(r"<<[Cc]?[Gg]e?:[^<>]*>>")
# Other <<...>> constructs (<<m:{CONCEPT}>> links): content must match exactly
LINK_RE = re.compile(r"<<[^<>]*>>")


def tokens(text: str) -> list[str]:
    out = ["<<Hero>>"] * len(HERO_RE.findall(text))
    rest = HERO_RE.sub(" ", text)
    # Grammar constructs normalize to their fixed token part (after the comma)
    for m in G_RE.findall(rest):
        token = m.split(",")[-1]
        out.append(f"<<G:{token}")
    rest = G_RE.sub(" ", rest)
    out += LINK_RE.findall(rest)
    rest = LINK_RE.sub(" ", rest)
    out += TOKEN_RE.findall(rest)
    return sorted(out)


def load_work() -> dict:
    return json.loads(WORK.read_text(encoding="utf-8"))


def save_work(work: dict) -> None:
    tmp = WORK.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(work, ensure_ascii=False, indent=0), encoding="utf-8")
    tmp.replace(WORK)


def keys_in_order(work: dict) -> list[str]:
    return sorted(work.keys())


def batch_range(n: int, total: int) -> tuple[int, int]:
    start = (n - 1) * BATCH_SIZE
    end = min(start + BATCH_SIZE, total)
    return start, end


def cmd_extract(n: int) -> None:
    work = load_work()
    keys = keys_in_order(work)
    start, end = batch_range(n, len(keys))
    BATCH_DIR.mkdir(exist_ok=True)
    out = []
    for k in keys[start:end]:
        out.append({"key": k, "en": work[k]["en"], "pt_old": work[k]["pt_old"]})
    path = BATCH_DIR / f"batch-{n:03d}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    filled = sum(1 for v in work.values() if v["pt"])
    print(f"batch {n:03d}: strings {start+1}-{end} of {len(keys)} | done so far: {filled}/{len(keys)}")
    print(path)


def cmd_merge(n: int) -> None:
    work = load_work()
    keys = keys_in_order(work)
    start, end = batch_range(n, len(keys))
    batch_keys = keys[start:end]
    path = BATCH_DIR / f"batch-{n:03d}.pt.json"
    pts = json.loads(path.read_text(encoding="utf-8"))
    if len(pts) != len(batch_keys):
        sys.exit(f"ERROR: {len(pts)} translations but batch {n:03d} has {len(batch_keys)} strings")
    problems = []
    for k, pt in zip(batch_keys, pts):
        en = work[k]["en"]
        if pt == "<old>":
            pt = work[k]["pt_old"]
        want, got = tokens(en), tokens(pt)
        if want != got:
            problems.append((k, want, got))
        if en.count("\\n") != pt.count("\\n"):
            problems.append((k, f"\\n x{en.count(chr(92)+'n')}", f"\\n x{pt.count(chr(92)+'n')}"))
    if problems:
        for k, a, b in problems[:10]:
            print(f"  MISMATCH {k}:\n    want {a}\n    got  {b}")
        sys.exit(f"ERROR: {len(problems)} strings with placeholder/escape mismatches")
    for k, pt in zip(batch_keys, pts):
        work[k]["pt"] = work[k]["pt_old"] if pt == "<old>" else pt
    save_work(work)
    hist_dir = BATCH_DIR / "history"
    hist_dir.mkdir(exist_ok=True)
    hist = {k: work[k]["pt"] for k in batch_keys if work[k]["pt"] != work[k]["pt_old"]}
    (hist_dir / f"batch-{n:03d}.json").write_text(
        json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    path.unlink()
    filled = sum(1 for v in work.values() if v["pt"])
    print(f"batch {n:03d} merged: {len(batch_keys)} strings | progress {filled}/{len(work)}")


def cmd_validate() -> None:
    work = load_work()
    bad = []
    for k, v in work.items():
        if v["pt"] and tokens(v["en"]) != tokens(v["pt"]):
            bad.append(k)
        if v["pt"] and v["en"].count("\\n") != v["pt"].count("\\n"):
            bad.append(k)
    filled = sum(1 for v in work.values() if v["pt"])
    print(f"progress: {filled}/{len(work)} | mismatches: {len(bad)}")
    for k in bad[:10]:
        print(" ", k)


def cmd_build_po() -> None:
    work = load_work()
    out = ['msgid ""', 'msgstr "Content-Type: text/plain; charset=UTF-8\\n"', '""', ""]
    for k in keys_in_order(work):
        pt = work[k]["pt"]
        if not pt:
            continue
        esc = lambda s: s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
        out.append(f'msgid "{esc(k)}"')
        out.append(f'msgstr "{esc(pt)}"')
        out.append("")
    (REPO / "PTBR" / "PTBR.po").write_text("\n".join(out), encoding="utf-8")
    print(f"PTBR.po rebuilt with {sum(1 for v in work.values() if v['pt'])} strings")


def cmd_build_mo() -> None:
    subprocess.run([sys.executable, str(REPO / "mo_convert.py")], cwd=REPO, check=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "extract":
        cmd_extract(int(sys.argv[2]))
    elif cmd == "merge":
        cmd_merge(int(sys.argv[2]))
    elif cmd == "validate":
        cmd_validate()
    elif cmd == "build-po":
        cmd_build_po()
    elif cmd == "build-mo":
        cmd_build_mo()
    else:
        sys.exit("usage: translation_batch.py extract|merge N | validate | build-po | build-mo")
