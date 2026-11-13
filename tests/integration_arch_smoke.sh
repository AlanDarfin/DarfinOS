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
python DarfinOSInstallScript-TUI.py --doctor-json | python -c 'import json,sys; x=json.load(sys.stdin); assert x["ready"] and x["steps"] == 64 and x["labs"] == 29, x'
python DarfinOSInstallScript-TUI.py --manifest | python -c 'import json,sys; x=json.load(sys.stdin); assert x["accuracy"] == "partial_static" and len(x["steps"]) == 64'
python DarfinOSInstallScript-TUI.py --plan --preset minimal >/dev/null
python DarfinOSInstallScript-TUI.py --plan --preset i3 >/dev/null
python DarfinOSInstallScript-TUI.py --plan --preset retro >/dev/null
python DarfinOSInstallScript-TUI.py --plan --preset workstation | grep -F lab_windowmaker >/dev/null
python darfinos_control.py styles | grep -F sonicde-kvantum >/dev/null
python DarfinOSInstallScript-TUI.py --check-modules | python -c 'import json,sys; x=json.load(sys.stdin); assert len(x["modules"])==64'
python DarfinOSInstallScript-TUI.py --labs | python -c 'import json,sys; p=json.load(sys.stdin)["projects"]; assert len(p)==29 and all(x["url"].startswith("https://") and x["step"] for x in p)'
bash DarfinOSInstallScript.sh --labs | grep -F 'https://i3wm.org/' >/dev/null
python DarfinOSInstallScript-TUI.py --compare-presets minimal gaming | python -c 'import json,sys; x=json.load(sys.stdin); assert "gaming" in x["add"] and "xlibre" in x["review_required"]'
python DarfinOSInstallScript-TUI.py --audit --preset minimal | python -c 'import json,sys; x=json.load(sys.stdin); assert x["accuracy"] == "partial_static" and x["selected_steps"] > 0'
python DarfinOSInstallScript-TUI.py --status-json | python -c 'import json,sys; x=json.load(sys.stdin); assert x["arch"] and x["tools"]["pacman"], x'
python darfinos_control.py status --json | python -c 'import json,sys; x=json.load(sys.stdin); assert x["arch"] and x["tools"]["pacman"], x'
echo "Smoke de Arch sem alterações no host: OK"
