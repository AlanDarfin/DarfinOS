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
