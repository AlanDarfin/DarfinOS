# DarfinOS

> **Uma distro Linux com opiniões que não são as suas.**

Olá, meus caros amantes de Linux! Sejam bem-vindos ao repositório do **DarfinOS** — um projeto para quem acredita que um sistema operacional pode ser mais do que uma coleção de pacotes instalados por padrão.

Nos últimos anos, o mundo Linux viu surgir projetos com filosofias cada vez mais próprias. Sistemas como o [Omarchy](https://github.com/basecamp/omarchy) mostram que não é necessário agradar a todo mundo para construir uma experiência coerente: basta ter uma visão clara do que o sistema deve ser, mesmo que algumas escolhas agradem uns e afastem outros.

Inspirado por essa filosofia, pela proposta inicial do [LinuxToys](https://github.com/psygreg/linux_toys) e por outros projetos que priorizam experiências opinativas, nasceu o **DarfinOS**.

A ideia é simples: e se eu pudesse transformar todas as minhas preferências, ferramentas, configurações e pequenas obsessões com Linux em um único processo de pós-instalação?

O resultado é um projeto deliberadamente pessoal, um tanto underground e sem muita preocupação em seguir o consenso da comunidade. Afinal, se eu vou passar horas usando meu sistema, por que não configurá-lo exatamente do jeito que eu gosto?

## O que é o DarfinOS?

O DarfinOS não é, atualmente, uma distribuição Linux independente. É um **script de pós-instalação para Arch Linux e derivados compatíveis**, criado para transformar uma instalação existente em um ambiente de trabalho completo, com ferramentas, serviços, aplicativos e configurações que refletem uma visão específica de como um desktop Linux deve funcionar.

Mas o objetivo vai além de automatizar a instalação dos meus programas favoritos.

A proposta é automatizar boa parte da construção de um ambiente Arch: desde ajustes no gerenciador de pacotes e configuração de repositórios até a instalação de um ambiente gráfico, ferramentas de desenvolvimento, aplicativos, recursos para jogos e tarefas de manutenção.

Em vez de simplesmente instalar programas, o DarfinOS busca estabelecer um **workflow inteiro**.

## Filosofia do projeto

- **Opiniões, não neutralidade.** O projeto faz escolhas deliberadas sobre ferramentas, ambiente gráfico, shell e organização do sistema. Não pretende ser uma solução universal.
- **Automação com personalidade.** Configurar um sistema deve ser menos repetitivo, sem eliminar a possibilidade de entender e controlar o que está acontecendo.
- **Um ambiente, não apenas uma lista de pacotes.** Shell, terminal, desktop, aplicativos e serviços devem fazer parte de uma experiência coerente.
- **Modularidade.** Nem todo mundo precisa de tudo. As etapas podem ser selecionadas ou ignoradas para adaptar a instalação às necessidades de cada máquina.
- **Transparência e controle.** O script inclui confirmações para operações sensíveis, registra a execução em log e procura preservar configurações existentes quando possível.
- **Experimentação acima do consenso.** O DarfinOS é também um laboratório pessoal para explorar ferramentas, combinações e ideias que nem sempre são as escolhas mais populares.

## O que o script oferece?

As funcionalidades variam conforme as opções selecionadas, mas o projeto atualmente reúne etapas para:

- **Sistema e repositórios:** ajustes do pacman, mirrors, atualização do sistema e configuração dos repositórios XLibre, SonicDE e Chaotic-AUR.
- **Ambiente gráfico:** instalação do [XLibre](https://xlibre.org/) e do [SonicDE](https://sonicde.org/), além de componentes complementares para desktop, áudio, rede e Bluetooth.
- **Terminal e shell:** Fish, Zsh, Starship, zoxide, fzf, eza, bat, yazi, Neovim, tmux e outras ferramentas de linha de comando.
- **Desenvolvimento:** compiladores, Git, Python, Node.js, Go, Rust e gerenciadores de pacotes.
- **Rede e sincronização:** opções para ZeroTier, Hamachi, Syncthing e Docker.
- **Aplicativos:** integração com Flatpak e Flathub, ferramentas de gerenciamento e aplicativos como Obsidian, Vesktop, Spotify, Proton Pass e Proton VPN.
- **Jogos:** Steam, RetroArch, Wine, Winetricks, GameMode e MangoHud.
- **Manutenção:** timers para limpeza de cache e TRIM, limpeza opcional de pacotes órfãos e outras tarefas administrativas.
- **Personalização:** configuração do Fastfetch, preset Gruvbox Rainbow para Starship, tema GTK para Flatpak, Pyroclear e pacotes adicionais opcionais.
- **Experimentação:** uma etapa opcional relacionada ao Bedrock Linux, destinada a quem deseja explorar uma abordagem mais radical de integração entre distribuições.

Nem todas essas etapas são obrigatórias. O objetivo é oferecer uma base personalizável, sem transformar cada escolha do autor em uma exigência para quem utiliza o script.

## Como usar

Clone o repositório:

```bash
git clone https://github.com/AlanDarfin/DarfinOS.git
cd DarfinOS
```

Consulte as etapas disponíveis:

```bash
bash DarfinOSInstallScript.sh --list
```

Execute o script interativamente:

```bash
bash DarfinOSInstallScript.sh
```

Execute apenas etapas específicas:

```bash
bash DarfinOSInstallScript.sh --only shells,dev_tools
```

Execute tudo, exceto determinadas etapas:

```bash
bash DarfinOSInstallScript.sh --skip gaming,hamachi
```

Use o modo que automatiza as perguntas do próprio script:

```bash
bash DarfinOSInstallScript.sh -y
```

> O modo `-y` não elimina todas as confirmações: operações sensíveis e transações do pacman continuam exigindo atenção.

Ou apenas use o `Curl`

```bash
curl -fsSL "https://raw.githubusercontent.com/AlanDarfin/DarfinOS/main/DarfinOSInstallScript.sh" | bash
```

> **Atenção:** o DarfinOS pode alterar repositórios, pacotes, serviços e configurações do sistema. Leia o código antes de executar, mantenha backups e confira as instruções específicas das etapas selecionadas. A instalação do XLibre/SonicDE e a etapa do Bedrock Linux merecem cuidado especial. Recomenda-se testar em uma máquina virtual ou em uma instalação que possa ser recuperada.

## Para quem é?

Para quem gosta de Arch Linux, quer automatizar a configuração do próprio ambiente e não se importa que o projeto tenha escolhas muito particulares.

Também é para quem gosta de experimentar, modificar scripts e descobrir que, às vezes, a melhor solução para um problema é uma ferramenta obscura que quase ninguém conhece — ou simplesmente aquela que funciona melhor para o seu próprio workflow.

Você não precisa concordar com as escolhas do DarfinOS. Na verdade, discordar delas, modificá-las e criar sua própria versão faz parte da ideia.

## Estado do projeto

O DarfinOS é um projeto pessoal em desenvolvimento. Suas escolhas, etapas e funcionalidades podem mudar conforme novas ferramentas são experimentadas e o script evolui.

Não há a pretensão de oferecer uma configuração perfeita para todos os computadores, nem de substituir o conhecimento necessário para administrar um sistema Arch Linux. O propósito é compartilhar uma visão pessoal de um desktop Linux e tornar sua reprodução mais simples.

## Considerações finais

O Linux sempre permitiu construir um sistema à sua maneira. O DarfinOS é a minha tentativa de levar essa liberdade um pouco mais longe: reunir minhas preferências em um processo reproduzível, compartilhar o resultado e continuar experimentando.

**Não é a configuração definitiva do Linux. É a minha configuração do Linux.**

E, sinceramente, isso já é motivo suficiente para existir.

---

*DarfinOS — opiniões fortes, escolhas questionáveis e um sistema do seu próprio jeito.*
