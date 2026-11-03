# Oficina de tradução de Age of Wonders 4

Este repositório reúne fontes, tradução, ferramentas e distribuição. A migração
preserva os textos existentes: o desenvolvimento da toolkit não produz novas
traduções nem aprova escolhas linguísticas.

## Primeiro uso no servidor

Após o clone/pull normal no Ubuntu Server 24.04 LTS ARM64, execute na raiz:

```bash
python3 -B translation-work/toolkit.py doctor
```

Esse é o único preflight necessário. Ele confere arquitetura, Python, hashes
normalizados pelo Git, dependências e reconstrução de uma amostra válida em
memória. Não instala pacotes, não exige sudo, não altera traduções e não gera
PTBR. Se falhar, encaminhe a mensagem completa e interrompa o trabalho de
tradução até a correção. Não regenere hashes para contornar um erro.

O adaptador usa somente a biblioteca padrão do Python 3.10 ou superior. Não
requer Mono, .NET, DLL, executável auxiliar, provedor de tradução ou credencial.
No Windows, `doctor --developer` executa as verificações locais sem afirmar
suporte ARM64 testado. A execução real em Ubuntu ARM64 e a apresentação dentro
do jogo permanecem **não verificadas** até os respectivos testes reais.

## Catálogo e proveniência

A origem inspecionada é Age of Wonders 4 para Windows/Steam, AppID 1669000,
build Steam 26274772. O MO do repositório foi comparado byte a byte com
`Language/EN/EN.MO` da instalação, sem modificar o jogo. A versão é evidência
da importação inicial, não uma promessa sobre futuras atualizações.

O catálogo contém 52.275 registros nativos: 52.243 textos com PT-BR importado
e 32 registros ofuscados compostos exclusivamente de `@`, preservados sem
tradução. Existem 52.260 chaves únicas; a diferença decorre de ocorrências
repetidas ofuscadas. O manifesto e o comando `status` são a fonte atual dos
totais. O preenchimento importado não significa revisão linguística nova.

`pt_old` do arquivo anterior foi mantido como contexto histórico de importação;
o inglês conhecido nesse registro é o da importação, não uma prova da origem
anterior associada a cada `pt_old`. Não use essa associação para aprovar texto
automaticamente. As revisões de origem posteriores passam a guardar pares
anteriores completos e verificados por sync.

Os lotes JSONL têm 500 registros, exceto o último, totalizando inicialmente
105 lotes. `EN`, identidade, contexto e endereço nativo são somente leitura;
`PTBR` é o campo editável. PTBR vazio representa pendência, exceto os
pass-throughs ofuscados explicitamente identificados.

## Organização e instalação nativa

```text
EN/Language/EN/{EN.MO,Name.txt,Credits.txt}  fontes originais preservadas
translation-work/translations/            JSONL e manifesto versionados
translation-work/docs/                    briefing, glossário e diretrizes
translation-work/history/                 entradas removidas em atualizações
translation-work/reports/                 migração e últimos diffs
translation-work/.state/                  recuperação local, ignorada pelo Git
PTBR/Language/PTBR/{PTBR.MO,Name.txt}        resultado do build completo
```

O ZIP contém `Language/PTBR/...`, sem diretório envoltório `PTBR/`. Seu
conteúdo é copiado à raiz da instalação. PO, ZIP, documentação e licenças da
toolkit não entram na árvore instalável. Créditos originais são preservados em
EN; fontes TTF, texturas e executáveis do jogo não são redistribuídos.

Os pacotes históricos Steam/Paradox e suas identidades são preservados como
referência de publicação. A migração não envia nada a essas plataformas.

## Comandos

Execute na raiz; a CLI resolve os caminhos também quando chamada de outra pasta.
A saída é JSON e falhas retornam código diferente de zero.

```bash
python3 -B translation-work/toolkit.py status
python3 -B translation-work/toolkit.py resume
python3 -B translation-work/toolkit.py check
python3 -B translation-work/toolkit.py diff
python3 -B translation-work/toolkit.py sync --dry-run
python3 -B translation-work/toolkit.py sync
python3 -B translation-work/toolkit.py update-sources --dry-run
python3 -B translation-work/toolkit.py update-sources --game-root "/caminho/Age of Wonders 4" --dry-run
python3 -B translation-work/toolkit.py update-sources --game-root "/caminho/Age of Wonders 4"
python3 -B translation-work/toolkit.py sync --source-root "/caminho/fontes-completas"
python3 -B translation-work/toolkit.py sync --source-file "/caminho/EN.MO" --dry-run
python3 -B translation-work/toolkit.py apply /caminho/alteracoes.json
python3 -B translation-work/toolkit.py build
python3 -B translation-work/toolkit.py verify-output
python3 -B translation-work/toolkit.py package --output /caminho/PTBR.zip
python3 -B translation-work/toolkit.py gc --dry-run
python3 -B translation-work/toolkit.py gc
python3 -B translation-work/toolkit.py recover
python3 -B translation-work/toolkit.py rollback
```

`extract` cria o espaço vazio para uma nova origem; `migrate` importa o arquivo
de trabalho anterior somente na inicialização. Ambos recusam sobrescrever um
manifesto existente. Não os execute para atualizar o jogo.

Os pontos de entrada antigos encaminham status/sync/validação/build à CLI nova;
o merge posicional foi aposentado. O conversor independente foi preservado para
exportações fora das árvores gerenciadas e recusa escrever EN, PTBR ou lotes,
para não contornar os gates de origem e de build completo.

### Atualizar a origem

`update-sources` consulta metadados delimitados das bibliotecas Steam e exige
um único candidato verificável. Não percorre discos inteiros. `--game-root`
tem precedência e aponta à pasta contendo o executável e `Language/EN`.
No servidor, a instalação do PC pode estar inacessível: use uma cópia completa
das fontes em `sync --source-root` ou atualize EN e execute `sync`. O toolkit
não acessa outra máquina nem instala arquivos no jogo.

O conjunto gerenciado exige MO válido, nome de idioma inglês e créditos.
Novos recursos de localização fora desse perfil falham visivelmente, inclusive
na verificação de publicação, até que o mapeamento seja investigado e testado;
não são ignorados nem recebem destinos inventados.
Para atualizar apenas o catálogo, `sync --source-file /caminho/EN.MO` aceita
explicitamente um MO original e conserva os companions aceitos de EN. O nome
de arquivo e as chaves são verificados; remoções continuam exigindo revisão.
Uma fonte traduzida fora do padrão não é aceita
como EN; a identidade de todas as versões futuras não pode ser provada por
assinatura do fabricante. Use recursos originais obtidos legitimamente,
sem alterações por mods; a validação de chaves não certifica sua procedência.

`sync` e `update-sources` usam o mesmo plano e a mesma transação. A comparação
é por identidade e conteúdo de cada registro. Entradas iguais mantêm PT-BR e
lote; reordenação atualiza somente o endereço nativo; alteração de texto ou
contexto esvazia PTBR e registra o texto anterior em `history`; novos textos
ficam pendentes. Remoções exigem `--allow-removals`: confira primeiro com
`--dry-run`. Registros removidos são preservados em history versionado.

O relatório JSON contém todos os IDs, textos anteriores/novos, classificações,
gerações e lotes afetados. O relatório Markdown resume o próximo trabalho.
`--dry-run` não cria estado nem substitui o relatório aceito. Em erro, a CLI
retorna falha; um relatório anterior continua pertencendo à geração nele
registrada. Uma atualização sem diferenças não regrava os lotes ou relatórios.

### Aplicar pequenos grupos

O payload deve conter a geração mostrada por `status` e IDs exatos:

```json
{"source_generation":"hash-do-status","updates":[{"id":"ID-exato-do-JSONL","PTBR":"texto escrito e revisado pelo tradutor"}]}
```

Identidades desconhecidas, repetidas, origem desatualizada, campos de origem
alterados ou estrutura inválida fazem o payload falhar antes da escrita.
Para substituir um PT-BR existente, use `apply --replace` explicitamente.
Repetir os mesmos valores é idempotente. Apenas os lotes realmente afetados
são escritos; o manifesto não é regravado em uma aplicação comum.
O índice ID→lote e os hashes de metadados imutáveis por lote ficam no manifesto.
`apply` carrega somente os lotes envolvidos e verifica seu catálogo contra
esses hashes; `check` valida o conjunto inteiro antes do build. Isso evita
reler todos os textos em cada pequena aplicação sem permitir alterar a origem.

As reescritas de constructs já existentes seguem a política histórica
preservada em `docs/NOTES.md`. Cinco pares EN/PTBR específicos necessitam de
compatibilidade técnica delimitada em `legacy-rewrite-policy.json`, com
diagnósticos e justificativas individuais. Qualquer edição deixa de corresponder
ao recibo e volta à validação estrita; não existe regra genérica de ignorar
variáveis desconhecidas ou permitir qualquer prefixo semelhante.

`context-reference.json` liga evidências biográficas verificadas de Sundren,
Yaka e Julia às chaves e pistas de identificadores pertinentes. Cada evidência
conserva a chave e o hash do inglês. Um nome parecido é apenas uma pista; não
atribui falante, destinatário ou referente por conta própria. As biografias
identificam a pessoa descrita, não quem fala em outro evento. Não há vínculos
de falantes de diálogo comprovados no perfil real disponível.

Uma mudança em uma biografia invalida o contexto dos registros relacionados,
mesmo quando seu inglês permanece igual, para revisão explícita. Evidências
desatualizadas voltam a desconhecidas, sem adivinhar gênero. As fixtures de
teste têm uma escalação explícita e verificada para testar separadamente
falante feminina, referente masculino, identidade desconhecida e jogador dinâmico;
essa escalação fictícia não é apresentada como dado real do jogo.

`migrate-context` é uma operação técnica de migração: só enriquece metadados
quando os recursos originais e todos os valores de origem são idênticos aos
aceitos. Preserva PTBR sem nova aprovação linguística. Se a origem mudou,
recusa a operação e exige sync, que invalida as traduções afetadas normalmente.
Depois da primeira migração, alterações nas evidências também exigem sync;
`migrate-context` não pode ser usado para contornar a revisão de contexto.

## Recuperação, retenção e espaço

Todas as operações de escrita usam trava de processo. A transação guarda somente
os arquivos alterados, com hashes anteriores/novos e diário durável. Uma
interrupção deixa o estado protegido; os comandos normais recusam continuar
até `recover` restaurar a geração anterior. Se houver uma edição concorrente
incompatível, a recuperação recusa sobrescrevê-la e mantém o diário para exame.
`rollback` desfaz a última operação completa retida, verificando os hashes do
estado atual. Não desfaz alterações externas silenciosamente.

Os padrões são **10 snapshots concluídos e 512 MiB**, definidos em
`storage.py`. Para configurar limites locais persistentes, use
`python3 -B translation-work/toolkit.py configure-storage --max-snapshots 10 --max-mib 512`.
O arquivo de configuração fica no estado local ignorado pelo Git.
Após cada operação verificada, snapshots antigos elegíveis são podados.
Uma operação maior que o orçamento falha antes de alterar dados. A previsão
de espaço inclui staging, cópia anterior e margem livre de 64 MiB.
`status` mostra quantidade, bytes, proteção, limites e espaço recuperável.

`gc --dry-run` apenas lista o que excede os limites; `gc` usa a mesma trava e
recusa qualquer limpeza com recuperação pendente, recibos inválidos ou caminhos
inseguros. Nunca apaga o snapshot mais recente. Não remove fontes, lotes,
histórico de tradução ou arquivos arbitrários do usuário.

O diário local limita recuperação de falhas recentes; histórico durável depende
dos registros versionados e dos commits feitos pelo responsável. A toolkit não
cria commits. Não confunda snapshots locais com uma cópia externa de segurança.

## Build e Releases

Somente `build` altera PTBR. Exige todos os textos ativos preenchidos, origem e
estrutura válidas; reconstrói o MO, relê o resultado e publica os arquivos e
`build-manifest.json` na mesma transação recuperável. Não altera traduções.
Falhas de validação preservam a saída anterior. Uma interrupção durante a
promoção bloqueia a leitura pela toolkit até recuperação; não há promessa de
troca instantânea de múltiplos arquivos para leitores externos ao protocolo.

Comite os arquivos PTBR e o manifesto de build juntos quando estiverem prontos.
Commits só de progresso não acionam Releases. `release.yml` roda em alterações
de PTBR na main, verifica hashes/contagens/gerações sem reconstruir o MO,
gera o ZIP permitido e publica com `GITHUB_TOKEN`/`contents: write`.

Uma história sem Releases começa em `v1.0.0`; alterações posteriores incrementam
o patch. Este repositório já tem tags históricas até `v1.0.39` na inspeção:
elas são preservadas, nunca reiniciadas ou movidas. A consulta remota posterior
confirmou a Release legada `v1.0.40`, no mesmo commit local; o planejamento usa
sempre o histórico remoto atual, sem fixar a próxima versão. A migração permite comparar
um MO legado publicado quando não havia manifesto. Histórias não ancestrais,
tags ambíguas ou bases ausentes fazem a publicação falhar visivelmente.
Um recibo não visível na apresentação das notas registra o digest do ZIP
publicado, sua geração nativa e seu commit. A repetição confirma esse recibo
sem confundir uma diferença de compressão/metadata ZIP com nova tradução.

A concorrência é serializada e o cliente reconfirma o HEAD remoto antes da
publicação. Um rascunho interrompido pode ser retomado somente para o mesmo
commit. Os endpoints HTTP, upload e confirmação de digest são exercitados
em testes offline. O único asset permitido é `PTBR.zip`; notas, manifestos,
licenças, logs, fontes e arquivos 7z não são anexados. Não há envio automático
ao Nexus, Workshop ou Paradox. Não há um segundo passo manual de upload.

Execução real do GitHub Actions/publicação não é realizada como teste local.
Após o push autorizado pelo mantenedor, confira a execução em Actions e a
Release/asset. O dispatch manual repete a verificação e deve resultar em no-op
quando a saída não mudou. Correções de assets públicos inesperados exigem
análise específica; o cliente não os apaga automaticamente.

## Trabalho linguístico

Leia o [briefing já pesquisado pelo desenvolvedor](docs/briefing-do-jogo.md), o
[glossário preservado](docs/glossario-ptbr.md) e as
[diretrizes](docs/diretrizes-de-traducao.md). O tradutor mantém decisões de
terminologia e estilo; não precisa produzir o briefing inicial.

Depois do preflight: consulte `status`, `diff`, revise grupos de registros,
aplique PTBR, rode `check` e faça seus commits de progresso. Para concordância,
distinga falante, interlocutor e pessoa descrita. Nomes e variáveis não provam
gênero. Leia o contexto relacionado e marque casos dinâmicos para teste no jogo.
Quando terminar a revisão, rode `check`, `build` e `verify-output`; o teste real
de apresentação permanece uma etapa separada, em ambiente autorizado.

## Verificação de desenvolvimento

```bash
python -B -m unittest discover -s translation-work/tests -v
python -B translation-work/toolkit.py doctor --developer
python -B translation-work/toolkit.py check
git diff --check
```

Os recibos de integridade usam LF/UTF-8 para arquivos de desenvolvimento, conforme
`.gitattributes`; recursos nativos usam seus bytes originais. Não dependa de
`core.autocrlf`. Testes com um índice Git temporário verificam CRLF→LF e adulteração.
Não há cadeia engine-shapes/Mono porque este formato não utiliza esses componentes;
`toolchain.json → runtime-support.json` é a cadeia real de dependências.

Tradução/documentação originais: CC BY-NC-SA 4.0; código: AGPL-3.0 preservada;
recursos originais do jogo conservam seus titulares. Consulte os documentos da
raiz e os registros de consentimento antes de uma integração oficial.
