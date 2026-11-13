# DarfinOS Control Center · terminal UI

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](pt-BR/TUI_V5.md)**

The Python `curses` terminal UI is an optional front end for the Bash installer. It can inspect 64 stages, handle seven presets, show dependency information, browse 29 Labs entries, record installation events and present a package audit. Opening the TUI does not begin installation.

```bash
python3 DarfinOSInstallScript-TUI.py --doctor
python3 DarfinOSInstallScript-TUI.py --local
python3 DarfinOSInstallScript-TUI.py --local --dry-run
python3 DarfinOSInstallScript-TUI.py --plan --preset minimal
python3 DarfinOSInstallScript-TUI.py --plan --preset retro
```

## Essential keys

| Key | Action |
| --- | --- |
| Arrow keys / j / k | Move between stages |
| Space | Select or deselect the current stage |
| / | Search stages by name and description |
| R or Enter | Review the plan before execution |
| D | Add required dependencies to the selection |
| O | Explore available presets |
| I | Refresh installed-module checks |
| X | Toggle explicit stage re-execution |
| L | Browse the Labs catalog and official upstream URLs |
| V | Show a **partial** package audit |
| C | Open Control Center system status |
| P | Profile management |
| M | Maintenance tools |
| Z | Recovery from an earlier run journal |
| Q | Quit |

The UI distinguishes **DONE** (executed now), **ALREADY** (a verified complete stage was skipped), **FAIL** (an execution failed) and **SKIP** (not selected or blocked).

The **X** toggle forwards `--reinstall` to Bash. It does not disable pacman's `--needed`, third-party confirmation requirements or safeguards against overwriting user files.

## Safe planning features

- `--list-presets`: list minimal, desktop, i3, retro, gaming and full.
- `--manifest`: output static JSON describing stage names, dependencies and some literal packages.
- `--audit --preset gaming`: compare a partial expected package inventory to local packages without installing anything.
- `--compare-presets minimal gaming`: declarative selection differences, not a real system migration.
- `--check-modules`: conservative installed/partial/missing/unknown status in JSON.
- `--labs` and `--lab-info NOME`: read-only catalog.
- `--status-json`: read-only system status.

The `full` preset contains high-risk conventional stages, including Bedrock, but deliberately excludes optional `lab_*` stages.

## Logs, resume and permissions

The TUI keeps a local run journal and event log. A stage marked `ALREADY` is considered successful for resume logic. A partially executed stage is **not** rolled back by the TUI: review the log and configuration before retrying.

A new install performs actions through the underlying Bash script with `sudo` when required. Read-only operations should not ask for root. Login/graphics changes are best tested from a TTY and in a disposable VM before use on a primary machine.

[Documentation](README.md) · [Module checks](MODULOS.md) · [Tests](TESTES.md)

**W** · [Theme Workshop / Oficina de Temas](CUSTOMIZATION.md).
