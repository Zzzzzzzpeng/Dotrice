#!/bin/sh

ACTION="$1"

# Start Eww daemon if needed
if ! eww ping >/dev/null 2>&1; then
    eww daemon >/dev/null 2>&1 &
    sleep 0.5
fi

case "$ACTION" in
    open)
        eww open dashboard
        ;;
    close)
        eww close dashboard
        ;;
esac
