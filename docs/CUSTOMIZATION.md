# After installation · Theme Workshop
[Português (Brasil)](pt-BR/CUSTOMIZATION.md)

Press **L** to install tools from Labs and **W** to open the Theme Workshop.
Presets choose packages. Appearance profiles control selected HOME files.
Each profile has a diff, per-file selection and a local undo history. Undo
keeps files edited after the run. **W** stays read-only with `--dry-run`.

```bash
bash DarfinOSInstallScript.sh --only lab_chezmoi,lab_matugen,lab_kvantum
python3 darfinos_control.py styles
python3 darfinos_control.py style sonicde-kvantum
python3 darfinos_control.py palette ~/wallpaper.png
python3 darfinos_control.py style-history
python3 darfinos_control.py style-undo RUN
```

- **Terminal**, **Compact i3** and **Workstation 1995** render local templates through chezmoi without importing your personal dotfile repository. For Window Maker, apply the profile and then select DarfinOS-1995 in its styles menu.
- **SonicDE + Kvantum** derives DarfinOSGold from the installed KvDark SVG theme. The profile sets only the relevant Qt style and theme settings. Apply all four listed files together, then reopen Qt apps or log back in. If the session overrides the setting, choose Kvantum in Application Style and DarfinOSGold in Kvantum Manager. It does not style the panel, change KWin or edit your login manager.
- **Xfce**. With Chicago95 and the desktop utilities installed, use **W → X** in an Xfce session. The action only sets the theme, icons, cursor and Xfwm style. This live Xfconf action is separate from the file-profile undo history.
- **autorandr**. Save a working layout with `autorandr --save notebook-720p` and try `autorandr --change`. Only save 30 Hz after verifying that it already works on the panel.
- **Maintenance**. `python3 darfinos_control.py maintenance --json` shows pending pacman config files using `pacdiff --output`. Opt in with `maintenance-timer enable` from a permanent checkout. The weekly user timer notifies only, never upgrades. Disable with `maintenance-timer disable`.
- **Backups**. etckeeper optionally initializes local /etc history. rustic is installed without setting up credentials, destinations or backup schedules. Neither is an OS snapshot.

For new Labs stages and original links, see [DarfinOS Labs](LABS.md). Arcan/Pipeworld and desktop sessions still need graphical validation in a disposable VM.

## i3 Notebook (720p)

**i3 Notebook** is separate from Compact i3. Install **i3 Notebook** in Labs
(**L**), then open **W → i3-notebook**, review the preview and apply it. The
Workshop keeps your previous i3 configuration in its undo history and leaves
global Polybar, Rofi and Dunst configs alone. Log out and back into i3 to load the
profile's session tools. XLibre is not required if X11 already works.

```bash
bash DarfinOSInstallScript.sh --only lab_i3_notebook
python3 darfinos_control.py style i3-notebook
python3 darfinos_control.py style i3-notebook --apply --all-files
```

| Shortcut | Action |
| --- | --- |
| Super+D / Super+Tab | Launch apps and switch windows in Rofi. dmenu is the app-launch fallback. |
| Super+F1 | Open the shortcut list, also available as the **Atalhos do i3** tab in Rofi. |
| Super+F2 | Inspect each output’s current resolution and refresh rate. If the built-in panel advertises 1280×720, test it and confirm within 15 seconds to keep it. |
| Super+Shift+P | Choose a wallpaper that is reapplied at login. Also available through **Fundo** on the bar. |
| Super+Enter / Super+B / Super+E | Open the terminal, the default browser, or your home folder in the default file manager. |
| Super+Shift+B | Show or hide the bar to free up screen space. |
| Super+1–9 / Super+0 | Switch to workspaces 1–10. Add Shift to move the current window. |
| Super+Ctrl+Tab | Return to the previous workspace. |
| Super+H / Super+V / Super+Ctrl+E | Split horizontally or vertically, or toggle the current split direction. |
| Super+W / Super+S | Switch to tabbed or stacked layout. |
| Super+Shift+Enter or Super+Grave / Super+R | Pocket terminal and arrow-key resizing (Esc to exit). |
| Brightness and audio keys | Adjust brightness, volume and mute using your existing PipeWire or PulseAudio setup. |
| Print / Super+Shift+S / Shift+Print | The first two select a region. Shift+Print copies the entire screen. |
| Super+L | Lock the screen. xss-lock also locks before suspend. |
| Super+N / Super+Shift+N / Super+Ctrl+N | Redisplay the last notification, toggle Do Not Disturb, and dismiss visible pop-ups. |

The 28 px Polybar sits at the top with arrow separators, JetBrains Mono and a
short active window title. **Apps**, **Janelas** (Windows), **Atalhos** (Shortcuts),
and **Fundo** (Wallpaper) are clickable. Brightness, battery, network, audio
and time appear on the right as available. The first workspace is **1**.
**Super+Enter** opens the terminal. Focus follows the pointer without warping
it between monitors. If Polybar is unavailable or fails to start, the profile
falls back to native i3bar.

The bar and Rofi design draw on [iamabhas’s dotfiles](https://github.com/iamabhas/dotfiles)
with DarfinOS colors and shortcuts. The Workshop accent applies to the bar,
Rofi, Dunst and the default wallpaper.

The profile reuses the SonicDE cursor theme and size if that theme is installed,
or tries an installed Bibata variant. It does not edit SonicDE settings. The
720p choice only changes the built-in panel and neither creates a mode nor
forces a refresh rate. With no image selected, the profile uses a graphite wallpaper with the
DarfinOS double lightning mark and motto.
When upgrading, run the Notebook Labs step again for the new dependencies,
then reapply the Workshop profile.

Dunst shows up to three notifications in the top-right corner below the bar,
with Rofi's graphite palette and accent color. The profile does not stop a notification daemon already
running on the same D-Bus session. If needed, sign out of the other desktop
before testing in i3. Run `dunstify "DarfinOS" "Notifications ready"` in the i3
session to see the theme. Picom is neither installed nor started by this profile.
