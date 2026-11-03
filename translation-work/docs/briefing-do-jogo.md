# Briefing de Age of Wonders 4

Pesquisa inicial preparada pelo desenvolvedor da toolkit em 03/11/2026 para
orientar o trabalho de tradução. As decisões finais de PT-BR pertencem ao
tradutor e ao glossário existente; os nomes em inglês abaixo são referências,
não propostas de renomeação. Há referências a antecedentes de personagens;
os desfechos das campanhas foram evitados.

## Identidade e recorte

Age of Wonders 4, da Triumph Studios e Paradox Interactive, foi lançado em
2 de maio de 2023. Combina estratégia 4X, gestão de império, elementos de RPG
e batalhas táticas por turnos. A identificação oficial e a premissa estão na
[página Steam, AppID 1669000](https://store.steampowered.com/app/1669000/Age_of_Wonders_4/).
O universo não funciona como um romance com um único protagonista fixo:
o jogador configura governantes e povos e participa de mundos narrativos
ou personalizados. O [site oficial](https://www.paradoxinteractive.com/games/age-of-wonders-4/about)
explica o retorno dos Wizard Kings, a transformação dos povos pela magia e
a continuidade das criações no panteão.

O recorte técnico desta oficina é o catálogo EN da build Steam 26274772,
encontrado na instalação Windows e preservado em
`EN/Language/EN/EN.MO`. Não foi feita uma campanha jogada durante a migração.
Presença de uma chave no catálogo não prova que ela esteja acessível em todas
as edições ou com qualquer conjunto de DLCs. O catálogo inclui também entradas
ofuscadas; elas não fornecem informação narrativa interpretável.

## Cosmologia, lugares e conflitos

A enciclopédia interna é uma fonte melhor que uma suposição baseada em nomes.
As entradas `INTERFACE@LORE_CONCEPT@...` descrevem a organização do mundo e
contêm links para outros conceitos. Siga esses links antes de fixar termos.

O **Astral Sea** conecta os mundos e está associado às energias arcanas.
Não deve ser confundido com um oceano comum navegável por embarcações:
a entrada `INTERFACE@LORE_CONCEPT@ASTRAL_SEA@DESCRIPTION` associa-o a fluxos
mágicos, nós de mana e ao percurso das almas. As entradas vizinhas
`ASTRAL_SEA_DWELLERS` e `ASTRAL_SEA_MONSTERS` distinguem habitantes e ameaças;
a natureza desconhecida de uma criatura não é sinônimo automático de maldade.
Essa distinção importa para descrições que alternam fascínio, perigo e luto.

**Athla** é apresentado como um mundo antigo ligado ao Valley of Wonders,+à corte de Inioch e a conflitos de alcance cósmico. A fonte é
`INTERFACE@LORE_CONCEPT@ATHLA@DESCRIPTION`. Nomes de locais dessa tradição
devem ser consultados em conjunto com o glossário da série; não se deve
transformar um nome próprio em uma descrição genérica só porque contém uma
palavra comum em inglês.

**Magehaven** serve como espaço de conselho e disputa dos Godir. Sua proteção
contra agressão permite negociação mesmo entre adversários. Isso está em
`INTERFACE@LORE_CONCEPT@MAGEHAVEN@DESCRIPTION` e ajuda a interpretar o contraste
entre a retórica grandiosa dos governantes e a necessidade prática de acordos.
Não confunda a localização desse fórum com o território particular de uma facção.

O catálogo diferencia conflitos políticos e mágicos de ameaças umbrais.
A [descrição oficial de Archon Prophecy](https://www.paradoxinteractive.com/games/age-of-wonders-4/add-ons/age-of-wonders-4-archon-prophecy)
situa os Archons contra Urrath e relaciona os mundos Emnora e Sordünn a essa
disputa. Profecias também são escolhas e objetivos de jogo: “destino” em um
texto poético não deve apagar uma condição mecânica de um objetivo.

## Personagens e evidências de identidade

O arquivo disponível não possui uma tabela autoritativa de falantes. A busca
por rótulos de speaker não encontrou entradas dedicadas nessa origem. Isso
não significa ausência de contexto: biografias, nomes de facção, IDs de eventos,
variáveis e falas próximas continuam sendo evidências úteis. Uma biografia
informa quem é descrito; não demonstra sozinha quem fala em outro evento.

| Referência | Evidência verificável | Uso e limite |
| --- | --- | --- |
| Sundren | `CAMPAIGN@LORDS@RACE_SUNDREN@BIO` identifica-a como filha da rainha Julia, fundadora dos Torchbearers e ligada à união de grupos élficos. | Feminino da pessoa descrita é explícito nesse texto. Não atribua automaticamente a ela toda fala do cenário. |
| Yaka | `CAMPAIGN@LORDS@RACE_YAKA@BIO` usa pronomes masculinos e o apresenta ligado ao fogo e à reverência exigida de seus seguidores. | A descrição sustenta o masculino para Yaka; seu tom autoritário não define o registro de todos os habitantes de sua facção. |
| Julia | `DLC@ARCHONPROPHECY@LORDS@RACE_JULIA@BIO` a descreve como Empress e usa pronome feminino. | Evidência da personagem descrita; sua história contém spoilers e deve ser lida antes de traduzir referências familiares. |
| Governante do jogador | `{Player.Name}`, `{Player.FirstName}`, variantes condicionais e constructs de gênero nos eventos. | Identidade e gênero podem variar. Não fixe uma concordância pelo nome de um governante de exemplo. |
| Heróis e interlocutores de eventos | `{EventHero}`, títulos e variáveis próprias do evento. | O papel de falante, destinatário ou terceiro precisa ser confirmado no conjunto da cena. |

Os bancos de nomes contêm chaves como
`AFFINITY_ASTRAL@HERO_FEMALE_FIRSTNAME_01@NAME`. O segmento FEMALE é uma
classificação explícita do banco, não uma ligação comprovada a um diálogo.
O contexto JSONL expõe essa diferença, a origem da pista e a incerteza.

Uma falante feminina pode estar descrevendo um homem; a concordância acompanha
o referente da frase. Uma fala em primeira pessoa exige identificar o falante,
enquanto um adjetivo depois de uma variável pode descrever cidade, unidade ou
governante. Se o evento não resolver a identidade, registre a dúvida e confronte
a cena em jogo. Não deduza gênero de grafia de nome, retrato ausente ou raça.

## Sistemas de jogo e terminologia em contexto

As seis afinidades aparecem em famílias `AFFINITYCONTENT@...`: Astral, Chaos,
Materium, Nature, Order e Shadow. Elas organizam opções e referências mecânicas;
não formam uma lista de personalidades obrigatórias. O catálogo distingue
conceito, nome de efeito, descrição e hyperlink. Preserve o termo técnico
segundo o glossário sem traduzir o endereço do recurso que o invoca.

Os tomos combinam identidade temática, desbloqueios, habilidades e progressão.
Um título de tomo não equivale ao nome de uma magia nele incluída. Consulte
entradas irmãs NAME/DESCRIPTION e referências `{GLOBAL....Hyperlink}` para
distinguir entidade, categoria e ação. Em tooltips, números, condições,+alcance, custos e duração são informação operacional: uma frase elegante que
troca quem recebe o efeito altera a compreensão da regra.

O mapa estratégico reúne cidades, províncias, recursos, diplomacia e expansão;
o combate usa unidades, ataques e efeitos com seus próprios contextos.
As regras já registradas em `diretrizes-de-traducao.md` tratam distinções como
categoria de ataque versus nome de magia e a ordem de composição de itens.
Essas são decisões históricas do projeto, preservadas na migração e sujeitas
à revisão do tradutor; a toolkit não propõe um glossário concorrente.

As famílias `CAMPAIGN`, `STORY_EVENT` e `DLC@...` ajudam a localizar escopo,
mas uma mesma frase pode conter variáveis selecionadas em execução. Procure
os irmãos de um ID e os registros que definem as entidades citadas antes de
interpretar uma frase isolada. Escolhas de botão precisam fazer sentido com
a introdução e com o efeito indicado, não apenas fora da janela de evento.

## Expansões encontradas e cuidados específicos

O catálogo contém famílias para Dragon Lords, Empires and Ashes, Primal Fury,
Eldritch Realms, Ways of War, Giant Kings, Archon Prophecy, Thrones of Blood,
Secrets of the Archmages, Rise from Ruin e Silver Seas, além de bônus menores.
Esses são escopos de origem, não uma garantia de todos os caminhos narrativos
testados. Consulte as descrições dos registros e as notas oficiais da edição
correspondente; não acrescente conteúdo futuro apenas porque foi anunciado.

[Primal Fury e a atualização Wolf](https://www.paradoxinteractive.com/games/age-of-wonders-4/news/primal-fury-and-wolf-update-out-now)
associam a cultura primal a animais e ambientes, e apresentam um conflito entre
Serena e Nimue nas Stormwreathed Isles. O vínculo a animal/terreno pode ser
regra mecânica, não simples metáfora. Diferencie devoção, invocação e transformação.

Em Archon Prophecy, a cultura Architects, profecias e os mundos narrativos
introduzem vocabulário religioso e de construção. A fonte oficial citada acima
distingue os propósitos dos tomos e o papel de Battlesaint; não confunda um
título de unidade com uma descrição de todos os personagens de uma cultura.

[The Silver Seas](https://www.paradoxinteractive.com/games/age-of-wonders-4/add-ons/age-of-wonders-4-the-silver-seas)
combina cultura Mercantile, Cartel e Barony, formas Aqualon e Sharkkin e relações
com capitães independentes. As subculturas têm meios diferentes de obter poder:
segredo/contrabando e riqueza/recompensas. O catálogo confirma famílias como
`DLC@SILVERSEAS@CULTURE_MERCANTILE@CARTEL@LEVERAGE@NAME` e
`DLC@SILVERSEAS@CULTURE_MERCANTILE@BARONY@ASSIGN_BOUNTY@NAME`.
“Leverage”, “bond” e “bounty” devem ser examinados como sistemas, além do sentido
coloquial. O mar físico dessa expansão não deve substituir a distinção cosmológica
do Astral Sea. O registro de atualização anterior preserva o trabalho já feito
nessa expansão em `legacy/docs/update-2026-11-03.md`.

## Voz, composição e riscos do português

Biografias e explicações de lore tendem ao registro descritivo; mensagens de
interface precisam orientar ações com rapidez; eventos alternam narração,
fala e escolhas. A entonação deve seguir a cena. Expressões grandiosas de um
governante não justificam tornar uma instrução de botão excessivamente solene.
Ironia, ameaça e hesitação dependem de quem fala e do que ocorreu, sem um
conjunto universal de substituições.

O jogo compõe frases usando `{variáveis}`, hyperlinks, ícones, tags de listas,
constructs `<<...>>` e marcadores de posição como `^a`, `^n`, `^z`. Parte do texto
gerado por constructs pode vir do inglês interno do motor. A política histórica
explica reescritas de possessivos e pronomes, mantendo a referência necessária.
Não edite código ou identificadores para resolver concordância.

Os cinco recibos técnicos de compatibilidade da migração abrangem somente
pares de texto já existentes. Eles não aprovam linguagem, não resolvem gênero
nem autorizam trocar livremente variáveis parecidas. Testes estruturais não
detectam toda ambiguidade: a sequência dos componentes de um nome e a pessoa
atingida por um efeito continuam exigindo leitura humana.

## Perguntas para revisão e limites

- Quem é o falante, o destinatário e o referente de cada trecho com concordância?
- A condição dinâmica seleciona gênero, número, título ou facção?
- O termo é uma categoria de ataque, uma magia, uma unidade ou um conceito linkado?
- Há um nome composto montado por peças fora da ordem natural em português?
- A atualização alterou contexto mesmo mantendo parte da redação inglesa?

O briefing inicial já está entregue; o tradutor deve consultá-lo e ampliá-lo
quando encontrar evidência nova, preservando as fontes. Não houve acesso a
todas as cenas, scripts internos ou seletores do motor, nem teste de campanha
durante esta migração. Casos sem vínculo verificável permanecem desconhecidos;
essa limitação não pode ser convertida em uma alegação de revisão contextual
completa.

## Referências e rastreabilidade

As fontes oficiais foram consultadas em 03/11/2026 e estão linkadas nas seções
correspondentes. A arte do README usa o header oficial Steam do AppID 1669000,
verificado por HTTP. O guia de modding do fabricante é referência adicional:
[Age of Wonders 4 Modding Guide v1.3](https://forumcontent.paradoxplaza.com/public/1271140/Age%20of%20Wonders%204%20-%20Modding%20Guide%20-%20V1.3.pdf).

As fontes locais são o MO original, as chaves indicadas acima, o glossário e
as notas preservadas. Os hashes e o mapeamento exato estão em
`translations/manifest.json`; o JSONL permite localizar a chave sem interpretar
uma posição física como identidade. Informações de publicação, formato e
testes de engenharia ficam no guia técnico, não são prova de apresentação em jogo.
