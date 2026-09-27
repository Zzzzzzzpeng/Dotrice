#!/bin/sh

# Kill old Polybar instances
pkill -x polybar 2>/dev/null || true

sleep 0.7

# Detect network
NETWORK_INTERFACE="$(ip route | awk '/default/ {print $5; exit}')"

if printf '%s\n' "$NETWORK_INTERFACE" | grep -q '^wl'; then
    NETWORK_TYPE="wireless"
else
    NETWORK_TYPE="wired"
fi

export NETWORK_INTERFACE
export NETWORK_TYPE

# Launch one Polybar per monitor
for monitor in $(polybar --list-monitors | cut -d: -f1); do
    MONITOR="$monitor" \
    polybar -q brenda \
        -c "$HOME/.config/polybar/brenda/config.ini" &
done
