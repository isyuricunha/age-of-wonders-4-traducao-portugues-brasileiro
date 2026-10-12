#!/usr/bin/env python3
"""Check translations: capitalization, preposition contractions, token presence.

Exit codes: 0 = no errors; 1 = errors found.
Capitalization rule (Yuri): the first word of every displayed sentence/segment is
capitalized, unless the sentence opens with a variable/construct token, a digit,
a gender marker (^f/^m/^z/^a...) or is a name-bank fragment mirrored from a
lowercase EN (epithets, item adjectives like "do Ceifador^a").
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORK = REPO / "translation-work.json"
sys.path.insert(0, str(REPO))

TOKEN = re.compile(r"\{[^{}]*\}|<<[^<>]*>>|\[[^\[\]]*\]")
SEG = re.compile(r"\[br/\]|\[br\]|\[bullet/\]|\[bulletlist\]|\[/bulletlist\]")

# Contraction patterns that are always wrong in PT-BR. The grammar-correct
# "de a/o" before an infinitive-clause subject ("antes de o Cavaleiro explodir")
# is allowed via ALLOW_DE_ARTICLE below.
PAT_DE_ART = re.compile(r"\b[Dd]e\s+(?:o|a|os|as)\b")
PAT_MIXED = re.compile(r"\b(?:[Dd]a\s+o|[Dd]o\s+a)\b")
PAT_EM_ART = re.compile(r"\b[Ee]m\s+(?:o|os)\b")
PAT_DE_PRON = re.compile(r"\b[Dd]e\s+(?:ela|ele|elas|eles)\b")
PAT_DOUBLE = re.compile(r"\b([A-Za-zÀ-ÿ]+)\s+\1\b", re.IGNORECASE)
PAT_DBLSPACE = re.compile(r"\S  +\S")

# Keys reviewed and accepted (grammar-correct norm or intentional wordplay):
# "de a/o" before infinitive subjects, "de ele/eles" before infinitives,
# compound/echo names and onomatopoeia.
ALLOW_DE_ART = {
    "CULTURE_SAVAGE@BASH@DESCRIPTION",
    "DIPLOMACY@CALLTOARMS@DESCRIPTION",
    "DIPLOMACY@HOUSE_WAR_CHANCE@DESCRIPTION",
    "DIPLOMACY@HOUSE_WAR_CHANCE@TEXT",
    "STORY_EVENT@1122_133@BODY_FOOTER",
    "STORY_EVENT@1122_133@BODY_FOOTER@PLAYERLEADER_=_S",
    "TOME_TRANSMUTATION@SKILL1@DESCRIPTION",
}
ALLOW_DE_PRON = {
    "DLC@ARCHONPROPHECY@STORY_EVENT@1229_99@BODY_LORE",
    "DLC@ELDRITCHREALMS@STORY_EVENT@1194_549@BODY_LORE",
}
ALLOW_DOUBLE = {
    "DLC@ELDRITCHREALMS@STORY_EVENT@1167_512@BODY_LORE",
    "DLC@ELDRITCHREALMS@STORY_EVENT@1167_512@BODY_LORE@BOOSTED_BY_OTHER",
    "DLC@ELDRITCHREALMS@TOME_CLEANSING_FLAMES@DESCRIPTION",
    "DLC@RISEFROMRUIN@STORY_EVENT@1224_805@BODY_LORE",
    "DLC@SECRETSOFTHEARCHMAGES@STORY_EVENT@1224_1759@BUTTON_6",
    "DLC@SECRETSOFTHEARCHMAGES@STORY_EVENT@1229_1037@BODY_LORE",
    "DLC@SECRETSOFTHEARCHMAGES@STORY_EVENT@1229_1351@BODY_LORE",
    "DLC@SECRETSOFTHEARCHMAGES@STORY_EVENT@1252_354@BODY_FOOTER",
    "DIPLOMACY@HOUSE_DIPLOMATIC_STATE@VASSALAGE_LEVEL_-3_DESCRIPTION",
    "INTERFACE@MAP_SETUP_TOOLTIP@FROZEN_WASTE",
    "STORY_EVENT@1013_487@BODY_LORE",
    "STORY_EVENT@1013_517@BODY_LORE",
    "STORY_EVENT@991_7687@BODY_LORE",
    "TOME_TRANSMUTATION@SKILL4@DESCRIPTION",
    "ONBOARDING_OBJECTIVES@ANNEX_EXPLORATION_SITE@DESCRIPTION",
}

MARKER = re.compile(r"^\^[A-Za-z]+$")


def strip_leading(text):
    """Strip spaces/quotes/parens; return None if next thing is a token/digit."""
    s = text.strip()
    while True:
        s2 = s.lstrip(" \t\"'«»„“”(")
        if s2 != s:
            s = s2
        m = TOKEN.match(s)
        if m:
            return None, s, len(text) - len(text.lstrip())  # token-led
        break
    if not s or s[0].isdigit():
        return None, s, 0
    return s, s, 0


def check_cap(text):
    """Return offset of a lowercase first word, or None if ok/not applicable."""
    s = text.strip()
    if not s or MARKER.match(s):
        return None
    while True:
        s2 = s.lstrip(" \t\"'«»„“”(")
        if s2 != s:
            s = s2
        if TOKEN.match(s):
            return None
        break
    if not s or s[0].isdigit():
        return None
    m = re.match(r"[A-Za-zÀ-ÿ]", s)
    if m and m.group(0).islower():
        return text.find(s)
    return None


def main():
    work = json.loads(WORK.read_text(encoding="utf-8"))
    errors = []
    warnings = []

    for k, v in sorted(work.items()):
        pt, en = v["pt"], v["en"]
        if not pt:
            errors.append(f"UNFILLED {k}")
            continue

        # tokens: same multiset, never dropped, never invented
        import translation_batch as tb
        want, got = tb.tokens(en), tb.tokens(pt)
        if want != got:
            missing = [t for t in want if t not in got]
            extra = [t for t in got if t not in want]
            errors.append(f"TOKENS {k}: missing={missing[:3]} extra={extra[:3]}")
        if en.count("\\n") != pt.count("\\n"):
            errors.append(f"NEWLINES {k}: en={en.count(chr(92)+'n')} pt={pt.count(chr(92)+'n')}")

        # capitalization: string start + every [br/]/[bullet/] segment
        targets = [(pt, 0)]
        for m in SEG.finditer(pt):
            targets.append((pt[m.end():], m.end()))
        for seg, base_off in targets:
            off = check_cap(seg)
            if off is not None:
                # name-bank fragments (gender/adj markers ^z, ^a...) stay lowercase by design
                if re.search(r"\^[A-Za-z]$", pt.strip()):
                    continue
                # fragment allowed when EN mirrors lowercase at string start
                if base_off == 0:
                    ew = en.strip().lstrip(" \t\"'«»(")
                    if TOKEN.match(ew) or not ew or ew[0].isdigit():
                        continue
                    if re.match(r"^[a-z]", ew) or MARKER.match(en.strip()):
                        continue
                errors.append(f"CAP {k}: ...{pt[max(0, base_off + off - 20):base_off + off + 30]!r}")

        # prepositions
        ctx = lambda m: pt[max(0, m.start() - 25):m.end() + 25]
        if PAT_MIXED.search(pt):
            errors.append(f"PREP {k}: {ctx(PAT_MIXED.search(pt))!r}")
        if PAT_EM_ART.search(pt):
            errors.append(f"PREP {k}: {ctx(PAT_EM_ART.search(pt))!r}")
        if PAT_DBLSPACE.search(pt):
            errors.append(f"SPACE {k}: {ctx(PAT_DBLSPACE.search(pt))!r}")
        m = PAT_DE_ART.search(pt)
        if m and k not in ALLOW_DE_ART:
            errors.append(f"PREP {k}: {ctx(m)!r}")
        m = PAT_DE_PRON.search(pt)
        if m and k not in ALLOW_DE_PRON:
            errors.append(f"PREP {k}: {ctx(m)!r}")
        m = PAT_DOUBLE.search(pt)
        if m and k not in ALLOW_DOUBLE:
            errors.append(f"DOUBLE {k}: {ctx(m)!r}")

        # EN capitalization: informational only (EN is the game's source, intocavel)
        if check_cap(en) is not None:
            warnings.append(f"EN-CAP {k}")

    for e in errors:
        print("ERROR", e)
    for w in warnings:
        print("WARN ", w)
    print(f"strings: {len(work)} | errors: {len(errors)} | warnings(en source): {len(warnings)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
