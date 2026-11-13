[🇺🇸 English (default)](../LABS.md) · **🇧🇷 Português (Brasil)**

# ⚡ DarfinOS Labs · catálogo de projetos independentes

**Seu Arch, minhas regras.** A ideia do Labs é experimentar ferramentas que
seguem caminhos menos convencionais no ecossistema Linux, sem instalar tudo
automaticamente nem confundir demonstração com funcionamento validado.

O catálogo traz **13 projetos**, com link para a origem, classificação de risco,
descrição e indicação exata do que o DarfinOS pode instalar. Nenhum é desenvolvido
ou mantido pelo DarfinOS.

## Modos de integração

- **Pacman oficial:** i3 e Xfce podem ser instalados pelos repositórios do Arch.
- **Assets com confirmação:** Chicago95 copia apenas os diretórios de temas/ícones upstream para o HOME, sem executar installer.py ou aplicar a aparência automaticamente.
- **AUR, confirmação especial:** NsCDE, JuNest, Decman e Metapac podem ser
  instalados apenas quando selecionados individualmente. As etapas exigem digitar
  `LABS` e recusam `-y`. O usuário deve revisar o PKGBUILD e suas perguntas.
- **Somente guia:** Conty, nix-portable, Trinity, yserver, xomposite, Wayback
  e Booster têm descrição e link original, mas não são instalados pelo Bash.
  São opções que demandam download manual, repositórios de terceiros, compilação
  ou intervenção em ambiente gráfico/boot.

`--all` e `--skip` **não executam etapas `lab_*`**. O preset `full` também as
exclui deliberadamente. Na TUI, `A` seleciona somente etapas convencionais:
acessar `L` e usar Espaço é o caminho para escolher Labs individualmente.

## Como explorar sem instalar

```bash
bash DarfinOSInstallScript.sh --labs
bash DarfinOSInstallScript.sh --lab-info yserver
python3 DarfinOSInstallScript-TUI.py --labs
python3 DarfinOSInstallScript-TUI.py --lab-info i3
python3 DarfinOSInstallScript-TUI.py --plan --preset i3
```

Na TUI, a tecla **L** abre o catálogo navegável. Enter apresenta descrição,
risco, modo e URL; Espaço marca somente as etapas instaláveis, sem executá-las.

## Catálogo original

| Projeto | Para quê? | Integração | Projeto original |
| --- | --- | --- | --- |
| **i3** | WM mosaico X11 | Pacman oficial, etapa `i3` | [i3](https://i3wm.org/) |
| **Chicago95** | Tema retrô Windows 95 para Xfce | Etapas `xfce` + `lab_chicago95`, preset `retro` | [Chicago95](https://github.com/grassmunk/Chicago95) |
| **NsCDE** | Desktop UNIX retrô sobre FVWM | AUR assistido | [NsCDE](https://github.com/NsCDE/NsCDE) |
| **JuNest** | Ambiente Arch no espaço de usuário | AUR assistido; sem `setup` | [JuNest](https://github.com/fsquillace/junest) |
| **Decman** | Configuração declarativa Python | AUR assistido, sem aplicar configs | [Decman](https://github.com/kiviktnm/decman) |
| **Metapac** | Gerenciar pacotes declarativamente | AUR assistido, sem `sync`/`clean` | [Metapac](https://github.com/ripytide/metapac) |
| **Conty** | Contêiner portátil para aplicativos e jogos | Guia manual, sem download automático | [Conty](https://github.com/Kron4ek/Conty) |
| **nix-portable** | Nix sem instalação tradicional | Guia manual | [nix-portable](https://github.com/DavHau/nix-portable) |
| **Trinity Desktop** | Continuar a experiência KDE 3 | Guia manual; repositório/chave de terceiros | [Trinity](https://www.trinitydesktop.org/) |
| **yserver** | Servidor X11 novo em Rust | Laboratório gráfico em VM | [yserver](https://github.com/joske/yserver) |
| **xomposite** | Compositor X11 Rust para XLibre | Laboratório gráfico; atenção ao KWin | [xomposite](https://github.com/demostenex/xlibre-compositor-poc) |
| **Wayback** | Desktop X11 usando componentes Wayland | Laboratório gráfico; GitLab oficial | [Wayback](https://gitlab.freedesktop.org/wayback/wayback) |
| **Booster** | Gerador alternativo de initramfs | Guia manual; sem tocar no bootloader | [Booster](https://github.com/anatol/booster) |

## i3 sem perder seu desktop

```bash
# Apenas verificar o plano, não instala nada:
python3 DarfinOSInstallScript-TUI.py --plan --preset i3

# Alternativa: instalar somente o WM e utilitários a partir do Arch oficial:
bash DarfinOSInstallScript.sh --only i3
```

A etapa instala `i3-wm`, `i3status`, `i3lock`, `dmenu` e `xorg-xinit`,
sem modificar `~/.config/i3`, `~/.xinitrc` ou o gerenciador de login.
O preset `i3` inclui XLibre e seu repositório; **não inclui SonicDE**.
Só use a instalação do servidor gráfico a partir de um TTY e com plano de recuperação.

`xorg-xinit` fornece `startx`, mas iniciar i3 via TTY exige que você
configure a sessão em `~/.xinitrc`; não há mudança automática do login manager.

## Cuidados específicos

- **AUR:** a origem do PKGBUILD pode mudar. Revise fontes e scripts; instalar
  o pacote não significa validar sua execução.
- **Decman/Metapac:** não execute sincronização, hooks ou remoção declarativa
  sem comparar o estado atual e manter um snapshot. O DarfinOS só instala os executáveis.
- **JuNest/Conty/nix-portable:** avalie namespaces, FUSE, proot, permissões e
  acesso ao HOME. Um contêiner não é garantia automática de isolamento total.
- **Trinity:** o projeto utiliza repositório e chave de confiança próprios,
  que o Labs não configura silenciosamente.
- **yserver, xomposite e Wayback:** faça testes em VM ou sessão isolada.
  Não combine xomposite com o compositor já ativo do SonicDE.
- **Booster:** nunca mude gerador initramfs, parâmetros de boot ou bootloader
  sem snapshot verificável e um meio de iniciar o sistema para recuperar.

Mais informações: [guia de segurança](SEGURANCA.md),
[matriz de VM](VALIDACAO_VM.md) e [site Labs](https://darfinos.vercel.app/labs/).

## Preset Retro: Xfce + Chicago95

```bash
python3 DarfinOSInstallScript-TUI.py --plan --preset retro
bash DarfinOSInstallScript.sh --only xfce,lab_chicago95
```

O Xfce é instalado como sessão alternativa e não substitui SonicDE. O Chicago95
usa um `git clone` da [fonte original](https://github.com/grassmunk/Chicago95),
verifica as pastas `Theme/Chicago95` e `Icons/Chicago95` e as copia para o HOME.
Ele não executa `installer.py`, não modifica o painel e recusa sobrescrever
arquivos já existentes. O tema deve ser habilitado manualmente em Xfce.
Confira a [instalação original](https://github.com/grassmunk/Chicago95/blob/master/INSTALL.md)
e o [verificador de módulos](MODULOS.md).
