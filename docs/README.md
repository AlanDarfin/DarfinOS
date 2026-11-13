# DarfinOS documentation

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](pt-BR/README.md)**

DarfinOS is an opinionated Arch Linux post-install toolkit with **64 installer stages**, **seven presets**, the **Control Center** terminal interface and **29 experimental Labs projects**. It is not an independently bootable Linux distribution.

Start with the [English README](../README.md), or browse these guides:

| Topic | English | Português |
| --- | --- | --- |
| Installation and terminal UI | [TUI / Control Center](TUI_V5.md) | [TUI / Control Center](pt-BR/TUI_V5.md) |
| Installed-module checks | [Module verification](MODULOS.md) | [Checagem de módulos](pt-BR/MODULOS.md) |
| Presets and static package inventory | [Presets and manifest](MANIFESTO_PRESETS.md) | [Presets e manifesto](pt-BR/MANIFESTO_PRESETS.md) |
| Experimental projects | [DarfinOS Labs](LABS.md) | [DarfinOS Labs](pt-BR/LABS.md) |
| Security and recovery | [Security](SEGURANCA.md) | [Segurança](pt-BR/SEGURANCA.md) |
| Validation | [VM acceptance checklist](VALIDACAO_VM.md) | [Checklist da VM](pt-BR/VALIDACAO_VM.md) |
| Automated testing | [Tests](TESTES.md) | [Testes](pt-BR/TESTES.md) |
| Publishing | [Releases and development candidates](LANCAMENTO.md) | [Lançamentos](pt-BR/LANCAMENTO.md) |

## Read-only first steps

```bash
git clone https://github.com/AlanDarfin/DarfinOS.git
cd DarfinOS
python3 DarfinOSInstallScript-TUI.py --doctor
python3 DarfinOSInstallScript-TUI.py --check-modules
python3 DarfinOSInstallScript-TUI.py --plan --preset minimal
```

`--doctor`, `--check-modules` and `--plan` are not installation commands. Open the TUI with `python3 DarfinOSInstallScript-TUI.py --local`; review the plan before any selected stage is executed.

## Downloads

- [Main source ZIP](https://github.com/AlanDarfin/DarfinOS/archive/refs/heads/main.zip), always available, not a stable release.
- [GitHub development prereleases](https://github.com/AlanDarfin/DarfinOS/releases), created only after matching Arch smoke and offline tests pass.
- [Website downloads and status](https://darfinos.vercel.app/downloads/), bilingual with browser-language detection.

No ISO or stable version is provided until the required graphical VM and recovery validation is complete.

[Theme Workshop and post-install automation](CUSTOMIZATION.md)
