<div align="center">

# ⚡ DarfinOS

### A Linux distribution with opinions that aren't yours.

**Your Arch, my rules.**

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](README.pt-BR.md)**

![Arch Linux](https://img.shields.io/badge/BASE-Arch_Linux-FFCB2E?style=for-the-badge&labelColor=171717&logo=archlinux&logoColor=white)
![SonicDE](https://img.shields.io/badge/DESKTOP-SonicDE-FFCB2E?style=for-the-badge&labelColor=171717)
![XLibre](https://img.shields.io/badge/DISPLAY-XLibre-FFCB2E?style=for-the-badge&labelColor=171717)
![Bash + Python](https://img.shields.io/badge/TOOLS-Bash_%2B_Python-FFCB2E?style=for-the-badge&labelColor=171717)

**[🌐 Website](https://darfinos.vercel.app/) · [⚡ Control Center](https://darfinos.vercel.app/controle/) · [📖 Documentation](docs/README.md) · [⬇️ Downloads](https://darfinos.vercel.app/downloads/) · [🧪 CI](https://github.com/AlanDarfin/DarfinOS/actions)**

</div>

---

## What is DarfinOS?

DarfinOS is my opinionated **Arch Linux post-installation and customization toolkit**. It is not a new Linux distribution, ISO or replacement for Arch. It combines modular installation scripts, a terminal interface and optional integrations into one reproducible, inspectable setup.

Think of it as a very personal collection of Linux preferences. My Arch, my ideas, my rules. The installer asks which modules to run instead of assuming you want everything installed. The original technologies are independent projects, and each deserves proper credit.

DarfinOS is still in development. Automated tests cover Python/Bash behavior and a safe Arch container, but **full graphical installation, reboot and recovery remain unverified in a disposable VM**. There is no stable release yet.

## Language / Idioma

**English is the default documentation language.** Read the complete original [Brazilian Portuguese README](README.pt-BR.md) or the [Portuguese documentation index](docs/pt-BR/README.md).

GitHub Markdown cannot detect a reader's browser locale or automatically render a different README. The [website](https://darfinos.vercel.app/) does detect Portuguese browser language and offers a manual EN/PT-BR switch.

## What you can customize

DarfinOS currently describes **48 modular stages**, **six presets**, and **13 independent projects in Labs**.

| Area | Modules and examples |
| --- | --- |
| System and repositories | pacman configuration, mirrors, CachyOS, XLibre, SonicDE, Chaotic-AUR, system upgrades |
| Desktop and window managers | SonicDE, XLibre, alternative i3 and Xfce sessions, Bluetooth and extras |
| Core and developer tools | Base, yay/paru, fonts, hardware, shells, Git, compilers, language package managers |
| Network and services | ZeroTier, Hamachi, Syncthing, Docker/Podman |
| Applications and games | Flatpak, selected desktop apps, browser, Steam, Wine, GameMode and MangoHud |
| Maintenance | Topgrade, Arch-Update/tray, service timers, firewall, cleanup and optional advanced steps |
| DarfinOS Labs | 13 projects with optional installer stages and original project links |

Features are conditional. A module is not guaranteed to install every named program on all hardware or configurations.

### My desktop choices

- [SonicDE](https://sonicde.org/) is a KDE-derived desktop focused on X11, used as a primary design reference.
- [XLibre](https://xlibre.net/) continues the X11 server family and can require high-impact package replacements.
- [i3](https://i3wm.org/) is an optional keyboard-driven X11 tiling window manager.
- [Xfce](https://www.xfce.org/) and [Chicago95](https://github.com/grassmunk/Chicago95) power the optional Retro preset. The installer copies themes, icons, cursors and fonts to the user's HOME but does not apply the theme automatically.
- [Bedrock Linux](https://bedrocklinux.org/) is an advanced, high-risk cross-distribution experiment, not a normal prerequisite.

These projects are independent and are not owned, maintained or endorsed by DarfinOS.

## Getting started

**Requirements:** Arch Linux or a compatible pacman-based system, a regular user account with `sudo`, and Python 3 (including `curses`) for the text UI. Review the source before running it.

```bash
git clone https://github.com/AlanDarfin/DarfinOS.git
cd DarfinOS

# Read-only structure and system checks
python3 DarfinOSInstallScript-TUI.py --doctor
bash DarfinOSInstallScript.sh --preflight

# Launch the local terminal interface
python3 DarfinOSInstallScript-TUI.py --local
```

Opening the TUI **does not immediately install anything**. Choose a preset or select modules, inspect dependencies and review the plan. Use a TTY and a recovery route for display-server changes.

### Inspect, plan and skip installed modules

```bash
# List every stage
bash DarfinOSInstallScript.sh --list

# Show conservative module status, no sudo
bash DarfinOSInstallScript.sh --check-modules
python3 DarfinOSInstallScript-TUI.py --check-modules

# Explore a selection without installing it
python3 DarfinOSInstallScript-TUI.py --plan --preset minimal
python3 DarfinOSInstallScript-TUI.py --plan --preset i3
python3 DarfinOSInstallScript-TUI.py --plan --preset retro

# Audit some expected packages (not a full proof of installation)
python3 DarfinOSInstallScript-TUI.py --audit --preset gaming
```

The module checker reports **installed**, **partial**, **missing** or **unknown**. Only stages with sufficient proof of completion are skipped automatically. A single SonicDE or Docker package does not prove all its services are configured.

In the TUI, press **I** to inspect again and **X** to toggle explicit re-execution. On the CLI, use `--reinstall`:

```bash
# Install only i3, if not already complete
bash DarfinOSInstallScript.sh --only i3

# Rerun the stage even if its module check says installed
bash DarfinOSInstallScript.sh --only i3 --reinstall
```

The installer **requires** an explicit `--only`, `--skip` or `--all`. Running Bash with no selection shows help and exits instead of installing everything. `--all` includes risky conventional modules such as Bedrock, but intentionally excludes Labs stages. Reinstalling does not disable `pacman --needed` or overwrite safeguards.

See [module verification details](docs/MODULOS.md) and the [TUI guide](docs/TUI_V5.md).

### Six built-in presets

| Preset | Purpose |
| --- | --- |
| `minimal` | Foundation and essential tooling |
| `desktop` | SonicDE and XLibre desktop |
| `i3` | Alternative i3 + XLibre session without SonicDE |
| `retro` | Xfce plus optional Chicago95 themes, icons, cursors and fonts |
| `gaming` | Desktop and gaming utilities |
| `full` | All conventional stages, including potentially destructive ones, excluding opt-in Labs stages |

Use `python3 DarfinOSInstallScript-TUI.py --list-presets` to list them or `--compare-presets minimal gaming` to inspect the difference.

### DarfinOS Labs

Labs catalogs 13 independent projects. Bash `--labs` and TUI `--labs` only list them. The **L** key opens the catalog in the terminal UI. All 13 projects can be installed. The advanced Labs stages require confirmation and reject `-y`. Trinity installs the signed repository and `tde-meta` without switching your login manager.

Full descriptions, integration limits and **original upstream links**: [DarfinOS Labs](docs/LABS.md) and the [Labs website](https://darfinos.vercel.app/labs/).

### Profiles, backups and maintenance

The Control Center can export/import/diff JSON profiles, inspect local maintenance infrastructure and back up an allowlisted set of configuration files inside HOME. This **is not a full-system snapshot**. It cannot restore pacman packages, `/etc`, display-manager settings or boot state.

```bash
python3 darfinos_control.py maintenance --json
python3 darfinos_control.py backup ~/darfinos-config.zip
python3 darfinos_control.py restore ~/darfinos-config.zip
```

The restore command above is a read-only preview until `--apply` is explicitly passed.

## Downloads and versioned releases

- **[Download current main source ZIP](https://github.com/AlanDarfin/DarfinOS/archive/refs/heads/main.zip)**: always points to the current development source, not a stable release.
- **[Development candidates (GitHub prereleases)](https://github.com/AlanDarfin/DarfinOS/releases)**: versioned `.tar.gz` archives with SHA-256 checksums. They are generated only after the offline tests and Arch container smoke pass on the same commit.
- **[Downloads and status on the website](https://darfinos.vercel.app/downloads/)**: distinguishes the source ZIP, prerelease packages and missing stable validation.

The release workflow never marks a candidate as stable or supplies an ISO. Stable releases remain gated on full manual VM/recovery checks.

## Documentation

- [English documentation index](docs/README.md)
- [Module verification and reinstallation](docs/MODULOS.md)
- [TUI / Control Center](docs/TUI_V5.md)
- [Profiles and presets](docs/MANIFESTO_PRESETS.md)
- [Labs and upstream credits](docs/LABS.md)
- [Security and recovery](docs/SEGURANCA.md)
- [VM acceptance checklist](docs/VALIDACAO_VM.md)
- [Testing and quality](docs/TESTES.md)
- [Português do Brasil](docs/pt-BR/README.md)

## Contributing and support

DarfinOS is community-visible, personal in design and openly documented. Issues and pull requests are welcome for improvements, documentation translations, safety checks, UI issues and upstream integration corrections.

See [CONTRIBUTING.md](CONTRIBUTING.md), [issues](https://github.com/AlanDarfin/DarfinOS/issues) and the [website](https://darfinos.vercel.app/).

---

*Your Arch, my rules. The decision to run each command is still yours.*
