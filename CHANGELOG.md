# DarfinOS development history

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](CHANGELOG.pt-BR.md)**

DarfinOS is under continuous development. These notes describe changes implemented in source and reviewed by automated CI; they do not imply complete compatibility with every Arch system, desktop or hardware configuration.

## In development · i3 Notebook desktop (November 2026)

- Refined graphite/gold Notebook theme inspired by iamabhas’s dotfiles, with focused workspace highlighting, consistent window borders, Rofi, Dunst and a branded wallpaper.
- Notebook Labs installs the official Bibata Modern Ice v2.0.7 cursor with a pinned checksum and preserves existing user themes; cursor reload updates the profile’s own XSETTINGS provider.
- Wallpaper selection includes restoring the DarfinOS default. Confirmed 720p uses a 1:1 pixel scale, restores the previous transform on rejection/timeout, and explains unsupported internal panels.

## In development · English website and development releases (November 2026)

- English is the default language for the website, README and core documentation, with full Portuguese routes, documents and a persistent manual language selector.
- The website detects Portuguese browser preferences and serves dedicated `/pt-br/` pages with localized navigation and metadata.
- The new Downloads page always provides a main-branch ZIP instead of an empty releases link, and lists actual available GitHub prerelease artifacts when published.
- GitHub Actions can publish SHA-256 checked prerelease candidates only after the offline Python/Bash suite and Arch smoke pass for the exact same commit. **No stable release or ISO is implied.**

## In development · Module checks and Chicago95 (November 2026)

- Read-only `--check-modules` reports complete, partial, missing and unknown modules before installation.
- Only verified complete stages are skipped; `STEP_ALREADY` and `ALREADY` are recognized by TUI history and resume logic.
- `--reinstall` on Bash and the X key in TUI re-execute selected stages without bypassing confirmation or pacman `--needed`.
- Optional Xfce session, Chicago95 GTK/icon assets copied with safeguards, and the `retro` preset.
- 41 stages, six presets and 13 independent Labs projects.

## In development · DarfinOS Labs and i3 (November 2026)

- An upstream-linked catalog of 13 independent projects with risk levels and optional installation modes, accessible via `--labs`, `--lab-info` and TUI key L.
- i3 X11 WM as a separate desktop option alongside SonicDE/XLibre.
- Individually confirmed AUR modules for NsCDE, JuNest, Decman and Metapac, without automatically running their system management commands.
- Documentation-only research into Conty, nix-portable, Trinity, yserver, xomposite, Wayback and Booster.

## In development · Control Center and safe installation (November 2026)

- Module dependencies, package audit previews, status/maintenance diagnostics, a persistent run journal and safe recovery selection.
- JSON profiles with import/export and diff.
- Allowlisted HOME configuration archives with SHA-256 integrity, preview-before-restore and confirmation on overwrite.
- Installer now requires explicit `--only`, `--skip` or `--all` instead of executing everything by default.
- Arch container smoke tests, Python/Bash offline tests and a manual candidate packaging workflow.
- Important limitations and a graphical VM validation checklist documented separately.

## Background

The project started as a personal Arch Linux post-install customization collection, evolving into a modular installer and terminal interface. The design includes optional SonicDE and XLibre, maintenance utilities, gaming tools and integrations with independent open-source projects.

[Documentation](docs/README.md) · [Testing](docs/TESTES.md) · [Download and release policy](docs/LANCAMENTO.md)
