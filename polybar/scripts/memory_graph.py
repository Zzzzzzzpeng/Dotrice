#!/usr/bin/env python3

import time

INTERVAL = 0.4

GREEN = "#a7c080"
BLUE = "#7fbbb3"
YELLOW = "#dbbc7f"
RED = "#e67e80"
BLACK = "#272e33"

FRAMES = [
    "⠋",
    "⠙",
    "⠚",
    "⠒",
    "⠂",
    "⠂",
    "⠒",
    "⠲",
    "⠴",
    "⠦",
    "⠖",
    "⠒",
    "⠐",
    "⠐",
    "⠒",
    "⠓",
    "⠋",
]


def read_memory():
    values = {}

    with open("/proc/meminfo", "r", encoding="utf-8") as file:
        for line in file:
            key, value = line.split(":", 1)
            values[key] = int(value.split()[0])

    total = values["MemTotal"]
    available = values["MemAvailable"]

    used = total - available

    return used, total


def get_colour(percent):
    if percent < 50:
        return GREEN

    if percent < 70:
        return BLUE

    if percent < 85:
        return YELLOW

    return RED


def gib(value):
    return value / 1024 / 1024


frame = 0

while True:
    try:
        used, total = read_memory()

        percent = (used / total) * 100
        colour = get_colour(percent)

        icon = FRAMES[frame % len(FRAMES)]
        frame += 1

        if frame >= 100000:
            frame = 0

        percent_text = f"{percent:5.1f}%"
        memory_text = f"{gib(used):4.1f}/{gib(total):4.1f}G"

        print(
            f"%{{F{colour}}} {icon}%{{F-}} "
            f"%{{F{BLACK}}}{percent_text} {memory_text}%{{F-}}",
            flush=True,
        )

    except (
        OSError,
        KeyError,
        ValueError,
        ZeroDivisionError,
    ):
        print(
            f"%{{F{RED}}} ◌%{{F-}} "
            f"%{{F{BLACK}}}Memory Error%{{F-}}",
            flush=True,
        )

    time.sleep(INTERVAL)
