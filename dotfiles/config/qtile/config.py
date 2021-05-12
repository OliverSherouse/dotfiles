import collections
import os

import subprocess

from libqtile.config import Key, Screen, Group, Drag, Click
from libqtile.command import lazy
from libqtile import layout, bar, widget, hook

try:
    from typing import List  # noqa: F401
except ImportError:
    pass
mod = "mod4"

Theme = collections.namedtuple("Theme", ["fg", "bg", "selected_fg", "selected_bg"])

arc = Theme(fg="#D3DAE3", bg="#383C4A", selected_fg="#D3DAE3", selected_bg="#5294e2")

adapta = Theme(fg="#cfd8dc", bg="#263238", selected_fg="#ffffff", selected_bg="#00bcd4")

theme = arc
terminal = "kitty"

keys = [
    Key([mod], "j", lazy.layout.down()),
    Key([mod], "k", lazy.layout.up()),
    Key([mod], "h", lazy.layout.left()),
    Key([mod], "l", lazy.layout.right()),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down()),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up()),
    Key([mod, "shift"], "h", lazy.layout.shuffle_left()),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right()),
    Key([mod, "control"], "j", lazy.layout.grow_down()),
    Key([mod, "control"], "k", lazy.layout.grow_up()),
    Key([mod, "control"], "h", lazy.layout.grow_left()),
    Key([mod, "control"], "l", lazy.layout.grow_right()),
    Key([mod], "n", lazy.layout.normalize()),
    Key([mod, "shift"], "space", lazy.layout.rotate()),
    Key([mod, "shift"], "Return", lazy.layout.toggle_split()),
    Key([mod], "Return", lazy.spawn(terminal)),
    Key([mod], "e", lazy.spawn(f"{terminal} -e ranger")),
    Key([mod], "i", lazy.spawn(os.environ.get("BROWSER", "firefox"))),
    # Toggle between different layouts as defined below
    Key([mod], "space", lazy.next_layout()),
    Key([mod], "m", lazy.window.toggle_maximize()),
    Key([mod, "shift"], "space", lazy.window.toggle_floating()),
    Key([mod], "q", lazy.window.kill()),
    Key([mod, "control"], "r", lazy.restart()),
    Key(
        [mod, "control"],
        "q",
        lazy.spawn(
            "logout_menu"
            # "lxde-logout"
        ),
    ),
    Key([mod], "r", lazy.spawncmd()),
    Key([mod], "o", lazy.spawn("op")),
    Key([], "XF86AudioRaiseVolume", lazy.spawn("amixer -q sset Master 5%+")),
    Key([], "XF86AudioLowerVolume", lazy.spawn("amixer -q sset Master 5%-")),
    Key([], "XF86AudioMute", lazy.spawn("amixer -q sset Master toggle")),
    Key([], "XF86MonBrightnessUp", lazy.spawn("brightnessctl s 5%+")),
    Key([], "XF86MonBrightnessDown", lazy.spawn("brightnessctl s 5%-")),
    Key([], "XF86Display", lazy.spawn("lxrandr")),
]

groups = [Group(i) for i in "1234"]

for i in groups:
    keys.append(Key([mod], i.name, lazy.group[i.name].toscreen()))
    keys.append(Key([mod, "shift"], i.name, lazy.window.togroup(i.name)))

layouts = [
    layout.Max(),
    layout.columns.Columns(
        border_focus=theme.selected_bg,
        border_focus_stack=theme.selected_bg,
        border_normal=theme.bg,
        border_normal_stack=theme.bg,
        border_width=1,
    ),
]


widget_defaults = dict(
    background=theme.bg,
    foreground=theme.fg,
    font="Noto Sans",
    fontsize=16,
    padding=5,
    borderwidth=0,
)
extension_defaults = widget_defaults.copy()

screens = [
    Screen(
        top=bar.Bar(
            [
                widget.GroupBox(
                    highlight_method="block",
                    active=theme.selected_fg,
                    inactive=theme.fg,
                    this_screen_border=theme.selected_bg,
                    this_current_screen_border=theme.selected_bg,
                    rounded=False,
                    borderwidth=1,
                ),
                widget.Prompt(),
                widget.Spacer(),
                widget.Systray(),
                widget.Volume(
                    volume_app="myxer",
                    theme_path="/usr/share/icons/Faenza-Dark/",
                    padding=3,
                ),
                widget.Battery(
                    format="{char} {percent:.0%}",
                    show_short_text=False,
                    discharge_char="\N{DOWNWARDS WHITE ARROW}",
                    charge_char="\N{UPWARDS WHITE ARROW}",
                    full_char="\N{WHITE CIRCLE}",
                    notify_below=20,
                    hide_threshold=0.5,
                ),
                widget.Clock(format="%l:%M "),
            ],
            24,
            background=theme.bg,
        )
    )
]

# Drag floating layouts.
mouse = [
    Drag(
        [mod],
        "Button1",
        lazy.window.set_position_floating(),
        start=lazy.window.get_position(),
    ),
    Drag(
        [mod],
        "Button3",
        lazy.window.set_size_floating(),
        start=lazy.window.get_size(),
    ),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: List
main = None
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
floating_layout = layout.Floating(
    float_rules=[
        {"wmclass": "confirm"},
        {"wmclass": "dialog"},
        {"wmclass": "download"},
        {"wmclass": "error"},
        {"wmclass": "file_progress"},
        {"wmclass": "notification"},
        {"wmclass": "splash"},
        {"wmclass": "toolbar"},
        {"wmclass": "confirmreset"},  # gitk
        {"wmclass": "makebranch"},  # gitk
        {"wmclass": "maketag"},  # gitk
        {"wname": "branchdialog"},  # gitk
        {"wname": "pinentry"},  # GPG key password entry
        {"wmclass": "ssh-askpass"},  # ssh-askpass
    ]
)
auto_fullscreen = True
focus_on_window_activation = "smart"

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, github issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"


@hook.subscribe.startup_once
def autostart_once():
    subprocess.run([os.path.expanduser("~/.config/qtile/autostart.sh")])
