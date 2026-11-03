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

## Demonkin
- **Demonkin = Demonídeo.** Neologismo por analogia com os -ídeos taxonômicos reais (hominídeo, canídeo, felídeo); não está em dicionário. Decisão do usuário (2026-10-11): manter, preserva o matiz de "povo descendente de demônios". Não trocar por "demônio" ou "demoníaco" nos nomes de raça.

## Regra de validação de tokens (Yuri, 2026-10-11)
- Se o validador barrar um ajuste, e a versão nova fizer mais sentido: mantém-se a versão nova e reescreve-se a frase para que cada token apareça exatamente uma vez, com a grafia exata da origem. Não se volta à ordem truncada do EN.
- Mover token/variável dentro da frase é sempre livre (o validador compara conjuntos ordenados; ordem nunca dispara mismatch).
- Nunca deixar a frase SEM o token. Nunca duplicar. Nunca renomear (adicionar `.Hyperlink` ou mudar maiúscula/minúscula cria um token diferente).

## Rise from Ruin (DLC)
- Unmaker/Unmakers = Desfazedor/Desfazedores (a facção; dentro de tokens como `{GLOBAL.UnmakersLoreConcept.Hyperlink}` permanece verbatim).
- The Fracturing (o cataclismo, conceito) = A Fraturação; as fraturas físicas = Fraturas; o arco de história "Echoes of the Fracturing" = "Ecos da Fratura" (padrão das chaves de evento).
- The Undone = Os Desfeitos (facção rival nos eventos).

## Pronoun constructs (<<o:>> <<p:>> <<P:>> <<Cp:>> <<r:>>)

These markup constructs resolve to engine-internal English words (his, he, him, He,
himself/herself). The game ships pronouns in English only (he/him, she/her) and
exposes no po key to localize them, so they render English inside PT text.

Policy: rewrite the PT sentence to avoid the construct while keeping the referenced
variable verbatim in the string. The possessive <<o:X>> becomes "seu/sua" agreeing
with the possessed noun (PT possessives do not mark the owner's gender). Subject,
object and reflexive forms are rewritten around the entity (name or title
repetition, "em pessoa", phrasing without clitics).

Each dropped construct makes the validator report a deliberate token mismatch;
the mismatch list must match the rewrite log, never grow silently.

Mire Crocodile spirit lore names (Primal Fury), translated 2026-10: Deep-Maw =
Goela Profunda, High-Squall = Alto Bramido, Loom-Frost = Geada Gigante,
Fell-Fang = Presa Mortal, Under-Atter = Peçonha do Subsolo. Serpent = Espiral de
Terra and Wolf = Mae do Juramento were already translated.

## The Silver Seas (atualização de 2026-11-03)

- The Silver Seas = Os Mares de Prata; Silver Seas = Mares de Prata.
- Mercantile = Mercantil; Barony = Baronia; Cartel = Cartel.
- Free Captain = Capitão Livre; Free Captains = Capitães Livres.
- Pirate Raid = Incursão Pirata; Avaricious/Bloodthirsty/Heroic = Avarento/Sanguinário/Heroico.
- Salt/Gold/Blood/Life Bond = Vínculo de Sal/Ouro/Sangue/Vida.
- Leverage = Alavancagem, seguindo o termo já usado nos eventos existentes.
- Bounty (estado de combate) = Recompensa; Bounty Hunter = Caçador de Recompensas. O Contrato diplomático existente pertence a outro conceito.
- Hoarfrost Manta = Arraia da Geada; Ancient Hoarfrost Manta = Arraia da Geada Ancestral.
- Hoarfrost Doomray = Arraia da Perdição Gélida; Doomray = Arraia da Perdição.
- Seamare = Cavalo-Marinho; Sharkkin = Tubarídeos; Aqualon = Aqualon.
- Runecrab = Caranguejo Rúnico; Lightning/Storm Rune Crab = Caranguejo Rúnico Relampejante/da Tempestade.
- Accursed Lamenter = Lamentadora Amaldiçoada; Accursed Wisp = Fogo-Fátuo Amaldiçoado.
- Ghostfire = Fogo Fantasma; Ember Dust = Poeira de Brasa; Damned = Condenado.
- Dirge = Elegia; Requiem = Réquiem; Rime Healing = Cura de Geada.
- Pearltide = Maré Perolada; Pearltide Dome = Cúpula da Maré Perolada.
- Pale Tidebloom = Flor da Maré Pálida; Tempestuous Vortex = Vórtice Tempestuoso.
- Spawning Shoal = Banco de Desova; Paragon of the Seas = Expoente dos Mares.
- Nevermoor = Nevermoor (nome do navio); Haunted Armada = Armada Assombrada.
- Gravegold Island = Ilha do Ouro Sepulcral; Cursed Gold = Ouro Amaldiçoado.
- Billowborne = Nascidos das Ondas; Children of the Waves = Filhos das Ondas.
- Nomes próprios neerlandeses são preservados; títulos, epítetos descritivos e nomes transparentes em inglês são traduzidos.
- As alternâncias de gênero em nomes e parentesco mantêm o identificador do personagem e traduzem as duas opções. Alternâncias puramente gramaticais (`bows/curtsies`, `he's/she's`) podem ser reescritas como uma única expressão natural, preservando a referência ao personagem na frase.
