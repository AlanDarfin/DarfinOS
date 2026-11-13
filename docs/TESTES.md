# Tests, CI and reliability

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](pt-BR/TESTES.md)**

Automated tests validate the installer structure, read-only commands, optional Labs metadata, conservative package detection, interactive confirmation protocol, module skip logic and terminal-run records. They deliberately do not change the host operating system.

## Local validation

```bash
bash -n DarfinOSInstallScript.sh
python3 -m py_compile DarfinOSInstallScript-TUI.py darfinos_control.py
python3 -m unittest discover -s tests -v
python3 DarfinOSInstallScript-TUI.py --doctor
bash DarfinOSInstallScript.sh --list
```

## GitHub Actions

- **DarfinOS · Testes:** Python 3.10, 3.12, 3.13 and 3.14 offline test matrix; Bash syntax; ShellCheck report and checksum/packaging checks.
- **DarfinOS · Smoke real de ambiente Arch:** safe checks inside an ephemeral `archlinux:latest` container. It is *not* a bootable VM or full desktop installation.
- **DarfinOS · Preparar pacote candidato:** manually prepare an artifact for review without publishing a release.
- **DarfinOS · Development preview:** after the Arch smoke succeeds on `main`, verify the offline test matrix also succeeded for the **same exact commit**, package with SHA-256 and publish a clearly marked **GitHub prerelease**. If any check fails, no candidate is published.

The development preview workflow does not create stable releases or ISO images. It uses a `0.1.0-rcN` version suffix so it is visibly a release candidate.

## What the tests cover

- Correct and unique list of all 48 stage names and six presets.
- Installer refuses accidental implicit full installations.
- Module checks show complete/partial/missing/unknown without sudo.
- Only verified complete modules generate `STEP_ALREADY`; `--reinstall` allows manual re-execution.
- TUI records `ALREADY` correctly and does not requeue it during recovery.
- 13 Labs projects with original upstream HTTPS links and safe handling of AUR confirmations.
- Chicago95/Xfce integration planning without running a graphical session, remote Python installer or real clone during offline CI.
- Profile diff, read-only maintenance status, limited ZIP backup validation and restore-preparation behavior.

## Not yet certified

Real XLibre and SonicDE login, i3/Xfce sessions, Chicago95 appearance activation, reboot, full recovery, the behavior of every upstream AUR package and low-level Bedrock/Booster changes still require the separate manual [VM acceptance checklist](VALIDACAO_VM.md).

[Documentation index](README.md) · [Publishing policy](LANCAMENTO.md) · [CI runs](https://github.com/AlanDarfin/DarfinOS/actions)
