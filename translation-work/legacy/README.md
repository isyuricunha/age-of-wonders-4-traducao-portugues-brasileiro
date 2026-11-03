# Material anterior à migração

Arquivo de referência do projeto anterior. Os scripts e os históricos foram
preservados; o ponto de entrada de desenvolvimento é agora `../toolkit.py`.
Não execute scripts antigos de merge/build/sync para escrever no espaço novo.
Os arquivos Python conservam a AGPL-3.0; a mudança de licença dos textos foi
autorizada pelo mantenedor no registro de consentimento da migração.

`output/` conserva os arquivos e pacotes anteriores, sem recompor ou traduzir seu
conteúdo. `Steam-Paradox/` e `Português Brasileiro - PTBR/` conservam os pacotes,
miniaturas, ACP e identidade Workshop 3657814946/Paradox 133369. O pacote ativo
`Português Brasileiro - PTBR/` foi restaurado na raiz para atualização do mod;
essas cópias em legacy continuam como referência histórica. A nova automação
não publica nem modifica esses canais. Não são variantes independentes.

`docs/`, `batches/history/` e os scripts documentam escolhas e validações anteriores.
As cópias de trabalho/exportações redundantes em `EN/` ficam locais e ignoradas;
as versões previamente comitadas continuam recuperáveis no histórico Git. Os
recursos nativos autoritativos permanecem versionados na raiz EN, no caminho
completo `Language/EN`. A importação JSONL preserva o PT-BR ativo, `pt_old` e
a proveniência, sem depender do JSON de trabalho local em um clone novo.

Os nomes temporários `arquivo.tmp-<32 dígitos hexadecimais>` pertencem à toolkit
e são reservados para recuperação. Não use esse padrão para arquivos pessoais.
