# Age of Wonders 4 PT-BR Glossary

Living standardization record for the translation overhaul. Entries are
string-level: the English term as it appears in game text, the fixed PT-BR
rendering, and a note when the choice needs context. Older decisions win over
newer ones; a new term only replaces an old choice when clearly better, and
replaced strings get flagged for revision.

## Campaign and scenario names

- Rise of the Godir = Ascensão dos Godir
- Empires and Ashes = Impérios e Cinzas
- Eldritch Realms = Reinos Arcanos
- Gloom = Penumbra; Gloom Terrain = Terreno Penumbroso; Gloom Tear = Fenda da Penumbra (never "Sombras" or "Lágrima": collides with Shadow).
- Umbral Malady = Moléstia Umbral (never "Maldição Umbral").
- Thrall = Servo everywhere; Umbral Thralls = Servos Umbriais; Enthralled state = Escravizado.
- Leana's Draw = Sorte de Leana (constellation).
- Invading Sylviculture = Silvicultura Invasora (never "Sylvicultura").
- Archon Prophecy = Profecia do Arconte (never "Profecia do Arcon").
- Tome of the Archon = Tomo do Arconte (never "Tomo do Arcan").
- Cosmic Wanderer = Andarilho Cósmico (title, DLC name and staff share it).
- Thrones of Blood = Tronos de Sangue
- Secrets of the Archmages = Segredos dos Arquimagos
- Valley of Wonders = Vale das Maravilhas
- The Enchanted Archipelago = Arquipélago Encantado (no article)
- Crimson Caldera = Caldeira Carmesim
- The Eternal Court = A Corte Eterna
- Freed Lands of Manuhari = Terras Livres de Manuhari
- Sehiran Oasis = Oásis de Sehiran
- The Azh'Ruun Pit = O Poço Azh'Ruun
- Burrow Downs = Burrow Downs (place name, kept)
- Rings of Emnora = Anéis de Emnora
- Cliffs of Sordünn = Penhascos de Sordünn
- Tharru'Cath, Arcalot, Grexolis, Evermore = kept as proper nouns

## People and titles

- Godir = Godir
- Wizard King = Rei-Feiticeiro
- Arch Mage = Arquimago (no hyphen; one word)
- Lord of Chaos = Suserano do Caos
- Eternal Lord = Suserano Eterno
- Dragon Lord = Suserano Dragão
- Giant King = Rei Gigante
- Elder Vampire = Vampiro Ancião
- Eldritch Sovereign = Soberano Arcano
- Ruler = Governante
- Liege = Suserano; Rally of the Lieges = Ajuntamento dos Suseranos
- Wizards of Evermore = Feiticeiros de Evermore
- Champion = Campeão; Ranger = Patrulheiro

## Races and units

- Halfling = Halfling; Owlkin = Owlkin; Harefolk = Harefolk; Naga = Naga
- Dark Goblins = Goblins Negros; Righteous Orcs = Orcs Justos
- Ironclad = Blindado
- Endailon = Endailon
- Decaying Zombie concept stays behind its {GLOBAL.UNITS.DECAYING_ZOMBIE.Hyperlink} token

## Magic and empire concepts

- Tome = Tomo (the magic books; never "Tome" in PT text)
- Affinity = Afinidade; the six: Ordem, Caos, Astral, Materium, Natureza, Sombra
- Imperium = Imperium (kept)
- Allegiance = Lealdade
- Happening = Evento (Intrigue Happening = Evento de Intriga)
- Throne City = Cidade do Trono
- Free City = Cidade Livre
- Ancient Wonder = Maravilha Ancestral
- Tier = Nível (Tier V = Nível V)
- Grievances = Agravos
- Major/Minor Transformation = Transformação Maior/Menor
- Major/Minor Ambitions = Ambições Maiores e Menores
- Graze = Raspão (Graze Tactics = Táticas de Raspão)
- Ironclad Ammunition = Munição

## Style rules

- Achievement/quest descriptions: imperative mood ("Vença...", never
  infinitive "Vencer...").
- Trailing punctuation mirrors the English string exactly (no added period
  when EN has none; titles never take one).
- Gender: prefer neutral phrasing for achievement titles and ruler-facing
  text ("Purificação", "Sob Juramento", "Com o Favor dos Espíritos",
  "pereceu" instead of "foi morto"); when neutrality is impossible, both
  forms must read correctly.
- Hyphens: ASCII hyphen only (U+002D); replace U+2011 non-breaking hyphens
  found in the old text.
- Race names coined by the game (Owlkin, Harefolk) stay in English; common
  nouns (Goblins, Orcs, Dwarves) translate.
- Obsidian Dragon = Dragão de Obsidiana (standard mineral name).
- Insectoid = Insetoide (no hyphen, post-reform spelling).
- Devotion Paragon level = nível de Devoção Exemplar.
- Archon = Arconte (never "Arcanjo"; that is a different being).
- Seal = Selo (Seals Victory = Vitória dos Selos; never "sela").
- Covenant = Aliança (the Godir alliance in the campaign).
- Blight = Calamidade (existing choice: Blight Blast = Explosão de
  Calamidade, Blight Bolts = Raios de Calamidade).
- Epithet article rule: contracted article when the epithet refers to a
  specific or conceptual thing ("Tecelão da Luz", "Portador da Guerra",
  "Tecelão do Destino"); plain "de" for material, composition or generic
  plurals ("Martelo de Ouro", "Ceifador de Vidas", "Ladrão de Reis").
- Willbreaker = Quebra-Ânimo everywhere (the Chaos epithet
  "Esmagador de Vontades" is superseded by this).
- Gender construct: EN "the <<Hero{A^z/B^z}>>" renders in PT as
  "<<Hero{o A^z/a B^z}>>": the article goes INSIDE the alternation so
  the game picks the matching form; "o/a" outside is wrong.
- Hero epithets without the construct keep the masculine default with
  lowercase article ("o Inanimado^z"): documented exception; the game
  offers no other gender hook for fixed strings.
- The Pit / Azh'Ruun Pit / the Pit of eternal torment = "o Abismo" /
  "Abismo Azh'Ruun" / "um abismo de tormento eterno" (Yuri's choice;
  never "Fossa" or "Poço"). A literal molten pit stays lowercase "fossa".
- "halfling" is lowercase in prose; race compound titles capitalize as
  in the RACE_*@NAME keys.
- Sabertooth creature family (Ash Sabertooth etc.) = "Dente-de-Sabre de
  Cinzas" etc., following PT-BR order like "tigre dente-de-sabre";
  never "Sabre-dente" (backwards calque of the English).
- "Stonestele" (Primal culture structure) = "Menir"; never "Estela de
  Pedra" (correct dictionary word, but opaque in a game UI) or
  "Stonesteel" (garbage).
- The `<<m:word>>` construct is a closed game key: the word inside is
  never translated and must stay verbatim ("<<m:stack>>"); only the
  `<<G:word>>` family renders free display text that gets translated.
