#!/usr/bin/env bash
# ==========================================================
# Pós-instalação Arch Linux — SonicDE + XLibre (v4.2)
# ==========================================================
# Uso:
#   ./PostInstall.sh                       # interativo, roda tudo
#   ./PostInstall.sh -y                    # automatiza perguntas do script; pacman segue interativo
#   ./PostInstall.sh --only docker,shells  # roda só estas etapas
#   ./PostInstall.sh --skip gaming,hamachi # roda tudo, menos estas
#   ./PostInstall.sh --list                # lista as etapas
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
  # Shell e desenvolvimento
  cli_tools dev_tools pkg_managers shells git_setup
  # Rede e serviços
  zerotier hamachi syncthing docker
  # Aplicativos
  flatpak apps gaming browser
  # Manutenção
  maintenance firewall cleanup bobagens bedrock terminal_extras
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
  [cli_tools]="Ferramentas de terminal (fzf, eza, yazi, starship...)"
  [dev_tools]="Desenvolvimento (neovim, gcc, clang, rust, go, node...)"
  [pkg_managers]="pip, pipx, cargo, npm e go: instalação, PATH e config"
  [shells]="fish + zsh, starship/zoxide/fzf e shell padrão"
  [git_setup]="Configuração do git e chave SSH"
  [zerotier]="ZeroTier"
  [hamachi]="Hamachi"
  [syncthing]="Syncthing"
  [docker]="Contêineres (Docker ou Podman)"
  [flatpak]="Flatpak + Flathub + ferramentas"
  [apps]="Aplicativos (Flatpak/AUR, Discord, Shelter e Spicetify)"
  [gaming]="Steam, Wine, GameMode, MangoHud"
  [browser]="Navegador"
  [maintenance]="Timers de manutenção (paccache, fstrim)"
  [firewall]="Firewall (ufw)"
  [cleanup]="Limpeza de órfãos e caches"
  [bobagens]="Coisas extras ai"
  [bedrock]="Instalação do Bedrock Linux"
  [terminal_extras]="Extras do terminal (tmux, ranger, OpenCode e sudo)"
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

usage() { sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; }

# ----------------------------------------------------------
# Opções
# ----------------------------------------------------------
ASSUME_YES=0
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
)

list_steps() {
  local s
  for s in "${STEPS[@]}"; do
    printf '  %-16s %s\n' "$s" "${STEP_DESC[$s]:-}"
  done
}

validate_steps() {
  local item
  local -a items
  IFS=',' read -ra items <<<"$1"
  for item in "${items[@]}"; do
    [[ -z "$item" ]] && continue
    [[ " ${STEPS[*]} " == *" $item "* ]] || die "Etapa desconhecida: '$item' (veja --list)"
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes)  ASSUME_YES=1 ;;
    --only)    [[ -n "${2:-}" ]] || die "--only exige uma lista"; ONLY="$2"; validate_steps "$ONLY"; shift ;;
    --skip)    [[ -n "${2:-}" ]] || die "--skip exige uma lista"; SKIP="$2"; validate_steps "$SKIP"; shift ;;
    --list)    list_steps; exit 0 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Opção desconhecida: $1 (use --help)" ;;
  esac
  shift
done

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
    [[ ",$SKIP," != *",$name,"* ]]
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
      git clone "https://aur.archlinux.org/${choice}-bin.git" "$TMP_DIR/$choice"
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
  # Limpa cache do pacman semanalmente (mantém 3 versões)
  sudo systemctl enable --now paccache.timer
  # TRIM semanal para SSD
  sudo systemctl enable --now fstrim.timer
  # Atualização de Flatpaks fica a cargo do Discover/Bazaar
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
  flatpak override --user --env=GTK_THEME=Breeze

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

    for pkg in arch-update stylepak-git topgrade-bin; do
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

if confirm "Reiniciar agora?" n; then
  sudo reboot
fi
