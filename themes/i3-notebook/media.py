"""Compact MPRIS controls, with one selected player for all three dock buttons."""
import re
import subprocess
import sys
import time

ACTIONS = {"previous": "󰒮", "play-pause": "󰐊", "next": "󰒭"}
INSTANCE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,199}", re.ASCII)
FORMAT = "{{playerInstance}} {{status}}"


def run_player(*args):
    try:
        return subprocess.run(["playerctl", *args], capture_output=True, text=True,
                              timeout=1, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None


def players():
    result = {}
    for line in (run_player("--all-players", "--format", FORMAT, "status") or "").splitlines():
        name, _, state = line.partition(" ")
        if INSTANCE.fullmatch(name) and state in ("Playing", "Paused", "Stopped"):
            result[name] = state
    return result


def select(states, last=None, *, allow_paused=False):
    if states.get(last) == "Playing":
        return last
    if playing := next((name for name, state in states.items() if state == "Playing"), None):
        return playing
    if states.get(last) == "Paused":
        return last
    if allow_paused:
        return next((name for name, state in states.items() if state == "Paused"), None)
    return None


def render(player, state):
    if not player or not INSTANCE.fullmatch(player) or state not in ("Playing", "Paused"):
        return ""
    command = 'sh "$HOME/.config/darfinos/i3-notebook/session.sh" media'
    return "".join(
        "%{A1:" + f"{command} {action} {player}:" + "} "
        + ("󰏤" if action == "play-pause" and state == "Playing" else icon) + " %{A}"
        for action, icon in ACTIONS.items()
    )


def watch():
    last, previous = None, None
    while True:
        states = players()
        # Only appear once a player is playing. Keep its controls during pause;
        # don't fill the dock with other apps that were already paused at login.
        player = select(states, last)
        last = player
        row = render(player, states.get(player))
        if row != previous:
            print(row, flush=True)
            previous = row
        time.sleep(1)


def main():
    args = sys.argv[1:]
    if args == ["watch"]:
        watch()
        return 0
    if len(args) not in (1, 2) or args[0] not in ACTIONS:
        return 2
    player = args[1] if len(args) == 2 else select(players(), allow_paused=True)
    if not player or not INSTANCE.fullmatch(player):
        return 0
    # Don't fall through to another app if the selected player has just closed.
    return int(run_player("--player", player, args[0]) is None)


if __name__ == "__main__":
    sys.exit(main())
