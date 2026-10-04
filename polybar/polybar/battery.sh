#!/bin/sh

BAT="$(find /sys/class/power_supply -maxdepth 1 -type d -name 'BAT*' | head -n 1)"

[ -n "$BAT" ] || exit 0

CAPACITY="$(cat "$BAT/capacity" 2>/dev/null)"
STATUS="$(cat "$BAT/status" 2>/dev/null)"

[ -n "$CAPACITY" ] || exit 0


# Everforest colours
GREEN="#a7c080"
BLUE="#7fbbb3"
YELLOW="#dbbc7f"
RED="#e67e80"
BLACK="#272e33"


# ---------------------------------------------------------
# BATTERY ICON
# ---------------------------------------------------------

case "$STATUS" in

    Charging)
        ICON=""
        COLOR="$BLUE"
        ;;

    Full)
        ICON=""
        COLOR="$GREEN"
        ;;

    Discharging)

        if [ "$CAPACITY" -ge 80 ]; then
            ICON=""
            COLOR="$GREEN"

        elif [ "$CAPACITY" -ge 60 ]; then
            ICON=""
            COLOR="$GREEN"

        elif [ "$CAPACITY" -ge 40 ]; then
            ICON=""
            COLOR="$BLUE"

        elif [ "$CAPACITY" -ge 20 ]; then
            ICON=""
            COLOR="$YELLOW"

        else
            ICON=""
            COLOR="$RED"
        fi

        ;;

    *)
        ICON=""
        COLOR="$YELLOW"
        ;;
esac


# ---------------------------------------------------------
# POLYBAR COLOUR TAGS
# ---------------------------------------------------------

printf \
    '%%{B%s}%%{F%s} %s %%{F-}%%{B-} %%{F%s}%3s%%%%{F-}\n' \
    "$COLOR" \
    "$BLACK" \
    "$ICON" \
    "$BLACK" \
    "$CAPACITY"
