# Formato e identidade nativa

O recurso autoritativo é `Language/EN/EN.MO`, gettext MO revisão 0, UTF-8.
Nesta implementação, **msgid é uma chave técnica**, não a frase inglesa;
msgstr contém o inglês. Não foram encontrados msgctxt ou plurais gettext.
Constructs do motor, e não uma tabela plural gettext, realizam parte da composição.

O adaptador aceita MO little/big endian, verifica cabeçalhos, limites de tabelas,
NUL terminal, UTF-8 estrito e separadores. Formatos/contextos desconhecidos
falham explicitamente. O build usa MO little endian e um cabeçalho gettext
UTF-8 para ferramentas independentes.

Uma reconstrução sem alteração devolve os bytes originais, incluindo layout e
metadados. Uma reconstrução com edição reserializa tabelas preservando todos os
pares e sua ordem nativa e é relida para confirmar equivalência. Não promete
igualdade binária ao regenerar um catálogo alterado.

Identidade: caminho nativo + representação JSON de `[chave, ocorrência]`.
Para chaves únicas, a ocorrência na identidade é nula. Somente chaves/valores
formados inteiramente por `@` podem se repetir; as demais duplicatas são
ambíguas e recusadas. Registros ofuscados conservam suas ocorrências e valores
originais, sem importar a tradução colapsada de um dicionário antigo. Sua
identidade entre versões não é semanticamente garantida; não há reaproveitamento
linguístico dessas ocorrências. Remoções/alterações aparecem no diff.

O manifesto e os campos EN/contexto dos JSONL formam o catálogo anterior
durável. Mesmo que EN já tenha sido substituído, sync compara com esse catálogo.
Linhas e nomes dos lotes não definem identidade; `row` conserva o endereço para
reconstrução na ordem atual. Históricos preservam PT-BR anterior e remoções.

O contexto registra escopo, variáveis e pistas explícitas de bancos de nomes.
Não existe associação geral comprovada de falantes nesse MO. Biografias e
referências verificadas estão no briefing; nome de personagem não prova o gênero
do interlocutor ou de um terceiro descrito.

O destino é `Language/PTBR/PTBR.MO` acompanhado de `Name.txt`; o nome do idioma
e os caminhos seguem os pacotes preservados. O ZIP corresponde ao conteúdo de
PTBR, copiável à raiz do jogo. Fontes e texturas de EN/Title não são necessárias
ao pacote histórico de idioma e não são incorporadas à distribuição da toolkit.
O funcionamento desse caminho após a migração ainda exige o teste real de jogo.
