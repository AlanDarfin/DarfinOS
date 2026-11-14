#!/usr/bin/env bash
# ==========================================================
# DarfinOS — pós-instalação modular para Arch Linux
# ==========================================================
# Uso:
#   bash DarfinOSInstallScript.sh --list
#   bash DarfinOSInstallScript.sh --only base,cli_tools
#   bash DarfinOSInstallScript.sh --skip bedrock,cleanup
#   bash DarfinOSInstallScript.sh --only i3         # WM opcional
#   bash DarfinOSInstallScript.sh --labs            # catálogo sem sudo
#   bash DarfinOSInstallScript.sh --only base -y    # confirmações elegíveis
#
# Segurança: -y não desativa as confirmações do pacman e NÃO aprova substituições,
# confiança em chaves, remoções, ativação do firewall ou reinicialização. AUR e
# instalações Flatpak podem usar modo não interativo quando -y é informado.
#
# Dica: para instalar XLibre/SonicDE, rode de um TTY (Ctrl+Alt+F3),
# não de dentro de uma sessão gráfica.
# ==========================================================

set -euo pipefail

# ----------------------------------------------------------
# Etapas (na ordem de execução) e descrições
# ----------------------------------------------------------
STEPS=(
  # Sistema e repositórios
  pacman_conf mirrors repo_cachyos repo_xlibre repo_sonicde repo_chaotic sysupgrade
  # Base
  base aur_helper fonts hardware
  # Desktop (SonicDE + XLibre)
  xlibre sonicde desktop_extras bluetooth
  # Window managers independentes
  i3 xfce
  # Shell e desenvolvimento
  cli_tools dev_tools pkg_managers shells git_setup
  # Rede e serviços
  zerotier hamachi syncthing docker
  # Aplicativos
  flatpak apps gaming browser
  # Manutenção
  maintenance firewall cleanup bobagens bedrock terminal_extras
  # DarfinOS Labs (seleção individual; presets Retro e Workstation são explícitos)
  lab_nscde lab_junest lab_decman lab_metapac lab_chicago95
  lab_conty lab_nix_portable lab_trinity lab_yserver lab_xomposite lab_wayback lab_booster
  lab_windowmaker lab_notion lab_e16 lab_xpra lab_opengamepadui
  lab_wmutils lab_pkgsrc lab_pipeworld lab_chezmoi lab_matugen
  lab_autorandr lab_desktop_config lab_etckeeper lab_rustic lab_kvantum lab_i3_notebook
)

declare -A STEP_DESC=(
  [pacman_conf]="Ajustes do pacman.conf (Color, downloads paralelos, multilib)"
  [mirrors]="Mirrors do Brasil via reflector + timer semanal"
  [repo_cachyos]="Repositórios otimizados do CachyOS (opcional)"
  [repo_xlibre]="Repositório do XLibre (chave PGP + pacman.conf)"
  [repo_sonicde]="Repositório do SonicDE (chave PGP + pacman.conf)"
  [repo_chaotic]="Repositório Chaotic-AUR (binários pré-compilados do AUR)"
  [sysupgrade]="Atualização completa do sistema (pacman -Syu)"
  [base]="Pacotes base do sistema"
  [aur_helper]="AUR helper (paru/yay)"
  [fonts]="Fontes"
  [hardware]="Microcode, driver de vídeo e zram"
  [xlibre]="Servidor gráfico XLibre (substitui o X.Org)"
  [sonicde]="Ambiente SonicDE, login manager, rede e áudio"
  [desktop_extras]="Extras do desktop (portais, energia, KDE Connect...)"
  [bluetooth]="Bluetooth"
  [i3]="i3 WM: tiling X11, i3status, i3lock e dmenu (sem trocar sua sessão)"
  [xfce]="Xfce: desktop X11 alternativo, mantém SonicDE e login atuais"
  [cli_tools]="Ferramentas de terminal (fzf, eza, yazi, starship...)"
  [dev_tools]="Desenvolvimento (neovim, gcc, clang, rust, go, node...)"
  [pkg_managers]="pip, pipx, cargo, npm e go: instalação, PATH e config"
  [shells]="fish + Fisher + zsh, tema DarfinOS, starship/zoxide/fzf e shell padrão"
  [git_setup]="Configuração do git e chave SSH"
  [zerotier]="ZeroTier"
  [hamachi]="Hamachi"
  [syncthing]="Syncthing"
  [docker]="Contêineres (Docker ou Podman)"
  [flatpak]="Flatpak + Flathub + ferramentas"
  [apps]="Aplicativos (Flatpak/AUR, Discord, Shelter e Spicetify)"
  [gaming]="Steam, Wine, GameMode, MangoHud"
  [browser]="Navegador"
  [maintenance]="Topgrade, Arch-Update (bandeja) e timers de manutenção"
  [firewall]="Firewall (ufw)"
  [cleanup]="Limpeza de órfãos e caches"
  [bobagens]="Coisas extras ai"
  [bedrock]="Instalação do Bedrock Linux"
  [terminal_extras]="Extras do terminal (tmux, ranger, OpenCode e sudo)"
  [lab_nscde]="Labs · NsCDE (AUR, desktop estilo UNIX clássico)"
  [lab_junest]="Labs · JuNest (AUR, ambientes Arch em usuário)"
  [lab_decman]="Labs · Decman (AUR, configuração declarativa; sem aplicar)"
  [lab_metapac]="Labs · Metapac (AUR, pacotes declarativos; sem aplicar)"
  [lab_chicago95]="Labs · Chicago95: tema, ícones, cursores e fontes para Xfce"
  [lab_conty]="Labs · Conty: ambiente Linux portátil no HOME"
  [lab_nix_portable]="Labs · nix-portable: Nix em espaço de usuário"
  [lab_trinity]="Labs · Trinity Desktop: repositório assinado e ambiente completo"
  [lab_yserver]="Labs · yserver: servidor X11 alternativo com Vulkan (AUR)"
  [lab_xomposite]="Labs · Xomposite: compositor X11 compilado no HOME"
  [lab_wayback]="Labs · Wayback: camada experimental de X11 sobre Wayland (AUR)"
  [lab_booster]="Labs · Booster: gerador alternativo de initramfs"
  [lab_windowmaker]="Labs · Window Maker"
  [lab_notion]="Labs · Notion WM"
  [lab_e16]="Labs · Enlightenment E16"
  [lab_xpra]="Labs · Xpra"
  [lab_opengamepadui]="Labs · OpenGamepadUI"
  [lab_wmutils]="Labs · wmutils"
  [lab_pkgsrc]="Labs · pkgsrc"
  [lab_pipeworld]="Labs · Arcan + Pipeworld"
  [lab_chezmoi]="Labs · chezmoi"
  [lab_matugen]="Labs · Matugen"
  [lab_autorandr]="Labs · autorandr"
  [lab_desktop_config]="Labs · Xfconf + KConfig"
  [lab_etckeeper]="Labs · etckeeper"
  [lab_rustic]="Labs · rustic"
  [lab_kvantum]="Labs · Kvantum"
  [lab_i3_notebook]="Labs · i3 Notebook: Polybar, controles rápidos e Fastfetch"
)

# Explicações para a TUI: informações gerais, sem prometer instalações condicionais.
declare -A STEP_INFO=(
  [pacman_conf]="Configura o pacman e o multilib, preservando backup do arquivo anterior."
  [mirrors]="Revisa os servidores de download usados pelo pacman e a renovação periódica."
  [repo_cachyos]="Configura os repositórios opcionais de otimização do CachyOS."
  [repo_xlibre]="Registra a chave e o repositório necessário ao servidor gráfico XLibre."
  [repo_sonicde]="Registra a chave e o repositório do ambiente SonicDE."
  [repo_chaotic]="Disponibiliza pacotes binários da comunidade pelo Chaotic-AUR."
  [sysupgrade]="Sincroniza e atualiza todos os pacotes do sistema com pacman -Syu."
  [base]="Instala utilitários essenciais para administrar e recuperar o Arch."
  [aur_helper]="Configura yay ou paru para instalar pacotes do AUR."
  [fonts]="Instala famílias de fontes para aplicações e a interface."
  [hardware]="Configura microcode, drivers e recursos de memória conforme o hardware."
  [xlibre]="Substitui componentes X.Org pelo servidor XLibre, quando selecionado."
  [sonicde]="Instala e configura o ambiente gráfico SonicDE e serviços associados."
  [desktop_extras]="Acrescenta integração, portais e utilitários do desktop."
  [bluetooth]="Instala os componentes Bluetooth e prepara o serviço."
  [i3]="Instala a sessão i3 como alternativa X11. Não substitui SonicDE nem altera gerenciador de login ou configuração pessoal."
  [xfce]="Instala pacotes Xfce oficiais como sessão alternativa. Não modifica tema, painel nem gerenciador de login."
  [cli_tools]="Adiciona utilitários de produtividade, navegação e busca no terminal."
  [dev_tools]="Instala compiladores, linguagens e ferramentas de programação."
  [pkg_managers]="Prepara gerenciadores de pacotes de linguagens e seus caminhos."
  [shells]="Instala shells e personaliza o terminal com tema e plugins do DarfinOS."
  [git_setup]="Auxilia na configuração de identidade Git e de autenticação SSH."
  [zerotier]="Instala o cliente de redes virtuais ZeroTier e configura o serviço."
  [hamachi]="Instala clientes de rede Hamachi e interfaces disponíveis."
  [syncthing]="Instala e prepara a sincronização de arquivos entre dispositivos."
  [docker]="Instala e configura opções de contêineres após confirmação."
  [flatpak]="Prepara o Flatpak, o Flathub e integração de apps."
  [apps]="Instala aplicativos selecionados; clientes e mods podem depender de escolhas."
  [gaming]="Instala ferramentas de jogos, compatibilidade e monitoramento de desempenho."
  [browser]="Oferece a instalação de navegador e a revisão de opções existentes."
  [maintenance]="Instala Topgrade e Arch-Update com tray; habilita notificações e timers quando possível."
  [firewall]="Configura regras de rede e firewall somente após consentimento."
  [cleanup]="Revisa pacotes órfãos e cache; remoções exigem confirmação."
  [bobagens]="Ferramentas e personalizações experimentais/opcionais com perguntas próprias."
  [bedrock]="Executa processo avançado e opcional do Bedrock Linux com avisos."
  [terminal_extras]="Adiciona ferramentas e personalizações avançadas do terminal."
  [lab_nscde]="Requer confirmação LABS para instalar pacote nscde do AUR. Sessão gráfica separada; revise o PKGBUILD."
  [lab_junest]="Instala junest-git do AUR e prepara o ambiente Arch com junest setup no HOME. Não altera namespaces do host."
  [lab_decman]="Requer confirmação LABS para instalar decman do AUR. NÃO executa configurações Python ou sincroniza pacotes."
  [lab_metapac]="Requer confirmação LABS para instalar metapac do AUR. NÃO executa sync nem clean."
  [lab_chicago95]="Instala Xfce, tema GTK/XFWM, ícones, cursor e fontes VGA. Preserva o painel, a sessão e o tema ativo."
  [lab_conty]="Instala conty_lite.sh (x86_64) com SHA-256 fixo e FUSE, sem executar o contêiner."
  [lab_nix_portable]="Instala o binário x86_64 com SHA-256 fixo, sem daemon ou alterações em /nix."
  [lab_trinity]="Confere a chave completa, configura o repositório Trinity e instala tde-meta com pacman -Syu. Mantém o gerenciador de login."
  [lab_yserver]="Instala yserver pelo AUR e oferece driver Vulkan Intel/AMD. Não troca X.Org/XLibre, login ou permissões de dispositivos."
  [lab_xomposite]="Instala dependências Arch e compila um commit fixo com Cargo. Não inicia o compositor nem edita o i3."
  [lab_wayback]="Instala wayback-x11 pelo AUR, sem substituir o X padrão ou editar o login."
  [lab_booster]="Instala Booster em paralelo. O hook do pacote gera imagens alternativas, sem trocar o initramfs padrão ou configurar o bootloader."
  [lab_windowmaker]="Sessão X11 inspirada no NeXTSTEP; não troca o login."
  [lab_notion]="WM X11 com mosaico estático e abas; pacote notion-git."
  [lab_e16]="Window manager X11 retrô; sessão alternativa."
  [lab_xpra]="Encaminha janelas X11; não inicia serviços nem abre portas."
  [lab_opengamepadui]="Launcher e overlay para controle pelo AUR; não troca a sessão ativa."
  [lab_wmutils]="Utilitários para mover e organizar janelas X11 por script."
  [lab_pkgsrc]="Bootstrap sem sudo no HOME com prefixo separado e sem alterar PATH."
  [lab_pipeworld]="Instala Arcan pelo AUR e prepara um lançador Pipeworld no HOME; uso experimental."
  [lab_chezmoi]="Motor dos perfis de personalização com prévia e aplicação seletiva."
  [lab_matugen]="Extrai paletas de wallpapers para a Oficina de Temas."
  [lab_autorandr]="Perfis de monitores X11; aplica somente modos disponíveis."
  [lab_desktop_config]="Ajustes pontuais de tema no Xfce e estilo Qt no SonicDE."
  [lab_etckeeper]="Histórico local de /etc; inicialização separada, sem envio remoto."
  [lab_rustic]="Backups criptografados em destino escolhido; sem repositório automático."
  [lab_kvantum]="Temas Qt SVG para SonicDE com opção de suporte Qt5."
  [lab_i3_notebook]="Instala i3 e ferramentas do perfil Notebook sem alterar a sessão ou os arquivos pessoais."
)

# ----------------------------------------------------------
# DarfinOS Labs · catálogo estático auditável, sem execução automática.
# Cada projeto tem uma etapa; full não seleciona lab_*.
# ----------------------------------------------------------
LABS=(
  i3 chicago95 nscde junest decman metapac conty nix_portable trinity
  yserver xomposite wayback booster
  windowmaker notion e16 xpra opengamepadui wmutils
  pkgsrc pipeworld chezmoi matugen autorandr desktop_config
  etckeeper rustic kvantum i3_notebook
)
declare -A LABS_URL=(
  [i3]="https://i3wm.org/"
  [chicago95]="https://github.com/grassmunk/Chicago95"
  [nscde]="https://github.com/NsCDE/NsCDE"
  [junest]="https://github.com/fsquillace/junest"
  [decman]="https://github.com/kiviktnm/decman"
  [metapac]="https://github.com/ripytide/metapac"
  [conty]="https://github.com/Kron4ek/Conty"
  [nix_portable]="https://github.com/DavHau/nix-portable"
  [trinity]="https://www.trinitydesktop.org/"
  [yserver]="https://github.com/joske/yserver"
  [xomposite]="https://github.com/demostenex/xomposite"
  [wayback]="https://gitlab.freedesktop.org/wayback/wayback"
  [booster]="https://github.com/anatol/booster"
  [windowmaker]="https://www.windowmaker.org/"
  [notion]="https://notionwm.net/"
  [e16]="https://www.enlightenment.org/e16"
  [xpra]="https://xpra-org.github.io/xpra/"
  [opengamepadui]="https://github.com/ShadowBlip/OpenGamepadUI"
  [wmutils]="https://github.com/wmutils/core"
  [pkgsrc]="https://www.netbsd.org/docs/pkgsrc/pkgsrc.html"
  [pipeworld]="https://github.com/letoram/pipeworld"
  [chezmoi]="https://www.chezmoi.io/"
  [matugen]="https://github.com/InioX/matugen"
  [autorandr]="https://github.com/phillipberndt/autorandr"
  [desktop_config]="https://docs.xfce.org/xfce/xfconf/xfconf-query"
  [etckeeper]="https://etckeeper.branchable.com/"
  [rustic]="https://rustic.cli.rs/"
  [kvantum]="https://github.com/tsujan/Kvantum"
  [i3_notebook]="https://dunst-project.org/"
)
declare -A LABS_INFO=(
  [i3]="WM tiling para X11: janela alternativa, sem remover SonicDE."
  [chicago95]="Tema GTK/XFWM, ícones, cursor e fontes Windows 95 para Xfce; aplicação opcional."
  [nscde]="Desktop retro UNIX com FVWM; pacote AUR e login alternativo."
  [junest]="Instala junest-git e inicializa um ambiente Arch no HOME, sem alterar o host."
  [decman]="Estado declarativo em Python; aplicar perfis pode remover pacotes."
  [metapac]="Gerenciador declarativo; sync/clean podem alterar ou remover pacotes."
  [conty]="Baixa Conty Lite oficial com SHA-256 e instala FUSE; não abre o contêiner."
  [nix_portable]="Instala o binário Nix portátil no HOME; cache inicializado no primeiro uso."
  [trinity]="Instala tde-meta com repositório e chave Trinity; sessão X11 paralela."
  [yserver]="Instala o servidor X11 Rust e seu lançador starty; teste em um TTY separado."
  [xomposite]="Compila compositor X11 para sessão separada; não roda junto do KWin."
  [wayback]="Instala Wayback pelo AUR sem alterar o servidor gráfico padrão."
  [booster]="Instala Booster e suas imagens alternativas, sem trocar a entrada de boot."
  [windowmaker]="Sessão X11 inspirada no NeXTSTEP; não troca o login."
  [notion]="WM X11 com mosaico estático e abas; pacote notion-git."
  [e16]="Window manager X11 retrô; sessão alternativa."
  [xpra]="Encaminha janelas X11; não inicia serviços nem abre portas."
  [opengamepadui]="Launcher e overlay para controle pelo AUR; não troca a sessão ativa."
  [wmutils]="Utilitários para mover e organizar janelas X11 por script."
  [pkgsrc]="Bootstrap sem sudo no HOME com prefixo separado e sem alterar PATH."
  [pipeworld]="Instala Arcan pelo AUR e prepara um lançador Pipeworld no HOME; uso experimental."
  [chezmoi]="Motor dos perfis de personalização com prévia e aplicação seletiva."
  [matugen]="Extrai paletas de wallpapers para a Oficina de Temas."
  [autorandr]="Perfis de monitores X11; aplica somente modos disponíveis."
  [desktop_config]="Ajustes pontuais de tema no Xfce e estilo Qt no SonicDE."
  [etckeeper]="Histórico local de /etc; inicialização separada, sem envio remoto."
  [rustic]="Backups criptografados em destino escolhido; sem repositório automático."
  [kvantum]="Temas Qt SVG para SonicDE com opção de suporte Qt5."
  [i3_notebook]="Pacotes Arch para i3 com Polybar, áudio, rede, Bluetooth, calendário e Fastfetch. Ativação separada na Oficina."
)
declare -A LABS_RISK=(
  [i3]="opcional"
  [chicago95]="avancado"
  [nscde]="avancado"
  [junest]="avancado"
  [decman]="avancado"
  [metapac]="avancado"
  [conty]="avancado"
  [nix_portable]="avancado"
  [trinity]="critico"
  [yserver]="critico"
  [xomposite]="critico"
  [wayback]="critico"
  [booster]="critico"
  [windowmaker]="opcional"
  [notion]="avancado"
  [e16]="opcional"
  [xpra]="opcional"
  [opengamepadui]="avancado"
  [wmutils]="avancado"
  [pkgsrc]="avancado"
  [pipeworld]="critico"
  [chezmoi]="opcional"
  [matugen]="opcional"
  [autorandr]="opcional"
  [desktop_config]="opcional"
  [etckeeper]="avancado"
  [rustic]="opcional"
  [kvantum]="opcional"
  [i3_notebook]="opcional"
)
declare -A LABS_MODE=(
  [i3]="pacman"
  [chicago95]="assets"
  [nscde]="aur"
  [junest]="aur"
  [decman]="aur"
  [metapac]="aur"
  [conty]="binario"
  [nix_portable]="binario"
  [trinity]="repositorio"
  [yserver]="aur"
  [xomposite]="compilacao"
  [wayback]="aur"
  [booster]="pacman"
  [windowmaker]="pacman"
  [notion]="aur"
  [e16]="pacman"
  [xpra]="pacman"
  [opengamepadui]="aur"
  [wmutils]="aur"
  [pkgsrc]="compilacao"
  [pipeworld]="aur + fonte"
  [chezmoi]="pacman"
  [matugen]="pacman"
  [autorandr]="pacman"
  [desktop_config]="pacman"
  [etckeeper]="pacman"
  [rustic]="pacman"
  [kvantum]="pacman"
  [i3_notebook]="pacman"
)
declare -A LABS_STEP=(
  [i3]="i3"
  [chicago95]="lab_chicago95"
  [nscde]="lab_nscde"
  [junest]="lab_junest"
  [decman]="lab_decman"
  [metapac]="lab_metapac"
  [conty]="lab_conty"
  [nix_portable]="lab_nix_portable"
  [trinity]="lab_trinity"
  [yserver]="lab_yserver"
  [xomposite]="lab_xomposite"
  [wayback]="lab_wayback"
  [booster]="lab_booster"
  [windowmaker]="lab_windowmaker"
  [notion]="lab_notion"
  [e16]="lab_e16"
  [xpra]="lab_xpra"
  [opengamepadui]="lab_opengamepadui"
  [wmutils]="lab_wmutils"
  [pkgsrc]="lab_pkgsrc"
  [pipeworld]="lab_pipeworld"
  [chezmoi]="lab_chezmoi"
  [matugen]="lab_matugen"
  [autorandr]="lab_autorandr"
  [desktop_config]="lab_desktop_config"
  [etckeeper]="lab_etckeeper"
  [rustic]="lab_rustic"
  [kvantum]="lab_kvantum"
  [i3_notebook]="lab_i3_notebook"
)

# ----------------------------------------------------------
# Constantes dos repositórios de terceiros
# ----------------------------------------------------------
readonly XLIBRE_KEY_ID="B97F7C613F359424"
readonly XLIBRE_SITE="https://xlibre-arch.github.io"
readonly XLIBRE_KEY_URL="$XLIBRE_SITE/xlibre-archlinux.asc"

readonly SONIC_KEY_ID="3B87898C73F11DF5"
readonly SONIC_SITE="https://sonicde-arch.github.io"
readonly SONIC_KEY_URL="$SONIC_SITE/sonicde-archlinux.asc"
readonly SONIC_HOME="https://sonicde.org"

readonly CHAOTIC_KEY_ID="3056513887B78AEB"
readonly CHAOTIC_KEYSERVER="keyserver.ubuntu.com"
readonly CHAOTIC_PKG_URL="https://cdn-mirror.chaotic.cx/chaotic-aur"

readonly TRINITY_FINGERPRINT="D6D6FAA25E9A3E4ECD9FBDBEC93AF1698685AD8B"
readonly TRINITY_SERVER='https://mirror.ppa.trinitydesktop.org/trinity/archlinux/$arch'
readonly BIBATA_VERSION="v2.0.7"
readonly BIBATA_SHA256="a68cae60c4dc706350e194ebc91c5fe48bc7bc9d59e119555834a2a7ee5078ef"
readonly CHICAGO95_REV="5da19b8b1e2a886ebf6628403023d5fac3acc3ee"
readonly XOMPOSITE_REV="44e2dc8e1f843509871b956d9ad4ae4ffc0cfcc2"
readonly CONTY_SHA256="9bb53bdf1bf72b9358a34e5bfe19bebf81fe27ef3ac5f3cd0b15152a59e1be34"
readonly NIX_PORTABLE_SHA256="b409c55904c909ac3aeda3fb1253319f86a89ddd1ba31a5dec33d4a06414c72a"

readonly KNOWN_LMS="emptty gdm greetd lemurs lightdm lxdm ly plasmalogin sddm slim soniclogin xdm"

# ----------------------------------------------------------
# Visual
# ----------------------------------------------------------
if [[ -t 1 ]]; then
  C_BLUE=$'\e[1;34m'; C_GREEN=$'\e[1;32m'; C_YELLOW=$'\e[1;33m'
  C_RED=$'\e[1;31m';  C_OFF=$'\e[0m'
else
  C_BLUE=""; C_GREEN=""; C_YELLOW=""; C_RED=""; C_OFF=""
fi

info() { echo "${C_BLUE}==>${C_OFF} $*"; }
ok()   { echo "${C_GREEN} ✔${C_OFF} $*"; }
warn() { echo "${C_YELLOW} ⚠${C_OFF} $*"; }
die()  { echo "${C_RED} ✘ $*${C_OFF}" >&2; exit 1; }

usage() {
  cat <<'HELP'
DarfinOS · instalador modular de pós-instalação para Arch Linux
Uso: bash DarfinOSInstallScript.sh [opções]
  --list                 Lista etapas disponíveis (somente leitura).
  --labs                 Catálogo dos projetos Labs, sem sudo.
  --lab-info NOME        Detalhes e URL original de um projeto Labs.
  --preflight            Verifica requisitos básicos sem sudo nem alterações.
  --check-modules        Inspeciona módulos e mostra TSV, sem sudo.
  --reinstall            Força repetir módulos já detectados como instalados.
  --only a,b,c           Executa apenas as etapas informadas.
  --skip a,b,c           Executa etapas convencionais, exceto as listadas; exclui etapas lab_*.
  --all                  Executa as etapas convencionais, inclusive Bedrock; exclui etapas lab_*.
  -y, --yes              Usa valores padrão apenas em perguntas elegíveis.
  -h, --help             Exibe esta ajuda.
É obrigatório escolher --only, --skip ou --all antes de instalar.
Uma chamada sem seleção mostra esta ajuda e não altera o sistema.
Para uma seleção inicial segura, use: python3 DarfinOSInstallScript-TUI.py --local
Para validar sem alterar o sistema: python3 DarfinOSInstallScript-TUI.py --doctor
HELP
}

# ----------------------------------------------------------
# Opções
# ----------------------------------------------------------
ASSUME_YES=0
FORCE_MODULES=0
EXPLICIT_ALL=0
ONLY=""
SKIP=""
LOG_FILE=""

# A lista contém dependências que, se falharem nesta execução, impedem a
# execução das etapas dependentes. Pré-requisitos já satisfeitos no sistema
# continuam sendo validados dentro da própria etapa.
declare -A STEP_DEPS=(
  [sysupgrade]="repo_xlibre repo_sonicde"
  [xlibre]="repo_xlibre sysupgrade"
  [sonicde]="repo_sonicde sysupgrade"
  [desktop_extras]="sonicde"
  [gaming]="hardware"
  [apps]="flatpak"
  [maintenance]="aur_helper"
  [lab_nscde]="aur_helper"
  [lab_junest]="aur_helper"
  [lab_decman]="aur_helper"
  [lab_metapac]="aur_helper"
  [lab_yserver]="aur_helper"
  [lab_wayback]="aur_helper"
  [lab_chicago95]="xfce"
  [lab_notion]="aur_helper"
  [lab_opengamepadui]="aur_helper"
  [lab_wmutils]="aur_helper"
  [lab_pipeworld]="aur_helper"
)


# ------------------------------------------------------------------
# Conservador: somente "installed" permite pular toda a etapa. Estados
# "partial", "missing" ou "unknown" NUNCA significam conclusão.
# Sem sudo, escrita, downloads ou execução de ferramentas externas ao Arch.
# ------------------------------------------------------------------
declare -A MODULE_PACKAGES=()
MODULE_PACMAN_AVAILABLE=0
MODULE_STATUS=unknown
MODULE_REASON="Configuração condicional não certificada pelo inventário."

modules_refresh() {
  local pkg catalog
  MODULE_PACKAGES=()
  MODULE_PACMAN_AVAILABLE=0
  command -v pacman >/dev/null 2>&1 || return 0
  catalog=$(pacman -Qq 2>/dev/null) || return 0
  MODULE_PACMAN_AVAILABLE=1
  while IFS= read -r pkg; do
    [[ "$pkg" =~ ^[a-zA-Z0-9@_.+:-]+$ ]] || continue
    MODULE_PACKAGES["$pkg"]=1
  done <<< "$catalog"
}
module_packages_ready() {
  (( MODULE_PACMAN_AVAILABLE )) || return 2
  local pkg
  for pkg in "$@"; do
    [[ -n "${MODULE_PACKAGES[$pkg]:-}" ]] || return 1
  done
}
module_any_package() {
  (( MODULE_PACMAN_AVAILABLE )) || return 1
  local pkg
  for pkg in "$@"; do
    [[ -n "${MODULE_PACKAGES[$pkg]:-}" ]] && return 0
  done
  return 1
}
notebook_cursor_ready() {
  local theme="${1:-${XDG_DATA_HOME:-$HOME/.local/share}/icons/Bibata-Modern-Ice}"
  [[ -f "$theme/index.theme" && -f "$theme/cursors/left_ptr" ]]
}

junest_environment_ready() {
  local root="${JUNEST_HOME:-$HOME/.junest}"
  [[ -x "$root/usr/bin/pacman" && -r "$root/etc/junest/info" ]]
}

chicago95_ready() {
  module_packages_ready xfce4-session &&
    [[ -f "$HOME/.themes/Chicago95/index.theme" &&
       -f "$HOME/.themes/Chicago95/gtk-3.0/gtk.css" &&
       -f "$HOME/.themes/Chicago95/xfwm4/themerc" &&
       -f "$HOME/.icons/Chicago95/index.theme" &&
       -d "$HOME/.icons/Chicago95_Standard_Cursors/cursors" &&
       -f "$HOME/.local/share/fonts/Chicago95/LessPerfectDOSVGA.ttf" &&
       -f "$HOME/.local/share/fonts/Chicago95/MorePerfectDOSVGA.ttf" ]]
}

trinity_configured() {
  # pacman-conf segue Includes e aplica a mesma sintaxe e precedência do pacman.
  pacman-conf --repo-list 2>/dev/null | grep -Fx trinity >/dev/null
}

trinity_repo_valid() {
  local servers levels
  servers=$(pacman-conf --repo trinity Server 2>/dev/null) || return 1
  levels=$(pacman-conf --repo trinity SigLevel 2>/dev/null) || return 1
  [[ "$servers" == "$TRINITY_SERVER" || "$servers" == "${TRINITY_SERVER%/\$arch}/$(uname -m)" ]] || return 1
  # Exige assinatura de pacote confiável, inclusive em configurações existentes.
  [[ "$levels" =~ (^|[[:space:]])(PackageRequired|Required)($|[[:space:]]) &&
     ! "$levels" =~ (^|[[:space:]])(PackageNever|Never|PackageOptional|Optional|PackageTrustAll|TrustAll)($|[[:space:]]) ]]
}

trinity_session_ready() {
  [[ -x /opt/trinity/bin/starttde && -r /usr/share/xsessions/trinity.desktop ]]
}

yserver_vulkan_ready() {
  pacman -T vulkan-driver >/dev/null 2>&1
}

yserver_ready() {
  command -v yserver >/dev/null && command -v starty >/dev/null && yserver_vulkan_ready
}

module_probe() {
  local name="$1"
  local -a required=()
  MODULE_STATUS=unknown
  MODULE_REASON="Etapa configura serviços, repositórios ou escolhas; checagem manual necessária."
  case "$name" in
    base) required=(base-devel git curl wget unzip p7zip rsync htop fastfetch man-db man-pages rclone fuse2 pacman-contrib bash-completion pciutils usbutils) ;;
    i3) required=(i3-wm i3status i3lock dmenu xorg-xinit) ;;
    xfce) required=(exo garcon thunar thunar-volman tumbler xfce4-appfinder xfce4-panel xfce4-power-manager xfce4-session xfce4-settings xfce4-terminal xfconf xfdesktop xfwm4 xorg-xinit) ;;
    lab_nscde)
      if module_any_package nscde-git; then required=(nscde-git); else required=(nscde); fi ;;
    lab_junest)
      if (( MODULE_PACMAN_AVAILABLE )); then
        if module_any_package junest junest-git; then
          if junest_environment_ready; then
            MODULE_STATUS=installed
            MODULE_REASON="JuNest e ambiente Arch encontrados."
          else
            MODULE_STATUS=partial
            MODULE_REASON="Pacote JuNest instalado; ambiente ainda não encontrado."
          fi
        else
          MODULE_STATUS=missing
          MODULE_REASON="Pacote JuNest não encontrado."
        fi
      fi
      return 0 ;;
    lab_trinity)
      if (( MODULE_PACMAN_AVAILABLE )); then
        if module_any_package tde-meta tde-tdebase || trinity_configured; then
          if module_packages_ready tde-meta tde-tdebase && trinity_session_ready && trinity_repo_valid; then
            MODULE_STATUS=installed
            MODULE_REASON="Trinity completo, sessão X11 e repositório com assinaturas de pacote encontrados."
          else
            MODULE_STATUS=partial
            MODULE_REASON="Faltam pacotes, sessão ou repositório válido do Trinity."
          fi
        else
          MODULE_STATUS=missing
          MODULE_REASON="Trinity não encontrado."
        fi
      fi
      return 0 ;;
    lab_conty|lab_nix_portable|lab_xomposite)
      local executable
      case "$name" in
        lab_conty) executable="$HOME/.local/bin/conty" ;;
        lab_nix_portable) executable="$HOME/.local/bin/nix-portable" ;;
        lab_xomposite) executable="$HOME/.local/bin/xomposite" ;;
      esac
      if [[ -f "$executable" && -x "$executable" ]] &&
         { [[ "$name" != lab_conty ]] || module_packages_ready fuse3; }; then
        MODULE_STATUS=installed
        MODULE_REASON="Executável local e dependências declaradas encontrados."
      elif [[ -e "$executable" || -L "$executable" ]]; then
        MODULE_STATUS=partial
        MODULE_REASON="Executável local incompleto ou dependência ausente."
      else
        MODULE_STATUS=missing
        MODULE_REASON="Executável não encontrado em ~/.local/bin."
      fi
      return 0 ;;
    lab_yserver)
      if (( MODULE_PACMAN_AVAILABLE )); then
        if ! module_any_package yserver yserver-git; then
          MODULE_STATUS=missing
          MODULE_REASON="Pacote yserver não encontrado."
        elif yserver_ready; then
          MODULE_STATUS=installed
          MODULE_REASON="yserver, starty e um provedor Vulkan encontrados."
        else
          MODULE_STATUS=partial
          MODULE_REASON="yserver instalado; falta o lançador ou um provedor Vulkan."
        fi
      fi
      return 0 ;;
    lab_wayback)
      if module_any_package wayback-x11-git; then required=(wayback-x11-git); else required=(wayback-x11); fi ;;
    lab_booster) required=(booster) ;;
    lab_windowmaker) required=(windowmaker xorg-xinit) ;;
    lab_notion) required=(notion-git xorg-xinit) ;;
    lab_e16) required=(e16 xorg-xinit) ;;
    lab_xpra) required=(xpra) ;;
    lab_opengamepadui) required=(opengamepadui-bin) ;;
    lab_wmutils) required=(wmutils-git) ;;
    lab_chezmoi) required=(chezmoi) ;;
    lab_matugen) required=(matugen) ;;
    lab_autorandr) required=(autorandr) ;;
    lab_desktop_config) required=(xfconf kconfig) ;;
    lab_etckeeper) required=(etckeeper git) ;;
    lab_rustic) required=(rustic) ;;
    lab_kvantum) required=(kvantum) ;;
    lab_i3_notebook) required=(i3-wm i3status i3lock dmenu xorg-xinit chezmoi rofi dunst i3status-rust brightnessctl xss-lock flameshot xterm ttf-dejavu libpulse libnotify feh zenity xorg-xrandr xorg-xrdb xorg-xsetroot xsettingsd polybar xdotool ttf-jetbrains-mono-nerd powerline-fonts librsvg xdg-utils gtk3 python-gobject pavucontrol network-manager-applet bluez-utils blueman polkit-gnome fastfetch chafa python-xlib playerctl arandr lxappearance curl tar xz) ;;
    lab_pkgsrc)
      if [[ -x "$HOME/.local/share/darfinos/pkgsrc-prefix/bin/bmake" && -x "$HOME/.local/share/darfinos/pkgsrc-prefix/sbin/pkg_info" && -d "$HOME/.local/share/darfinos/pkgsrc-tree/pkgtools" ]]; then
        MODULE_STATUS=installed; MODULE_REASON="Bootstrap pkgsrc e árvore de pacotes encontrados."
      elif [[ -e "$HOME/.local/share/darfinos/pkgsrc-prefix" || -e "$HOME/.local/share/darfinos/pkgsrc-tree" ]]; then
        MODULE_STATUS=partial; MODULE_REASON="Bootstrap ou árvore do pkgsrc incompletos."
      else
        MODULE_STATUS=missing; MODULE_REASON="Bootstrap local pkgsrc não encontrado."
      fi
      return 0 ;;
    lab_pipeworld)
      if module_packages_ready arcan && [[ -x "$HOME/.local/bin/darfinos-pipeworld" && -f "$HOME/.local/share/darfinos/pipeworld/pipeworld/pipeworld.lua" ]]; then
        MODULE_STATUS=installed; MODULE_REASON="Arcan, aplicativo Pipeworld e lançador encontrados; sessão não testada."
      elif module_any_package arcan || [[ -e "$HOME/.local/share/darfinos/pipeworld" || -e "$HOME/.local/bin/darfinos-pipeworld" ]]; then
        MODULE_STATUS=partial; MODULE_REASON="Falta o Arcan, o aplicativo ou o lançador."
      else
        MODULE_STATUS=missing; MODULE_REASON="Pipeworld não encontrado."
      fi
      return 0 ;;
    lab_decman) required=(decman) ;;
    lab_metapac)
      if module_any_package metapac-bin; then required=(metapac-bin); else required=(metapac); fi ;;
    lab_chicago95)
      if chicago95_ready; then
        MODULE_STATUS=installed
        MODULE_REASON="Xfce, tema, ícones, cursor e fontes Chicago95 encontrados; aplicação do tema é opcional."
      elif [[ -e "$HOME/.themes/Chicago95" || -L "$HOME/.themes/Chicago95" ||
              -e "$HOME/.icons/Chicago95" || -L "$HOME/.icons/Chicago95" ]]; then
        MODULE_STATUS=partial
        MODULE_REASON="Chicago95 parcial; os arquivos existentes serão preservados."
      else
        MODULE_STATUS=missing
        MODULE_REASON="Tema e ícones Chicago95 não encontrados no HOME."
      fi
      return 0 ;;
    aur_helper)
      if command -v paru >/dev/null 2>&1 || command -v yay >/dev/null 2>&1; then
        MODULE_STATUS=installed
        MODULE_REASON="yay/paru disponível no PATH."
      else
        MODULE_STATUS=missing
        MODULE_REASON="Nenhum AUR helper encontrado."
      fi
      return 0 ;;
    xlibre)
      if module_any_package xlibre-server xlibre-xserver xlibre; then
        MODULE_STATUS=partial
        MODULE_REASON="Componente XLibre detectado, mas sessão e repositório não verificados."
      fi
      return 0 ;;
    sonicde)
      if module_any_package sonicde-meta; then
        MODULE_STATUS=partial
        MODULE_REASON="Pacote SonicDE presente, mas serviços, login e áudio não verificados."
      fi
      return 0 ;;
    maintenance)
      if module_any_package topgrade-bin topgrade arch-update-bin arch-update; then
        MODULE_STATUS=partial
        MODULE_REASON="Atualizadores detectados; timers, applet e serviços não certificados."
      fi
      return 0 ;;
    docker)
      if module_any_package docker podman; then
        MODULE_STATUS=partial
        MODULE_REASON="Contêineres detectados; serviços e configuração não certificados."
      fi
      return 0 ;;
    syncthing|zerotier|bluetooth|gaming)
      local candidate="$name"
      [[ "$name" == bluetooth ]] && candidate=bluez
      [[ "$name" == gaming ]] && candidate=gamemode
      if module_any_package "$candidate"; then
        MODULE_STATUS=partial
        MODULE_REASON="Pacote detectado; configurações e outras ações não verificadas."
      fi
      return 0 ;;
    *) return 0 ;;
  esac
  if (( ! MODULE_PACMAN_AVAILABLE )); then
    MODULE_STATUS=unknown
    MODULE_REASON="pacman -Qq indisponível; não pular por precaução."
  elif module_packages_ready "${required[@]}"; then
    if [[ "$name" == lab_i3_notebook ]] && ! notebook_cursor_ready; then
      MODULE_STATUS=partial
      MODULE_REASON="Pacotes Notebook instalados; cursor Bibata Modern Ice ainda não encontrado."
    else
      MODULE_STATUS=installed
      MODULE_REASON="Todos os ${#required[@]} pacotes esperados já instalados."
    fi
  elif module_any_package "${required[@]}"; then
    MODULE_STATUS=partial
    MODULE_REASON="Alguns pacotes presentes; etapa ainda não está completa."
  else
    MODULE_STATUS=missing
    MODULE_REASON="Pacotes principais não detectados."
  fi
}
list_module_status() {
  local step
  modules_refresh
  printf 'module\tstatus\treason\n'
  for step in "${STEPS[@]}"; do
    module_probe "$step"
    printf '%s\t%s\t%s\n' "$step" "$MODULE_STATUS" "$MODULE_REASON"
  done
}

preflight() {
  local errors=0 tool
  echo "DarfinOS · Pré-verificação (somente leitura)"
  if [[ -f /etc/arch-release ]]; then
    echo "OK: Arch Linux / derivado detectado"
  else
    echo "ERRO: /etc/arch-release não encontrado"
    errors=1
  fi
  for tool in pacman sudo curl; do
    if command -v "$tool" >/dev/null 2>&1; then
      echo "OK: $tool disponível"
    else
      echo "ERRO: $tool ausente"
      errors=1
    fi
  done
  if [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
    echo "AVISO: ambiente gráfico detectado; use TTY para trocar SonicDE/XLibre"
  fi
  if [[ "$EUID" -eq 0 ]]; then
    echo "AVISO: o instalador deve ser executado como usuário comum (não root)"
  fi
  if (( errors )); then
    echo "Pré-verificação encontrou requisitos ausentes."
    return 1
  fi
  echo "Pré-verificação básica OK. Não valida rede, hardware nem mudanças de pacotes."
}

list_steps() {
  local s
  for s in "${STEPS[@]}"; do
    printf '  %-16s %s\n' "$s" "${STEP_DESC[$s]:-}"
  done
}

list_labs() {
  local name
  printf 'DarfinOS Labs · catalogo de projetos independentes\n'
  for name in "${LABS[@]}"; do
    printf '%-15s %-14s %-12s %s\n' "$name" "${LABS_RISK[$name]}" "${LABS_MODE[$name]}" "${LABS_URL[$name]}"
    printf '  %s\n' "${LABS_INFO[$name]}"
  done
  printf 'Selecione uma etapa com --only; nenhum lab_* entra em --all ou --skip.\n'
}
lab_info() {
  local name="${1:-}"
  if [[ ! "$name" =~ ^[a-z0-9_]+$ || -z "${LABS_URL[$name]:-}" ]]; then
    die "Projeto Labs desconhecido: $name (veja --labs)"
  fi
  printf 'Projeto: %s\nOrigem: %s\nNivel: %s\nModo: %s\nEtapa: %s\n\n%s\n' \
    "$name" "${LABS_URL[$name]}" "${LABS_RISK[$name]}" "${LABS_MODE[$name]}" \
    "${LABS_STEP[$name]:-manual}" "${LABS_INFO[$name]}"
  echo 'Consulte o link original para opções de uso e ativação depois da instalação.'
}

validate_steps() {
  local item
  local -a items
  [[ -n "$1" && "$1" != ,* && "$1" != *, && "$1" != *,,* ]] || die "Seleção inválida: informe nomes separados por vírgula, sem itens vazios."
  IFS=',' read -ra items <<<"$1"
  (( ${#items[@]} )) || die "A seleção precisa conter pelo menos uma etapa."
  for item in "${items[@]}"; do
    [[ -n "$item" ]] || die "Seleção contém etapa vazia."
    [[ " ${STEPS[*]} " == *" $item "* ]] || die "Etapa desconhecida: '$item' (veja --list)"
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes)  ASSUME_YES=1 ;;
    --only)    [[ -n "${2:-}" ]] || die "--only exige uma lista"; ONLY="$2"; validate_steps "$ONLY"; shift ;;
    --skip)    [[ -n "${2:-}" ]] || die "--skip exige uma lista"; SKIP="$2"; validate_steps "$SKIP"; shift ;;
    --all)     EXPLICIT_ALL=1 ;;
    --reinstall) FORCE_MODULES=1 ;;
    --check-modules) list_module_status; exit $? ;;
    --list)    list_steps; exit 0 ;;
    --labs)    list_labs; exit 0 ;;
    --lab-info) [[ -n "${2:-}" ]] || die "--lab-info exige um nome"; lab_info "$2"; exit $? ;;
    --preflight) preflight; exit $? ;;
    -h|--help) usage; exit 0 ;;
    *) die "Opção desconhecida: $1 (use --help)" ;;
  esac
  shift
done

# Impede uma instalação completa acidental, antes de sudo e de qualquer alteração.
if [[ -n "$ONLY" && ( -n "$SKIP" || "$EXPLICIT_ALL" -eq 1 ) ]]; then
  die "Combine somente uma estratégia: --only, --skip ou --all."
fi
if [[ -z "$ONLY" && -z "$SKIP" && "$EXPLICIT_ALL" -ne 1 ]]; then
  usage
  warn "Nenhuma seleção informada. Use a TUI ou escolha explicitamente --only, --skip ou --all."
  exit 2
fi

if (( ASSUME_YES )) && [[ ",$ONLY," == *,lab_* ]]; then
  die "Labs não permite -y. Use modo interativo para instalar etapas lab_*."
fi

# ----------------------------------------------------------
# Pré-requisitos e log
# ----------------------------------------------------------
[[ $EUID -eq 0 ]] && { echo "Não rode como root. O script usa sudo quando necessário." >&2; exit 1; }
[[ -f /etc/arch-release ]] || { echo "Este script é para Arch Linux ou derivado compatível com pacman." >&2; exit 1; }
command -v sudo >/dev/null 2>&1 || { echo "sudo não está instalado." >&2; exit 1; }

# O log é criado antes das alterações. Em modo não interativo, HOME precisa
# existir e ser gravável para evitar perder o relatório.
LOG_DIR="${HOME}/.local/state/postinstall"
mkdir -p "$LOG_DIR" || { echo "Não foi possível criar $LOG_DIR" >&2; exit 1; }
LOG_FILE="${LOG_DIR}/postinstall-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

info "Log: $LOG_FILE"
info "Autenticando sudo..."
sudo -v

# Mantém o sudo ativo enquanto o script roda.
( while true; do sudo -n true; sleep 50; kill -0 "$$" 2>/dev/null || exit; done ) &
SUDO_KEEPALIVE_PID=$!
TMP_DIR=$(mktemp -d)
cleanup_on_exit() {
  kill "$SUDO_KEEPALIVE_PID" 2>/dev/null || true
  rm -rf -- "$TMP_DIR"
}
trap cleanup_on_exit EXIT
trap 'exit 130' INT TERM

command -v curl >/dev/null 2>&1 || die "curl não está instalado. Instale-o antes de executar este script."
if ! { curl -fsSI --connect-timeout 5 --max-time 10 https://archlinux.org &>/dev/null \
       || ping -c 1 -W 3 archlinux.org &>/dev/null; }; then
  die "Sem conectividade com a internet. Verifique DNS/rede e tente novamente."
fi

# ----------------------------------------------------------
# Funções utilitárias
# ----------------------------------------------------------
install_pkgs() {
  darfinos_event "PKG:pacman:$*"
  # Mantém a confirmação do pacman mesmo com -y: uma instalação aparentemente
  # comum pode exigir remoções/substituições por conflitos de dependências.
  sudo pacman -S --needed "$@"
}

# Para pacotes que podem substituir componentes centrais (SonicDE/XLibre),
# nunca responder automaticamente a perguntas do pacman. Mesmo com -y,
# o usuário deve revisar e aceitar a transação conscientemente.
install_pkgs_replace() {
  darfinos_event "PKG:pacman:$*"
  warn "A operação pode substituir pacotes existentes: $*"
  sudo pacman -S --needed "$@"
}

detect_aur_helper() {
  local h
  for h in paru yay; do
    command -v "$h" &>/dev/null && { echo "$h"; return; }
  done
  echo ""
}

aur_install() {
  darfinos_event "PKG:aur:$*"
  local helper
  helper=$(detect_aur_helper)
  if [[ -n "$helper" ]]; then
    # Também preserva a confirmação do helper: transações AUR podem remover
    # ou substituir pacotes existentes.
    "$helper" -S --needed "$@"
  else
    warn "Nenhum AUR helper instalado. Pulando: $*"
    return 0
  fi
}

flatpak_install() {
  darfinos_event "PKG:flatpak:$*"
  local app failed=0
  for app in "$@"; do
    if flatpak info --system "$app" >/dev/null 2>&1; then
      ok "Flatpak já instalado: $app"
      continue
    fi
    if (( ASSUME_YES )); then
      flatpak install -y --system flathub "$app" || { warn "Falhou ao instalar Flatpak: $app"; failed=1; }
    else
      flatpak install --system flathub "$app" || { warn "Falhou ao instalar Flatpak: $app"; failed=1; }
    fi
  done
  return "$failed"
}

# DarfinOS TUI V4: canal opcional de eventos; execução normal permanece igual.
# FD separado evita que eventos contaminem logs, prompts ou saídas de comandos.
darfinos_event() {
  [[ "${DARFINOS_EVENT_FD:-}" =~ ^[0-9]+$ ]] || return 0
  local payload="$1"
  printf '%s\n' "$payload" >&"$DARFINOS_EVENT_FD" || true
}


# confirm "pergunta" [s|n]  -> o segundo argumento é o padrão (padrão: n)
confirm() {
  local prompt="$1" default="${2:-n}" resp hint
  [[ $default == s ]] && hint="[S/n]" || hint="[s/N]"
  if (( ASSUME_YES )); then
    [[ $default == s ]]
    return
  fi
  darfinos_event "PROMPT_CONFIRM:${default}:${prompt}"
  read -rp "$prompt $hint: " resp
  resp=${resp,,}
  [[ -z "$resp" ]] && resp=$default
  [[ "$resp" =~ ^(s|sim|y|yes)$ ]]
}

# choose "pergunta" "opções" "padrão" -> ecoa a resposta
choose() {
  local prompt="$1" options="$2" default="$3" resp
  if (( ASSUME_YES )); then echo "$default"; return; fi
  darfinos_event "PROMPT_CHOOSE:${default}:${options}:${prompt}"
  read -rp "$prompt [$options]: " resp
  resp=${resp,,}
  echo "${resp:-$default}"
}

has_pkg() { pacman -Qi "$1" &>/dev/null; }

enable_service() {
  sudo systemctl enable --now "$1"
}

require_x86_64() {
  [[ "$(uname -m)" == x86_64 ]] || die "Este repositório só tem pacotes x86_64."
}

conf_has_repo() { grep -qE "^\[$1\][[:space:]]*$" /etc/pacman.conf; }

repo_section_text() {
  local name="$1"
  awk -v target="[$name]" '
    $0 ~ /^\[[^]]+\][[:space:]]*$/ { if (inside) exit; inside=($0==target) }
    inside { print }
  ' /etc/pacman.conf
}

repo_section_has() {
  local name="$1" needle="$2"
  repo_section_text "$name" \
    | grep -E '^[[:space:]]*(Server|Include)[[:space:]]*=' \
    | grep -Fq -- "$needle"
}

# add_repo NOME "Server = ..." ... -> adiciona seção se ainda não existir.
# Se existir, não presume que esteja correta: mostra e valida o conteúdo.
add_repo() {
  local name="$1"; shift
  if conf_has_repo "$name"; then
    info "Seção existente [$name]:"
    repo_section_text "$name"
    warn "O repositório [$name] já existe; não vou sobrescrever sua configuração."
    return 0
  fi
  { printf '\n[%s]\n' "$name"; printf '%s\n' "$@"; } | sudo tee -a /etc/pacman.conf >/dev/null
  ok "Repositório [$name] adicionado ao pacman.conf"
}

# Importa uma chave somente depois de conferir que o arquivo contém o ID
# esperado e de o usuário comparar a impressão digital COMPLETA com a fonte
# oficial. A aprovação é sempre explícita (padrão não), mesmo com -y.
import_repo_key() {
  local name="$1" url="$2" key_id="$3" site="$4"
  local file fingerprint short_id
  file="$TMP_DIR/$name.asc"
  short_id="${key_id^^}"

  if sudo pacman-key --list-keys "$key_id" &>/dev/null; then
    ok "Chave do $name já está no chaveiro. Impressão digital para auditoria:"
    sudo pacman-key --finger "$key_id"
    info "Se a chave não foi previamente verificada por você, compare a impressão digital completa com a fonte oficial: $site"
    return 0
  fi

  info "Baixando chave de assinatura do $name"
  curl -fsSL --retry 3 --connect-timeout 10 --max-time 30 -o "$file" "$url" \
    || { warn "Falha ao baixar $url"; return 1; }

  fingerprint=$(gpg --batch --show-keys --with-colons "$file" 2>/dev/null \
    | awk -F: '$1=="pub" { want=1; next } want && $1=="fpr" { print toupper($10); exit }')
  [[ -n "$fingerprint" ]] || { warn "O arquivo baixado não contém uma chave OpenPGP legível."; return 1; }
  [[ "$fingerprint" == *"$short_id" ]] || {
    warn "A chave baixada não corresponde ao ID esperado ($key_id). Fingerprint: $fingerprint"
    return 1
  }

  echo "Impressão digital completa encontrada: $fingerprint"
  warn "Compare TODOS os caracteres com a impressão digital publicada em $site, por um canal confiável."
  confirm "A impressão digital completa foi verificada e está correta?" n || {
    warn "Chave rejeitada; não foi adicionada ao chaveiro."
    return 1
  }

  sudo pacman-key --add "$file"
  sudo pacman-key --lsign-key "$key_id"
  ok "Chave do $name adicionada após verificação explícita"
}

# rc_block ARQUIVO NOME  (conteúdo via stdin)
# Cria ou substitui um bloco gerenciado dentro de um arquivo de config.
# Reexecutar o script atualiza o bloco em vez de duplicar.
rc_block() {
  local file="$1" name="$2"
  local begin="# >>> postinstall:${name} >>>" end="# <<< postinstall:${name} <<<"
  local legacy_b="__nenhum__" legacy_e="__nenhum__"
  local content tmp backup

  if [[ "$name" == shell ]]; then
    legacy_b="# >>> postinstall >>>"; legacy_e="# <<< postinstall <<<"
  fi

  content=$(cat)
  mkdir -p "$(dirname "$file")"
  touch "$file"

  # Não modificar arquivo se os marcadores estiverem incompletos ou duplicados.
  local begins ends
  begins=$(grep -Fxc -e "$begin" -e "$legacy_b" "$file" 2>/dev/null || true)
  ends=$(grep -Fxc -e "$end" -e "$legacy_e" "$file" 2>/dev/null || true)
  if (( begins != ends || begins > 1 )); then
    warn "Marcadores de configuração inconsistentes em $file; pulando bloco '$name' para não danificar o arquivo."
    return 1
  fi

  if [[ -s "$file" ]]; then
    backup="${file}.postinstall.bak"
    if [[ ! -e "$backup" ]]; then
      cp -p -- "$file" "$backup"
      ok "Backup criado: $backup"
    fi
  fi

  tmp=$(mktemp -p "$TMP_DIR")
  awk -v b="$begin" -v e="$end" -v lb="$legacy_b" -v le="$legacy_e" '
    $0 == b || $0 == lb { skip = 1; next }
    $0 == e || $0 == le { skip = 0; next }
    !skip { print }
  ' "$file" > "$tmp"
  cat "$tmp" > "$file"

  if [[ -s "$file" && -n "$(tail -n 1 "$file")" ]]; then printf '\n' >> "$file"; fi
  printf '%s\n%s\n%s\n' "$begin" "$content" "$end" >> "$file"
}

step_enabled() {
  local name="$1"
  if [[ -n "$ONLY" ]]; then
    [[ ",$ONLY," == *",$name,"* ]]
  else
    # --all / --skip nunca selecionam lab_* sem --only explícito.
    [[ "$name" != lab_* ]] && [[ ",$SKIP," != *",$name,"* ]]
  fi
}

find_login_manager() {
  local re lm
  re=$(tr ' ' '|' <<<"$KNOWN_LMS")
  lm=$(ps -A -o comm= | grep -E "^(${re})$" | head -n 1 || true)
  if [[ -z "$lm" && -e /etc/systemd/system/display-manager.service ]]; then
    lm=$(basename "$(readlink -f /etc/systemd/system/display-manager.service)" .service)
  fi
  echo "$lm"
}

if (step_enabled xlibre || step_enabled sonicde) && [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
  warn "Você está numa sessão gráfica. Para trocar servidor X/DE o ideal é rodar de um TTY (Ctrl+Alt+F3)."
fi

FAILED_STEPS=()
SKIPPED_STEPS=()
run_step() {
  local name="$1" rc=0 dep failed failed_dep=""
  step_enabled "$name" || { echo "--- pulando: $name"; darfinos_event "STEP_SKIP:$name:desmarcada"; return 0; }

  # Não continuar etapas dependentes de outra etapa que falhou nesta execução.
  for dep in ${STEP_DEPS[$name]:-}; do
    for failed in "${FAILED_STEPS[@]}" "${SKIPPED_STEPS[@]}"; do
      if [[ "$failed" == "$dep" ]]; then failed_dep="$dep"; break; fi
    done
    [[ -n "$failed_dep" ]] && break
  done
  if [[ -n "$failed_dep" ]]; then
    warn "Pulando '$name': a dependência '$failed_dep' falhou."
    SKIPPED_STEPS+=("$name")
    darfinos_event "STEP_SKIP:$name:dependencia:$failed_dep"
    return 0
  fi

  if (( ! ${FORCE_MODULES:-0} )); then
    modules_refresh
    module_probe "$name"
    if [[ "$MODULE_STATUS" == installed ]]; then
      info "Módulo '$name' já instalado: $MODULE_REASON"
      darfinos_event "STEP_ALREADY:$name"
      return 0
    fi
  fi

  echo
  info "[$name] ${STEP_DESC[$name]:-}"
  darfinos_event "STEP_START:$name"
  set +e
  ( set -e; "step_$name" )
  rc=$?
  set -e
  if (( rc != 0 )); then
    FAILED_STEPS+=("$name")
    warn "Etapa '$name' terminou com erro (código $rc). Etapas dependentes serão puladas; as independentes continuarão."
    darfinos_event "STEP_FAIL:$name:$rc"
  else
    darfinos_event "STEP_DONE:$name"
  fi
}

# ==========================================================
# ETAPAS — SISTEMA E REPOSITÓRIOS
# ==========================================================

step_pacman_conf() {
  local conf=/etc/pacman.conf
  [[ -e "${conf}.bak" ]] || sudo cp -p "$conf" "${conf}.bak"

  sudo sed -i 's/^[[:space:]]*#Color[[:space:]]*$/Color/' "$conf"
  sudo sed -i 's/^[[:space:]]*#VerbosePkgLists[[:space:]]*$/VerbosePkgLists/' "$conf"
  if grep -qE '^[[:space:]]*#?[[:space:]]*ParallelDownloads[[:space:]]*=' "$conf"; then
    sudo sed -i -E 's/^[[:space:]]*#?[[:space:]]*ParallelDownloads[[:space:]]*=.*/ParallelDownloads = 10/' "$conf"
  else
    printf '\nParallelDownloads = 10\n' | sudo tee -a "$conf" >/dev/null
  fi
  grep -qE '^[[:space:]]*ILoveCandy[[:space:]]*$' "$conf" || sudo sed -i '/^Color$/a ILoveCandy' "$conf"

  # multilib (necessário para Steam e Wine 32 bits)
  if ! grep -q '^\[multilib\]' "$conf"; then
    sudo sed -i '/^#\[multilib\]/,/^#Include/ s/^#//' "$conf"
  fi
  ok "pacman.conf ajustado (backup em ${conf}.bak)"
}

step_mirrors() {
  install_pkgs reflector

  [[ -e /etc/pacman.d/mirrorlist.bak ]] || sudo cp -p /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak
  if sudo reflector --country Brazil,Argentina,Chile,United\ States --latest 20 \
       --protocol https --sort rate --save /etc/pacman.d/mirrorlist; then
    ok "Mirrors do Brasil configurados"
  else
    warn "Reflector falhou. Restaurando mirrorlist anterior."
    sudo cp /etc/pacman.d/mirrorlist.bak /etc/pacman.d/mirrorlist
  fi

  # Atualização semanal automática dos mirrors; preserve config existente.
  sudo install -d -m 755 /etc/xdg/reflector
  if [[ -e /etc/xdg/reflector/reflector.conf && ! -e /etc/xdg/reflector/reflector.conf.bak ]]; then
    sudo cp -p /etc/xdg/reflector/reflector.conf /etc/xdg/reflector/reflector.conf.bak
  fi
  sudo tee /etc/xdg/reflector/reflector.conf >/dev/null <<'EOF'
--country Brazil,Argentina,Chile,United States
--latest 20
--protocol https
--sort rate
--save /etc/pacman.d/mirrorlist
EOF
  sudo systemctl enable --now reflector.timer
}

# Os três repositórios são anexados ao FIM do pacman.conf, nesta ordem:
# xlibre -> sonicde -> chaotic. Chaotic fica por último de propósito:
# se ele tiver um pacote com o mesmo nome de um dos repositórios
# dedicados, o dedicado vence.

# Instalação oficial opcional dos repositórios otimizados do CachyOS.
# O script upstream detecta o nível de instruções do CPU e pode instalar
# o pacman modificado do CachyOS; exige revisão e consentimento explícitos.
step_repo_cachyos() {
  require_x86_64
  if grep -qE '^\[cachyos[^]]*\][[:space:]]*$' /etc/pacman.conf; then
    info "Repositórios CachyOS já presentes no pacman.conf; não serão reinstalados."
    return 0
  fi

  warn "O instalador oficial pode alterar pacman e a ordem dos repositórios."
  info "Documentação: https://wiki.cachyos.org/pt/features/optimized_repos/"
  if (( ASSUME_YES )); then
    info "Modo -y: ignorando CachyOS; exige confirmação explícita."
    return 0
  fi
  confirm "Deseja preparar a instalação dos repositórios CachyOS?" n || return 0

  local workdir="$TMP_DIR/cachyos-repo-install"
  mkdir -p "$workdir"
  curl -fL --retry 3 --connect-timeout 10 --max-time 120 \
    https://mirror.cachyos.org/cachyos-repo.tar.xz \
    -o "$workdir/cachyos-repo.tar.xz" || return 1

  # Verifica cada componente do caminho sem regex com barras escapadas.
  if ! tar -tJf "$workdir/cachyos-repo.tar.xz" | awk -F/ '
    substr($0,1,1)=="/" { bad=1 }
    { for (i=1; i<=NF; i++) if ($i=="..") bad=1 }
    END { exit bad ? 1 : 0 }
  '; then
    warn "Arquivo CachyOS inválido ou com caminhos inseguros."
    return 1
  fi
  tar -xJf "$workdir/cachyos-repo.tar.xz" -C "$workdir" || return 1

  local installer="$workdir/cachyos-repo/cachyos-repo.sh"
  [[ -f "$installer" ]] || { warn "Instalador não encontrado."; return 1; }
  info "Revise o script oficial antes de autorizar execução como root: $installer"
  confirm "Você revisou e autoriza executar o script como root?" n || return 0
  # O instalador upstream usa arquivos auxiliares relativos ao diretório atual.
  # Executá-lo fora dessa pasta provoca erros como install-v4-repo.awk ausente.
  ( cd -- "$(dirname -- "$installer")" && sudo bash "./$(basename -- "$installer")" )
}

step_repo_xlibre() {
  require_x86_64
  if grep -qE '^\[xlibre[^]]*\][[:space:]]*$' /etc/pacman.conf; then
    local existing_xlibre
    existing_xlibre=$(grep -E '^\[xlibre[^]]*\][[:space:]]*$' /etc/pacman.conf | tail -n 1 | tr -d '[]')
    if repo_section_has "$existing_xlibre" 'packages.xlibre.net/arch/'; then
      ok "Repositório XLibre existente validado: [$existing_xlibre]"
      return 0
    fi
    die "A seção [$existing_xlibre] existe, mas seu Server não corresponde ao host esperado packages.xlibre.net. Revise /etc/pacman.conf manualmente."
  fi

  local channel
  channel=$(choose "Canal do XLibre?" "stable/oldstable/beta" "stable")
  [[ "$channel" =~ ^(stable|oldstable|beta)$ ]] || die "Canal inválido: $channel"

  import_repo_key xlibre "$XLIBRE_KEY_URL" "$XLIBRE_KEY_ID" "$XLIBRE_SITE"
  add_repo "xlibre-$channel" "Server = https://packages.xlibre.net/arch/$channel/\$arch"
}

step_repo_sonicde() {
  require_x86_64
  if grep -qE '^\[sonicde[^]]*\][[:space:]]*$' /etc/pacman.conf; then
    local existing_sonicde
    existing_sonicde=$(grep -E '^\[sonicde[^]]*\][[:space:]]*$' /etc/pacman.conf | tail -n 1 | tr -d '[]')
    if repo_section_has "$existing_sonicde" 'github.com/sonicde-arch/'; then
      ok "Repositório SonicDE existente validado: [$existing_sonicde]"
      return 0
    fi
    die "A seção [$existing_sonicde] existe, mas seu Server não corresponde ao host esperado do SonicDE. Revise /etc/pacman.conf manualmente."
  fi

  local channel
  channel=$(choose "Canal do SonicDE?" "stable/stable-testing/beta" "stable")
  [[ "$channel" =~ ^(stable|stable-testing|beta)$ ]] || die "Canal inválido: $channel"

  import_repo_key sonicde "$SONIC_KEY_URL" "$SONIC_KEY_ID" "$SONIC_SITE"
  add_repo "sonicde-$channel" \
    "Server = https://github.com/sonicde-arch/$channel/releases/download/\$arch"
}

step_repo_chaotic() {
  require_x86_64
  if conf_has_repo chaotic-aur; then
    if repo_section_has chaotic-aur '/etc/pacman.d/chaotic-mirrorlist'; then
      ok "Chaotic-AUR já configurado e seu Include foi validado"
      return 0
    fi
    die "[chaotic-aur] existe, mas não inclui /etc/pacman.d/chaotic-mirrorlist. Revise /etc/pacman.conf manualmente."
  fi

  warn "Chaotic-AUR é um repositório de terceiros com binários compilados a partir do AUR."

  local chaotic_key="$TMP_DIR/chaotic-key.asc" chaotic_fpr
  curl -fsSL --retry 3 --connect-timeout 10 --max-time 30 \
    "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x${CHAOTIC_KEY_ID}" \
    -o "$chaotic_key" || die "Não foi possível baixar a chave Chaotic-AUR."
  chaotic_fpr=$(gpg --batch --show-keys --with-colons "$chaotic_key" 2>/dev/null \
    | awk -F: '$1=="pub" { want=1; next } want && $1=="fpr" { print toupper($10); exit }')
  [[ -n "$chaotic_fpr" && "$chaotic_fpr" == *"${CHAOTIC_KEY_ID^^}" ]] \
    || die "A chave baixada do Chaotic-AUR não corresponde ao ID esperado."
  echo "Impressão digital completa da chave Chaotic-AUR: $chaotic_fpr"
  warn "Compare a impressão digital completa com a documentação oficial do Chaotic-AUR."
  confirm "A impressão digital completa foi verificada?" n || die "Chave Chaotic-AUR não aprovada."
  sudo pacman-key --add "$chaotic_key"
  sudo pacman-key --lsign-key "$CHAOTIC_KEY_ID"

  # Baixa os pacotes primeiro, valida o tipo de arquivo e deixa o pacman
  # apresentar a transação antes de instalar os componentes do repositório.
  local keyring="$TMP_DIR/chaotic-keyring.pkg.tar.zst" mirrorlist="$TMP_DIR/chaotic-mirrorlist.pkg.tar.zst"
  curl -fsSL --retry 3 --connect-timeout 10 --max-time 60 -o "$keyring" "$CHAOTIC_PKG_URL/chaotic-keyring.pkg.tar.zst"
  curl -fsSL --retry 3 --connect-timeout 10 --max-time 60 -o "$mirrorlist" "$CHAOTIC_PKG_URL/chaotic-mirrorlist.pkg.tar.zst"
  file "$keyring" "$mirrorlist"
  sudo pacman -U --needed "$keyring" "$mirrorlist"

  add_repo chaotic-aur "Include = /etc/pacman.d/chaotic-mirrorlist"
}

step_sysupgrade() {
  info "Sincronizando bancos de dados e atualizando o sistema..."
  sudo pacman -Syu
}

# ==========================================================
# LABS · instalação assistida, sempre fora dos presets tradicionais
# ==========================================================
lab_aur_install() {
  local project="$1" package="$2" helper reply
  # AUR é código de terceiros. Recusa automação -y em toda etapa Labs.
  if (( ASSUME_YES )); then
    warn "Labs/AUR não permite -y. Use modo interativo, revise o PKGBUILD."
    return 1
  fi
  if pacman -Qq "$package" >/dev/null 2>&1; then
    ok "Labs: $package já está instalado."
    return 0
  fi
  helper=$(detect_aur_helper)
  info "Upstream oficial: ${LABS_URL[$project]}"
  warn "PKGBUILD do AUR é de terceiros. Revise alterações, fontes e dependências no helper."
  # Usa o protocolo de prompts da TUI para que o modal aceite a confirmação.
  # O choose normaliza para minúsculas e publica PROMPT_CHOOSE no FD de eventos.
  reply=$(choose "Digite LABS para abrir a transação de $package" "labs/n" "n") || return 1
  if [[ "$reply" != "labs" ]]; then
    warn "Instalação Labs cancelada; etapa não concluída."
    return 1
  fi
  if [[ -z "$helper" ]]; then
    info "Nenhum AUR helper encontrado. Escolha yay ou paru para continuar."
    install_pkgs base-devel git || return 1
    step_aur_helper || return 1
    helper=$(detect_aur_helper)
    [[ -n "$helper" ]] || { warn "Sem AUR helper; $package não foi instalado."; return 1; }
  fi
  aur_install "$package" || return 1
  if ! pacman -Qq "$package" >/dev/null 2>&1; then
    warn "Labs: o pacote $package não foi detectado após a transação."
    return 1
  fi
  ok "Pacote $package instalado; execução/configuração ficam a seu critério."
}

step_lab_nscde() {
  if ! pacman -Qq nscde-git >/dev/null 2>&1; then
    lab_aur_install nscde nscde || return 1
  fi
  info "Selecione NsCDE na tela de login. O assistente upstream configura as preferências no primeiro login."
}

step_lab_junest() {
  local root="${JUNEST_HOME:-$HOME/.junest}"
  if ! pacman -Qq junest-git >/dev/null 2>&1 && ! pacman -Qq junest >/dev/null 2>&1; then
    lab_aur_install junest junest-git || return 1
  fi
  if ! junest_environment_ready; then
    lab_confirm junest "Baixa e extrai o ambiente Arch upstream em $root, como usuário comum." || return 1
    junest setup || return 1
    junest_environment_ready || { warn "O JuNest não criou um ambiente completo em $root."; return 1; }
  fi
  info "Use junest ns ou, se os namespaces estiverem indisponíveis, junest proot."
}

step_lab_decman() {
  lab_aur_install decman decman
}
step_lab_metapac() {
  if ! pacman -Qq metapac-bin >/dev/null 2>&1; then
    lab_aur_install metapac metapac || return 1
  fi
}

# Todos os módulos lab_* exigem consentimento individual antes de alterações.
lab_confirm() {
  local project="$1" message="$2" reply
  if (( ASSUME_YES )); then
    warn "Labs não permite -y. Use modo interativo."
    return 1
  fi
  info "Projeto original: ${LABS_URL[$project]}"
  info "$message"
  reply=$(choose "Digite LABS para instalar $project" "labs/n" "n") || return 1
  [[ "$reply" == labs ]] || { warn "Instalação Labs cancelada."; return 1; }
}

# Não troca o shell/PATH do usuário. A instalação só publica um executável
# completo e não sobrescreve uma instalação existente, mesmo com --reinstall.
lab_publish_binary() {
  local source="$1" name="$2" dest="$HOME/.local/bin/$2" staged
  mkdir -p -- "$HOME/.local/bin" || return 1
  staged=$(mktemp "$HOME/.local/bin/.$name.XXXXXXXX") || return 1
  if ! install -m 755 -- "$source" "$staged" || ! ln -T -- "$staged" "$dest"; then
    rm -f -- "$staged"
    warn "Não consegui instalar $dest. Nenhum arquivo existente foi substituído."
    return 1
  fi
  rm -f -- "$staged"
}

lab_download_binary() {
  local name="$1" url="$2" checksum="$3" file="$TMP_DIR/$1.download" dest="$HOME/.local/bin/$1"
  if [[ -f "$dest" && -x "$dest" ]]; then
    info "Mantendo executável existente: $dest"
    return 0
  fi
  if [[ -e "$dest" || -L "$dest" ]]; then
    warn "Destino existente não executável: $dest. Revise antes de tentar novamente."
    return 1
  fi
  curl --proto '=https' --proto-redir '=https' -fsSL --retry 2 --connect-timeout 15 --max-time 1800 \
    -o "$file" "$url" || return 1
  if ! printf '%s  %s\n' "$checksum" "$file" | sha256sum --check --status; then
    warn "SHA-256 não corresponde ao arquivo esperado de $name. Não foi instalado."
    return 1
  fi
  lab_publish_binary "$file" "$name"
}

lab_source_checkout() {
  local url="$1" revision="$2" dest="$3"
  git init -q "$dest" || return 1
  git -C "$dest" fetch --depth 1 --quiet -- "$url" "$revision" || return 1
  git -C "$dest" checkout --detach --quiet FETCH_HEAD || return 1
  [[ "$(git -C "$dest" rev-parse HEAD)" == "$revision" ]]
}

step_lab_conty() {
  require_x86_64
  lab_confirm conty "Instala FUSE e baixa Conty Lite 1.29.4 (SHA-256 fixo) para ~/.local/bin/conty." || return 1
  install_pkgs fuse3 || return 1
  lab_download_binary conty "https://github.com/Kron4ek/Conty/releases/download/1.29.4/conty_lite.sh" "$CONTY_SHA256" || return 1
  if ! unshare --user true 2>/dev/null; then
    warn "Namespaces de usuário indisponíveis; consulte os requisitos upstream para executar o Conty. O host não foi reconfigurado."
  fi
  info 'Para usar: ~/.local/bin/conty <comando> [argumentos]'
}

step_lab_nix_portable() {
  require_x86_64
  lab_confirm nix_portable "Instala Nix portátil v012 (SHA-256 fixo) para ~/.local/bin/nix-portable, sem daemon." || return 1
  lab_download_binary nix-portable "https://github.com/DavHau/nix-portable/releases/download/v012/nix-portable-x86_64" "$NIX_PORTABLE_SHA256" || return 1
  info 'Para inicializar o cache do usuário: ~/.local/bin/nix-portable nix --version'
}

trinity_key() {
  local file="$TMP_DIR/trinity.asc" primary
  if ! sudo pacman-key --list-keys "$TRINITY_FINGERPRINT" >/dev/null 2>&1; then
    curl --proto '=https' --proto-redir '=https' -fsSL --retry 2 --connect-timeout 10 --max-time 45 \
      "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x$TRINITY_FINGERPRINT" -o "$file" || return 1
    # Compara todas as chaves primárias presentes: rejeita chaves extras ou parciais.
    primary=$(gpg --batch --show-keys --with-colons "$file" 2>/dev/null | awk -F: '
      $1=="pub" { want=1; next }
      want && $1=="fpr" { print toupper($10); want=0 }
    ') || return 1
    if [[ "$primary" != "$TRINITY_FINGERPRINT" ]]; then
      warn "A chave baixada não corresponde à impressão digital oficial do Trinity."
      return 1
    fi
    sudo pacman-key --add "$file" || return 1
  fi
  sudo pacman-key --lsign-key "$TRINITY_FINGERPRINT"
}

trinity_repo_stanza() {
  printf '\n[trinity]\nSigLevel = PackageRequired PackageTrustedOnly DatabaseOptional DatabaseTrustedOnly\nServer = %s\n' "$TRINITY_SERVER"
}

trinity_install() {
  local config="$1" previous="$TMP_DIR/trinity-pacman.original" candidate="$TMP_DIR/trinity-pacman.conf"
  local needs_repo=0 arch repos original_hash current_hash
  arch=$(uname -m)
  case "$arch" in x86_64|aarch64|armv7h) ;; *) warn "Trinity indisponível para $arch."; return 1 ;; esac
  info "Instruções do Trinity: https://wiki.trinitydesktop.org/Arch_Trinity_Repository_Installation_Instructions"
  info "Servidor: $TRINITY_SERVER · impressão digital: $TRINITY_FINGERPRINT"
  lab_confirm trinity "Instala tde-meta com atualização completa e registra o repositório assinado. Não ativa o TDM." || return 1
  command -v pacman-conf >/dev/null || { warn "pacman-conf indisponível."; return 1; }
  repos=$(pacman-conf --repo-list) || return 1
  if grep -Fx trinity >/dev/null <<< "$repos"; then
    trinity_repo_valid || { warn "[trinity] existente usa outro servidor ou assinatura incompatível. Nenhuma configuração foi sobrescrita."; return 1; }
  else
    needs_repo=1
    cp -p -- "$config" "$previous" || return 1
    original_hash=$(sha256sum < "$previous") || return 1
    {
      cat -- "$previous" &&
      trinity_repo_stanza
    } > "$candidate" || return 1
    pacman-conf --config "$candidate" --repo trinity Server >/dev/null || return 1
  fi
  trinity_key || return 1
  darfinos_event "PKG:pacman:tde-meta"
  if (( needs_repo )); then
    # Valida e usa a nova configuração só nesta transação. Um espelho ou
    # pacote indisponível não deixa o pacman.conf permanente quebrado.
    sudo pacman --config "$candidate" -Syu --needed trinity/tde-meta || return 1
    current_hash=$(sha256sum < "$config") || return 1
    if [[ "$current_hash" != "$original_hash" ]]; then
      warn "O pacman.conf mudou durante a instalação. Preserve as alterações e adicione [trinity] manualmente."
      return 1
    fi
    sudo cp -p --backup=numbered -- "$previous" "$config.darfinos-trinity.bak" || return 1
    # Grava a seção que já foi usada e validada pelo pacman, sem reescrever a configuração.
    trinity_repo_stanza | sudo tee -a "$config" >/dev/null || return 1
  else
    sudo pacman -Syu --needed trinity/tde-meta || return 1
  fi
  trinity_repo_valid && pacman -Qq tde-meta tde-tdebase >/dev/null 2>&1 && trinity_session_ready || {
    warn "Trinity não passou na verificação de pacotes, repositório e sessão X11."
    return 1
  }
  ok "Trinity instalado. Escolha Trinity na tela de login X11 atual."
  info "Se você usa startx, o iniciador da sessão é /opt/trinity/bin/starttde."
}

step_lab_trinity() {
  trinity_install /etc/pacman.conf
}

step_lab_yserver() {
  local driver
  if ! pacman -Qq yserver-git >/dev/null 2>&1; then
    lab_aur_install yserver yserver || return 1
  fi
  if ! yserver_vulkan_ready; then
    driver=$(choose "Driver Vulkan para sua GPU? NVIDIA ou outra GPU: instale o driver apropriado à parte" "intel/amd/n" "n")
    case "$driver" in
      intel) install_pkgs vulkan-intel || return 1 ;;
      amd) install_pkgs vulkan-radeon || return 1 ;;
      *) warn "Falta um provedor vulkan-driver. Instale o driver da sua GPU e rode a etapa novamente."; return 1 ;;
    esac
  fi
  yserver_ready || { warn "yserver, starty ou driver Vulkan não encontrados."; return 1; }
  info "Em VM ou TTY livre, confira KMS, Vulkan e acesso aos dispositivos antes de executar starty."
  info "Guia: https://github.com/joske/yserver/blob/master/docs/setup.md"
}

step_lab_xomposite() {
  local source="$TMP_DIR/xomposite-source"
  if [[ -f "$HOME/.local/bin/xomposite" && -x "$HOME/.local/bin/xomposite" ]]; then
    info "Mantendo Xomposite existente em ~/.local/bin/xomposite."
    return 0
  fi
  lab_confirm xomposite "Instala dependências do Arch e compila o commit $XOMPOSITE_REV sem sudo no Cargo." || return 1
  install_pkgs base-devel git libxcb libx11 mesa || return 1
  if ! command -v cargo >/dev/null || ! command -v rustc >/dev/null; then
    install_pkgs rust || return 1
  fi
  lab_source_checkout "${LABS_URL[xomposite]}.git" "$XOMPOSITE_REV" "$source" || return 1
  (cd -- "$source" && CARGO_TARGET_DIR="$source/target" cargo build --release --locked) || return 1
  lab_publish_binary "$source/target/release/xlibre-compositor-poc" xomposite || return 1
  info "Execute ~/.local/bin/xomposite em uma sessão X11 sem outro compositor ativo (por exemplo i3)."
}

step_lab_wayback() {
  if ! pacman -Qq wayback-x11-git >/dev/null 2>&1; then
    lab_aur_install wayback wayback-x11 || return 1
  fi
  info "O Wayback não foi configurado como servidor gráfico padrão; consulte ${LABS_URL[wayback]} para testar uma sessão separada."
}

step_lab_booster() {
  local path
  lab_confirm booster "O hook do pacote gera imagens alternativas de boot. O DarfinOS não muda o initramfs padrão, o bootloader ou a entrada ativa." || return 1
  for path in /boot /efi /boot/efi; do
    if findmnt --fstab --mountpoint "$path" >/dev/null && ! mountpoint -q -- "$path"; then
      warn "Monte $path antes de instalar Booster."
      return 1
    fi
  done
  install_pkgs extra/booster || return 1
  command -v booster >/dev/null || { warn "Booster não foi encontrado após a instalação."; return 1; }
  info "O hook do pacote informa o caminho das imagens. Para testar, mantenha a entrada de boot original e siga https://wiki.archlinux.org/title/Booster"
}




step_xfce() {
  info "Xfce opcional: instalar sessão X11 paralela, sem substituir SonicDE."
  # Grupo xfce4 com nomes explícitos: sem prompt de escolha de grupo.
  install_pkgs exo garcon thunar thunar-volman tumbler xfce4-appfinder \
    xfce4-panel xfce4-power-manager xfce4-session xfce4-settings \
    xfce4-terminal xfconf xfdesktop xfwm4 xorg-xinit || return 1
  ok "Xfce instalado. Selecione a sessão Xfce no gerenciador de login."
  info "O DarfinOS não altera a sessão padrão nem ~/.config/xfce4."
}

# Links relativos fazem parte dos temas. Valide o destino canônico, inclusive
# através de outros links, em vez de rejeitar todos os ícones legítimos.
chicago95_links_safe() {
  local root="$1" link target canonical
  while IFS= read -r -d '' link; do
    target=$(readlink -- "$link") || return 1
    [[ "$target" != /* ]] || return 1
    canonical=$(realpath -e -- "$link") || return 1
    [[ "$canonical" == "$root/"* ]] || return 1
  done < <(find "$root" -type l -print0)
}

chicago95_copy_component() {
  local src="$1" dest="$2" marker="$3" parent staged
  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ -e "$dest/$marker" ]]; then
      info "Preservando componente Chicago95 existente: $dest"
      return 0
    fi
    warn "Componente Chicago95 incompleto em $dest. Mova-o para um backup antes de tentar novamente."
    return 1
  fi
  [[ -e "$src/$marker" ]] && chicago95_links_safe "$src" || {
    warn "Componente Chicago95 inesperado ou com link inválido: $src"
    return 1
  }
  parent=$(dirname -- "$dest")
  mkdir -p -- "$parent" || return 1
  staged=$(mktemp -d "$parent/.chicago95-stage.XXXXXXXX") || return 1
  if ! cp -a -- "$src/." "$staged/" || ! chmod 755 "$staged" ||
     ! mv -nT -- "$staged" "$dest" || [[ -e "$staged" ]]; then
    rm -rf -- "$staged"
    return 1
  fi
}

step_lab_chicago95() {
  local source="$TMP_DIR/chicago95-upstream"
  lab_confirm chicago95 "Instala Xfce, tema, ícones, cursores e fontes no HOME. Não executa installer.py nem altera painel ou tema ativo." || return 1
  modules_refresh
  module_probe xfce
  if [[ "$MODULE_STATUS" != installed ]]; then
    step_xfce || return 1
  fi
  install_pkgs git fontconfig || return 1
  lab_source_checkout "${LABS_URL[chicago95]}.git" "$CHICAGO95_REV" "$source" || return 1
  chicago95_copy_component "$source/Theme/Chicago95" "$HOME/.themes/Chicago95" "index.theme" || return 1
  chicago95_copy_component "$source/Icons/Chicago95" "$HOME/.icons/Chicago95" "index.theme" || return 1
  chicago95_copy_component "$source/Cursors/Chicago95_Standard_Cursors" "$HOME/.icons/Chicago95_Standard_Cursors" "index.theme" || return 1
  chicago95_copy_component "$source/Fonts/vga_font" "$HOME/.local/share/fonts/Chicago95" "LessPerfectDOSVGA.ttf" || return 1
  fc-cache -f "$HOME/.local/share/fonts/Chicago95" || return 1
  modules_refresh
  chicago95_ready || { warn "Chicago95 não passou na checagem final dos arquivos."; return 1; }
  ok "Chicago95 instalado. Selecione Chicago95 em Aparência e no Gerenciador de Janelas do Xfce."
  info "O cursor aparece em Mouse e Touchpad. Para GTK4, painel e outros extras: ${LABS_URL[chicago95]}/blob/$CHICAGO95_REV/INSTALL.md"
}

step_lab_windowmaker() {
  lab_confirm windowmaker "Instala Window Maker como sessão X11 paralela." || return 1
  install_pkgs windowmaker xorg-xinit || return 1
  info "Escolha Window Maker na tela de login ou use wmaker como cliente do startx."
}

step_lab_notion() {
  lab_aur_install notion notion-git || return 1
  install_pkgs xorg-xinit || return 1
  info "Escolha Notion na tela de login se a sessão estiver disponível; em TTY, startx /usr/bin/notion."
}

step_lab_e16() {
  lab_confirm e16 "Instala E16 como sessão X11 alternativa." || return 1
  install_pkgs e16 xorg-xinit || return 1
  info "Escolha Enlightenment DR16 no login ou inicie e16 como cliente do startx."
}

step_lab_xpra() {
  lab_confirm xpra "Instala Xpra, sem habilitar serviços ou abrir portas." || return 1
  install_pkgs xpra || return 1
  info "Para usar sobre SSH, leia https://xpra-org.github.io/xpra/Usage/Seamless.html"
}

step_lab_opengamepadui() {
  lab_aur_install opengamepadui opengamepadui-bin || return 1
  info "Abra OpenGamepadUI pelo menu. Não habilitamos serviços de entrada nem trocamos sua sessão."
}

step_lab_wmutils() {
  lab_aur_install wmutils wmutils-git || return 1
  info "Use os utilitários em uma sessão X11. Não mexemos nas teclas nem no WM atual."
}

# Mantém o prefixo, a árvore de pacotes e o PATH sob controle do usuário.
step_lab_pkgsrc() {
  local parent="$HOME/.local/share/darfinos" prefix="$HOME/.local/share/darfinos/pkgsrc-prefix"
  local tree="$HOME/.local/share/darfinos/pkgsrc-tree" staging="$TMP_DIR/pkgsrc-tree"
  lab_confirm pkgsrc "Prepara pkgsrc 2026Q3 no HOME. O bootstrap compila ferramentas como usuário comum." || return 1
  install_pkgs base-devel git openssl ncurses gawk zlib || return 1
  mkdir -p -- "$parent" || return 1
  if [[ ! -d "$tree/pkgtools" ]]; then
    if [[ -e "$tree" || -L "$tree" ]]; then
      warn "Árvore pkgsrc existente em $tree; revise antes de continuar."
      return 1
    fi
    lab_source_checkout "https://github.com/NetBSD/pkgsrc.git" b905145c25084a9b3173e6647a3f21e6e5aabf80 "$staging" || return 1
    mv -nT -- "$staging" "$tree" && [[ ! -e "$staging" ]] || return 1
  fi
  if [[ ! -x "$prefix/bin/bmake" || ! -x "$prefix/sbin/pkg_info" ]]; then
    if [[ -e "$prefix" || -L "$prefix" ]]; then
      warn "Prefixo incompleto em $prefix; preserve ou mova-o antes de repetir o bootstrap."
      return 1
    fi
    (cd -- "$tree/bootstrap" && ./bootstrap --unprivileged --prefix "$prefix" --workdir "$TMP_DIR/pkgsrc-bootstrap") || return 1
  fi
  [[ -x "$prefix/bin/bmake" && -x "$prefix/sbin/pkg_info" ]] || return 1
  info "pkgsrc pronto em $prefix. Use $prefix/bin/bmake na árvore $tree; o PATH foi preservado."
}

step_lab_pipeworld() {
  local dest="$HOME/.local/share/darfinos/pipeworld" staging="$TMP_DIR/pipeworld"
  local launcher="$HOME/.local/bin/darfinos-pipeworld" draft="$TMP_DIR/pipeworld-launcher"
  lab_confirm pipeworld "Instala o Arcan e copia o Pipeworld experimental, sem iniciar ou substituir sua sessão." || return 1
  lab_aur_install pipeworld arcan || return 1
  install_pkgs git || return 1
  if [[ ! -f "$dest/pipeworld/pipeworld.lua" ]]; then
    if [[ -e "$dest" || -L "$dest" ]]; then
      warn "Pasta Pipeworld existente em $dest; não será sobrescrita."
      return 1
    fi
    mkdir -p -- "$(dirname -- "$dest")" || return 1
    lab_source_checkout "https://github.com/letoram/pipeworld.git" edc3821404b3a1274b8a50d2fb1c6b523fbd4a1c "$staging" || return 1
    [[ -f "$staging/pipeworld/pipeworld.lua" ]] || return 1
    mv -nT -- "$staging" "$dest" && [[ ! -e "$staging" ]] || return 1
  fi
  if [[ ! -x "$launcher" ]]; then
    cat > "$draft" <<'LAUNCHER'
#!/bin/sh
exec arcan "$HOME/.local/share/darfinos/pipeworld/pipeworld" "$@"
LAUNCHER
    lab_publish_binary "$draft" darfinos-pipeworld || return 1
  fi
  info "Teste com $launcher. O upstream do Pipeworld recomenda Arcan recente; a execução gráfica ainda é experimental."
}

step_lab_chezmoi() {
  lab_confirm chezmoi "Instala o motor dos perfis do Control Center sem importar dotfiles externos." || return 1
  install_pkgs chezmoi
}

step_lab_matugen() {
  lab_confirm matugen "Instala o gerador de paletas da Oficina de Temas." || return 1
  install_pkgs matugen
}

step_lab_autorandr() {
  lab_confirm autorandr "Instala autorandr. O pacote pode reagir a monitores conectados quando houver perfis salvos." || return 1
  install_pkgs autorandr || return 1
  info "No X11, ajuste a tela primeiro e use autorandr --save notebook-720p; use autorandr --change para testar."
}

step_lab_desktop_config() {
  lab_confirm desktop_config "Instala os utilitários Xfconf e KConfig, sem alterar a aparência ativa." || return 1
  install_pkgs xfconf kconfig
}

step_lab_etckeeper() {
  lab_confirm etckeeper "Instala etckeeper. Inicializar o histórico local de /etc é uma escolha separada." || return 1
  install_pkgs etckeeper git || return 1
  local vcs present=0
  for vcs in .git .hg .bzr _darcs; do
    if sudo test -e "/etc/$vcs"; then present=1; break; fi
  done
  if (( ! present )) && confirm "Inicializar histórico LOCAL de /etc (sem remoto)?" n; then
    sudo etckeeper init || return 1
    sudo etckeeper commit "Initial DarfinOS configuration baseline" || return 1
  fi
  info "Não publique o histórico de /etc. Ele pode conter credenciais e outros dados privados."
}

step_lab_rustic() {
  lab_confirm rustic "Instala o rustic sem criar repositório, agendar backup ou selecionar destino." || return 1
  install_pkgs rustic || return 1
  info "Escolha destino, senha e faça um teste de restauração: https://rustic.cli.rs/docs/"
}

step_lab_kvantum() {
  lab_confirm kvantum "Instala o estilo Qt6 e o Kvantum Manager. Não modifica seu tema ativo." || return 1
  install_pkgs kvantum || return 1
  if confirm "Instalar também o plugin para aplicativos Qt5?" n; then
    install_pkgs kvantum-qt5 || return 1
  fi
  info "No SonicDE, selecione Kvantum em Estilo dos aplicativos. Use o Kvantum Manager para escolher o tema."
  info "No Control Center: perfil sonicde-kvantum para prévia/aplicação do estilo KvDark."
}

# Official pinned asset; staged publication preserves existing user themes.
notebook_install_cursor() {
  local icons="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
  local dest="$icons/Bibata-Modern-Ice" archive="$TMP_DIR/Bibata-Modern-Ice.tar.xz"
  local extracted staged entry link target canonical
  if notebook_cursor_ready "$dest"; then
    info "Preservando Bibata existente: $dest"
    return 0
  fi
  if [[ -e "$dest" || -L "$dest" ]]; then
    warn "Bibata incompleto em $dest. Mova-o para um backup antes de tentar novamente."
    return 1
  fi
  curl --proto '=https' --proto-redir '=https' -fsSL --retry 2 --connect-timeout 15 --max-time 1800 \
    -o "$archive" "https://github.com/ful1e5/Bibata_Cursor/releases/download/$BIBATA_VERSION/Bibata-Modern-Ice.tar.xz" || return 1
  if ! printf '%s  %s\n' "$BIBATA_SHA256" "$archive" | sha256sum --check --status; then
    warn "SHA-256 do Bibata não corresponde ao arquivo esperado. Não foi instalado."
    return 1
  fi
  # Reject unexpected archive roots and traversal before extraction.
  tar -tJf "$archive" > "$TMP_DIR/bibata-members" || return 1
  while IFS= read -r entry; do
    case "$entry" in
      Bibata-Modern-Ice/*) ;;
      *) warn "Arquivo Bibata com estrutura inesperada."; return 1 ;;
    esac
    case "/$entry/" in */../*) warn "Caminho inválido no arquivo Bibata."; return 1 ;; esac
  done < "$TMP_DIR/bibata-members"
  extracted=$(mktemp -d "$TMP_DIR/bibata.XXXXXXXX") || return 1
  if ! tar --no-same-owner -xJf "$archive" -C "$extracted" ||
     ! notebook_cursor_ready "$extracted/Bibata-Modern-Ice"; then
    rm -rf -- "$extracted"
    return 1
  fi
  # Cursor aliases are relative links contained in the official theme.
  while IFS= read -r -d '' link; do
    target=$(readlink -- "$link") || target=/
    canonical=$(realpath -e -- "$link") || canonical=
    if [[ "$target" == /* || "$canonical" != "$extracted/Bibata-Modern-Ice/"* ]]; then
      warn "Link inválido no tema Bibata."
      rm -rf -- "$extracted"
      return 1
    fi
  done < <(find "$extracted/Bibata-Modern-Ice" -type l -print0)
  mkdir -p -- "$icons" || { rm -rf -- "$extracted"; return 1; }
  staged=$(mktemp -d "$icons/.bibata-stage.XXXXXXXX") || { rm -rf -- "$extracted"; return 1; }
  if ! cp -a -- "$extracted/Bibata-Modern-Ice/." "$staged/" || ! chmod 755 "$staged" ||
     ! mv -nT -- "$staged" "$dest" || [[ -e "$staged" ]]; then
    rm -rf -- "$staged" "$extracted"
    return 1
  fi
  rm -rf -- "$extracted"
}

step_lab_i3_notebook() {
  lab_confirm i3_notebook "Instala i3, ferramentas Notebook e Bibata Modern Ice v2.0.7 (SHA-256 fixo) no HOME: https://github.com/ful1e5/Bibata_Cursor. Não aplica o perfil nem troca sua sessão." || return 1
  install_pkgs i3-wm i3status i3lock dmenu xorg-xinit chezmoi rofi dunst i3status-rust \
    brightnessctl xss-lock flameshot xterm ttf-dejavu libpulse libnotify feh zenity xorg-xrandr xorg-xrdb xorg-xsetroot xsettingsd \
    polybar xdotool ttf-jetbrains-mono-nerd powerline-fonts librsvg xdg-utils gtk3 python-gobject \
    pavucontrol network-manager-applet bluez-utils blueman polkit-gnome fastfetch chafa python-xlib playerctl arandr lxappearance curl tar xz || return 1
  notebook_install_cursor || return 1
  info "Abra a Oficina de Temas (W) e selecione i3-notebook. Entre novamente na sessão i3 para ativar."
  info "O perfil usa o áudio existente (wpctl ou pactl); não troca o servidor de áudio."
  info "Os controles usam NetworkManager e BlueZ quando ativos. Os Labs não trocam seu serviço de rede."
  info "Para ativar o BlueZ, use a etapa Bluetooth do DarfinOS."
}

step_i3() {
  info "Instalando i3 como window manager alternativo, sem substituir SonicDE."
  info "Fonte: ${LABS_URL[i3]}"
  install_pkgs i3-wm i3status i3lock dmenu xorg-xinit || return 1
  ok "i3 instalado. Selecione a sessão i3 no login ou configure ~/.xinitrc para startx."
  info "O DarfinOS não altera seu login manager, tema ou arquivos ~/.config/i3."
}

# ==========================================================
# ETAPAS — BASE
# ==========================================================

step_base() {
  install_pkgs \
    base-devel git curl wget unzip p7zip rsync \
    htop fastfetch man-db man-pages rclone fuse2 \
    pacman-contrib bash-completion pciutils usbutils
}

step_aur_helper() {
  local current choice
  current=$(detect_aur_helper)
  if [[ -n "$current" ]]; then
    ok "AUR helper já instalado: $current"
    return
  fi

  choice=$(choose "Qual AUR helper deseja instalar?" "paru/yay/N" "paru")
  case "$choice" in
    yay|paru)
      # Com o Chaotic-AUR ativo, o binário já vem pronto
      if conf_has_repo chaotic-aur && install_pkgs "$choice"; then
        ok "$choice instalado via Chaotic-AUR"
        return
      fi
      # Senão: versões -bin do AUR evitam compilar
      git clone "https://aur.archlinux.org/${choice}-bin.git" "$TMP_DIR/$choice" || return 1
      (cd "$TMP_DIR/$choice" && makepkg -si)
      ;;
    *) echo "Nenhum AUR helper será instalado." ;;
  esac
}

step_fonts() {
  install_pkgs \
    noto-fonts noto-fonts-cjk noto-fonts-emoji \
    ttf-dejavu ttf-liberation ttf-jetbrains-mono-nerd
}

step_hardware() {
  # Microcode
  if grep -qi 'GenuineIntel' /proc/cpuinfo; then
    install_pkgs intel-ucode
  elif grep -qi 'AuthenticAMD' /proc/cpuinfo; then
    install_pkgs amd-ucode
  fi

  # Detecta GRUB pela configuração e não tenta reconfigurar bootloaders alheios.
  if [[ -f /boot/grub/grub.cfg ]] && command -v grub-mkconfig &>/dev/null; then
    if confirm "Regenerar o grub.cfg (para carregar o microcode)" s; then
      sudo grub-mkconfig -o /boot/grub/grub.cfg
    fi
  else
    warn "GRUB não detectado em /boot/grub/grub.cfg. Confirme a configuração do microcode no seu bootloader."
  fi

  # Detecta todas as GPUs de lspci (incluindo híbridas) e mostra antes de agir.
  local gpu gpu_lower nvidia=0 amd=0 intel=0
  # Filtra pela classe PCI no início da linha. Um grep simples por "3D"
  # também capturava discos com nomes como "SanDisk Ultra 3D".
  gpu=$(lspci -nn 2>/dev/null | grep -Ei '^[[:xdigit:]:.]+[[:space:]]+(VGA compatible controller|3D controller|Display controller)' || true)
  gpu_lower=${gpu,,}
  printf 'GPU(s) detectada(s):\n%s\n' "${gpu:-desconhecida}"
  [[ -n "$gpu" ]] || warn "Nenhuma GPU foi identificada por lspci; drivers serão ignorados."
  [[ "$gpu_lower" == *nvidia* ]] && nvidia=1
  [[ "$gpu_lower" =~ (\[1002:|advanced micro devices|amd/ati|radeon) ]] && amd=1
  [[ "$gpu_lower" == *intel* ]] && intel=1

  if (( nvidia )); then
    if confirm "Instalar driver NVIDIA? Verifique antes o suporte da sua GPU ao driver aberto." n; then
      local headers=() k kernel_found=0
      for k in linux linux-lts linux-zen linux-hardened linux-cachyos linux-cachyos-lts linux-cachyos-rc; do
        if has_pkg "$k"; then
          kernel_found=1
          has_pkg "$k-headers" && headers+=("$k-headers")
        fi
      done
      if (( ! kernel_found )); then
        warn "Não reconheci um kernel comum instalado. Verifique manualmente o driver e os headers; não instalarei DKMS automaticamente."
      elif (( ${#headers[@]} == 0 )); then
        warn "Nenhum pacote de headers correspondente aos kernels instalados foi encontrado."
      else
        install_pkgs "${headers[@]}" nvidia-open-dkms nvidia-utils lib32-nvidia-utils nvidia-settings
      fi
    fi
  fi
  if (( amd )); then
    install_pkgs mesa lib32-mesa vulkan-radeon lib32-vulkan-radeon
  fi
  if (( intel )); then
    install_pkgs mesa lib32-mesa vulkan-intel lib32-vulkan-intel
  fi

  # zram (swap comprimida na RAM)
  if confirm "Configurar zram (swap em RAM)" s; then
    install_pkgs zram-generator
    if [[ -e /etc/systemd/zram-generator.conf && ! -e /etc/systemd/zram-generator.conf.postinstall.bak ]]; then
      sudo cp -p /etc/systemd/zram-generator.conf /etc/systemd/zram-generator.conf.postinstall.bak
    fi
    sudo tee /etc/systemd/zram-generator.conf >/dev/null <<'EOF'
[zram0]
zram-size = min(ram / 2, 8192)
compression-algorithm = zstd
EOF
    sudo systemctl daemon-reload
    sudo systemctl start systemd-zram-setup@zram0.service || warn "zram não iniciou agora; confira systemctl status systemd-zram-setup@zram0.service"
  fi
}

# ==========================================================
# ETAPAS — DESKTOP (XLibre + SonicDE)
# ==========================================================

step_xlibre() {
  conf_has_repo xlibre-stable || grep -qE '^\[xlibre' /etc/pacman.conf \
    || die "Repositório do XLibre não configurado (rode a etapa repo_xlibre)."

  if has_pkg xlibre-meta; then
    ok "XLibre já instalado"
  else
    info "Instalando XLibre (substitui os pacotes do X.Org)..."
    install_pkgs_replace xlibre-meta
  fi

  install_pkgs xorg-xdpyinfo
  info "Depois do próximo login, confirme com:  xdpyinfo | grep vendor"
}

step_sonicde() {
  grep -qE '^\[sonicde' /etc/pacman.conf \
    || die "Repositório do SonicDE não configurado (rode a etapa repo_sonicde)."

  if has_pkg sonicde-meta; then
    ok "SonicDE já instalado"
  else
    info "Instalando SonicDE (substitui componentes KDE conflitantes)..."
    install_pkgs_replace sonicde-meta
  fi

  # --- Login manager ---
  local current
  current=$(find_login_manager)
  echo "Login manager atual: ${current:-nenhum}"

  if [[ "$current" != soniclogin ]] \
     && confirm "Trocar para o Sonic Login Manager (recomendado pelo SonicDE)?" s; then
    install_pkgs_replace sonic-login-manager
    # sem --now: não derruba a sessão atual; vale a partir do próximo boot
    sudo systemctl enable --force soniclogin.service
    ok "soniclogin habilitado (ativo no próximo boot)"
  elif [[ -z "$current" ]]; then
    warn "Nenhum login manager habilitado. Habilite um (ex.: soniclogin) antes de reiniciar."
  fi

  # --- Rede ---
  if has_pkg networkmanager; then
    if systemctl is-active --quiet systemd-networkd; then
      warn "systemd-networkd está ativo; não habilitei o NetworkManager para não derrubar a rede."
    else
      enable_service NetworkManager.service
    fi
  else
    warn "NetworkManager não está instalado; pulando."
  fi

  # --- Áudio (PipeWire) ---
  install_pkgs_replace pipewire pipewire-pulse pipewire-alsa wireplumber
  systemctl --user enable --now pipewire.socket pipewire-pulse.socket wireplumber.service \
    || warn "Não foi possível habilitar o PipeWire agora (sem sessão de usuário). Ele inicia no login."

  info "Reinicie e escolha a sessão X11 do SonicDE na tela de login."
  info "Mais informações: $SONIC_HOME"
}

step_desktop_extras() {
  local pkgs=(ark kio-admin power-profiles-daemon fwupd kdeconnect wl-clipboard xclip)

  # Não instalar substitutos KDE quando os componentes equivalentes do SonicDE
  # já estão presentes: esses pacotes declaram conflitos entre si.
  if has_pkg sonic-gtk-theme-bridge; then
    warn "sonic-gtk-theme-bridge está instalado; pulando kde-gtk-config por conflito conhecido."
  else
    pkgs+=(kde-gtk-config)
  fi
  if has_pkg xdg-desktop-portal-sonicde; then
    warn "xdg-desktop-portal-sonicde está instalado; pulando xdg-desktop-portal-kde por conflito conhecido."
  else
    pkgs+=(xdg-desktop-portal-kde)
  fi

  # Instalar os extras em uma transação sem substituir componentes SonicDE.
  install_pkgs_replace "${pkgs[@]}"
  sudo systemctl enable --now power-profiles-daemon.service || true
}

step_bluetooth() {
  install_pkgs bluez bluez-utils
  enable_service bluetooth.service
}

# ==========================================================
# ETAPAS — SHELL E DESENVOLVIMENTO
# ==========================================================

step_cli_tools() {
  install_pkgs \
    zoxide fzf bat eza fd ripgrep btop ncdu tldr jq \
    lazygit nmap yazi starship
  aur_install doggo
}

step_dev_tools() {
  local pkgs=(git neovim gcc clang cmake python nodejs npm go)

  # 'rust' conflita com 'rustup'
  if has_pkg rustup; then
    warn "rustup instalado: pulando o pacote 'rust'. Use: rustup default stable"
  else
    pkgs+=(rust)
  fi

  install_pkgs "${pkgs[@]}"
}

# pip / pipx / cargo (+ npm e go): instalação, PATH e configuração.
# Os índices padrão são PyPI (pip/pipx) e crates.io (cargo); os arquivos
# de config abaixo são o lugar para trocar por mirrors, se precisar.
step_pkg_managers() {
  install_pkgs python-pip python-pipx

  # --- pip ---
  local pipconf="$HOME/.config/pip/pip.conf"
  if [[ ! -f "$pipconf" ]]; then
    mkdir -p "$(dirname "$pipconf")"
    cat > "$pipconf" <<'EOF'
[global]
# Índice padrão: PyPI. Para usar um mirror, descomente e ajuste:
# index-url = https://pypi.org/simple
disable-pip-version-check = true
EOF
    ok "Criado $pipconf"
  fi

  # --- cargo ---
  local cargoconf="$HOME/.cargo/config.toml"
  if [[ ! -f "$cargoconf" ]]; then
    mkdir -p "$(dirname "$cargoconf")"
    cat > "$cargoconf" <<'EOF'
# Registro padrão: crates.io (índice sparse). Para usar um mirror:
# [source.crates-io]
# replace-with = "meu-mirror"
#
# [source.meu-mirror]
# registry = "sparse+https://exemplo.org/index/"

[net]
git-fetch-with-cli = true
EOF
    ok "Criado $cargoconf"
  fi

  # --- npm: pacotes globais em ~/.local (sem sudo) ---
  if command -v npm &>/dev/null; then
    npm config set prefix "$HOME/.local"
    ok "npm: prefixo global em ~/.local"
  fi

  # --- PATH (~/.local/bin: pipx e npm; ~/.cargo/bin: cargo; ~/go/bin: go) ---
  rc_block ~/.bashrc path <<'EOF'
for d in "$HOME/.local/bin" "$HOME/.cargo/bin" "$HOME/go/bin"; do
  case ":$PATH:" in *":$d:"*) ;; *) PATH="$d:$PATH" ;; esac
done
export PATH
EOF
  rc_block ~/.zshrc path <<'EOF'
for d in "$HOME/.local/bin" "$HOME/.cargo/bin" "$HOME/go/bin"; do
  case ":$PATH:" in *":$d:"*) ;; *) PATH="$d:$PATH" ;; esac
done
export PATH
EOF
  rc_block ~/.config/fish/config.fish path <<'EOF'
fish_add_path -g $HOME/.local/bin $HOME/.cargo/bin $HOME/go/bin
EOF
  ok "PATH configurado para bash, zsh e fish"
}

step_shells() {
  install_pkgs fish zsh zsh-autosuggestions zsh-syntax-highlighting

  # --- fish ---
  rc_block ~/.config/fish/config.fish shell <<'EOF'
fastfetch
set -g fish_greeting
set -gx EDITOR nvim
set -gx VISUAL nvim

if status is-interactive
    command -q starship; and starship init fish | source
    command -q zoxide;   and zoxide init fish | source
    command -q fzf;      and fzf --fish | source

    abbr -a ll   'eza -lah --git'
    abbr -a lt   'eza --tree --level=2'
    abbr -a gs   'git status'
    abbr -a lg   lazygit
    command -q lazydocker; and abbr -a lzd lazydocker
    abbr -a v    nvim
    abbr -a up   'sudo pacman -Syu'
    abbr -a pkgs 'pacman -Qqe'
end

# yazi: ao sair, o shell entra na pasta onde você parou
function y
    set tmp (mktemp -t "yazi-cwd.XXXXXX")
    command yazi $argv --cwd-file="$tmp"
    if read -z cwd < "$tmp"; and [ -n "$cwd" ]; and [ "$cwd" != "$PWD" ]
        builtin cd -- "$cwd"
    end
    rm -f -- "$tmp"
end
EOF

  # --- Fisher: gerenciador de plugins do Fish ---
  if confirm "Instalar o Fisher (gerenciador de plugins do Fish)?" s; then
    if ! command -v fish >/dev/null 2>&1; then
      warn "Fish não encontrado; não é possível instalar o Fisher."
    elif fish -c 'functions -q fisher'; then
      ok "Fisher já está instalado."
    else
      local fisher_tmp
      fisher_tmp=$(mktemp) || return 1
      if curl -fsSL --retry 2 --max-time 30 \
        "https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish" \
        -o "$fisher_tmp" && [[ -s "$fisher_tmp" ]]; then
        if FISHER_BOOTSTRAP="$fisher_tmp" fish -c 'source $FISHER_BOOTSTRAP; fisher install jorgebucaran/fisher'; then
          ok "Fisher instalado. Use 'fisher install autor/plugin' para adicionar plugins."
        else
          warn "Falha ao instalar Fisher; consulte https://github.com/jorgebucaran/fisher"
        fi
      else
        warn "Não foi possível baixar o Fisher; configuração do Fish preservada."
      fi
      rm -f "$fisher_tmp"
    fi
  fi

  # --- tema de cores do Fish (opcional e seguro para reexecução) ---
  if confirm "Aplicar o tema de cores DarfinOS no Fish?" s; then
    local theme_dir="$HOME/.config/fish/themes"
    local theme_file="$theme_dir/DarfinOS.theme"
    local theme_tmp
    mkdir -p "$theme_dir"
    theme_tmp=$(mktemp) || return 1
    if curl -fsSL --retry 2 --max-time 30 \
      "https://raw.githubusercontent.com/AlanDarfin/DarfinOS/main/themes/fish/DarfinOS.theme" \
      -o "$theme_tmp"; then
      if [[ ! -s "$theme_tmp" ]] || ! grep -q 'fish_color_command' "$theme_tmp"; then
        warn "Tema Fish baixado está vazio ou inválido; mantendo configuração anterior."
      else
        if [[ -f "$theme_file" ]] && ! cmp -s "$theme_tmp" "$theme_file"; then
          cp -p "$theme_file" "$theme_file.bak" || warn "Não foi possível criar backup do tema anterior."
        fi
        if install -m 644 "$theme_tmp" "$theme_file"; then
          if command -v fish >/dev/null 2>&1 && fish -c 'fish_config theme choose DarfinOS'; then
            ok "Tema DarfinOS aplicado como padrão no Fish."
          else
            warn "Tema salvo em $theme_file, mas não foi possível ativá-lo automaticamente."
          fi
        else
          warn "Não foi possível salvar o tema do Fish."
        fi
      fi
    else
      warn "Falha ao baixar o tema Fish do repositório; configuração atual preservada."
    fi
    rm -f "$theme_tmp"
  fi

  # --- zsh ---
  rc_block ~/.zshrc shell <<'EOF'
export EDITOR=nvim
export VISUAL=nvim

HISTFILE=~/.zsh_history
HISTSIZE=50000
SAVEHIST=50000
setopt SHARE_HISTORY HIST_IGNORE_DUPS HIST_IGNORE_SPACE AUTO_CD

autoload -Uz compinit && compinit

command -v starship &>/dev/null && eval "$(starship init zsh)"
command -v zoxide   &>/dev/null && eval "$(zoxide init zsh)"
command -v fzf      &>/dev/null && source <(fzf --zsh)

alias ll='eza -lah --git'
alias lt='eza --tree --level=2'
alias gs='git status'
alias lg='lazygit'
command -v lazydocker >/dev/null 2>&1 && alias lzd='lazydocker'
alias v='nvim'
alias up='sudo pacman -Syu'
alias pkgs='pacman -Qqe'

# yazi: ao sair, o shell entra na pasta onde você parou
function y() {
  local tmp cwd
  tmp="$(mktemp -t "yazi-cwd.XXXXXX")"
  command yazi "$@" --cwd-file="$tmp"
  IFS= read -r -d '' cwd < "$tmp"
  [ "$cwd" != "$PWD" ] && [ -d "$cwd" ] && builtin cd -- "$cwd"
  rm -f -- "$tmp"
}

# plugins (o syntax-highlighting deve ser o último)
[[ -r /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh ]] \
  && source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
[[ -r /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ]] \
  && source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
EOF
  ok "Configs de fish e zsh atualizadas"

  # --- shell padrão ---
  local choice path current
  choice=$(choose "Shell padrão?" "fish/zsh/bash" "fish")
  case "$choice" in
    fish|zsh|bash) ;;
    *) warn "Opção inválida ('$choice'). Mantendo o shell atual."; return 0 ;;
  esac

  path=$(command -v "$choice")
  current=$(getent passwd "$USER" | cut -d: -f7)
  if [[ "$current" != "$path" ]]; then
    sudo chsh -s "$path" "$USER" \
      && ok "Shell padrão: $path (vale no próximo login)" \
      || warn "Não foi possível trocar o shell automaticamente"
  else
    ok "Shell padrão já é $path"
  fi
}

step_git_setup() {
  local name email
  name=$(git config --global user.name || true)
  email=$(git config --global user.email || true)

  if [[ -z "$name" || -z "$email" ]] && (( ! ASSUME_YES )); then
    read -rp "Nome para o git: " name
    read -rp "E-mail para o git: " email
    [[ -n "$name"  ]] && git config --global user.name  "$name"
    [[ -n "$email" ]] && git config --global user.email "$email"
  fi
  git config --global init.defaultBranch main
  git config --global pull.rebase false

  if [[ ! -f ~/.ssh/id_ed25519 ]] && confirm "Gerar chave SSH (ed25519)?" n; then
    install -d -m 700 "$HOME/.ssh"
    ssh-keygen -t ed25519 -C "${email:-$USER@$(hostname)}" -f ~/.ssh/id_ed25519
    echo "Chave pública:"; cat ~/.ssh/id_ed25519.pub
  fi
}

# ==========================================================
# ETAPAS — REDE E SERVIÇOS
# ==========================================================

step_zerotier() {
  install_pkgs zerotier-one
  enable_service zerotier-one.service

  case "$(choose "Instalar UI para ZeroTier?" "ui/gui/N" "n")" in
    ui)  aur_install zerotier-desktop-ui-git ;;
    gui) aur_install zerotier-gui-git ;;
  esac
}

step_hamachi() {
  aur_install logmein-hamachi haguichi
  sudo systemctl enable --now logmein-hamachi.service || warn "Serviço do Hamachi não iniciou"
}

step_syncthing() {
  install_pkgs syncthing
  systemctl --user enable --now syncthing.service \
    || warn "Não foi possível iniciar o Syncthing agora (sem sessão de usuário). Rode no login: systemctl --user enable --now syncthing"
  aur_install syncthingtray-qt6
}

step_docker() {
  local engine
  info "Escolha o mecanismo de contêineres:"
  info "  docker - Docker Engine (padrão)"
  info "  podman - Podman (sem daemon obrigatório; suporta rootless)"
  engine=$(choose "Qual mecanismo de contêineres deseja instalar?" "docker/podman" "docker")

  case "$engine" in
    docker)
      install_pkgs docker docker-compose docker-buildx lazydocker dive
      if confirm "Habilitar o daemon Docker na inicialização e iniciá-lo agora?" n; then
        enable_service docker.service
      else
        info "Docker instalado, mas o serviço ficou desabilitado. Inicie quando precisar: sudo systemctl start docker"
      fi
      if confirm "Adicionar $USER ao grupo docker (equivale, na prática, a conceder privilégios de root)?" n; then
        sudo usermod -aG docker "$USER"
        warn "Faça logout/login para aplicar a associação ao grupo docker."
      fi
      warn "Atenção: o Docker pode contornar regras de firewall ao publicar portas."
      ;;
    podman)
      install_pkgs podman podman-compose buildah
      ok "Podman instalado. Use 'podman' e 'podman-compose' sem daemon permanente."
      info "Para usar a API compatível com Docker, habilite opcionalmente o socket do usuário: systemctl --user enable --now podman.socket"
      ;;
    *)
      warn "Opção inválida: $engine"
      return 1
      ;;
  esac
}

# ==========================================================
# ETAPAS — APLICATIVOS
# ==========================================================

step_flatpak() {
  install_pkgs flatpak
  sudo flatpak remote-add --system --if-not-exists \
    flathub https://flathub.org/repo/flathub.flatpakrepo \
    || die "Não foi possível registrar o remote Flathub no escopo system."
  flatpak remotes --system --columns=name | grep -Fxq 'flathub' \
    || die "O remote Flathub não está disponível para instalações system."

  # Ferramentas
  flatpak_install \
    com.visualstudio.code \
    org.gtk.Gtk3theme.Breeze \
    io.github.kolunmi.Bazaar \
    com.github.sdv43.whaler \
    com.github.tchx84.Flatseal \
    io.github.giantpinkrobots.flatsweep \
    it.mijorus.gearlever \
    io.github.zarestia_dev.rclone-manager

  aur_install linuxtoys-bin
}

step_apps() {
  local discord_client discord_app spotify_ok=0 spicetify_script tmp

  if flatpak_install \
    org.qbittorrent.qBittorrent \
    me.proton.Pass \
    com.protonvpn.www \
    md.obsidian.Obsidian \
    com.spotify.Client \
    org.vinegarhq.Sober; then
    spotify_ok=1
  else
    flatpak info --system com.spotify.Client >/dev/null 2>&1 && spotify_ok=1
  fi

  if (( spotify_ok )) && confirm "Instalar e configurar Spicetify para Spotify?" n; then
    if ! command -v spicetify >/dev/null 2>&1; then
      tmp=$(mktemp) || return 1
      if curl -fsSL --retry 2 --max-time 40 https://raw.githubusercontent.com/spicetify/cli/main/install.sh -o "$tmp"; then
        info "Executando instalador oficial do Spicetify como usuário (sem sudo)."
        bash "$tmp" || warn "Instalação do Spicetify falhou."
      else
        warn "Não foi possível baixar o instalador oficial do Spicetify."
      fi
      rm -f "$tmp"
    fi
    if command -v spicetify >/dev/null 2>&1; then
      local spotify_path="" prefs_path="$HOME/.var/app/com.spotify.Client/config/spotify/prefs"
      for spotify_path in \
        /var/lib/flatpak/app/com.spotify.Client/current/active/files/extra/share/spotify \
        "$HOME/.local/share/flatpak/app/com.spotify.Client/current/active/files/extra/share/spotify"; do
        [[ -d "$spotify_path" ]] && break
      done
      if [[ -d "$spotify_path" && -f "$prefs_path" ]]; then
        spicetify config spotify_path "$spotify_path" prefs_path "$prefs_path" || true
        spicetify backup apply || warn "Spicetify não conseguiu aplicar o tema. O Spotify Flatpak pode exigir permissões adicionais."
      else
        warn "Abra o Spotify pelo menos uma vez e depois configure o Spicetify: caminho ou preferências do Flatpak não encontrados."
      fi
    else
      warn "Spicetify não está no PATH; tente novamente após abrir outro terminal."
    fi
  fi

  info "Escolha seu cliente de Discord:"
  info "  vesktop - Vesktop (padrão)"
  info "  legcord - Legcord"
  info "  discord - Discord oficial"
  info "  equibop - Equibop (AUR: equibop-bin)"

  discord_client=$(choose \
    "Qual cliente de Discord deseja instalar?" \
    "vesktop/legcord/discord/equibop" \
    "vesktop")

  case "$discord_client" in
    vesktop) discord_app="dev.vencord.Vesktop" ;;
    legcord) discord_app="io.github.Legcord.Legcord" ;;
    discord) discord_app="com.discordapp.Discord" ;;
    equibop) discord_app="" ;;
    *)
      warn "Opção inválida: $discord_client"
      return 1
      ;;
  esac

  if [[ "$discord_client" == equibop ]]; then
    aur_install equibop-bin
    has_pkg equibop-bin || { warn "Equibop não foi instalado (verifique o AUR helper)."; return 1; }
  else
    flatpak_install "$discord_app"
  fi

  if [[ "$discord_client" == discord ]] && confirm "Deseja instalar BetterDiscord no Discord oficial?" n; then
    warn "BetterDiscord modifica o cliente Discord e pode contrariar os termos de uso."
    if flatpak info --system com.discordapp.Discord >/dev/null 2>&1; then
      warn "O Discord foi instalado via Flatpak. O BetterDiscord CLI pode não detectar ou modificar essa instalação isolada automaticamente."
      info "Instalação oficial: https://docs.betterdiscord.app/users/getting-started/installation"
      info "Para instalar automaticamente, utilize uma instalação nativa do Discord compatível com bdcli."
    elif command -v bdcli >/dev/null 2>&1; then
      bdcli install --channel stable || warn "Falha ao aplicar BetterDiscord."
    else
      info "BetterDiscord CLI oficial: npm install -g @betterdiscord/cli"
      info "Depois execute: bdcli install --channel stable"
      warn "Instalação automática ignorada: bdcli não encontrado."
    fi
  fi

  if confirm "Deseja configurar o mod Shelter para Discord?" n; then
    info "Guia oficial do Shelter: https://shelter.uwu.network/install"
    warn "O Shelter depende do cliente escolhido. Por segurança, consulte o método compatível no guia oficial; a instalação não será executada automaticamente."
  fi
}
step_gaming() {
  has_pkg lib32-mesa || warn "Instale o driver de vídeo 32 bits (etapa 'hardware') para Steam/Wine."
  install_pkgs steam retroarch wine winetricks wine-mono wine-gecko gamemode lib32-gamemode mangohud
}

step_browser() {
  if has_pkg firefox && confirm "Remover o Firefox (pacman)?" n; then
    sudo pacman -Rns firefox
  fi
  flatpak_install com.vivaldi.Vivaldi
}

# ==========================================================
# ETAPAS — MANUTENÇÃO
# ==========================================================

step_maintenance() {
  local incomplete=0
  info "Instalando ferramentas padrão de atualização: Topgrade e Arch-Update com tray..."
  if [[ -z "$(detect_aur_helper)" ]]; then
    warn "Nenhum helper AUR disponível. Instale yay/paru (etapa aur_helper) para obter os atualizadores."
  else
    if ! command -v topgrade >/dev/null 2>&1; then
      aur_install topgrade-bin || warn "Não foi possível instalar topgrade-bin."
    else
      ok "Topgrade já disponível."
    fi
    if ! command -v arch-update >/dev/null 2>&1; then
      # arch-update-bin inclui o aplicativo arch-update-tray; não é um pacote separado.
      aur_install arch-update-bin || warn "Não foi possível instalar arch-update-bin."
    else
      ok "Arch-Update já disponível."
    fi
  fi

  # Não registrar STEP_DONE enquanto faltar algum dos dois atualizadores padrão.
  if ! command -v topgrade >/dev/null 2>&1; then
    warn "Topgrade ainda ausente após a etapa de manutenção."
    incomplete=1
  fi

  if command -v arch-update >/dev/null 2>&1; then
    if command -v arch-update-tray >/dev/null 2>&1; then
      # Gera a entrada XDG Autostart; funcionará no próximo login gráfico.
      arch-update --tray --enable || warn "Não foi possível habilitar a bandeja automaticamente."
    else
      warn "O Arch-Update instalado não inclui arch-update-tray; verifique a variante do pacote."
      incomplete=1
    fi
    # Um timer --user pode não estar disponível numa instalação executada de TTY.
    arch-update --check --enable || warn "Verificação automática não ativada nesta sessão; use: arch-update --check --enable"
  else
    warn "Arch-Update ainda ausente após a etapa de manutenção."
    incomplete=1
  fi

  if command -v systemctl >/dev/null 2>&1; then
    if command -v paccache >/dev/null 2>&1; then
      sudo systemctl enable --now paccache.timer || warn "Não foi possível habilitar paccache.timer."
    else
      warn "paccache não está instalado; a limpeza programada foi ignorada."
    fi
    sudo systemctl enable --now fstrim.timer || warn "Não foi possível habilitar fstrim.timer."
  else
    warn "systemctl indisponível; timers de manutenção não configurados."
  fi
  info "Para atualizar manualmente: topgrade (ou a opção T da TUI)."
  if (( incomplete )); then
    warn "Manutenção incompleta: revise o log e as ferramentas AUR. Os timers são opcionais."
    return 1
  fi
}

step_firewall() {
  confirm "Deseja ativar firewall (ufw)? Isso altera a política de entrada da máquina." n || return 0
  install_pkgs ufw

  if command -v ufw >/dev/null 2>&1; then
    sudo ufw default deny incoming
    sudo ufw default allow outgoing

    # Por padrão, portas de descoberta/serviços ficam limitadas à LAN privada.
    # O usuário pode optar por regras abertas se realmente precisar delas.
    local lan
    lan=$(choose "CIDR da sua rede local para regras de compartilhamento (ex.: 192.168.1.0/24; vazio para não abrir portas)" "CIDR/vazio" "")
    if [[ -n "$lan" ]]; then
      if [[ "$lan" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}/([0-9]|[12][0-9]|3[0-2])$ ]]; then
        sudo ufw allow from "$lan" to any port 22000 proto tcp comment 'Syncthing LAN'
        sudo ufw allow from "$lan" to any port 22000 proto udp comment 'Syncthing LAN'
        sudo ufw allow from "$lan" to any port 21027 proto udp comment 'Syncthing discovery LAN'
        sudo ufw allow from "$lan" to any port 1714:1764 proto tcp comment 'KDE Connect LAN'
        sudo ufw allow from "$lan" to any port 1714:1764 proto udp comment 'KDE Connect LAN'
      else
        warn "CIDR inválido; regras de LAN não foram adicionadas."
      fi
    else
      info "Nenhuma regra de Syncthing/KDE Connect aberta; configure-as depois se necessário."
    fi

    # ZeroTier usa tráfego de saída; regra de entrada não é necessária em todas
    # as configurações, então fica explicitamente opcional.
    if confirm "Adicionar regra de entrada UDP 9993 para ZeroTier?" n; then
      sudo ufw allow 9993/udp comment 'ZeroTier'
    fi

    sudo ufw --force enable
    sudo systemctl enable --now ufw.service
    sudo ufw status verbose
  fi
}

step_cleanup() {
  local orphans=()
  mapfile -t orphans < <(pacman -Qtdq 2>/dev/null || true)

  if (( ${#orphans[@]} > 0 )); then
    printf 'Pacotes órfãos candidatos à remoção:\n'
    printf '  %s\n' "${orphans[@]}"
    if confirm "Remover estes pacotes órfãos? Revise a lista antes de confirmar." n; then
      sudo pacman -Rns "${orphans[@]}"
    fi
  else
    ok "Nenhum pacote órfão encontrado"
  fi

  local keep=3
  keep=$(choose "Quantas versões de cada pacote manter no cache do pacman?" "1/2/3/5" "3")
  [[ "$keep" =~ ^(1|2|3|5)$ ]] || { warn "Valor inválido; mantendo 3 versões."; keep=3; }
  if ! sudo paccache -rk"$keep"; then warn "Falha ao limpar o cache do pacman."; fi

  if command -v flatpak >/dev/null 2>&1; then
    if confirm "Remover runtimes e aplicativos Flatpak não utilizados?" n; then
      if (( ASSUME_YES )); then
        flatpak uninstall --system --unused -y || warn "Falha na limpeza de Flatpak (ver log)."
      else
        flatpak uninstall --system --unused || warn "Falha na limpeza de Flatpak (ver log)."
      fi
    fi
  fi
}

# ==========================================================
# BOBAGENS
# ==========================================================
step_bobagens() {
  # --------------------------------------------------------
  # TEMA GTK PARA FLATPAK
  # --------------------------------------------------------
  # Não impõe Breeze: preserva o tema escolhido pelo usuário (ex.: Sonic Silver).
  # Overrides de GTK_THEME são globais e podem conflitar com o tema do desktop.
  info "Mantendo as preferências de tema GTK/Flatpak do usuário."

  # --------------------------------------------------------
  # PYROCLEAR — SUBSTITUTO DO CLEAR
  # --------------------------------------------------------
  info "Configurando Pyroclear..."

  if command -v cargo >/dev/null 2>&1; then
    if cargo install pyroclear; then
      mkdir -p "$HOME/.config/fish/functions"

      cat > "$HOME/.config/fish/functions/clear.fish" <<'EOF'
function clear
    pyroclear $argv
end
EOF

      info "Função clear configurada para usar Pyroclear no Fish."
    else
      warn "Falha ao instalar Pyroclear pelo Cargo."
    fi
  else
    warn "Cargo não encontrado; Pyroclear não foi instalado."
  fi

  # --------------------------------------------------------
  # STARSHIP — GRUVBOX RAINBOW
  # --------------------------------------------------------
  info "Configurando preset Gruvbox Rainbow..."

  if command -v starship >/dev/null 2>&1; then
    mkdir -p "$HOME/.config"

    if [[ -f "$HOME/.config/starship.toml" ]]; then
      cp -n "$HOME/.config/starship.toml" \
        "$HOME/.config/starship.toml.bak"
    fi

    if starship preset gruvbox-rainbow \
      -o "$HOME/.config/starship.toml"; then
      info "Preset Gruvbox Rainbow configurado."
    else
      warn "Falha ao configurar o preset do Starship."
    fi
  else
    warn "Starship não encontrado; preset ignorado."
  fi

  # --------------------------------------------------------
  # FASTFETCH — CONFIGURAÇÃO DARFINOS
  # --------------------------------------------------------
  info "Baixando configuração do Fastfetch do DarfinOS..."

  local repo_url="https://github.com/AlanDarfin/DarfinOS/archive/refs/heads/main.zip"
  local temp_dir
  temp_dir="$(mktemp -d)"

  if command -v curl >/dev/null 2>&1 &&
     command -v unzip >/dev/null 2>&1; then

    if curl -fL "$repo_url" -o "$temp_dir/darfinos.zip" &&
       unzip -q "$temp_dir/darfinos.zip" -d "$temp_dir"; then

      local source_dir="$temp_dir/DarfinOS-main/Fastfetch"
      local target_dir="$HOME/.config/fastfetch"

      if [[ -d "$source_dir" ]]; then
        mkdir -p "$target_dir"

        # Preserva a configuração anterior.
        if [[ -d "$target_dir" ]] &&
           find "$target_dir" -mindepth 1 -maxdepth 1 \
             -print -quit | grep -q .; then
          cp -an "$target_dir" \
            "${target_dir}.backup-$(date +%Y%m%d-%H%M%S)"
        fi

        if cp -a "$source_dir/." "$target_dir/"; then
          info "Configuração do Fastfetch copiada do DarfinOS."
        else
          warn "Falha ao copiar os arquivos do Fastfetch."
        fi
      else
        warn "Pasta Fastfetch não encontrada no repositório."
      fi
    else
      warn "Falha ao baixar ou extrair o repositório DarfinOS."
    fi
  else
    warn "Instale curl e unzip para configurar o Fastfetch."
  fi

  rm -rf "$temp_dir"

  # --------------------------------------------------------
  # PACOTES ADICIONAIS OPCIONAIS
  # --------------------------------------------------------
  if confirm "Deseja instalar os pacotes adicionais?" n; then
    info "Instalando pacotes adicionais dos repositórios oficiais..."

    if ! install_pkgs \
        linux-zen-headers \
        imagemagick \
        chafa \
        sddm \
        sddm-kcm \
        kate \
        v4l2loopback-dkms \
        vlc; then
      warn "Falha na instalação de um ou mais pacotes oficiais."
    fi

    info "Instalando pacotes adicionais do AUR..."

    for pkg in stylepak-git; do
      aur_install "$pkg" || warn "Falha ao instalar $pkg; continuando."
    done
  else
    info "Instalação dos pacotes adicionais ignorada."
  fi
  # --------------------------------------------------------
  # OMNIROUTE — GATEWAY DE IA (INICIALIZAÇÃO MANUAL)
  # --------------------------------------------------------
  info "Configurando OmniRoute..."

  if command -v npm >/dev/null 2>&1; then
    if confirm "Deseja instalar/atualizar o OmniRoute?" n; then
      if npm install -g omniroute; then
        info "OmniRoute instalado."
        info "Para iniciar manualmente, execute: omniroute"
        info "Acesse o painel local em: http://localhost:20128"
        info "Para encerrar, use Ctrl+C no terminal."
      else
        warn "Falha ao instalar o OmniRoute."
      fi
    else
      info "Instalação do OmniRoute ignorada."
    fi
  else
    warn "npm não encontrado. Instale o Node.js/npm antes do OmniRoute."
  fi

}

# ==========================================================
# BEDROCK LINUX — INSTALAÇÃO INTERATIVA
# ==========================================================
step_bedrock() {
  info "Etapa opcional: Bedrock Linux"

  # Evita tentar converter uma instalação Bedrock já existente.
  if [[ -e /bedrock ]] || command -v brl >/dev/null 2>&1; then
    info "Bedrock Linux parece já estar instalado. Ignorando etapa."
    return 0
  fi

  # Dependências para baixar o instalador.
  if ! command -v curl >/dev/null 2>&1; then
    warn "curl não encontrado. Não foi possível baixar o Bedrock."
    return 0
  fi

  # Identifica a arquitetura.
  local arch
  case "$(uname -m)" in
    x86_64)
      arch="x86_64"
      ;;
    aarch64)
      arch="aarch64"
      ;;
    *)
      warn "Arquitetura não suportada automaticamente: $(uname -m)"
      return 0
      ;;
  esac

  # Manifesto oficial de versões.
  local manifest_url="https://raw.githubusercontent.com/bedrocklinux/bedrocklinux-userland/0.7/releases"
  local installer_url
  local temp_dir
  local installer

  temp_dir="$(mktemp -d)" || {
    warn "Não foi possível criar o diretório temporário."
    return 0
  }

  info "Consultando a versão mais recente do Bedrock Linux..."

  local manifest_file="$temp_dir/releases"

  if ! curl -fsSL "$manifest_url" -o "$manifest_file"; then
    warn "Falha ao baixar o manifesto do Bedrock Linux."
    rm -rf "$temp_dir"
    return 0
  fi

  installer_url="$(
    grep -E \
      "^https://github\.com/bedrocklinux/bedrocklinux-userland/releases/download/[^/]+/bedrock-linux-[^/]+-${arch}\.sh$" \
      "$manifest_file" |
      head -n 1
  )"

  if [[ -z "$installer_url" ]]; then
    warn "Não foi possível localizar um instalador para $arch."
    rm -rf "$temp_dir"
    return 0
  fi

  installer="$temp_dir/$(basename "$installer_url")"

  info "Instalador encontrado: $(basename "$installer_url")"
  info "Baixando o instalador oficial..."

  if ! curl -fL --retry 2 "$installer_url" -o "$installer"; then
    warn "Falha ao baixar o instalador do Bedrock Linux."
    rm -rf "$temp_dir"
    return 0
  fi

  info "Download concluído."
  warn "ATENÇÃO: --hijack transforma a instalação atual em Bedrock Linux."
  warn "Faça backup e verifique a compatibilidade antes de continuar."
  warn "O SonicDE e o XLibre podem exigir ajustes após a conversão."

  if confirm "Deseja executar o instalador do Bedrock Linux agora?" n; then
    info "Iniciando o instalador do Bedrock Linux..."

    if sudo sh "$installer" --hijack; then
      info "O instalador do Bedrock Linux terminou."
      warn "Siga as instruções exibidas pelo instalador."
      warn "A documentação oficial exige reiniciar para concluir a instalação."
    else
      warn "O instalador terminou com erro ou foi interrompido."
    fi
  else
    info "Instalação do Bedrock ignorada. Continuando o script."
  fi

  rm -rf "$temp_dir"
}

# ==========================================================
# EXTRAS DO TERMINAL — SUDO
# ==========================================================
step_terminal_extras() {
  info "Instalando ferramentas de terminal: tmux e ranger..."
  install_pkgs tmux ranger

  if confirm "Deseja instalar o OpenCode (opencode-bin via AUR)?" n; then
    aur_install opencode-bin
  fi

  local -a sudo_options=()
  local sudoers_file="/etc/sudoers.d/90-darfinos-terminal"
  local candidate="$TMP_DIR/darfinos-terminal-sudoers"
  local backup="$TMP_DIR/darfinos-terminal-sudoers.previous"

  if confirm "Mostrar asteriscos ao digitar a senha no sudo (pwfeedback)?" n; then
    sudo_options+=(pwfeedback)
  fi
  if confirm "Ativar mensagens engraçadas para senhas incorretas (insults)?" n; then
    sudo_options+=(insults)
  fi

  if (( ${#sudo_options[@]} == 0 )); then
    info "Nenhuma personalização do sudo selecionada."
    return 0
  fi

  printf 'Defaults %s\n' "$(IFS=,; echo "${sudo_options[*]}")" > "$candidate"
  chmod 0440 "$candidate"

  if ! sudo visudo -cf "$candidate"; then
    warn "Configuração do sudo inválida; nada foi alterado."
    return 1
  fi

  # Registra falhas preexistentes (por exemplo, sudoers do Bedrock).
  local global_sudoers_ok=1
  if ! sudo visudo -c; then
    global_sudoers_ok=0
    warn "A validação global do sudoers já falhava antes desta alteração."
    warn "A configuração do DarfinOS será validada separadamente."
  fi

  if sudo test -e "$sudoers_file"; then
    sudo cp -p "$sudoers_file" "$backup" || return 1
  fi

  if ! sudo install -o root -g root -m 0440 "$candidate" "$sudoers_file"; then
    warn "Falha ao instalar a configuração do sudo."
    return 1
  fi

  if (( global_sudoers_ok )) && ! sudo visudo -c; then
    warn "A configuração global passou a falhar após a alteração; revertendo."
    if [[ -f "$backup" ]]; then
      sudo install -o root -g root -m 0440 "$backup" "$sudoers_file"
    else
      sudo rm -f -- "$sudoers_file"
    fi
    return 1
  fi

  if (( ! global_sudoers_ok )); then
    warn "Permanece uma falha global preexistente no sudoers; revise-a separadamente."
  fi
  ok "Personalizações do sudo ativadas: ${sudo_options[*]}"
}

# ==========================================================
# EXECUÇÃO
# ==========================================================
for s in "${STEPS[@]}"; do
  run_step "$s"
done

echo
info "Resumo"
if (( ${#FAILED_STEPS[@]} )); then
  warn "Etapas com erro: ${FAILED_STEPS[*]}"
fi
if (( ${#SKIPPED_STEPS[@]} )); then
  warn "Etapas ignoradas por dependências com falha: ${SKIPPED_STEPS[*]}"
fi
if (( ! ${#FAILED_STEPS[@]} && ! ${#SKIPPED_STEPS[@]} )); then
  ok "Todas as etapas selecionadas foram concluídas."
fi
info "Log completo: $LOG_FILE"

if step_enabled xlibre || step_enabled sonicde; then
  info "Próximos passos: reinicie, escolha a sessão X11 do SonicDE e rode: xdpyinfo | grep vendor"
fi

for s in "${STEPS[@]}"; do
  if [[ "$s" != lab_* ]] && step_enabled "$s"; then
    if confirm "Reiniciar agora?" n; then
      sudo reboot
    fi
    break
  fi
done

# Uma execução parcial com falhas não deve ser reportada como sucesso ao CI/TUI.
if (( ${#FAILED_STEPS[@]} || ${#SKIPPED_STEPS[@]} )); then
  exit 1
fi
