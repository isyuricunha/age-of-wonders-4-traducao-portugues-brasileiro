# Translation Notes: Constructs, Markers, and Composition Rules

Reference for future term and string work in this mod. Terminology
decisions live in `docs/GLOSSARY.md`; this file documents HOW the game
builds text, what can and cannot be fixed through the `.po` files, and
the policies we settled after in-game testing.

## 1. Construct reference (`<<...>>` markup)

| Construct | Renders | Policy |
|---|---|---|
| `<<m:X>>` | The entity NAME (mention) | Keep verbatim. Safe to use in PT rewrites as "de {name}" glue. |
| `<<o:X>>` | Possessive determiner ("his/her") | Engine-internal English. Rewrite the sentence without it; keep the referenced variable. |
| `<<p:X>>` | Subject pronoun ("he/she") | Same as above. |
| `<<P:X>>` | Object pronoun ("him/her") | Same as above. |
| `<<r:X>>` | Reflexive ("himself/herself") | Same as above ("apresenta-se", "em pessoa", "para si"). |
| `<<Cp:X>>` / `<<Co:X>>` | Capitalized subject / possessive | Same as above; replace with the entity name or "Seu/Sua + noun". |
| `<<Cr:X>>` | Emphatic reflexive ("... himself") | Rewrite as "em pessoa" / "o próprio {X}" / drop. |
| `<<G:word^n,X>>` / `<<g:...>>` | Word-slot construct | Renders in the EN possessive mold ("Goela Profunda's fome"). The `word` content is translatable, but the possessive 's is engine-side. Prefer rewriting without the construct ("a fome de {X}"). |
| `<<in:X>>` | Ordinal ("first/second/third") | Engine-internal English, no key. Avoid in PT; reword ("Com a {structure} reivindicada..." instead of "Com seu third..."). |
| `<<Cm:X>>` / `<<Cg:...>>` | Capitalized mention / capitalized word construct | Content is translatable; keep the construct. |
| `{GLOBAL.X.Concept.Hyperlink}` and friends | Variable token | Verbatim. Same count, same spelling, reposition freely. |

Spelling check (2026-10-13): pronoun constructs were rewritten out of all
strings (`o/p/P/r/Cp/Co/Cr` = 0 remaining); `in:` and `G:` remain only
where removal would lose information that cannot be rephrased.

## 2. Item name composition and the `^a` / `^n` / `^z` markers

The game builds equipment names as:

    [adjective with ^a] + [noun with ^n] + [adjective with ^z]

- `^a` = placed BEFORE the noun (prefix slot)
- `^n` = the noun itself
- `^z` = placed AFTER the noun (suffix slot)

English puts genitives and many adjectives before the noun ("Flanker's
Seal", "Heavy Fury"), which is wrong for Portuguese. PT item names place
the modifier AFTER the noun ("Selo do Flanqueador", "Fúria Pesada").

**Rule: in PT translations, infusion/equipment modifiers use `^z`
(suffix), not the EN `^a` (prefix).** The game obeys the marker.

- Genitives: "do Crocodilo^z", "do Flanqueador^z" (43 + 261 strings fixed 2026-10-13).
- True adjectives also read better postposed: "Pesado^z" renders
  "Fúria Pesada"; "Afiado^z" renders "Matador de Invocações Afiado".

Exception: `Magic Missile` = "Míssil Mágico" (the spell projectile, D&D
tradition) is a NAME, not the ranged-attack category. The category
concept is "Ataque à Distância" (matching "Unidade à Distância",
"Arma à Distância").

## 3. Known engine-English limits (not fixable via `.po`)

- **Pronoun words** (`his/her/himself/third`): the engine resolves
  constructs and ordinals internally in English. Fix = rewrite the PT
  sentence so the construct is not needed, keeping every referenced
  variable in the string.
- **Concept pluralizer**: after a number, the engine pluralizes concept
  names with EN rules ("20 Pontos de Vidas", "5 Hit Points"). The
  concept name in the po is singular ("Ponto de Vida") and correct;
  the extra "s" is engine-side. Accept and move on.
- **Panel composition order** ("{property} {unit}" chips, e.g.
  "Gigante Anjo Caído"): the panel glues the property chip to the unit
  name. If the composite reads badly, consider renaming the UNIT (e.g.
  "Anjo Caído dos Gigantes") rather than the property.
- **Lone single-letter words in notification logs**: the reborn log
  "Governante {Side} retornou a {City}" rendered WITHOUT the "a"
  (verified against the built .MO, which contains it). Event dialogs
  render lone "a" fine, so the log pipeline drops it. City gender also
  varies, so a/ao is not choosable anyway. Use neutral phrasing:
  "reapareceu em {City}". Watch for other log strings with lone "a"/"o"
  before a token.
- **"ataques + concept" compositions**: concepts whose NAME contains
  the word attack (Ataque à Distância, Ataque de Retaliação, Ataque de
  Oportunidade) cannot follow "ataques" ("ataques Ataque à Distância"
  is broken and "de" makes it worse). Rewrite: single-concept strings
  drop the redundant word and use a singular verb ("Ataque à Distância
  causa..."); paired strings put Magic/Melee first ("ataques de Magia
  e Ataque à Distância"). Applied to all 41 such strings (2026-10-14).
  Noun concepts (Magia, Corpo a Corpo, Flanco, Carga) take "de"
  instead ("ataques de Magia").

## 4. Gender-neutral phrasing for composed events

Event log templates inject settlement/unit names of unknown gender.
Fixed participles break ("{X} fundada" vs "Posto Avançado fundado").
Use noun-based phrasing that skips the participle:

- "{X} fundada" → "Fundação de {X}"
- "Melhoria {X} construída" → "Melhoria construída: {X}"

For possessives, PT uses "de + name" (no crase with proper names):
"implora a {EventHero}", "a fome de {PlayerSpirit.LoreName}".

## 5. Terminology anchors (see GLOSSARY for the full list)

- Missile (attack category) = **Ataque à Distância**; Magic Missile (spell) = **Míssil Mágico**
- Make Peace = **Fazer as Pazes**
- Bronze/Silver/Gold (wonder rarity) = **Bronze, Prata, Ouro**
- Fallen Angel (Archon Prophecy unit) = **Anjo Caído dos Gigantes**
- Spirit lore names (Primal Fury): Deep-Maw = Goela Profunda,
  High-Squall = Alto Bramido, Loom-Frost = Geada Gigante,
  Fell-Fang = Presa Mortal, Under-Atter = Peçonha do Subsolo,
  Serpent = Espiral de Terra, Wolf = Mãe do Juramento

## 6. Verification workflow for text bugs

1. Reproduce the rendered sentence from the screenshot.
2. Search `translation-work.json` by PT fragment; if absent, the text is
   composed engine-side from the pieces (constructs, concept names,
   panel templates) — identify each piece before editing.
3. Fix the piece(s), run `translation_batch.py validate` (token
   multiset; construct drops are allowed per policy), then
   `scripts/check_translations.py` (must exit 0; it enforces
   capitalization, contractions, and variable presence including the
   pronoun-construct allowlist).
4. Rebuild: `build-po` → `msgfmt --check` → `mo_convert.py to-mo` →
   regenerate `PTBR.zip`/`PTBR.7z` → copy to `Steam-Paradox/Language/PTBR/`
   and the `Português Brasileiro - PTBR` mod folder.
5. Push `main` to all three remotes (`origin` GitHub, `gitlab`, `yugit`).
