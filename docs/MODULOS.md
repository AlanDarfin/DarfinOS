# Module verification and safe re-execution

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](pt-BR/MODULOS.md)**

DarfinOS checks the Arch system **before each selected stage** and skips a stage only when there is sufficient local evidence that its intended installation is already complete. The checker is read-only; it does not use sudo, network downloads or file writes.

```bash
bash DarfinOSInstallScript.sh --check-modules           # TSV for shell tools
python3 DarfinOSInstallScript-TUI.py --check-modules   # JSON for automation
python3 DarfinOSInstallScript-TUI.py --local           # I to refresh, X to force
bash DarfinOSInstallScript.sh --only i3 --reinstall    # explicitly rerun a stage
```

## States

| State | Meaning | Automatically skipped? |
| --- | --- | --- |
| `installed` | Sufficient evidence exists for this module's implemented checks | **Yes**, logs `STEP_ALREADY` |
| `partial` | Some packages or files exist, but stage completion cannot be proven | No |
| `missing` | Expected primary packages or files are not detected | No |
| `unknown` | A safe local check cannot certify the full configuration | No |

The checker currently recognizes complete sets of packages for Base, i3 and Xfce; the presence of the AUR helper and optional independent AUR packages; and Chicago95 theme/icon assets in HOME. It deliberately does **not** mark SonicDE, XLibre, Docker, timers, firewall, repositories or boot changes complete just because one package is installed.

`--reinstall` overrides the *stage-level skip*, but retains the package manager's `--needed`, all interactive confirmations and safeguards against overwriting user themes. It is not a request to remove and reinstall everything.

### History and recovery

A verified skipped stage emits `STEP_ALREADY`. The TUI displays `ALREADY` separately from `DONE`, records that state in its run journal and does not propose it as a failed stage during recovery. Partial and unknown stages are still eligible for execution.

### Xfce and Chicago95

The optional `retro` preset selects `base`, `xfce`, and `lab_chicago95`. Xfce is installed from Arch repositories as an alternative desktop session. Chicago95 is fetched from [grassmunk/Chicago95](https://github.com/grassmunk/Chicago95) with confirmation and copies only the theme and icons into `~/.themes/Chicago95` and `~/.icons/Chicago95`. The upstream `installer.py` is **not** run. No desktop panel, login manager, sound pack or active theme is changed automatically. Existing destination folders are not overwritten.

For optional further customization, consult the [Chicago95 original installation guide](https://github.com/grassmunk/Chicago95/blob/master/INSTALL.md). The automated checker does not prove that the theme has been activated or the desktop starts correctly.

[Documentation index](README.md) · [Security](SEGURANCA.md) · [VM checklist](VALIDACAO_VM.md)
