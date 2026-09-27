#!/usr/bin/env python3

import time

CORES = 4
INTERVAL = 0.10
SMOOTHING = 0.65

GREEN = "#a7c080"
BLUE = "#7fbbb3"
YELLOW = "#dbbc7f"
RED = "#e67e80"
GREY = "#272e33"

BARS = "▁▂▃▄▅▆▇█"


def read_cpu():
    cpus = []

    with open("/proc/stat", "r", encoding="utf-8") as f:
        for line in f:
            if not line.startswith("cpu"):
                break

            parts = line.split()

            if not parts[0][3:].isdigit():
                continue

            values = list(map(int, parts[1:]))

            total = sum(values)
            idle = values[3] + values[4]

            cpus.append((total, idle))

    return cpus[:CORES]


def get_usage(previous, current):
    usages = []

    for old, new in zip(previous, current):
        old_total, old_idle = old
        new_total, new_idle = new

        total_delta = new_total - old_total
        idle_delta = new_idle - old_idle

        if total_delta <= 0:
            usage = 0.0
        else:
            usage = 100.0 * (
                total_delta - idle_delta
            ) / total_delta

        usages.append(max(0.0, min(100.0, usage)))

    return usages


def get_colour(value):
    if value < 50:
        return GREEN
    elif value < 70:
        return BLUE
    elif value < 85:
        return YELLOW
    else:
        return RED


def get_bar(value):
    level = int((value / 100) * (len(BARS) - 1))
    level = max(0, min(len(BARS) - 1, level))
    return BARS[level]


previous = read_cpu()

# Prime the counter
time.sleep(0.1)

smoothed = [0.0] * CORES

while True:
    current = read_cpu()

    usages = get_usage(previous, current)
    previous = current

    for i, usage in enumerate(usages):
        smoothed[i] = (
            smoothed[i] * SMOOTHING
            + usage * (1.0 - SMOOTHING)
        )

    output = []

    for usage in smoothed:
        icon = get_bar(usage)
        colour = get_colour(usage)

        output.append(
            f"%{{F{colour}}}{icon}%{{F-}}"
        )

    while len(output) < CORES:
        output.append(
            f"%{{F{GREY}}}▁%{{F-}}"
        )

    print(" ".join(output[:CORES]), flush=True)

    time.sleep(INTERVAL)
