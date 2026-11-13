# DarfinOS Labs · experimental independent projects

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](pt-BR/LABS.md)**

**Your Arch, my rules.** DarfinOS Labs is a catalog of **13 independently developed Linux projects** that explore unusual window managers, desktop environments, portability, declarative package management, and graphics/boot internals.

The catalog records upstream links, a risk tier and whether installation is supported. DarfinOS is not affiliated with these authors.

## Integration levels

- **Official Arch packages:** i3 and Xfce can be installed as alternative sessions without deleting SonicDE.
- **AUR with explicit confirmation:** NsCDE, JuNest, Decman and Metapac. Review the PKGBUILD before agreeing; unattended `-y` is rejected.
- **Optional upstream assets:** Chicago95 copies selected GTK and icon files into the user's HOME after confirmation. It does not run the upstream Python installer or modify active panel settings.
- **Documentation only:** Conty, nix-portable, Trinity, yserver, xomposite, Wayback, Booster. These tools may need manual downloads, special permissions, source builds, or changes to the desktop and boot chain; no automatic stage is provided.

```bash
bash DarfinOSInstallScript.sh --labs
bash DarfinOSInstallScript.sh --lab-info chicago95
python3 DarfinOSInstallScript-TUI.py --labs
python3 DarfinOSInstallScript-TUI.py --plan --preset retro
```

In the TUI, press **L** to browse, Enter to inspect and Space to select supported stages. Labs modules are never silently included by `--all`, `--skip` or the `full` preset.

## Original projects

| Project | Purpose | Integration | Upstream |
| --- | --- | --- | --- |
| i3 | Keyboard-focused X11 tiling WM | Official Arch package, preset `i3` | [i3](https://i3wm.org/) |
| Chicago95 | Windows 95-inspired theme for Xfce | Confirmed theme/icon copy, preset `retro` | [Chicago95](https://github.com/grassmunk/Chicago95) |
| NsCDE | Classic UNIX workstation-like desktop | Opt-in AUR | [NsCDE](https://github.com/NsCDE/NsCDE) |
| JuNest | User-space Arch environment | Opt-in AUR; no automatic setup | [JuNest](https://github.com/fsquillace/junest) |
| Decman | Declarative system configuration | Opt-in AUR, no automatic Python configuration | [Decman](https://github.com/kiviktnm/decman) |
| Metapac | Declarative package inventory | Opt-in AUR, no automatic sync/clean | [Metapac](https://github.com/ripytide/metapac) |
| Conty | Portable compressed Linux container | Manual guide | [Conty](https://github.com/Kron4ek/Conty) |
| nix-portable | Portable Nix setup | Manual guide | [nix-portable](https://github.com/DavHau/nix-portable) |
| Trinity | Classic KDE 3 continuation | Manual external repo, VM only | [Trinity](https://www.trinitydesktop.org/) |
| yserver | Experimental Rust X11 server | VM research only | [yserver](https://github.com/joske/yserver) |
| xomposite | Experimental XLibre/Rust compositor | Separate session research only | [xomposite](https://github.com/demostenex/xlibre-compositor-poc) |
| Wayback | X11 desktop via Wayland infrastructure | Experimental guide | [Wayback](https://gitlab.freedesktop.org/wayback/wayback) |
| Booster | Alternative initramfs generator | Manual boot research only | [Booster](https://github.com/anatol/booster) |

Do not run competing compositors alongside KWin, apply destructive Decman/Metapac synchronization without a reviewed plan, or replace boot components without tested recovery. Containers and portable binaries are not automatically secure sandboxes.

[Documentation index](README.md) · [Module checks](MODULOS.md) · [Labs on the website](https://darfinos.vercel.app/labs/)
