# Auditoria da migração

Escopo: implementação Windows de Age of Wonders 4, conforme o novo fluxo de
repositório único. Não inclui tradução nova, instalação, commit/push, publicação
real de Release nem execução no servidor ARM64.

| Requisito | Evidência no repositório |
| --- | --- |
| Repositório único e preservação | `translation-work/`, EN/PTBR na raiz; originais, históricos, scripts e identidades Steam/Paradox preservados em `legacy/` e no histórico Git. |
| Origem e formato reais | MO UTF-8 revisão 0, Steam AppID 1669000/build 26274772; `docs/formato-localizacao.md`, manifesto e comparação dos recursos com a instalação. |
| Identidade e duplicatas | Chave nativa e ocorrência para chaves ofuscadas; testes de reconstrução conservam todos os pares. Duplicatas visíveis ambíguas são recusadas. |
| JSONL e progresso | 52.275 registros em 105 lotes; 52.243 PT-BR importados e 32 pass-throughs ofuscados. Campos de origem imutáveis e manifesto com índice/hashes por lote. |
| Aplicação parcial segura | `apply` valida geração/IDs/estrutura e escreve somente lotes alterados. Repetição idempotente, sobrescrita explícita e entrada única pela CLI em translation-work/. |
| Atualizações incrementais | `sync` e `update-sources` compartilham plano/transação; autodetecção Steam delimitada, `--game-root`, `--source-root`, `--source-file` e dry-run. Recursos ausentes/novos desconhecidos falham antes da importação. |
| Diferenças e histórico | Textos/IDs/lotes anteriores e novos, remoções versionadas, fonte anterior nos registros e relatórios com geração e sinalização de obsolescência. |
| Contexto e gênero | Briefing pesquisado e referências biográficas por hash; papel de falante/destinatário/referente separado. Fixtures sem coluna de gênero cobrem falante feminina, referente masculino, nomes desconhecidos e jogador dinâmico. Mudanças nas evidências invalidam dependências. |
| Sintaxe nativa | Variáveis, multiplicidade, tags/nesting, controles, identidade/aridade de seletores e marcadores de nomes; cinco reescritas históricas exatas têm justificativa delimitada, não autorização genérica para ignorar tokens. |
| Durabilidade e recuperação | Trava OS, journal, staging, hashes, cópias só de arquivos alterados, recuperação/rollback e detecção de conflitos. Testes de interrupção e diário corrompido. |
| Retenção e desempenho | Stress de 500 pequenas aplicações sobre 50.502 registros/102 lotes completos; limite por quantidade/bytes, proteção de recuperação, `gc --dry-run`, configuração local e margem de espaço. Métricas em `verification.json`. |
| Build e publicação completos | Somente build publica a árvore PTBR e seu manifesto; incompletude/erros preservam a saída anterior. Verificação rápida recusa arquivos extras/ausentes/alterados, workspace desatualizado e sinalizadores forjados. |
| ZIP nativo | Somente `Language/PTBR/PTBR.MO` e `Name.txt`, sem pai PTBR nem fontes, PO, logs, licenças ou manifestos. Metadata ZIP portátil. |
| Release automático | Workflow com gate rápido, ZIP próprio, `contents: write`, concorrência serializada, commit exato e cliente HTTP. Simulações cobrem primeira versão, patch, no-op, rascunho interrompido, erros HTTP, histórico inválido e confirmação de assets. |
| Idempotência de Release | Recibo de publicação confirma digest/commit/geração sem tratar mudança de compressão como nova tradução; nenhuma exclusão automática de assets públicos. Histórico legado é preservado. |
| README público | Arte Steam verificada, três badges úteis, instruções de download/backup/cópia/restauração, ajuda, comunidade, portal, Pix discreto, créditos e licenças; renderização GFM inspecionada em desktop e 390px. |
| Briefing e passagem | `docs/briefing-do-jogo.md` contém cosmologia, personagens, afinidades, sistemas, expansões, ambiguidades e fontes oficiais/locais; glossário e diretrizes anteriores preservados. |
| Licenciamento e consentimento | LICENSE CC oficial integral; AGPL do código preservada; autorização adicional em inglês adaptada do modelo indicado; CONTRIBUTING, PR opt-in, verificador e registro explícito do mantenedor. |
| Windows → Git → ARM64 | `.gitattributes`, hashes LF de desenvolvimento e bytes nativos exatos; índice Git temporário testa normalização e adulteração. `doctor` verifica runtime/arquitetura/integridade e fixture parse/rewrite sem modificar traduções ou PTBR. |

## Limites verificados

- O perfil de produção não inventa vínculos de falantes: as biografias confirmam
  pessoas descritas; identificadores parecidos permanecem pistas. A escalação
  explícita das fixtures não é lore real do jogo.
- Testes de estrutura não equivalem a revisão linguística ou apresentação no jogo.
  O PT-BR foi preservado; não recebeu nova aprovação por estar preenchido.
- O preflight real no Ubuntu Server 24.04 ARM64 é a primeira etapa após o clone/pull.
  O teste Windows não é apresentado como execução ARM64.
- Publicação foi exercitada por mocks do cliente HTTP. A consulta real ao GitHub
  foi somente leitura de metadata/histórico; o novo workflow não foi executado
  remotamente nem publicou uma Release nesta migração.
- O pacote padrão é único; nenhuma variante de patch ou infraestrutura ARM64
  adicional foi criada. Os pacotes de mod antigos são referência histórica.

Os resultados e comandos finais, hashes e membros do ZIP estão em
`verification.json`; os detalhes de uso e recuperação ficam no README técnico.
