<div align="center">

<img src="Portugu%C3%AAs%20Brasileiro%20-%20PTBR/thumbnail.png" alt="Vai Brasil!" width="220"/>

# Age of Wonders 4

### 🇧🇷 Tradução em Português Brasileiro

**O jogo completo em português: mais de 48 mil strings traduzidas,
incluindo as DLCs mais recentes.**

[![Versão](https://img.shields.io/github/v/release/isyuricunha/age-of-wonders-4-traducao-portugues-brasileiro?style=for-the-badge&label=vers%C3%A3o&color=6f42c1)](https://github.com/isyuricunha/age-of-wonders-4-traducao-portugues-brasileiro/releases/latest)
[![Tradução](https://img.shields.io/badge/tradu%C3%A7%C3%A3o-100%25%20completa-2ea44f?style=for-the-badge)](#-sobre-o-projeto)
[![Strings](https://img.shields.io/badge/strings-48.000%2B-0969da?style=for-the-badge)](#-sobre-o-projeto)
[![Licença](https://img.shields.io/github/license/isyuricunha/age-of-wonders-4-traducao-portugues-brasileiro?style=for-the-badge&label=licen%C3%A7a&color=f9c513)](LICENSE)
[![Plataformas](https://img.shields.io/badge/Steam%20%C2%B7%20GOG%20%C2%B7%20Epic%20%C2%B7%20Paradox-1b1f24?style=for-the-badge)](#-onde-encontrar-a-tradu%C3%A7%C3%A3o)

[⬇️ Baixar](#-instalação) · [🌐 Nexus Mods](https://www.nexusmods.com/ageofwonders4/mods/124) · [🎮 Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3657814946) · [💬 Discord](https://discord.gg/uFEwSMwUYb) · [▶️ Série no YouTube](https://www.youtube.com/watch?v=JFH4A1-OK1c)

</div>

---

## 📖 Sobre o projeto

Esta é uma tradução completa do Age of Wonders 4 para Português Brasileiro,
mantida pela comunidade [Vai Brasil](https://discord.gg/uFEwSMwUYb). Todo o
texto do jogo está traduzido: interface, missões, tomos de magia, unidades,
itens e descrições.

- ✅ **Jogo base e DLCs recentes**, incluindo Rise from Ruin (a DLC do deserto), Secrets of the Archmages, Thrones of Blood e Singer of Storms
- 📚 **48.000+ strings traduzidas**, com revisão de terminologia, gênero e concordância
- 🔧 **Ferramentas próprias** para converter, verificar e atualizar os arquivos de idioma
- 🔄 **Atualizada junto com o jogo**, a cada patch e DLC nova
- 🆓 **Gratuita e de código aberto**, sob licença AGPL-3.0

## 📦 Instalação

> [!TIP]
> Resumo rápido: baixe a release, extraia, copie a pasta `PTBR` para dentro
> da pasta `Language` do jogo e selecione o idioma no jogo. Os passos
> detalhados estão logo abaixo.

### Passo 1: Baixar os arquivos

1. Acesse a [página de releases](https://github.com/isyuricunha/age-of-wonders-4-traducao-portugues-brasileiro/releases/latest).
2. Baixe o `PTBR.zip` (ou o `PTBR.7z`, são o mesmo conteúdo em formatos diferentes).
3. Salve em uma pasta fácil de encontrar, como "Downloads".

Você também pode baixar pelo [Nexus Mods](https://www.nexusmods.com/ageofwonders4/mods/124),
[Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3657814946)
ou [Paradox Mods](https://mods.paradoxplaza.com/mods/133369/Any).

### Passo 2: Extrair os arquivos

1. Clique com o botão direito no arquivo baixado.
2. Selecione "Extrair Tudo..." (ZIP) ou use o 7-Zip (arquivo .7z).
3. Ao final, você terá uma pasta chamada `PTBR`.

### Passo 3: Copiar para a pasta do jogo

Copie a pasta `PTBR` para dentro da pasta `Language` do jogo. O caminho
depende de onde você comprou:

| Loja | Caminho da pasta `Language` |
|---|---|
| **Steam** | `C:\Program Files (x86)\Steam\steamapps\common\Age of Wonders 4\Language` |
| **GOG Galaxy** | `C:\Program Files (x86)\GOG Galaxy\Games\Age of Wonders 4\Language` |
| **Epic Games** | `C:\Program Files\Epic Games\AgeOfWonders4\Language` |
| **Outras instalações** | Procure a pasta do jogo e, dentro dela, a pasta `Language`. Se não encontrar, procure por arquivos `.mo` no diretório do jogo. |

### Passo 4: Ativar a tradução

1. Ative o mod no launcher da Paradox.
2. Abra o jogo e vá em **Options > Language**.
3. Selecione **Portuguese (Brazil)**.
4. Se o idioma não aplicar de imediato, reinicie o jogo.

Pronto, bom jogo! ⚔️

## 🌐 Onde encontrar a tradução

| Canal | Link |
|---|---|
| 📦 GitHub Releases | [isyuricunha/age-of-wonders-4-traducao-portugues-brasileiro](https://github.com/isyuricunha/age-of-wonders-4-traducao-portugues-brasileiro/releases/latest) |
| 🌐 Nexus Mods | [ageofwonders4/mods/124](https://www.nexusmods.com/ageofwonders4/mods/124) |
| 🎮 Steam Workshop | [Workshop item 3657814946](https://steamcommunity.com/sharedfiles/filedetails/?id=3657814946) |
| 🛠️ Paradox Mods | [mods/133369](https://mods.paradoxplaza.com/mods/133369/Any) |
| 💬 Discord (comunidade) | [discord.gg/uFEwSMwUYb](https://discord.gg/uFEwSMwUYb) |
| ▶️ Série no YouTube | [Vídeo de apresentação](https://www.youtube.com/watch?v=JFH4A1-OK1c) |

## 🛠️ Para tradutores e curiosos

Se você quer fuçar na tradução, ajustar termos ou criar a sua própria
versão, o repositório traz tudo o que é necessário.

### Ferramentas

| Script | O que faz |
|---|---|
| `mo_convert.py` | Converte entre MO (binário usado pelo jogo) e PO (texto editável) com os comandos `to-po` e `to-mo` |
| `update_ptbr.py` | Copia para o `PTBR.po` as strings que existem no `EN.po` e ainda faltam na tradução |
| `missing_translations.py` | Compara EN e PTBR e lista as entradas idênticas ao inglês (possivelmente sem tradução) |
| `scripts/check_translations.py` | Verifica capitalização, contrações de preposição e presença de tokens obrigatórios |
| `translation_batch.py` | Ferramentas em lote usadas na revisão da tradução |

A pasta [`docs/`](docs/) guarda o glossário de termos padronizados
([GLOSSARY.md](docs/GLOSSARY.md)), as regras de composição de texto do jogo
([NOTES.md](docs/NOTES.md)) e a documentação do fluxo de trabalho
([PIPELINE.md](docs/PIPELINE.md)).

### Organização do repositório

```text
.
├── PTBR/                        # arquivos de idioma da tradução (PTBR.po, PTBR.MO)
├── EN/                          # arquivos de referência em inglês
├── Português Brasileiro - PTBR/ # pacote no formato do Paradox Mods
├── Steam-Paradox/               # pacote para o Steam Workshop
├── scripts/                     # scripts de verificação
├── docs/                        # glossário, notas de tradução e pipeline
├── mo_convert.py                # conversor MO <-> PO
├── update_ptbr.py               # sincroniza strings novas do EN para o PTBR
└── translation_batch.py         # ferramentas em lote
```

<details>
<summary><b>Guia passo a passo do <code>mo_convert.py</code> (para iniciantes)</b></summary>

#### Preparação

1. Instale o [Python](https://www.python.org/downloads/). Durante a instalação, marque a opção **"Add Python to PATH"**.
2. Copie o `mo_convert.py` para uma pasta do seu computador, de preferência junto com os arquivos de tradução.
3. Abra o Prompt de Comando (tecla **Windows + R**, digite `cmd` e pressione Enter) e navegue até a pasta:

   ```
   cd C:\Users\SeuNome\Desktop\Age of Wonders Tradução
   ```

#### Editar uma tradução existente

1. Converta o arquivo do jogo (MO) para texto editável (PO):

   ```
   python mo_convert.py to-po PTBR.MO minha_traducao.po
   ```

2. Abra o arquivo `.po` em um editor de texto (Bloco de Notas, Notepad++ ou VS Code).
   Cada bloco tem um `msgid` (o texto original em inglês) e um `msgstr` (a
   tradução). Escreva a sua tradução entre as aspas do `msgstr` e salve.

3. Converta de volta para o formato do jogo:

   ```
   python mo_convert.py to-mo minha_traducao.po PTBR.MO
   ```

4. Copie o `PTBR.MO` de volta para a pasta `Language\PTBR` do jogo.

#### Dicas

- Teste as mudanças no jogo depois de cada conversão.
- Faça backups frequentes dos seus arquivos.
- Se o script reclamar, confira se o Python está no PATH e se os caminhos dos arquivos estão corretos.

</details>

## 💛 Apoie o projeto

Se a tradução foi útil pra você, considere apoiar o trabalho com uma doação
via PIX: **pix@yuricunha.com**

<div align="center">

<img src="https://i.imgur.com/jx1MAIO.png" alt="QR Code PIX" width="200"/>

</div>

É uma ótima forma de mostrar que você quer que o projeto continue sendo
atualizado enquanto o jogo receber novidades. 🍻

## 📄 Licença

Este projeto está sob a licença [AGPL-3.0](LICENSE). Age of Wonders 4 é um
jogo da Triumph Studios, publicado pela Paradox Interactive. Este é um
projeto de fãs, sem vínculo oficial com os estúdios.
