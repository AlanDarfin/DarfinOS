# Static manifest and installer presets

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](pt-BR/MANIFESTO_PRESETS.md)**

DarfinOS uses a versioned list of **48 Bash stages**, with names, descriptions and known dependencies. The Python TUI parses that structure for inspection and offers six curated selections.

```bash
python3 DarfinOSInstallScript-TUI.py --manifest
python3 DarfinOSInstallScript-TUI.py --list-presets
python3 DarfinOSInstallScript-TUI.py --plan --preset gaming
python3 DarfinOSInstallScript-TUI.py --compare-presets minimal gaming
```

## Presets

| Preset | Intent | Special considerations |
| --- | --- | --- |
| `minimal` | Base Arch customization, core tools and maintenance | Default safe starting point |
| `desktop` | SonicDE + XLibre and desktop utilities | Display stack and login changes require care |
| `i3` | i3 tiling WM + XLibre | Does not install SonicDE |
| `retro` | Xfce and Chicago95 | Copies upstream GTK/icons into HOME with explicit confirmation; does not activate theme |
| `gaming` | SonicDE + games tools | Compatibility depends on GPU and package availability |
| `full` | All conventional stages | Includes high-risk Bedrock; deliberately excludes all `lab_*` |

The manifest is a **partial static inventory**, not an exact simulation of what every step will do. Conditional logic, runtime choices, package groups and services may not be fully reflected. The preset comparison shows differences between **selected module names**, not packages installed on the current machine.

The `maintenance` stage depends on `aur_helper`. The ordinary presets that include maintenance select the helper in advance. Labs AUR modules also require explicit opt-in; `--all`, `--skip`, the `full` preset and TUI select-all do not add them silently.

Before executing, use [module verification](MODULOS.md) to distinguish fully present modules from partial or unknown ones.

[Documentation index](README.md) · [VM safety checklist](VALIDACAO_VM.md)
