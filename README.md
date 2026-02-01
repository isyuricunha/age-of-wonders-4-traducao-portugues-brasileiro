# Guia Completo para Tradução de Age of Wonders 4

## Introdução

**Participe da comunidade no Discord:** https://discord.com/invite/aYbWBr4


Este repositório contém uma tradução completa para português brasileiro do jogo Age of Wonders 4. Se você quer apenas instalar e jogar com a tradução pronta, siga as instruções abaixo. Se você é do tipo que gosta de fuçar e quer traduzir por conta própria, há uma seção separada no final explicando como usar o script `mo_convert.py` para facilitar o processo.

Este guia é feito para novatos em computadores, então vamos passo a passo, devagar e explicando tudo direitinho.

## Requisitos do Sistema

Para instalar a tradução, você só precisa ter o jogo Age of Wonders 4 instalado no seu computador. Nada mais é necessário!

## Como Instalar a Tradução Pronta

### Passo 1: Baixar os Arquivos

1. Abra seu navegador web (como Chrome, Firefox ou Edge).
2. Vá para a página de releases do repositório: <https://github.com/isyuricunha/age-of-wonders-4-traducao-portugues-brasileiro/releases/latest>
3. Procure pelos arquivos de download. Você verá opções como `PTBR.zip` ou `PTBR.7z`.
4. Clique no arquivo que preferir (ambos contêm a mesma coisa, apenas formatos diferentes de compactação).
5. O download começará automaticamente. Salve o arquivo em uma pasta fácil de encontrar, como "Downloads" ou "Desktop".

### Passo 2: Extrair os Arquivos

1. Localize o arquivo baixado (PTBR.zip ou PTBR.7z) na pasta onde você salvou.
2. Clique com o botão direito do mouse no arquivo.
3. Selecione "Extrair Tudo..." (para ZIP) ou use um programa como 7-Zip para extrair o 7z.
4. Escolha uma pasta de destino. Recomendo criar uma nova pasta chamada "Age of Wonders Tradução" na sua área de trabalho para manter tudo organizado.
5. Após extrair, você verá uma pasta chamada "PTBR" com vários arquivos dentro.

### Passo 3: Instalar no Jogo

Agora você precisa colocar a pasta "PTBR" na pasta de idiomas do jogo. A localização varia dependendo de onde você comprou o jogo:

#### Para Jogos da Steam

- Caminho padrão: `C:\Program Files (x86)\Steam\steamapps\common\Age of Wonders 4\Language`
- Como chegar lá:
  1. Abra o Explorador de Arquivos (clique na pasta amarela na barra de tarefas).
  2. Vá para "Este PC" > "Disco Local (C:)" > "Program Files (x86)" > "Steam" > "steamapps" > "common" > "Age of Wonders 4" > "Language".
  3. Cole a pasta "PTBR" dentro da pasta "Language".

#### Para Jogos da GOG Galaxy

- Caminho padrão: `C:\Program Files (x86)\GOG Galaxy\Games\Age of Wonders 4\Language`
- Como chegar lá:
  1. Abra o Explorador de Arquivos.
  2. Vá para "Este PC" > "Disco Local (C:)" > "Program Files (x86)" > "GOG Galaxy" > "Games" > "Age of Wonders 4" > "Language".
  3. Cole a pasta "PTBR" dentro da pasta "Language".

#### Para Jogos da Epic Games

- Caminho padrão: `C:\Program Files\Epic Games\AgeOfWonders4\Language`
- Como chegar lá:
  1. Abra o Explorador de Arquivos.
  2. Vá para "Este PC" > "Disco Local (C:)" > "Program Files" > "Epic Games" > "AgeOfWonders4" > "Language".
  3. Cole a pasta "PTBR" dentro da pasta "Language".

#### Para Versões Piratas ou Outras Instalações

- Se você instalou o jogo em outro lugar, procure pela pasta do jogo e dentro dela uma pasta chamada "Language" ou "Lang".
- Exemplos comuns:
  - `D:\Games\Age of Wonders 4\Language`
  - `C:\Games\Age of Wonders 4\Language`
- Se não encontrar, procure por arquivos com extensão ".mo" no diretório do jogo.

### Passo 4: Ativar a Tradução no Jogo

1. Abra o jogo Age of Wonders 4.
2. Vá para as configurações de idioma (geralmente em Options > Language).
3. Selecione "Portuguese (Brazil)" ou "PTBR" na lista de idiomas disponíveis.
4. Reinicie o jogo se necessário.

Pronto! Agora você pode jogar em português brasileiro.

## Para Quem Quer Traduzir por Conta Própria

Se você não quer usar a tradução pronta e prefere criar a sua própria, ou modificar a existente, o script `mo_convert.py` vai te ajudar. Ele converte arquivos de tradução entre os formatos MO (binário, usado pelo jogo) e PO (texto editável), facilitando o trabalho.

### Requisitos Adicionais

Para usar o script, você precisa do Python instalado:

1. **Python**: Baixe a versão mais recente do site oficial: <https://www.python.org/downloads/>. Durante a instalação, marque a opção "Add Python to PATH" (Adicionar Python ao PATH) para que funcione no terminal.

### Como Usar o Script mo_convert.py

#### Preparação

1. Baixe ou copie o arquivo `mo_convert.py` para uma pasta no seu computador (por exemplo, junto com os arquivos de tradução).
2. Abra o Prompt de Comando ou PowerShell:
   - Pressione Windows + R, digite "cmd" e pressione Enter.
   - Ou procure por "Prompt de Comando" no menu Iniciar.

3. Navegue até a pasta onde está o script:
   - Digite `cd` seguido do caminho da pasta, por exemplo: `cd C:\Users\SeuNome\Desktop\Age of Wonders Tradução`
   - Pressione Enter.

#### Convertendo MO para PO (para Editar)

Se você quer editar uma tradução existente:

1. No Prompt de Comando, digite o comando:

   ```bash
   python mo_convert.py to-po arquivo_original.mo arquivo_editavel.po
   ```

   - Substitua `arquivo_original.mo` pelo nome do arquivo MO que você quer converter.
   - Substitua `arquivo_editavel.po` pelo nome que você quer dar ao arquivo PO de saída.

2. Pressione Enter. O script criará um arquivo PO que você pode abrir em qualquer editor de texto (como Bloco de Notas, Notepad++, ou VS Code).

3. Edite o arquivo PO:
   - Abra o arquivo .po em um editor de texto.
   - Procure pelas linhas que começam com `msgstr ""`.
   - Entre as aspas, escreva a tradução em português.
   - Salve o arquivo.

#### Convertendo PO para MO (para Usar no Jogo)

Depois de editar o PO:

1. No Prompt de Comando, digite o comando:

   ```bash
   python mo_convert.py to-mo arquivo_editavel.po arquivo_final.mo
   ```

   - Substitua `arquivo_editavel.po` pelo nome do seu arquivo PO editado.
   - Substitua `arquivo_final.mo` pelo nome que você quer dar ao arquivo MO final.

2. Pressione Enter. O arquivo MO será criado e pode ser usado no jogo.

3. Copie o arquivo MO para a pasta apropriada no jogo (dentro da pasta PTBR que você instalou).

#### Exemplo Prático

Vamos supor que você quer traduzir o arquivo "PTBR.mo":

1. Converta para PO: `python mo_convert.py to-po PTBR.mo minha_traducao.po`
2. Edite "minha_traducao.po" no Bloco de Notas.
3. Converta de volta: `python mo_convert.py to-mo minha_traducao.po PTBR.mo`
4. Substitua o arquivo original no jogo.

### Dicas para Tradução

- Sempre teste suas mudanças no jogo para ver se funcionam.
- Faça backups frequentes dos seus arquivos.
- Se encontrar erros no script, verifique se o Python está instalado corretamente e se os caminhos dos arquivos estão certos.
- Os arquivos PO têm uma estrutura específica: msgid é o texto original, msgstr é a tradução.

## Suporte e Doações

Se você gostou desta tradução e quer apoiar o trabalho, considere fazer uma doação via PIX para: <pix@yuricunha.com>

Para dúvidas ou problemas, verifique se seguiu todos os passos corretamente. Lembre-se: tradução de jogos é um processo que requer paciência e testes constantes.
