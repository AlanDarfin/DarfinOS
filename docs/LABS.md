# DarfinOS Labs · independent experimental projects

**🇺🇸 English (default) · [🇧🇷 Português (Brasil)](pt-BR/LABS.md)**

**Your Arch, my rules.** All 13 independent projects now have an installer stage. Press **L** in the TUI, **Enter** to read the details, and **Space** to select. From Bash, use `--only` with the stage name.

```bash
bash DarfinOSInstallScript.sh --labs
bash DarfinOSInstallScript.sh --lab-info trinity
bash DarfinOSInstallScript.sh --only lab_trinity
```

The `lab_*` stages are interactive, reject `-y` and stay out of `--all`, `--skip` and `full`. The optional Retro preset includes Chicago95, and i3 is also available as an ordinary Arch stage. Verified complete stages are skipped. AUR stages can set up yay or paru if needed and ask you to review the PKGBUILD.

| Project | Stage | What gets installed |
| --- | --- | --- |
| [i3](https://i3wm.org/) | `i3` | Official Arch packages for the parallel X11 session. |
| [Chicago95](https://github.com/grassmunk/Chicago95) | `lab_chicago95` | Xfce plus GTK/Xfwm themes, icons, standard cursors and VGA fonts. Existing assets are preserved. |
| [NsCDE](https://github.com/NsCDE/NsCDE) | `lab_nscde` | `nscde` from the AUR. Choose NsCDE at login to run its first-session setup. |
| [JuNest](https://github.com/fsquillace/junest) | `lab_junest` | `junest-git` and an Arch environment initialized with `junest setup` under HOME. No host namespace settings are changed. |
| [Decman](https://github.com/kiviktnm/decman) | `lab_decman` | `decman` from the AUR. No Python system profile is applied. |
| [Metapac](https://github.com/ripytide/metapac) | `lab_metapac` | `metapac` from the AUR. No `sync` or `clean` is run. |
| [Conty](https://github.com/Kron4ek/Conty) | `lab_conty` | Conty Lite 1.29.4 (x86_64), verified by SHA-256, plus FUSE. Run `~/.local/bin/conty <command>` after installation. |
| [nix-portable](https://github.com/DavHau/nix-portable) | `lab_nix_portable` | The verified v012 x86_64 binary in `~/.local/bin`, without a daemon. Run `~/.local/bin/nix-portable nix --version` to initialize its user cache. |
| [Trinity](https://www.trinitydesktop.org/) | `lab_trinity` | Trinity's signed repository and the complete `tde-meta` desktop through `pacman -Syu`. |
| [yserver](https://github.com/joske/yserver) | `lab_yserver` | `yserver` and `starty` from the AUR, with a prompt to install Intel or AMD Vulkan if needed. For other GPUs use your matching driver. |
| [Xomposite](https://github.com/demostenex/xomposite) | `lab_xomposite` | Arch dependencies and a pinned Cargo build in `~/.local/bin/xomposite`. Run in an X11 session without another compositor. |
| [Wayback](https://gitlab.freedesktop.org/wayback/wayback) | `lab_wayback` | `wayback-x11` from the AUR, without replacing the default X server. |
| [Booster](https://github.com/anatol/booster) | `lab_booster` | Arch package whose hook builds alternative initramfs images. DarfinOS does not switch boot entries. |

### After installation

- **Trinity:** the installer checks the complete published signing fingerprint and takes a backup before committing a new `[trinity]` section. It leaves the login manager alone. Select Trinity in your existing X11 login screen. [Upstream Arch instructions](https://wiki.trinitydesktop.org/Arch_Trinity_Repository_Installation_Instructions).
- **Chicago95:** select the theme, icons and cursor in Xfce. Optional GTK4 overrides, panel layouts, startup sounds and greeters are not applied. [Upstream Chicago95 setup](https://github.com/grassmunk/Chicago95/blob/master/INSTALL.md).
- **Graphics and boot:** test `starty` from a free TTY after checking device access and Vulkan. Test Wayback in a separate session. On a VM, try Booster with an alternate boot entry while keeping the working entry. [yserver setup](https://github.com/joske/yserver/blob/master/docs/setup.md) · [Booster on ArchWiki](https://wiki.archlinux.org/title/Booster).
- **Portability and declarative tools:** installation does not change host namespaces, apply your package inventory or guarantee isolation. Decide separately what to run or synchronize.

[Documentation index](README.md) · [Module checks](MODULOS.md) · [Labs website](https://darfinos.vercel.app/labs/)
