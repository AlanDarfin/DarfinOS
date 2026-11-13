# Contributing to DarfinOS

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](CONTRIBUTING.pt-BR.md)**

Thanks for helping improve this opinionated Arch Linux post-install toolkit.

## Suggested workflow

1. Open an issue describing the current behavior, the expected result and reproduction steps.
2. Create a focused branch. Avoid mixing UI refactoring, theming and destructive system changes in the same pull request.
3. Run local offline checks:

   ```bash
   bash -n DarfinOSInstallScript.sh
   python3 -m py_compile DarfinOSInstallScript-TUI.py darfinos_control.py
   python3 -m unittest discover -s tests -v
   python3 DarfinOSInstallScript-TUI.py --doctor
   ```
4. Describe risks, new external dependencies, source URLs, how a module behaves when already installed, and interactions with `--only`, `--reinstall` and `-y`.
5. For user-facing website or documentation changes, update **both English and Brazilian Portuguese** copies.

## Engineering principles

- Prefer safe, repeatable operations and explicit consent for important changes.
- Never silently run remote `curl | bash`, leak credentials or check secrets into the repository.
- Preserve the standalone Bash installer; the TUI is a convenience, not a mandatory dependency.
- Preserve the `STEPS`, `STEP_DESC`, `STEP_DEPS`, read-only checker and structured events used by the UI.
- Tests must not require `sudo`, install packages or mutate contributors' machines.
- Add tests for both newly introduced behavior and opt-out/cancellation paths.
- Keep upstream credits and original source links for all external Linux projects.
- Never claim a stable release or full graphical VM validation unless the acceptance checks have been performed.

[Security](docs/SEGURANCA.md) · [Tests](docs/TESTES.md) · [Releases](docs/LANCAMENTO.md)
