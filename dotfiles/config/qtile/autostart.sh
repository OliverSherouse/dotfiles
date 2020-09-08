#! /bin/bash
dunst &
nitrogen --restore &
cbatticon -i notification -c "systemctl suspend" &
volumeicon &
udiskie --tray &
dex -a -e QTILE &
