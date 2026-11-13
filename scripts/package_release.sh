#!/usr/bin/env bash
# Empacota somente arquivos rastreados pela revisão atual. Não publica releases.
set -euo pipefail
cd "$(dirname "$0")/.."
version="${1:-}"
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-rc[0-9]+)?$ ]]; then
  echo "Uso: bash scripts/package_release.sh 0.1.0-rc1" >&2
  exit 2
fi
command -v git >/dev/null || { echo "git ausente" >&2; exit 1; }
mkdir -p dist
file="dist/darfinos-${version}.tar.gz"
if [[ -e "$file" ]]; then
  echo "Arquivo existente: $file" >&2
  exit 1
fi
git archive --format=tar --prefix="darfinos-${version}/" HEAD | gzip -n -9 > "$file"
[[ -s "$file" ]] || { rm -f "$file"; echo "Pacote vazio" >&2; exit 1; }
(cd dist && sha256sum "darfinos-${version}.tar.gz" > "darfinos-${version}.tar.gz.sha256")
# Read the full table of contents once: early-exiting grep + pipefail could
# otherwise make a perfectly valid package fail with SIGPIPE.
listing="$(tar -tzf "$file")" || { echo "Pacote inválido: $file" >&2; exit 1; }
grep -Fxq "darfinos-${version}/darfinos_control.py" <<<"$listing" || {
  echo "Pacote sem darfinos_control.py" >&2
  exit 1
}
grep -Fxq "darfinos-${version}/DarfinOSInstallScript.sh" <<<"$listing" || {
  echo "Pacote sem instalador Bash" >&2
  exit 1
}
printf 'Pacote: %s\nSHA256: %s\n' "$file" "$file.sha256"
