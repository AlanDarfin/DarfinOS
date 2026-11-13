# Security, risk levels and recovery

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](pt-BR/SEGURANCA.md)**

DarfinOS is a post-install configuration tool. Selected stages can modify packages, repositories, services and the desktop stack, so **review the exact source and make a backup before using it**.

## Before installation

1. Keep a tested backup of important files and an independent way to recover your system.
2. Start with `python3 DarfinOSInstallScript-TUI.py --doctor`, `--check-modules` and `--plan --preset minimal`; those do not install packages.
3. Run the main installer as a **regular user with sudo**, not as root.
4. Use a TTY and a disposable VM when changing SonicDE, XLibre, a display manager or low-level boot components.
5. Do not run the broad `--all` or `full` selections without inspecting the high-risk Bedrock and cleanup stages.

## Installation controls

- The Bash installer refuses to install anything if no `--only`, `--skip` or `--all` selection is supplied.
- Pacman uses `--needed`; potentially destructive transactions still require review.
- `--check-modules` uses read-only package and HOME-file checks. It skips only verified complete stages. Partial and unknown stages are not falsely marked complete.
- `--reinstall` re-executes a stage but does not disable overwrite protection or confirmation.
- Advanced Labs stages require explicit selection and individual confirmation. They reject unattended `-y`.
- Chicago95 downloads selected files from [grassmunk/Chicago95](https://github.com/grassmunk/Chicago95) and copies themes/icons to HOME after confirmation. It does not execute the project's remote `installer.py`, overwrite existing folders or activate a new session.

## Backups are limited

The Control Center's ZIP backup contains a specifically allowlisted subset of user configuration under HOME. It can contain sensitive personal data. The restore preview does **not** change files until explicit apply; overwrite requires an extra choice.

This feature cannot restore packages, `/etc`, arbitrary HOME files, service state, XLibre, Bedrock or the bootloader. A full-system rollback requires your own filesystem snapshot or backup strategy.

## External projects

AUR PKGBUILDs and upstream binaries can change independently of DarfinOS. Inspect sources and dependencies. Do not execute destructive declarative synchronization with Decman or Metapac without a reviewed plan.

yserver, xomposite, Wayback, Trinity and Booster remain manual/research integrations because they can affect the desktop, compositor, trust chain or boot process.

**No stable release or ISO is advertised** until the graphical VM/recovery checklist is completed. Automated Python/Bash tests and an Arch container smoke check are not substitutes.

[Module checks](MODULOS.md) · [Labs](LABS.md) · [VM checklist](VALIDACAO_VM.md)
