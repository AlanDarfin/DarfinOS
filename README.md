<div align="center">

# ⚡ DarfinOS

### Uma distro Linux com opiniões que não são as suas.

**Seu Arch, minhas regras.**

![Arch Linux](https://img.shields.io/badge/BASE-Arch_Linux-FFCB2E?style=for-the-badge&labelColor=171717&logo=archlinux&logoColor=white)
![SonicDE](https://img.shields.io/badge/DESKTOP-SonicDE-FFCB2E?style=for-the-badge&labelColor=171717)
![XLibre](https://img.shields.io/badge/DISPLAY-XLibre-FFCB2E?style=for-the-badge&labelColor=171717)
![Bash + Python](https://img.shields.io/badge/TOOLS-Bash_%2B_Python-FFCB2E?style=for-the-badge&labelColor=171717)

**[🌐 Site do projeto](https://github.com/AlanDarfin/darfinos-website) · [⬇️ Releases](https://github.com/AlanDarfin/DarfinOS/releases) · [📖 Documentação](docs/) · [🧪 Actions](https://github.com/AlanDarfin/DarfinOS/actions)**

[Instalação](#-começando) · [TUI V5](#-darfinos-tui-v5--control-center) · [Etapas](#-o-que-o-darfinos-configura) · [Créditos](#-os-projetos-por-trás-do-darfinos) · [Documentação](#-documentação) · [Segurança](#-avisos-importantes) · [Contato](#-contato)

</div>

---

Olá, meus caros amantes de Linux! Sejam bem-vindos ao **DarfinOS** — um projeto para quem acredita que um sistema operacional pode ser mais do que uma coleção de pacotes instalados por padrão.

Inspirado por projetos opinativos como o [Omarchy](https://github.com/basecamp/omarchy), pela proposta inicial do [LinuxToys](https://github.com/psygreg/linux_toys) e por muitas horas personalizando o Arch Linux, o DarfinOS nasceu de uma pergunta simples: **e se eu reunisse todas as minhas preferências, ferramentas, configurações e pequenas obsessões com Linux em um único processo de pós-instalação?**

O resultado é deliberadamente pessoal, um tanto underground e sem muita preocupação em seguir o consenso. Afinal, se eu vou passar horas usando meu sistema, por que não configurá-lo exatamente do jeito que eu gosto?

> [!IMPORTANT]
> **O DarfinOS ainda não é uma distribuição Linux independente.** Atualmente é um conjunto de ferramentas de **pós-instalação para Arch Linux e derivados compatíveis**, formado por um instalador Bash e uma interface de terminal opcional em Python.

## ✦ Filosofia

- **Opiniões, não neutralidade.** O projeto escolhe ferramentas e configurações com uma identidade própria.
- **Um workflow inteiro.** Não se trata apenas de instalar aplicativos, mas de organizar desktop, terminal, serviços e manutenção.
- **Automação com controle.** Reduzir trabalho repetitivo sem esconder decisões importantes.
- **Modularidade.** Instalar tudo ou selecionar somente as etapas desejadas.
- **Experimentação.** Explorar combinações incomuns, sem fingir que elas servem para todo mundo.
- **Transparência.** Código aberto para inspeção, logs e confirmações em operações sensíveis.

## 🖼️ Conheça o DarfinOS

O site do projeto reúne **capturas de tela, explicações visuais e links rápidos** para conhecer o ambiente e as ferramentas que inspiram sua identidade. O README concentra as instruções práticas; a galeria visual fica no site.

> [!TIP]
> **Quer ver antes de instalar?** Explore a [página do projeto](https://github.com/AlanDarfin/darfinos-website) e os [arquivos publicados](https://github.com/AlanDarfin/DarfinOS/releases). O DarfinOS é um projeto de **personalização e pós-instalação do Arch**, não uma ISO independente.

## 🧩 Os projetos por trás do DarfinOS

O DarfinOS é uma camada de integração e configuração. **As tecnologias que dão identidade ao ambiente vêm de projetos independentes, com seus próprios desenvolvedores e comunidades.** Eles merecem destaque e crédito.

### SonicDE — o rosto do desktop

**[Site oficial do SonicDE](https://sonicde.org/)** · [Projeto no GitHub](https://github.com/Sonic-DE)

O **SonicDE** é um ambiente de desktop derivado do ecossistema KDE Plasma, com desenvolvimento e escolhas próprias. É a principal referência visual e funcional da experiência gráfica que o DarfinOS procura montar: interface, componentes de desktop e integração com o sistema.

O DarfinOS **não desenvolve nem mantém o SonicDE**; ele automatiza sua instalação e configura componentes complementares conforme as etapas escolhidas.

### XLibre — a base gráfica

**[Site oficial do XLibre](https://xlibre.org/)** · [Projeto no GitHub](https://github.com/X11Libre)

O **XLibre** é um projeto de servidor gráfico baseado na linhagem do X.Org/X11. No DarfinOS, ele representa a escolha por uma pilha gráfica X11 alternativa, combinada ao SonicDE nas etapas de configuração do desktop.

A instalação ou substituição do servidor gráfico pode afetar a sessão gráfica existente. **É recomendável executar essas etapas a partir de um TTY**, com um meio de recuperação disponível.

### Bedrock Linux — distribuições sem fronteiras

**[Site oficial do Bedrock Linux](https://bedrocklinux.org/)** · [Código-fonte e documentação](https://github.com/bedrocklinux/bedrocklinux-userland)

O **Bedrock Linux** é uma metadistribuição que permite combinar componentes de diferentes distribuições Linux em um mesmo ambiente. É uma proposta particularmente interessante para quem gosta de experimentar além dos limites de uma única distribuição.

O DarfinOS oferece uma **etapa opcional** relacionada ao Bedrock. Ela não é necessária para utilizar o restante do projeto e exige atenção especial: integrar o Bedrock altera aspectos fundamentais do sistema e deve ser considerado somente depois de consultar a documentação oficial e preparar backups.

> [!NOTE]
> **Crédito e independência:** SonicDE, XLibre e Bedrock Linux são projetos independentes. O DarfinOS não é uma versão oficial, afiliada ou endossada por eles. O mérito pelo desenvolvimento dessas tecnologias pertence às respectivas equipes e comunidades.

## 🛠 O que o DarfinOS configura

O instalador Bash organiza **32 etapas** em grupos. A seleção pode ser feita pela linha de comando ou pela TUI.

| Área | Exemplos de etapas | O que faz |
| --- | --- | --- |
| Sistema e repositórios | `pacman_conf`, `mirrors`, `repo_xlibre`, `repo_sonicde`, `repo_chaotic`, `sysupgrade` | Ajustes do pacman, espelhos, repositórios e atualização |
| Base | `base`, `aur_helper`, `fonts`, `hardware` | Ferramentas essenciais, AUR, fontes e hardware |
| Desktop | `xlibre`, `sonicde`, `desktop_extras`, `bluetooth` | Servidor gráfico, ambiente de desktop e integração |
| Terminal e desenvolvimento | `cli_tools`, `dev_tools`, `pkg_managers`, `shells`, `git_setup` | Fish, Zsh, Starship, ferramentas CLI e desenvolvimento |
| Rede e serviços | `zerotier`, `hamachi`, `syncthing`, `docker` | Rede virtual, sincronização e containers |
| Aplicativos e jogos | `flatpak`, `apps`, `gaming`, `browser` | Flathub, aplicativos, Steam e ferramentas para jogos |
| Manutenção e extras | `maintenance`, `firewall`, `cleanup`, `bobagens`, `bedrock` | Timers, firewall, limpeza e experimentos opcionais |

Entre os programas e recursos previstos pelo projeto estão **Obsidian, Vesktop, Spotify, Proton Pass, Proton VPN, Steam, RetroArch, Wine, GameMode, MangoHud, Fastfetch, Neovim, tmux, fzf, eza, yazi, Syncthing e Docker**, conforme as opções e condições do sistema.

A lista é ilustrativa, não uma garantia de que todos esses aplicativos serão instalados em qualquer execução. Consulte o Bash para verificar a seleção efetiva.

## 🚀 Começando

### Pré-requisitos

- **Arch Linux** ou derivado compatível com `pacman`, com acesso à internet.
- **Usuário comum com `sudo`**. Não execute o instalador inteiro como root.
- **Python 3 com `curses`** para a TUI; não é necessário instalar dependências via `pip`.
- Um **terminal interativo** para navegar na TUI. Para mudanças profundas em XLibre/SonicDE, prefira um TTY e tenha um plano de recuperação.

Clone o repositório:

```bash
git clone https://github.com/AlanDarfin/DarfinOS.git
cd DarfinOS
```

### Opção A — TUI V5 (recomendada para seleção e acompanhamento)

Com o frontend e o instalador Bash na raiz do repositório:

```bash
python3 DarfinOSInstallScript-TUI.py --local
```

Explore as etapas, escolha um preset, confira dependências e revise tudo antes de confirmar. **Abrir a TUI não inicia uma instalação automaticamente.**

```bash
# Revisar a seleção sem executar a instalação
python3 DarfinOSInstallScript-TUI.py --local --dry-run

# Listar presets disponíveis
python3 DarfinOSInstallScript-TUI.py --list-presets

# Abrir com o preset Gaming selecionado
python3 DarfinOSInstallScript-TUI.py --local --preset gaming

# Exportar manifesto JSON (não instala pacotes)
python3 DarfinOSInstallScript-TUI.py --manifest > manifest.json

# Consultar o histórico local de execuções
python3 DarfinOSInstallScript-TUI.py --runs

# Preparar retomada de uma execução incompleta
python3 DarfinOSInstallScript-TUI.py --resume
```

> [!NOTE]
> O frontend atual se chama **`DarfinOSInstallScript-TUI.py`**. Nomes antigos como `darfinos_tui_v4.py` e `darfinos_tui_v4_2.py` pertencem a versões anteriores. Ao atualizar, mantenha o frontend, o Bash e os testes da mesma revisão.

### Opção B — Bash tradicional

O instalador continua independente da interface:

```bash
# Consultar as 32 etapas
bash DarfinOSInstallScript.sh --list

# Executar interativamente
bash DarfinOSInstallScript.sh

# Executar somente etapas escolhidas
bash DarfinOSInstallScript.sh --only shells,dev_tools

# Excluir etapas da seleção
bash DarfinOSInstallScript.sh --skip gaming,hamachi

# Automatizar apenas perguntas elegíveis do script
bash DarfinOSInstallScript.sh -y
```

O modo `-y` **não é aprovação irrestrita** de operações do `pacman`, chaves de assinatura ou outras ferramentas. Evite executar o instalador por `curl | bash` sem revisar o código.

## 🖥 DarfinOS TUI V5 — Control Center

A TUI é escrita em **Python + `curses`**, sem dependências externas de interface. Ela lê as etapas e dependências do Bash, organiza a seleção e acompanha a execução por **PTY**, sem substituir a lógica de instalação.

### Interface visual e seleção

- **Layout responsivo**, projetado para terminais a partir de **54×16**; em terminais largos, exibe painel lateral de detalhes.
- **Marcadores de seleção, foco destacado, estados coloridos e barras de progresso** com significado explícito.
- **Busca, filtros, seleção por grupo, seleção total e inclusão de dependências**.
- **Prévia de pacotes**, informações de cada etapa e detecção consultiva de itens já instalados.
- **Perfis pessoais**, histórico/diff de versões baixadas e central de manutenção somente leitura.
- **Presets oficiais** e integração com manifesto de aplicativos.

A barra da seleção indica quantas etapas estão marcadas. A barra durante a execução indica **etapas encerradas** — inclusive falhas e ignoradas — e não percentual de downloads ou garantia de sucesso.

### Acompanhamento da instalação

A comunicação entre o frontend e o Bash usa eventos estruturados enviados por um canal separado:

| Evento | Significado |
| --- | --- |
| `STEP_START` | Etapa iniciada |
| `STEP_DONE` | Etapa finalizada com sucesso |
| `STEP_FAIL` | Etapa registrada como falha |
| `STEP_SKIP` | Etapa ignorada |
| `PKG` | Pacotes encaminhados aos wrappers instrumentados |
| `PROMPT_CONFIRM` / `PROMPT_CHOOSE` | Confirmações ou escolhas originadas das funções Bash correspondentes |

O painel mostra andamento, estados, tempo decorrido e logs. Há **modais para perguntas reconhecidas** e um **terminal PTY integral** para interações externas que não podem ser interpretadas com segurança, como certas perguntas do `pacman` e de helpers AUR.

> [!IMPORTANT]
> O código de saída do Bash, isoladamente, pode não representar o estado de todas as etapas. O diário da TUI considera também os eventos de falha e os estados incompletos.

### Atalhos principais

| Tecla | Ação |
| --- | --- |
| `↑` / `↓`, `J` / `K` | Navegar |
| `Espaço` | Marcar/desmarcar etapa |
| `G` | Marcar/desmarcar grupo |
| `A` / `N` | Selecionar todas / nenhuma |
| `/` | Pesquisar |
| `F` | Filtrar selecionadas |
| `D` | Incluir dependências |
| `O` | Escolher preset oficial |
| `P` | Gerenciar perfis personalizados |
| `Z` | Diagnóstico e recuperação |
| `B` | Prévia de aplicativos |
| `I` | Consultar pacotes instalados |
| `M` | Manutenção (somente leitura) |
| `H` | Histórico e diferenças |
| `U` | Atualizar fonte remota |
| `Y` | Alternar `-y` |
| `R` / `Enter` | Revisar instalação |
| `Q` | Sair da seleção |

**Durante a instalação:** `L` alterna painel/logs; `T` abre o terminal integral; `Ctrl+]` volta ao painel. Prompts desconhecidos devem ser respondidos no terminal integral, não por automação presumida.

Para detalhes do layout e das limitações, consulte **[docs/TUI_V5.md](docs/TUI_V5.md)**.

## ♻ Recuperação e retomada — V4.2

A partir da V4.2, a TUI mantém um **diário JSON persistente por execução**, registrando as etapas, seus estados e a identidade do Bash usado.

- **Estados acompanhados:** concluída, falha, ignorada, pendente ou interrompida/incerta.
- **Retomada seletiva:** prepara as etapas não concluídas e as dependências necessárias, sem repetir automaticamente tudo.
- **Proteção por SHA-256:** a retomada verifica se o instalador Bash corresponde ao usado no registro.
- **Rastreabilidade:** uma execução retomada pode registrar a execução anterior que lhe deu origem.
- **Revisão obrigatória:** a seleção recuperada ainda deve ser conferida antes de instalar.

```bash
# Consultar execuções anteriores
python3 DarfinOSInstallScript-TUI.py --runs

# Preparar seleção para retomada
python3 DarfinOSInstallScript-TUI.py --resume
```

Na interface, use **`Z`** para acessar o diagnóstico.

> [!WARNING]
> **Retomar não é fazer rollback.** Uma etapa interrompida pode ter aplicado parte das mudanças. Confira os logs e os efeitos da etapa antes de executá-la novamente. O hash detecta diferenças de conteúdo, mas não autentica a origem do arquivo.

## ✦ Manifesto e presets — V4.4

### Presets oficiais

| Preset | Proposta | Observação |
| --- | --- | --- |
| `minimal` | Base enxuta e ferramentas essenciais | Menor conjunto de etapas |
| `desktop` | SonicDE, XLibre, integração e aplicativos | Modifica a pilha gráfica |
| `gaming` | Desktop e ferramentas para jogos | Inclui recursos voltados a jogos |
| `full` | Todas as **32 etapas** | **Inclui Bedrock e outras operações avançadas** |

Um preset **apenas marca etapas**; ele não executa nada por conta própria. Perfis personalizados (`P`) e presets oficiais (`O`) são recursos distintos.

### Manifesto de aplicativos

```bash
python3 DarfinOSInstallScript-TUI.py --manifest > manifest.json
```

O JSON descreve as etapas e dependências, inclui o SHA-256 do Bash e reúne pacotes identificados estaticamente, organizados por origem quando possível. A indicação **`accuracy: partial_static`** significa que a lista é parcial: condicionais, variáveis, arrays e instalações indiretas podem não ser capturados.

A exportação é **somente leitura** e não instala nada. Os eventos `PKG` complementam a prévia durante a execução real.

**Documentação:** [docs/MANIFESTO_PRESETS.md](docs/MANIFESTO_PRESETS.md).

## 🧪 Testes automatizados e GitHub Actions — V4.3+

O DarfinOS possui testes automatizados com **`unittest`**, sem dependências Python externas, para validar partes críticas do projeto antes de publicar alterações.

Os testes cobrem, entre outros pontos:

- Parser das **32 etapas** e resolução de dependências.
- Perfis, presets e exportação do manifesto.
- Registros de execução, recuperação e proteção contra Bash diferente.
- Eventos de progresso e confirmações do Bash em cenários isolados.
- Componentes não interativos da interface visual V5.

Execute na raiz do repositório:

```bash
bash -n DarfinOSInstallScript.sh
python3 -m py_compile DarfinOSInstallScript-TUI.py
python3 -m unittest discover -s tests -v
```

O workflow **[DarfinOS · Testes](.github/workflows/tests.yml)** executa verificações em múltiplas versões do Python e mantém um job de ShellCheck com relatório de qualidade. O resultado de cada execução pode ser consultado em **[GitHub Actions](https://github.com/AlanDarfin/DarfinOS/actions)**.

> [!NOTE]
> Os testes offline **não instalam pacotes, não pedem sudo e não substituem testes reais** de sessão gráfica, PTY e prompts de ferramentas externas. A quantidade de testes pode mudar conforme o projeto evolui.

**Documentação:** [docs/TESTES.md](docs/TESTES.md).

## 📁 Logs, estado e arquivos locais

| Caminho | Conteúdo |
| --- | --- |
| `~/.local/state/postinstall/` | Logs produzidos pelo instalador Bash |
| `~/.local/state/darfinos-tui/logs/` | Logs da execução acompanhada pela TUI |
| `~/.local/state/darfinos-tui/runs/` | Diários JSON de execução e recuperação |
| `~/.config/darfinos-tui/profiles/` | Perfis personalizados |
| `~/.cache/darfinos-tui/` | Cópias do Bash, histórico de versões e diffs |

Esses são os caminhos padrão documentados; variantes locais podem modificá-los.

## ⚡ Links rápidos

| Projeto | Para que serve | Acesso |
| --- | --- | --- |
| **Arch Linux** | Base do DarfinOS | [Site oficial](https://archlinux.org/) |
| **SonicDE** | Ambiente gráfico | [Site oficial](https://sonicde.org/) |
| **XLibre** | Servidor gráfico X11 | [Site oficial](https://xlibre.org/) |
| **Bedrock Linux** | Integração experimental entre distribuições | [Site oficial](https://bedrocklinux.org/) |
| **LinuxToys** | Grande inspiração para a proposta de automação | [GitHub](https://github.com/psygreg/linux_toys) |

## 📚 Documentação

O README é a porta de entrada. Os documentos abaixo aprofundam os componentes específicos:

| Documento | Conteúdo |
| --- | --- |
| **[TUI V5](docs/TUI_V5.md)** | Layout, controles, progresso visual, limitações e validação |
| **[Manifesto e presets](docs/MANIFESTO_PRESETS.md)** | Presets oficiais, inventário parcial e comandos de exportação |
| **[Testes e CI](docs/TESTES.md)** | Testes offline, GitHub Actions, escopo e limitações |

**Outros pontos de referência:** [instalador Bash](DarfinOSInstallScript.sh) · [frontend Python](DarfinOSInstallScript-TUI.py) · [workflow de CI](.github/workflows/tests.yml) · [código dos testes](tests/).

## ⚠ Avisos importantes

O DarfinOS pode alterar **repositórios, chaves, pacotes, serviços, shells, configurações de usuário e componentes gráficos**. Algumas operações exigem recuperação manual.

1. **Leia o código e revise as etapas selecionadas.** Mantenha backups antes de mudanças profundas.
2. **Não execute o instalador inteiro como root.** Use um usuário normal com `sudo`.
3. **Não trate `-y` como confirmação universal.** Algumas decisões continuam interativas.
4. **Para XLibre e SonicDE, prefira um TTY** e tenha um caminho de recuperação da sessão gráfica.
5. **Bedrock Linux é opcional e avançado.** O preset `full` inclui essa etapa.
6. **Não confunda testes verdes com instalação real validada.** CI e testes offline verificam apenas o escopo automatizado.
7. **Retomada não é reversão.** Etapas parcialmente executadas podem exigir análise manual.
8. **Atualizações remotas merecem revisão.** Hash e diff não equivalem a verificação de autoria.

## 🤝 Créditos, inspirações e independência

O DarfinOS se inspira na ideia de ambientes Linux opinativos e reproduzíveis. Agradecimentos especiais aos mantenedores e colaboradores de:

- **[SonicDE](https://sonicde.org/)** — ambiente de desktop que dá a cara do projeto.
- **[XLibre](https://xlibre.org/)** — servidor gráfico utilizado na proposta de desktop.
- **[Bedrock Linux](https://bedrocklinux.org/)** — inspiração para a integração experimental entre distribuições.
- **[Arch Linux](https://archlinux.org/)** — base do sistema e do ecossistema de pacotes.
- **[Omarchy](https://github.com/basecamp/omarchy)** e **[LinuxToys](https://github.com/psygreg/linux_toys)** — inspirações de filosofia e automação.

**DarfinOS não substitui esses projetos e não reivindica a autoria de seus componentes.** Visite os sites oficiais, consulte as licenças e apoie os desenvolvedores originais.

## 🧪 Estado do projeto

O DarfinOS é um **projeto pessoal em desenvolvimento**. Etapas, escolhas e funcionalidades podem mudar conforme novas ferramentas forem testadas. Não existe a pretensão de oferecer uma configuração perfeita para todo computador — e muito menos de substituir o conhecimento necessário para administrar o Arch Linux.

É para quem gosta de experimentar, modificar scripts e descobrir que, às vezes, a melhor solução é aquela ferramenta obscura que quase ninguém conhece — ou simplesmente a que funciona melhor para o próprio workflow.

Você não precisa concordar com as escolhas do DarfinOS. Discordar, modificar e criar sua própria versão faz parte da ideia.

O projeto evoluiu de um **script de pós-instalação** para um conjunto de ferramentas com **TUI visual, eventos estruturados, recuperação, presets, manifesto e testes automatizados**. Ainda assim, permanece experimental e sujeito a mudanças.

## ✉ Contato

Dúvidas, sugestões, relatórios de problemas ou vontade de conversar sobre o projeto?

- **GitHub:** [@AlanDarfin](https://github.com/AlanDarfin) · [Repositório DarfinOS](https://github.com/AlanDarfin/DarfinOS)
- **Twitter / X:** [@srdarfin](https://twitter.com/srdarfin)
- **E-mail:** [srdarfin@gmail.com](mailto:srdarfin@gmail.com)
- **Issues:** [Abrir ou consultar uma issue](https://github.com/AlanDarfin/DarfinOS/issues)

## ✦ Considerações finais

O Linux sempre permitiu construir um sistema à sua maneira. O DarfinOS é minha tentativa de levar essa liberdade um pouco mais longe: reunir minhas preferências em um processo reproduzível, compartilhar o resultado e continuar experimentando.

**Não é a configuração definitiva do Linux. É a minha configuração do Linux.**

E, sinceramente, isso já é motivo suficiente para existir.

---

<div align="center">

*DarfinOS — opiniões fortes, escolhas questionáveis e um sistema do seu próprio jeito.*

**Arch Linux · SonicDE · XLibre · automação · experimentação**

</div>
