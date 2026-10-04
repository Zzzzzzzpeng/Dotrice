#!/usr/bin/env python3

import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib


# =========================================================
# SPOTIFY
# =========================================================

PLAYER = "spotify"

HOME = Path.home()

CACHE = HOME / ".cache" / "spotify-polybar"
CACHE.mkdir(parents=True, exist_ok=True)

PID_FILE = CACHE / "popup.pid"
ART_FILE = CACHE / "cover.jpg"


# =========================================================
# POSITION / SIZE
# =========================================================

# Polybar kau berada di bottom.
BAR_HEIGHT = 24
BAR_BOTTOM_OFFSET = 17

# Popup: width sahaja dikecilkan.
POPUP_WIDTH = 300
POPUP_HEIGHT = 470

# Lebih besar = makin ke atas.
POPUP_GAP = 14

# Lebih besar = makin ke kiri.
RIGHT_MARGIN = 240

# =========================================================
# EVERBLUSH
# =========================================================

EB_BG = "#141b1e"
EB_BG_LIGHT = "#232a2d"

EB_RED = "#e57474"
EB_GREEN = "#8ccf7e"
EB_YELLOW = "#e5c76b"

EB_BLUE = "#67b0e8"
EB_CYAN = "#6cbfbf"

EB_PURPLE = "#c47fd5"
EB_ORANGE = "#fcb163"

EB_WHITE = "#dadada"
EB_GREY = "#b3b9b8"

EB_BORDER = "#303a3e"


# =========================================================
# GTK CSS
# =========================================================

APP_CSS = f"""
window {{
    background-color: transparent;
}}

#spotify-root {{
    background-color: {EB_BG};
    border: 2px solid {EB_CYAN};
    border-radius: 16px;
}}

#spotify-header {{
    background-color: transparent;
}}

#spotify-cover-frame {{
    background-color: {EB_BG_LIGHT};
    border: 1px solid {EB_BORDER};
    border-radius: 14px;
}}

#spotify-title {{
    color: {EB_WHITE};
    font-family: "JetBrainsMono Nerd Font";
    font-size: 14px;
    font-weight: bold;
}}

#spotify-artist {{
    color: {EB_GREEN};
    font-family: "JetBrainsMono Nerd Font";
    font-size: 12px;
    font-weight: bold;
}}

#spotify-album {{
    color: {EB_GREY};
    font-family: "JetBrainsMono Nerd Font";
    font-size: 10px;
}}

#spotify-status {{
    color: {EB_CYAN};
    font-family: "JetBrainsMono Nerd Font";
    font-size: 9px;
    font-weight: bold;
}}

#spotify-bars {{
    color: {EB_BLUE};
    font-family: "JetBrainsMono Nerd Font";
    font-size: 13px;
    font-weight: bold;
}}

button {{
    font-family: "JetBrainsMono Nerd Font";
    font-weight: bold;
    outline: none;
}}

.spotify-normal {{
    background-color: {EB_BG_LIGHT};
    color: {EB_WHITE};

    border: 1px solid {EB_BORDER};
    border-radius: 9px;

    font-size: 15px;
    padding: 0;
}}

.spotify-normal:hover {{
    background-color: {EB_BLUE};
    color: {EB_BG};
    border-color: {EB_BLUE};
}}

.spotify-main {{
    background-color: {EB_GREEN};
    color: {EB_BG};

    border: 1px solid {EB_GREEN};
    border-radius: 11px;

    font-size: 17px;
    padding: 0;
}}

.spotify-main:hover {{
    background-color: {EB_CYAN};
    border-color: {EB_CYAN};
}}

.spotify-small {{
    background-color: {EB_BG_LIGHT};
    color: {EB_GREY};

    border: 1px solid {EB_BORDER};
    border-radius: 8px;

    font-size: 13px;
    padding: 0;
}}

.spotify-small:hover {{
    background-color: {EB_PURPLE};
    color: {EB_BG};
    border-color: {EB_PURPLE};
}}

.spotify-close {{
    background-color: {EB_RED};
    color: {EB_BG};

    border: 1px solid {EB_RED};
    border-radius: 7px;

    font-size: 13px;
    padding: 0;
}}

.spotify-close:hover {{
    background-color: {EB_ORANGE};
    border-color: {EB_ORANGE};
}}
"""


# =========================================================
# CSS LOAD
# =========================================================

def load_css():

    provider = Gtk.CssProvider()

    provider.load_from_data(
        APP_CSS.encode("utf-8")
    )

    screen = Gdk.Screen.get_default()

    Gtk.StyleContext.add_provider_for_screen(
        screen,
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


# =========================================================
# PLAYERCTL
# =========================================================

def playerctl(*args):

    try:

        result = subprocess.run(
            [
                "playerctl",
                "--player",
                PLAYER,
                *args,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=2,
            check=False,
        )

        if result.returncode != 0:
            return ""

        return result.stdout.strip()

    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        OSError,
    ):
        return ""


def control(action):

    try:

        subprocess.Popen(
            [
                "playerctl",
                "--player",
                PLAYER,
                action,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    except OSError:
        pass


# =========================================================
# TEXT
# =========================================================

def clean(text):

    return " ".join(
        (text or "").split()
    )


def shorten(text, limit):

    text = clean(text)

    if len(text) <= limit:
        return text

    return (
        text[: limit - 1].rstrip()
        + "…"
    )


# =========================================================
# ALBUM ART
# =========================================================

def get_art():

    return playerctl(
        "metadata",
        "mpris:artUrl",
    )


def fetch_art(url):

    if not url:
        return None

    try:

        # Local image
        if url.startswith("file://"):

            path = unquote(
                urlparse(url).path
            )

            path = Path(path)

            if path.is_file():
                return path

            return None

        # Remote image
        if url.startswith(
            ("http://", "https://")
        ):

            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent":
                        "Mozilla/5.0"
                },
            )

            with urllib.request.urlopen(
                request,
                timeout=8,
            ) as response:

                data = response.read()

            if not data:
                return None

            tmp = ART_FILE.with_suffix(
                ".tmp"
            )

            tmp.write_bytes(data)
            tmp.replace(ART_FILE)

            return ART_FILE

    except Exception:
        return None

    return None


# =========================================================
# BUTTON
# =========================================================

def make_button(
    text,
    callback,
    css_class,
    width,
    height,
):

    btn = Gtk.Button(
        label=text
    )

    btn.set_size_request(
        width,
        height,
    )

    btn.get_style_context().add_class(
        css_class
    )

    btn.connect(
        "clicked",
        callback,
    )

    return btn


# =========================================================
# POPUP
# =========================================================

class SpotifyPopup:

    def __init__(self):

        self.bar_index = 0

        self.window = Gtk.Window(
            type=Gtk.WindowType.TOPLEVEL
        )

        self.window.set_title(
            "Spotify"
        )

        self.window.set_default_size(
            POPUP_WIDTH,
            POPUP_HEIGHT,
        )

        self.window.set_decorated(
            False
        )

        self.window.set_resizable(
            False
        )

        self.window.set_keep_above(
            True
        )

        self.window.set_skip_taskbar_hint(
            True
        )

        self.window.set_skip_pager_hint(
            True
        )

        self.window.connect(
            "destroy",
            self.on_destroy,
        )

        load_css()

        self.build()

    # =====================================================
    # BUILD
    # =====================================================

    def build(self):

        root = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8,
        )

        root.set_name(
            "spotify-root"
        )

        root.set_border_width(
            12
        )

        self.window.add(
            root
        )

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        header = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL
        )

        header.set_name(
            "spotify-header"
        )

        header.set_halign(
            Gtk.Align.END
        )

        close = make_button(
            "󰅖",
            self.close,
            "spotify-close",
            28,
            26,
        )

        header.pack_end(
            close,
            False,
            False,
            0,
        )

        root.pack_start(
            header,
            False,
            False,
            0,
        )

        # -------------------------------------------------
        # ALBUM COVER
        # -------------------------------------------------

        cover_frame = Gtk.Frame()

        cover_frame.set_name(
            "spotify-cover-frame"
        )

        cover_frame.set_shadow_type(
            Gtk.ShadowType.NONE
        )

        cover_frame.set_halign(
            Gtk.Align.CENTER
        )

        self.image = Gtk.Image()

        self.image.set_size_request(
            180,
            180,
        )

        cover_frame.add(
            self.image
        )

        root.pack_start(
            cover_frame,
            False,
            False,
            0,
        )

        # -------------------------------------------------
        # TITLE
        # -------------------------------------------------

        self.title = Gtk.Label(
            label="No track"
        )

        self.title.set_name(
            "spotify-title"
        )

        self.title.set_max_width_chars(
            29
        )

        self.title.set_ellipsize(
            3
        )

        self.title.set_halign(
            Gtk.Align.CENTER
        )

        root.pack_start(
            self.title,
            False,
            False,
            0,
        )

        # -------------------------------------------------
        # ARTIST
        # -------------------------------------------------

        self.artist = Gtk.Label(
            label="Spotify"
        )

        self.artist.set_name(
            "spotify-artist"
        )

        self.artist.set_max_width_chars(
            29
        )

        self.artist.set_ellipsize(
            3
        )

        self.artist.set_halign(
            Gtk.Align.CENTER
        )

        root.pack_start(
            self.artist,
            False,
            False,
            0,
        )

        # -------------------------------------------------
        # ALBUM
        # -------------------------------------------------

        self.album = Gtk.Label(
            label="Album"
        )

        self.album.set_name(
            "spotify-album"
        )

        self.album.set_max_width_chars(
            29
        )

        self.album.set_ellipsize(
            3
        )

        self.album.set_halign(
            Gtk.Align.CENTER
        )

        root.pack_start(
            self.album,
            False,
            False,
            0,
        )

        # -------------------------------------------------
        # CAVA-STYLE BARS
        # -------------------------------------------------

        self.bars = Gtk.Label(
            label="▁▂▃▄▅▆▇█"
        )

        self.bars.set_name(
            "spotify-bars"
        )

        self.bars.set_halign(
            Gtk.Align.CENTER
        )

        root.pack_start(
            self.bars,
            False,
            False,
            0,
        )

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------

        self.status = Gtk.Label(
            label="Stopped"
        )

        self.status.set_name(
            "spotify-status"
        )

        self.status.set_halign(
            Gtk.Align.CENTER
        )

        root.pack_start(
            self.status,
            False,
            False,
            0,
        )

        # -------------------------------------------------
        # MAIN CONTROLS
        # -------------------------------------------------

        controls = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=7,
        )

        controls.set_halign(
            Gtk.Align.CENTER
        )

        previous = make_button(
            "󰒮",
            lambda *_:
                control("previous"),
            "spotify-normal",
            43,
            38,
        )

        self.play_button = make_button(
            "󰐊",
            lambda *_:
                control("play-pause"),
            "spotify-main",
            50,
            42,
        )

        next_button = make_button(
            "󰒭",
            lambda *_:
                control("next"),
            "spotify-normal",
            43,
            38,
        )

        controls.pack_start(
            previous,
            False,
            False,
            0,
        )

        controls.pack_start(
            self.play_button,
            False,
            False,
            0,
        )

        controls.pack_start(
            next_button,
            False,
            False,
            0,
        )

        root.pack_start(
            controls,
            False,
            False,
            0,
        )

        # -------------------------------------------------
        # SECONDARY CONTROLS
        # -------------------------------------------------

        extra = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=7,
        )

        extra.set_halign(
            Gtk.Align.CENTER
        )

        shuffle = make_button(
            "󰒝",
            lambda *_:
                control("shuffle"),
            "spotify-small",
            44,
            31,
        )

        repeat = make_button(
            "󰑖",
            self.toggle_repeat,
            "spotify-small",
            44,
            31,
        )

        stop = make_button(
            "󰓛",
            lambda *_:
                control("stop"),
            "spotify-small",
            44,
            31,
        )

        extra.pack_start(
            shuffle,
            False,
            False,
            0,
        )

        extra.pack_start(
            repeat,
            False,
            False,
            0,
        )

        extra.pack_start(
            stop,
            False,
            False,
            0,
        )

        root.pack_start(
            extra,
            False,
            False,
            0,
        )

    # =====================================================
    # UPDATE
    # =====================================================

    def update(self):

        status = playerctl(
            "status"
        )

        title = playerctl(
            "metadata",
            "xesam:title",
        )

        artist = playerctl(
            "metadata",
            "xesam:artist",
        )

        album = playerctl(
            "metadata",
            "xesam:album",
        )

        self.title.set_text(
            shorten(
                title,
                30,
            ) or "No track"
        )

        self.artist.set_text(
            shorten(
                artist,
                30,
            ) or "Spotify"
        )

        self.album.set_text(
            shorten(
                album,
                30,
            ) or "No album"
        )

        self.status.set_text(
            status or "Stopped"
        )

        # -------------------------------------------------
        # CAVA BARS
        # -------------------------------------------------

        if status == "Playing":

            frames = (
                "▁▂▃▄▅▆▇█▇▆▅▄",
                "▂▃▄▅▆▇█▇▆▅▄▃",
                "▃▄▅▆▇█▇▆▅▄▃▂",
                "▄▅▆▇█▇▆▅▄▃▂▁",
                "▅▆▇█▇▆▅▄▃▂▁▂",
                "▆▇█▇▆▅▄▃▂▁▂▃",
                "▇█▇▆▅▄▃▂▁▂▃▄",
                "█▇▆▅▄▃▂▁▂▃▄▅",
            )

            self.bars.set_text(
                frames[
                    self.bar_index
                    % len(frames)
                ]
            )

            self.bar_index += 1

            self.play_button.set_label(
                "󰏤"
            )

        elif status == "Paused":

            self.bars.set_text(
                "▁▁▂▂▁▁▂▂▁▁▂▂"
            )

            self.play_button.set_label(
                "󰐊"
            )

        else:

            self.bars.set_text(
                "────────────"
            )

            self.play_button.set_label(
                "󰐊"
            )

        return True

    # =====================================================
    # ALBUM ART UPDATE
    # =====================================================

    def update_art(self):

        url = get_art()

        if not url:
            return True

        path = fetch_art(
            url
        )

        if not path:
            return True

        try:

            pixbuf = (
                GdkPixbuf.Pixbuf
                .new_from_file_at_scale(
                    str(path),
                    180,
                    180,
                    True,
                )
            )

            self.image.set_from_pixbuf(
                pixbuf
            )

        except Exception:
            pass

        return True

    # =====================================================
    # REPEAT
    # =====================================================

    def toggle_repeat(self):

        current = playerctl(
            "loop"
        )

        if current == "None":

            playerctl(
                "loop",
                "Playlist",
            )

        elif current == "Playlist":

            playerctl(
                "loop",
                "Track",
            )

        else:

            playerctl(
                "loop",
                "None",
            )

    # =====================================================
    # POSITION
    # =====================================================

    def position_popup(self):

        self.window.realize()

        display = Gdk.Display.get_default()

        monitor = display.get_primary_monitor()

        if monitor is None:
            monitor = display.get_monitor(0)

        geometry = monitor.get_geometry()

        # Geser kiri:
        x = (
            geometry.x
            + geometry.width
            - POPUP_WIDTH
            - RIGHT_MARGIN
        )

        # Geser ke atas dari Polybar:
        y = (
            geometry.y
            + geometry.height
            - BAR_BOTTOM_OFFSET
            - BAR_HEIGHT
            - POPUP_GAP
            - POPUP_HEIGHT
        )

        self.window.move(
            x,
            y,
        )

    # =====================================================
    # SHOW
    # =====================================================

    def show(self):

        self.window.show_all()

        self.position_popup()

        self.update_art()

        GLib.timeout_add(
            450,
            self.update,
        )

        GLib.timeout_add(
            1200,
            self.update_art,
        )

    # =====================================================
    # CLOSE
    # =====================================================

    def close(self, *_):

        Gtk.main_quit()

    def on_destroy(self, *_):

        PID_FILE.unlink(
            missing_ok=True
        )

        Gtk.main_quit()


# =========================================================
# PID
# =========================================================

def popup_running():

    if not PID_FILE.exists():
        return False

    try:

        pid = int(
            PID_FILE.read_text().strip()
        )

        os.kill(
            pid,
            0,
        )

        return True

    except (
        ValueError,
        ProcessLookupError,
        PermissionError,
        OSError,
    ):

        PID_FILE.unlink(
            missing_ok=True
        )

        return False


def write_pid():

    PID_FILE.write_text(
        str(os.getpid())
    )


def close_popup():

    if not PID_FILE.exists():
        return

    try:

        pid = int(
            PID_FILE.read_text().strip()
        )

        os.kill(
            pid,
            signal.SIGTERM,
        )

    except (
        ValueError,
        ProcessLookupError,
        PermissionError,
        OSError,
    ):
        pass

    PID_FILE.unlink(
        missing_ok=True
    )


# =========================================================
# POLYBAR CAVA
# =========================================================

def polybar():

    frames = (
        "▁▂▃▄",
        "▂▃▄▅",
        "▃▄▅▆",
        "▄▅▆▇",
        "▅▆▇█",
        "▄▅▆▇",
        "▃▄▅▆",
        "▂▃▄▅",
    )

    frame = 0

    while True:

        status = playerctl(
            "status"
        )

        artist = clean(
            playerctl(
                "metadata",
                "xesam:artist",
            )
        )

        if status == "Playing":

            visual = frames[
                frame % len(frames)
            ]

            artist = (
                shorten(
                    artist,
                    23,
                )
                or "Spotify"
            )

            print(
                f"{visual}  {artist}",
                flush=True,
            )

            frame += 1

        elif status == "Paused":

            artist = (
                shorten(
                    artist,
                    23,
                )
                or "Spotify"
            )

            print(
                f"▁▁▁  {artist}",
                flush=True,
            )

        else:

            print(
                " Spotify",
                flush=True,
            )

        time.sleep(
            0.45
        )


# =========================================================
# POPUP
# =========================================================

def open_popup():

    if popup_running():
        return

    write_pid()

    popup = SpotifyPopup()

    popup.show()

    Gtk.main()


# =========================================================
# MAIN
# =========================================================

def main():

    if len(sys.argv) > 1:

        command = sys.argv[1]

        if command == "open":
            open_popup()
            return

        if command == "close":
            close_popup()
            return

    polybar()


if __name__ == "__main__":
    main()
