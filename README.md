<div align="center">

# ◆ DarfinOS

### Uma distro Linux com opiniões que não são as suas.

**Arch Linux · SonicDE · XLibre · automação · experimentação**

[Instalação](#-começando) · [TUI](#-darfinos-tui--control-center) · [Etapas](#-o-que-o-darfinos-configura) · [Créditos](#-os-projetos-por-trás-do-darfinos) · [Segurança](#-avisos-importantes)

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

- Arch Linux ou derivado compatível com `pacman`.
- Um usuário comum com acesso ao `sudo` (**não execute o instalador como root**).
- Conexão com a internet para baixar pacotes e configurar repositórios.
- Para a TUI: **Python 3 com módulo `curses`**, disponível normalmente em instalações Linux; **nenhuma dependência de pip**.
- Para mudanças no XLibre/SonicDE: prefira um **TTY** em vez de uma sessão gráfica em uso.

Clone o projeto:

```bash
git clone https://github.com/AlanDarfin/DarfinOS.git
cd DarfinOS
```

### Opção A — interface visual no terminal (TUI V4)

Com `darfinos_tui_v4.py` e `DarfinOSInstallScript.sh` **na mesma pasta**:

```bash
python3 darfinos_tui_v4.py
```

Para testar a seleção e a montagem do comando **sem instalar nada**:

```bash
python3 darfinos_tui_v4.py --dry-run
```

Para apontar para outro instalador Bash:

```bash
python3 darfinos_tui_v4.py ./meu-script.sh
```

Para solicitar a versão remota do Bash:

```bash
python3 darfinos_tui_v4.py --fetch
```

> [!WARNING]
> A versão remota pode ainda não conter o protocolo de eventos da V4. Para aproveitar progresso detalhado e confirmações integradas, utilize o **Bash V4 correspondente**. Revise diferenças antes de executar código atualizado.

### Opção B — Bash tradicional

O instalador continua funcionando **sem a TUI**, com seus comandos e confirmações originais:

```bash
# Ver todas as etapas
bash DarfinOSInstallScript.sh --list

# Executar todas as etapas, interativamente
bash DarfinOSInstallScript.sh

# Executar somente algumas etapas
bash DarfinOSInstallScript.sh --only shells,dev_tools

# Executar tudo, exceto determinadas etapas
bash DarfinOSInstallScript.sh --skip gaming,hamachi

# Automatizar perguntas elegíveis do próprio script
bash DarfinOSInstallScript.sh -y
```

O modo `-y` **não** equivale a aceitar tudo: transações do pacman, verificação de chaves e outras operações sensíveis continuam exigindo atenção.

**Prefira clonar e inspecionar o código antes de executar.** Não é recomendável usar diretamente `curl | bash` em um instalador que altera repositórios e componentes centrais do sistema.

## 🖥 DarfinOS TUI — Control Center

A interface foi construída com **Python e `curses`**, sem bibliotecas externas de interface. O objetivo é oferecer uma experiência visual no terminal, sem duplicar a lógica do instalador: **o Bash continua sendo a fonte das etapas e responsável por instalar e configurar o sistema**.

### Seleção inteligente

- Carrega as etapas, descrições e dependências diretamente de `STEPS`, `STEP_DESC` e `STEP_DEPS` no Bash.
- Permite selecionar etapas individualmente, por grupo, todas ou nenhuma.
- Oferece busca, filtro de selecionadas e inclusão de dependências conhecidas.
- Exibe revisão antes da execução e permite alternar o modo `-y`.
- Permite salvar e recuperar **perfis de instalação nomeados**.
- Consulta pacotes instalados via `pacman` e Flatpak; não confunde a presença de um pacote com a conclusão de uma etapa inteira.

### Prévia dos aplicativos

A tela de aplicativos apresenta os pacotes que podem ser identificados a partir do Bash. **Essa prévia é parcial**: arrays, condicionais, instalações indiretas e escolhas feitas durante a execução podem mudar o resultado. Durante a instalação, eventos `PKG` também informam pacotes enviados aos wrappers instrumentados.

### Instalação acompanhada

A V4 acrescenta uma tela dedicada à execução com:

- Eventos `STEP_START`, `STEP_DONE`, `STEP_FAIL` e `STEP_SKIP` enviados pelo Bash por um canal separado.
- Progresso baseado nas **etapas finalizadas**, com distinção entre concluídas, falhas e ignoradas.
- Atividade recente, tempo decorrido e acesso aos logs em tempo real.
- Execução em **pseudo-terminal (PTY)** para preservar a interação com programas de terminal.
- Confirmações integradas para as funções Bash `confirm` e `choose`.
- Entrada mascarada para prompts de senha do `sudo` reconhecidos pelo frontend.
- Modo de terminal integral para perguntas externas não reconhecidas, como as do pacman e de helpers AUR.

**O percentual de etapas não representa progresso de download nem garante que cada pacote individual foi instalado.** Falhas antes do início das etapas aparecem pelo código de saída do processo, sem inventar eventos de etapa.

### Perfis, manutenção e histórico

- **Perfis:** salvar e carregar conjuntos de etapas para diferentes instalações.
- **Manutenção:** consultar pacotes, órfãos, atualizações registradas localmente, Flatpaks, serviços com falha e espaço em disco. **Somente leitura:** a central não remove nem atualiza nada.
- **Histórico do GitHub:** manter cópias em cache, calcular hashes SHA-256 e mostrar diferenças textuais entre versões baixadas.
- **Modo offline:** quando disponível, usar uma cópia válida em cache em vez de depender de uma conexão permanente.

> [!NOTE]
> Um hash SHA-256 permite comparar conteúdo, mas **não autentica o autor do arquivo**. O histórico/diff não substitui a revisão do código e não garante a identidade de um commit específico.

### Atalhos da TUI

| Tecla | Ação |
| --- | --- |
| `↑` / `↓` ou `J` / `K` | Navegar |
| `Espaço` | Marcar ou desmarcar uma etapa |
| `G` | Selecionar/desmarcar grupo |
| `A` / `N` | Todas / nenhuma |
| `/` | Pesquisar |
| `F` | Mostrar apenas selecionadas |
| `D` | Incluir dependências |
| `P` | Gerenciar perfis |
| `I` | Consultar pacotes instalados |
| `B` | Ver prévia de aplicativos |
| `M` | Central de manutenção |
| `H` | Histórico e diferenças |
| `U` | Atualizar fonte remota |
| `Y` | Alternar `-y` |
| `R` / `Enter` | Revisar a instalação |
| `Q` | Sair da seleção |

**Durante a instalação:** `L` alterna o painel de progresso/logs; `T` abre o terminal interativo; `Ctrl+]` retorna ao painel. `Ctrl+C` solicita a interrupção do processo.

Em prompts não reconhecidos, use o terminal integral em vez de presumir que o painel responderá automaticamente.

## 📁 Logs e arquivos locais

| Local | Conteúdo |
| --- | --- |
| `~/.local/state/postinstall/` | Logs próprios do instalador Bash |
| `~/.local/state/darfinos-tui/logs/` | Logs de execução acompanhada pela TUI |
| `~/.config/darfinos-tui/profiles/` | Perfis nomeados |
| `~/.cache/darfinos-tui/` | Script em cache, versões, histórico e diff |

Os caminhos acima são os padrões das versões documentadas; consulte o código se utilizar uma variante modificada.

## ⚠ Avisos importantes

O DarfinOS pode alterar **repositórios, chaves de assinatura, pacotes, serviços, shells, configurações de usuário e componentes gráficos**. Algumas mudanças podem exigir intervenção manual ou afetar a inicialização do desktop.

1. **Leia as etapas selecionadas e mantenha backups** antes de executar.
2. **Não execute como root.** O instalador pede `sudo` quando necessário.
3. **Não confunda `-y` com aprovação irrestrita.** Verificações sensíveis continuam interativas.
4. **Para SonicDE e XLibre, prefira um TTY** e tenha um caminho de recuperação.
5. **Bedrock Linux é opcional e avançado.** Leia sua documentação oficial antes de considerar a integração.
6. **Teste primeiro em ambiente recuperável**, especialmente se estiver modificando uma instalação que você usa diariamente.
7. **A TUI V4 ainda exige validação em instalações reais.** Testes de sintaxe e componentes não substituem testes completos de PTY, prompts e operações de sistema.

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

## ✦ Considerações finais

O Linux sempre permitiu construir um sistema à sua maneira. O DarfinOS é minha tentativa de levar essa liberdade um pouco mais longe: reunir minhas preferências em um processo reproduzível, compartilhar o resultado e continuar experimentando.

**Não é a configuração definitiva do Linux. É a minha configuração do Linux.**

E, sinceramente, isso já é motivo suficiente para existir.

---

<div align="center">

*DarfinOS — opiniões fortes, escolhas questionáveis e um sistema do seu próprio jeito.*

</div>
