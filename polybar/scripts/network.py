#!/usr/bin/env python3

import time
from pathlib import Path

INTERVAL = 0.20

GREEN = "#a7c080"
BLUE = "#7fbbb3"
YELLOW = "#dbbc7f"
RED = "#e67e80"
BLACK = "#272e33"

FRAMES = [
    ("↓", "↑"),
    ("⇣", "⇡"),
    ("↡", "↟"),
    ("⇣", "⇡"),
]


def get_interface():
    try:
        for line in Path("/proc/net/route").read_text().splitlines()[1:]:
            parts = line.split()

            if len(parts) >= 2 and parts[1] == "00000000":
                return parts[0]

    except OSError:
        pass

    return None


def read_bytes(interface):
    if not interface:
        return 0, 0

    try:
        for line in Path("/proc/net/dev").read_text().splitlines():
            line = line.strip()

            if line.startswith(f"{interface}:"):
                data = line.split(":", 1)[1].split()

                return int(data[0]), int(data[8])

    except (OSError, ValueError):
        pass

    return 0, 0


def format_rate(value):
    if value < 1024:
        return f"{value:.0f} B/s"

    if value < 1024**2:
        return f"{value / 1024:.1f} KB/s"

    if value < 1024**3:
        return f"{value / 1024**2:.1f} MB/s"

    return f"{value / 1024**3:.2f} GB/s"


def get_speed_colour(total_rate):
    # Total throughput RX + TX
    #
    # < 100 KB/s     -> green
    # < 1 MB/s       -> blue
    # < 5 MB/s       -> yellow
    # >= 5 MB/s      -> red

    if total_rate < 100 * 1024:
        return GREEN

    if total_rate < 1024 * 1024:
        return BLUE

    if total_rate < 5 * 1024 * 1024:
        return YELLOW

    return RED


interface = get_interface()

previous = read_bytes(interface)
previous_time = time.monotonic()

frame = 0

time.sleep(INTERVAL)

while True:
    current_interface = get_interface()

    if current_interface != interface:
        interface = current_interface
        previous = read_bytes(interface)
        previous_time = time.monotonic()

    current = read_bytes(interface)

    now = time.monotonic()
    elapsed = max(now - previous_time, 0.01)

    rx_rate = max(
        0,
        (current[0] - previous[0]) / elapsed
    )

    tx_rate = max(
        0,
        (current[1] - previous[1]) / elapsed
    )

    previous = current
    previous_time = now

    if not interface:
        print(
            f"%{{F{YELLOW}}}󰤭%{{F-}} "
            f"%{{F{BLACK}}}Offline%{{F-}}",
            flush=True,
        )

        time.sleep(INTERVAL)
        continue

    total_rate = rx_rate + tx_rate
    colour = get_speed_colour(total_rate)

    rx_icon, tx_icon = FRAMES[frame % len(FRAMES)]
    frame += 1

    wifi_icon = " "

    # Idle network = small neutral dot
    if total_rate < 1:
        activity = f"%{{F{BLACK}}}·%{{F-}}"
    else:
        activity = f"%{{F{colour}}}●%{{F-}}"

    print(
        f"%{{F{colour}}}{wifi_icon}%{{F-}} "
        f"{activity} "
        f"%{{F{colour}}}{rx_icon}%{{F-}} "
        f"%{{F{BLACK}}}{format_rate(rx_rate)}%{{F-}} "
        f"%{{F{colour}}}{tx_icon}%{{F-}} "
        f"%{{F{BLACK}}}{format_rate(tx_rate)}%{{F-}}",
        flush=True,
    )

    time.sleep(INTERVAL)
