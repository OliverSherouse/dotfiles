#! /bin/bash
dunst &
nitrogen --restore &
cbatticon -i notification -c "systemctl suspend" &
volumeicon &
udiskie --tray &
picom &
dex -a -e QTILE &
