#!/usr/bin/env bash
# Rodar somente em container/VM Arch descartável. Nenhum pacote de usuário é instalado.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -f /etc/arch-release ]] || { echo "Requer Arch Linux ou derivado compatível" >&2; exit 1; }
command -v pacman >/dev/null || exit 1
bash -n DarfinOSInstallScript.sh
python -m py_compile DarfinOSInstallScript-TUI.py darfinos_control.py
python -m unittest discover -s tests -v
bash DarfinOSInstallScript.sh --preflight
bash DarfinOSInstallScript.sh --list >/tmp/darfinos-steps.txt
python DarfinOSInstallScript-TUI.py --doctor-json | python -c 'import json,sys; x=json.load(sys.stdin); assert x["ready"] and x["steps"] == 34, x'
python DarfinOSInstallScript-TUI.py --manifest | python -c 'import json,sys; x=json.load(sys.stdin); assert x["accuracy"] == "partial_static" and len(x["steps"]) == 34'
python DarfinOSInstallScript-TUI.py --plan --preset minimal >/dev/null
python DarfinOSInstallScript-TUI.py --compare-presets minimal gaming | python -c 'import json,sys; x=json.load(sys.stdin); assert "gaming" in x["add"] and "xlibre" in x["review_required"]'
python DarfinOSInstallScript-TUI.py --audit --preset minimal | python -c 'import json,sys; x=json.load(sys.stdin); assert x["accuracy"] == "partial_static" and x["selected_steps"] > 0'
python DarfinOSInstallScript-TUI.py --status-json | python -c 'import json,sys; x=json.load(sys.stdin); assert x["arch"] and x["tools"]["pacman"], x'
python darfinos_control.py status --json | python -c 'import json,sys; x=json.load(sys.stdin); assert x["arch"] and x["tools"]["pacman"], x'
echo "Smoke de Arch sem alterações no host: OK"
