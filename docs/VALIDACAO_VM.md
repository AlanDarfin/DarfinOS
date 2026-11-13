# Disposable VM acceptance checklist

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](pt-BR/VALIDACAO_VM.md)**

**This is a manual acceptance plan, not evidence that these steps were already tested.** A successful CI workflow does not prove a graphical Linux desktop will boot. Do not run risky display-server or boot changes on a primary installation without reliable recovery.

## 1. Prepare a clean Arch virtual machine

- [ ] Install Arch in a disposable VM with snapshots enabled.
- [ ] Record initial packages, enabled services, network configuration and boot entries.
- [ ] Confirm a working user account with sudo and a stable network connection.
- [ ] Take a baseline snapshot and verify it can restore the VM.
- [ ] Clone DarfinOS and run Doctor, `--check-modules` and `--plan --preset minimal`.

## 2. Exercise the minimal installer

- [ ] Review package transactions and execute the Minimal preset interactively.
- [ ] Check logs, services, installed-module states and all interactive confirmation prompts.
- [ ] Rerun the same stages and verify complete stages use `STEP_ALREADY` without reinstalling.
- [ ] Test the `--reinstall` override and verify pacman still respects `--needed`.

## 3. Validate the graphical stack

- [ ] From a TTY, install XLibre/SonicDE with a recovery snapshot.
- [ ] Boot to the graphical login manager, sign in, log out and reboot.
- [ ] Check networking, audio, display geometry, session startup and rollback to the baseline.
- [ ] Install i3 in a separate session; verify SonicDE is still available.
- [ ] Test the alternative Retro (Xfce + Chicago95) preset. Verify the assets are copied to HOME and the existing desktop settings are preserved.
- [ ] Re-run Chicago95 with existing assets and confirm they are never overwritten.

## 4. Test Labs boundaries

- [ ] Verify all 13 original project links in the Bash/TUI catalog.
- [ ] Verify `--all`, `--skip` and `full` do not silently select Labs modules.
- [ ] Review NsCDE, JuNest, Decman and Metapac AUR PKGBUILDs before any individual installation.
- [ ] Confirm the special AUR confirmation and rejection of unattended `-y`.
- [ ] Do not run Decman/Metapac synchronization or JuNest setup automatically.
- [ ] Keep yserver, xomposite, Wayback, Trinity and Booster in isolated sessions/VMs with an explicit recovery procedure.

## 5. Backup and recovery

- [ ] Generate a HOME configuration backup and inspect its list of files.
- [ ] Corrupt a disposable allowed file, preview restore, then apply with explicit approval.
- [ ] Test partial failure handling and confirm originals are preserved where possible.
- [ ] Demonstrate recovery of packages, systemd and graphical state using **your VM snapshot**, not DarfinOS's limited HOME backup.

## 6. Release gate

- [ ] All Python/Bash tests and Arch smoke checks pass on the release commit.
- [ ] Desktop login, reboot and manual rollback succeed across relevant presets.
- [ ] Package downloads, checksums, documentation and locale navigation work.
- [ ] Clearly label incomplete/experimental modules and keep a reproducible recovery guide.
- [ ] Only then consider promoting a development prerelease to a stable release.

[Security](SEGURANCA.md) · [Tests](TESTES.md) · [Publishing](LANCAMENTO.md)
