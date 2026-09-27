#!/usr/bin/env python3
"""
PENGNET — Everblush Network Control Centre for Arch Linux

A native Linux TUI around the tools already present on most Arch systems.
Read-only inspection is the default; actions are limited to common network
operations such as Wi-Fi scan/connect/disconnect/power, interface up/down,
DNS cache flush, and diagnostics.

Main sections
-------------
Dashboard • Wi-Fi • Interfaces • Addresses • Routes • Neighbours • DNS
Sockets • Firewall • Services • Diagnostics • Hardware • Logs • System

Navigation
----------
Mouse or arrows/Enter: sidebar + tables
1-0, -, =: quick page switching
r: refresh     /: command palette     s: Wi-Fi scan
c: connect     d: disconnect          p: Wi-Fi power
u: interface up                       x: interface down
a: next interface                     w: next Wi-Fi
q: quit

No passwords are persisted by PENGNET.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import psutil
from rich.console import Group
from rich.markup import escape
from rich.table import Table
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.theme import Theme
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    OptionList,
    Select,
    Sparkline,
    Static,
)
from textual.widgets.option_list import Option


# ---------------------------------------------------------------------------
# Everblush palette
# ---------------------------------------------------------------------------

BG = "#141b1e"
BG_ALT = "#232a2d"
BG_DEEP = "#0f1619"
FG = "#dadada"
MUTED = "#b3b9b8"
GREEN = "#8ccf7e"
RED = "#e57474"
YELLOW = "#e5c76b"
BLUE = "#67b0e8"
PURPLE = "#bab3e5"
MAGENTA = "#c47fd5"
CYAN = "#6cbfbf"
ORANGE = "#fcb163"

# Textual theme layer so popovers, selects, focus cursors and other
# framework-owned widgets also follow Everblush instead of the default theme.
EVERBLUSH_THEME = Theme(
    name="everblush",
    primary=GREEN,
    secondary=BLUE,
    accent=CYAN,
    foreground=FG,
    background=BG,
    surface=BG_ALT,
    panel=BG_DEEP,
    success=GREEN,
    warning=YELLOW,
    error=RED,
    dark=True,
    variables={
        "block-cursor-background": BG_ALT,
        "block-cursor-foreground": GREEN,
        "block-cursor-text-style": "bold",
        "block-hover-background": BG_ALT,
        "input-selection-background": "#8ccf7e55",
        "footer-key-foreground": GREEN,
        "scrollbar": BG_ALT,
        "scrollbar-hover": MUTED,
        "scrollbar-active": GREEN,
        "scrollbar-background": BG_DEEP,
    },
)

APP_TITLE = "PENGNET"
REFRESH_SECONDS = 1.0
HISTORY = 60


# Nerd Font / Unicode icons. Most terminals fall back gracefully if a glyph
# is unavailable.
ICONS = {
    "dashboard": "󰕮",
    "wifi": "󰤨",
    "interfaces": "󰈀",
    "addresses": "󰩟",
    "routes": "󰣺",
    "neighbours": "󰖟",
    "dns": "󰇖",
    "sockets": "󰗚",
    "firewall": "󰒃",
    "services": "󰒋",
    "diagnostics": "󰙏",
    "hardware": "󰒓",
    "logs": "󰆍",
    "system": "󰣇",
    "scan": "󰍉",
    "connect": "󰌘",
    "refresh": "󰑐",
}

PAGES: list[tuple[str, str, str]] = [
    ("dashboard", "Dashboard", ICONS["dashboard"]),
    ("wifi", "Wi-Fi", ICONS["wifi"]),
    ("interfaces", "Interfaces", ICONS["interfaces"]),
    ("addresses", "Addresses", ICONS["addresses"]),
    ("routes", "Routes", ICONS["routes"]),
    ("neighbours", "Neighbours", ICONS["neighbours"]),
    ("dns", "DNS", ICONS["dns"]),
    ("sockets", "Sockets", ICONS["sockets"]),
    ("firewall", "Firewall", ICONS["firewall"]),
    ("services", "Services", ICONS["services"]),
    ("diagnostics", "Diagnostics", ICONS["diagnostics"]),
    ("hardware", "Hardware", ICONS["hardware"]),
    ("logs", "Logs", ICONS["logs"]),
    ("system", "System", ICONS["system"]),
]
PAGE_KEYS = [name for name, _, _ in PAGES]


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_cmd(args: list[str], timeout: float = 5.0) -> tuple[int, str, str]:
    """Run a command without opening a shell or leaking terminal state."""
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        return 127, "", str(exc)


def human_bytes(value: float) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    value = max(0.0, float(value))
    idx = 0
    while value >= 1024.0 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    return f"{value:.1f} {units[idx]}"


def human_rate(mbps: float) -> str:
    if mbps < 0.001:
        return "0 Kb/s"
    if mbps < 1:
        return f"{mbps * 1000:.0f} Kb/s"
    return f"{mbps:.2f} Mb/s"


def compact(value: Any, width: int = 42) -> str:
    text = str(value).replace("\n", " ")
    if len(text) <= width:
        return text
    return text[: max(1, width - 1)] + "…"


def json_cmd(args: list[str], timeout: float = 5.0) -> Any:
    rc, out, _ = run_cmd(args, timeout)
    if rc != 0 or not out:
        return []
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return []


def default_interface() -> str | None:
    routes = json_cmd(["ip", "-j", "route", "show", "default"])
    if isinstance(routes, list):
        for row in routes:
            if isinstance(row, dict) and row.get("dev"):
                return str(row["dev"])
    names = [name for name in psutil.net_if_addrs() if name != "lo"]
    return names[0] if names else None


def wireless_devices() -> list[str]:
    devices: list[str] = []
    root = Path("/sys/class/net")
    try:
        for path in root.iterdir():
            if (path / "wireless").exists():
                devices.append(path.name)
    except OSError:
        pass
    return sorted(devices)


def interface_addresses(name: str | None) -> tuple[list[str], list[str]]:
    ipv4: list[str] = []
    ipv6: list[str] = []
    if not name:
        return ipv4, ipv6
    for row in psutil.net_if_addrs().get(name, []):
        if row.family == socket.AF_INET:
            ipv4.append(f"{row.address}/{row.netmask}" if row.netmask else row.address)
        elif row.family == socket.AF_INET6:
            ipv6.append(row.address.split("%", 1)[0])
    return ipv4, ipv6


def interface_counters(name: str | None):
    if not name:
        return None
    return psutil.net_io_counters(pernic=True).get(name)


def gateway() -> str:
    routes = json_cmd(["ip", "-j", "route", "show", "default"])
    if isinstance(routes, list):
        for row in routes:
            if isinstance(row, dict) and row.get("gateway"):
                return str(row["gateway"])
    return "—"


def current_routes() -> list[dict[str, Any]]:
    value = json_cmd(["ip", "-j", "route", "show", "table", "main"])
    return value if isinstance(value, list) else []


def current_rules() -> list[dict[str, Any]]:
    value = json_cmd(["ip", "-j", "rule", "show"])
    return value if isinstance(value, list) else []


def neighbour_rows() -> list[dict[str, Any]]:
    value = json_cmd(["ip", "-j", "neigh", "show"])
    return value if isinstance(value, list) else []


def dns_servers() -> list[str]:
    if command_exists("resolvectl"):
        rc, out, _ = run_cmd(["resolvectl", "dns"], timeout=4)
        if rc == 0:
            result: list[str] = []
            for line in out.splitlines():
                if ":" in line:
                    result.extend(line.split(":", 1)[1].split())
            return sorted(dict.fromkeys(result))
    try:
        text = Path("/etc/resolv.conf").read_text(errors="ignore")
        return re.findall(r"^nameserver\s+(\S+)", text, flags=re.M)
    except OSError:
        return []


def dns_link_status(interface: str | None) -> str:
    if interface and command_exists("resolvectl"):
        rc, out, _ = run_cmd(["resolvectl", "status", interface], timeout=4)
        if rc == 0:
            values: list[str] = []
            capture = False
            for line in out.splitlines():
                if "DNS Servers:" in line:
                    values.append(line.split(":", 1)[1].strip())
                    capture = True
                    continue
                if capture and line.startswith(" ") and line.strip():
                    values.append(line.strip())
                    continue
                if capture and line.strip() and not line.startswith(" "):
                    break
            return ", ".join(values) or ", ".join(dns_servers()) or "—"
    return ", ".join(dns_servers()) or "—"


def read_hostname() -> str:
    try:
        return socket.gethostname()
    except OSError:
        return "unknown"


def read_uptime() -> float | None:
    try:
        return float(Path("/proc/uptime").read_text().split()[0])
    except (OSError, ValueError, IndexError):
        return None


def human_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    seconds = max(0, int(seconds))
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    mins, _ = divmod(rem, 60)
    if days:
        return f"{days}d {hours}h {mins}m"
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def parse_iw_link(device: str | None) -> dict[str, str]:
    result: dict[str, str] = {
        "state": "disconnected",
        "ssid": "—",
        "bssid": "—",
        "signal": "—",
        "frequency": "—",
        "tx_bitrate": "—",
    }
    if not device or not command_exists("iw"):
        return result
    rc, out, _ = run_cmd(["iw", "dev", device, "link"], timeout=3)
    if rc != 0:
        return result
    if "Not connected" not in out:
        result["state"] = "connected"
    patterns = {
        "ssid": r"SSID:\s*(.+)",
        "signal": r"signal:\s*(-?\d+)\s*dBm",
        "frequency": r"freq:\s*(\d+)\s*MHz",
        "tx_bitrate": r"tx bitrate:\s*(.+)",
        "bssid": r"Connected to\s+([0-9A-Fa-f:]{17})",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, out)
        if match:
            result[key] = match.group(1).strip()
    return result


def parse_iwctl_kv(output: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def wifi_detail(device: str | None) -> dict[str, str]:
    result = parse_iw_link(device)
    if device and command_exists("iwctl"):
        rc, out, _ = run_cmd(["iwctl", "station", device, "show"], timeout=4)
        if rc == 0:
            data = parse_iwctl_kv(out)
            state = data.get("State") or result["state"]
            result["state"] = state
            result["ssid"] = result["ssid"] if result["ssid"] != "—" else data.get("Connected network", "—")
            result["signal"] = result["signal"] if result["signal"] != "—" else data.get("RSSI", "—")
            result["bssid"] = result["bssid"] if result["bssid"] != "—" else data.get("ConnectedBss", "—")
    return result


def parse_wifi_scan(output: str) -> list[tuple[str, str, str, str]]:
    """Best-effort parser for iwctl's get-networks table.

    iwd emits human-facing columns and may align them with variable spacing,
    so this parser deliberately favours a safe display over false precision.
    """
    rows: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("Network name") or line.startswith("---"):
            continue
        if line.lower().startswith("known network"):
            continue
        parts = re.split(r"\s{2,}", line)
        if len(parts) >= 3:
            ssid = parts[0].strip()
            security = parts[1].strip()
            signal = parts[2].strip()
            state = parts[3].strip() if len(parts) >= 4 else ""
            if ssid and ssid not in seen:
                seen.add(ssid)
                rows.append((ssid, security, signal, state))
    return rows


def get_network_scan(device: str | None) -> tuple[str, list[tuple[str, str, str, str]]]:
    if not device or not command_exists("iwctl"):
        return "iwctl or Wi-Fi device unavailable", []
    run_cmd(["iwctl", "station", device, "scan"], timeout=15)
    rc, out, err = run_cmd(["iwctl", "station", device, "get-networks"], timeout=8)
    if rc != 0:
        return err or "Wi-Fi scan failed", []
    rows = parse_wifi_scan(out)
    return out, rows


def public_ip() -> str:
    if not command_exists("curl"):
        return "unavailable"
    for args in (
        ["curl", "-4", "-fsS", "--max-time", "3", "https://api.ipify.org"],
        ["curl", "-6", "-fsS", "--max-time", "3", "https://api64.ipify.org"],
    ):
        rc, out, _ = run_cmd(args, timeout=5)
        if rc == 0 and out:
            return out.strip()
    return "unavailable"


def ping_host(host: str, count: int = 1) -> tuple[float | None, float | None, str]:
    if not command_exists("ping"):
        return None, None, "ping unavailable"
    rc, out, err = run_cmd(
        ["ping", "-n", "-c", str(max(1, count)), "-W", "2", host], timeout=8
    )
    combined = out or err
    times = [float(value) for value in re.findall(r"time[=<]([0-9.]+)\s*ms", combined)]
    loss = None
    loss_match = re.search(r"([0-9.]+)%\s*packet loss", combined)
    if loss_match:
        loss = float(loss_match.group(1))
    if times:
        return sum(times) / len(times), loss if loss is not None else 0.0, "online"
    return None, loss, "unreachable"


def dns_lookup(host: str) -> tuple[str, list[str]]:
    try:
        results = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        addresses = sorted({item[4][0] for item in results})
        return "resolved", addresses[:10]
    except OSError as exc:
        return "failed", [str(exc)]


def socket_counts() -> tuple[int, int, int, int]:
    if not command_exists("ss"):
        return 0, 0, 0, 0
    rc, out, _ = run_cmd(["ss", "-tunapH"], timeout=5)
    if rc != 0:
        return 0, 0, 0, 0
    tcp = sum(1 for line in out.splitlines() if line.startswith("tcp"))
    udp = sum(1 for line in out.splitlines() if line.startswith("udp"))
    listening = sum(1 for line in out.splitlines() if "LISTEN" in line)
    total = len([line for line in out.splitlines() if line.strip()])
    return tcp, udp, listening, total


def service_state(service: str) -> str:
    if not command_exists("systemctl"):
        return "unavailable"
    rc, out, err = run_cmd(["systemctl", "is-active", service], timeout=2)
    if rc == 0 and out:
        return out
    return "inactive"


def manager_snapshot() -> list[tuple[str, str]]:
    services = [
        "iwd",
        "NetworkManager",
        "systemd-networkd",
        "systemd-resolved",
        "dhcpcd",
        "nftables",
        "firewalld",
    ]
    return [(service, service_state(service)) for service in services]


def rfkill_output() -> str:
    if not command_exists("rfkill"):
        return "rfkill is not installed"
    rc, out, err = run_cmd(["rfkill", "list"], timeout=4)
    return out or err or "No RF-kill devices reported."


def firewall_data() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    rows.append(("nftables", service_state("nftables")))
    rows.append(("firewalld", service_state("firewalld")))
    if command_exists("nft"):
        rc, out, err = run_cmd(["nft", "list", "ruleset"], timeout=6)
        if rc == 0:
            lines = [line for line in out.splitlines() if line.strip()]
            rules = sum(1 for line in lines if line.strip().startswith(("ip", "ip6", "tcp", "udp", "ct", "iif", "oif", "counter", "meta")))
            rows.append(("nft ruleset", f"loaded • {rules} rule-ish lines"))
        else:
            rows.append(("nft ruleset", err or "unreadable"))
    else:
        rows.append(("nft", "not installed"))
    return rows


def command_inventory() -> list[tuple[str, str]]:
    names = [
        "ip",
        "iw",
        "iwctl",
        "ping",
        "ss",
        "resolvectl",
        "ethtool",
        "rfkill",
        "nft",
        "tracepath",
        "traceroute",
        "nmcli",
        "networkctl",
        "curl",
        "journalctl",
    ]
    return [(name, "✓ available" if command_exists(name) else "— missing") for name in names]


# ---------------------------------------------------------------------------
# Rich helpers
# ---------------------------------------------------------------------------


def status_text(value: str) -> Text:
    lowered = value.lower()
    if lowered in {"up", "connected", "active", "online", "resolved", "running", "✓ available"}:
        return Text(value, style=GREEN)
    if lowered in {"down", "disconnected", "inactive", "failed", "unreachable", "blocked", "— missing"}:
        return Text(value, style=RED)
    if "degraded" in lowered or "timeout" in lowered or "unavailable" in lowered:
        return Text(value, style=YELLOW)
    return Text(value, style=FG)


def info_table(title: str, headers: list[str], rows: list[tuple[Any, ...]], border: str = CYAN) -> Table:
    table = Table(title=title, expand=True, border_style=border, header_style=f"bold {FG}", padding=(0, 1))
    for header in headers:
        table.add_column(header, overflow="ellipsis")
    for row in rows:
        rendered: list[Any] = []
        for cell in row:
            if isinstance(cell, Text):
                rendered.append(cell)
            else:
                rendered.append(str(cell))
        table.add_row(*rendered)
    return table


def metric_card(icon: str, title: str, value: str, accent: str) -> Text:
    return Text.from_markup(f"[{accent}]{icon}[/]  [bold {FG}]{escape(title)}[/]\n[bold {accent}]{escape(value)}[/]")


def section_text(title: str, value: str, accent: str = CYAN) -> Text:
    return Text.from_markup(f"[bold {accent}]{escape(title)}[/]\n{escape(value)}")


# ---------------------------------------------------------------------------
# Modal / helper screens
# ---------------------------------------------------------------------------


class NoticeScreen(Screen[None]):
    CSS = f"""
    Screen {{ align: center middle; background: {BG_DEEP} 92%; }}
    #notice {{ width: 80%; height: 70%; background: {BG}; border: round {CYAN}; padding: 2; }}
    #notice_title {{ height: 2; color: {GREEN}; text-style: bold; }}
    #notice_body {{ height: 1fr; overflow-y: auto; }}
    #notice_hint {{ height: 2; color: {YELLOW}; }}
    """

    def __init__(self, title: str, body: str) -> None:
        super().__init__()
        self.title_text = title
        self.body = body

    def compose(self) -> ComposeResult:
        with Container(id="notice"):
            yield Static(self.title_text, id="notice_title")
            yield Static(self.body[:30000], id="notice_body")
            yield Static("Esc / Enter / any key • close", id="notice_hint")

    def on_key(self, event) -> None:
        self.dismiss()


class ConnectScreen(Screen[None]):
    CSS = f"""
    Screen {{ align: center middle; background: {BG_DEEP} 94%; }}
    #connect_box {{ width: 72%; height: 43%; background: {BG}; border: round {GREEN}; padding: 2; }}
    #connect_title {{ height: 2; color: {GREEN}; text-style: bold; }}
    Label {{ margin: 1 0 0 0; color: {MUTED}; }}
    Input {{ margin: 0 0 1 0; border: round {BG_ALT}; background: {BG_DEEP}; }}
    #buttons {{ height: 3; align: right middle; }}
    Button {{ margin-left: 1; }}
    #hint {{ color: {YELLOW}; }}
    """

    def __init__(self, device: str, ssid: str = "") -> None:
        super().__init__()
        self.device = device
        self.initial_ssid = ssid

    def compose(self) -> ComposeResult:
        with Vertical(id="connect_box"):
            yield Static(f"󰤨  CONNECT WI-FI  •  {self.device}", id="connect_title")
            yield Label("SSID")
            yield Input(value=self.initial_ssid, id="ssid")
            yield Label("Passphrase  •  leave empty for an open network")
            yield Input(placeholder="••••••••", password=True, id="passphrase")
            with Horizontal(id="buttons"):
                yield Button("Connect", id="do_connect", variant="success")
                yield Button("Cancel", id="cancel")
            yield Static("Enter on Connect  •  Esc to cancel", id="hint")

    def on_mount(self) -> None:
        self.query_one("#ssid", Input).focus()

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel":
            self.dismiss()
            return
        if event.button.id != "do_connect":
            return
        ssid = self.query_one("#ssid", Input).value.strip()
        passphrase = self.query_one("#passphrase", Input).value
        if not ssid:
            self.app.notify("SSID is required", severity="error")
            return
        if not command_exists("iwctl"):
            self.app.notify("iwctl is not installed", severity="error")
            return
        app = self.app
        if isinstance(app, PengNet):
            app.wifi_connect(self.device, ssid, passphrase)
        self.dismiss()


class CommandScreen(Screen[None]):
    CSS = f"""
    Screen {{ align: center middle; background: {BG_DEEP} 94%; }}
    #command_box {{ width: 82%; height: 72%; background: {BG}; border: round {PURPLE}; padding: 2; }}
    #command_title {{ height: 2; color: {PURPLE}; text-style: bold; }}
    Input {{ background: {BG_DEEP}; border: round {BG_ALT}; }}
    #result {{ height: 1fr; overflow-y: auto; margin-top: 1; }}
    #hint {{ color: {YELLOW}; height: 2; }}
    """

    def __init__(self) -> None:
        super().__init__()
        self.result = ""

    def compose(self) -> ComposeResult:
        with Vertical(id="command_box"):
            yield Static("󰘳  COMMAND PALETTE", id="command_title")
            yield Input(placeholder="e.g. ip route get 1.1.1.1", id="command")
            yield Static("", id="result")
            yield Static("Run read-only diagnostics. No shell expansion is performed.  •  Esc close", id="hint")

    def on_mount(self) -> None:
        self.query_one("#command", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        if not command:
            return
        parts = shlex.split(command)
        if parts and parts[0] in {"sudo", "su"}:
            self.query_one("#result", Static).update("Privilege escalation is intentionally disabled inside PENGNET.")
            return
        self.run_worker(lambda: self._run(parts), thread=True, exclusive=True, exit_on_error=False)

    def _run(self, parts: list[str]) -> None:
        allowed = {
            "ip", "iw", "iwctl", "ss", "resolvectl", "ping", "tracepath",
            "traceroute", "ethtool", "rfkill", "nft", "networkctl", "nmcli",
            "curl", "hostname", "uname", "journalctl",
        }
        blocked_tokens = {"set", "add", "del", "delete", "flush", "replace", "change", "connect", "disconnect", "power"}
        if not parts or parts[0] not in allowed:
            text = "Blocked: command palette only allows read-only network/system commands."
        elif any(token in blocked_tokens for token in parts[1:]):
            text = "Blocked: mutating network operations are disabled in the command palette."
        else:
            rc, out, err = run_cmd(parts, timeout=8)
            text = out or err or f"exit={rc}"
        self.call_from_thread(self._update_result, text[:30000])

    def _update_result(self, text: str) -> None:
        self.query_one("#result", Static).update(text)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss()


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------


class PengNet(App[None]):
    TITLE = "PENGNET • Everblush Network Control Centre"
    SUB_TITLE = "Arch Linux • Network observability & control"

    CSS = f"""
    * {{
        color: {FG};
    }}

    Screen {{
        background: {BG};
    }}

    Header {{
        height: 3;
        background: {BG_DEEP};
        color: {CYAN};
    }}

    Footer {{
        background: {BG_DEEP};
        color: {MUTED};
    }}

    #root {{
        height: 1fr;
    }}

    #sidebar {{
        width: 28;
        min-width: 28;
        background: {BG_DEEP};
        border: round {BG_ALT};
        padding: 1;
    }}

    #brand {{
        height: 6;
        content-align: center middle;
        color: {GREEN};
        text-style: bold;
        border: round {BG_ALT};
        background: {BG};
        padding: 1;
        margin-bottom: 1;
    }}

    #nav_label, #action_label {{
        height: 1;
        color: {MUTED};
        text-style: bold;
        margin: 1 1 0 1;
    }}

    #nav {{
        height: 1fr;
        border: none;
        background: transparent;
        padding: 0;
    }}

    #nav > .option-list--option {{
        color: {FG};
        padding: 0 1;
        height: 2;
    }}

    #nav > .option-list--option-highlighted {{
        background: {BG_ALT};
        color: {GREEN};
        text-style: bold;
    }}

    #nav > .option-list--option-hover {{
        background: {BG_ALT};
        color: {CYAN};
    }}

    #brand_meta {{
        height: 4;
        border: round {BG_ALT};
        background: {BG};
        padding: 1;
        color: {MUTED};
    }}

    #main {{
        width: 1fr;
        padding: 1;
    }}

    #toolbar {{
        height: 3;
        background: {BG_DEEP};
        border: round {BG_ALT};
        padding: 0 1;
    }}

    #page_title {{
        width: 1fr;
        content-align: left middle;
        color: {GREEN};
        text-style: bold;
    }}

    #filter {{
        width: 20;
        background: {BG};
        border: round {BG_ALT};
        margin-right: 1;
    }}

    Select {{
        width: 23;
        background: {BG};
        border: round {BG_ALT};
        margin-right: 1;
    }}

    #scan_btn, #connect_btn, #refresh_btn {{
        min-width: 5;
        margin-left: 1;
    }}

    #content {{
        height: 1fr;
        margin-top: 1;
    }}

    #cards {{
        height: 8;
        min-height: 8;
    }}

    .card {{
        width: 1fr;
        background: {BG_DEEP};
        border: round {BG_ALT};
        padding: 1;
        margin-right: 1;
    }}

    .card:last-child {{
        margin-right: 0;
    }}

    #graphs {{
        height: 16;
        min-height: 16;
        margin-top: 1;
    }}

    .graph {{
        width: 1fr;
        background: {BG_DEEP};
        border: round {BG_ALT};
        padding: 1;
        margin-right: 1;
    }}

    .graph:last-child {{
        margin-right: 0;
    }}

    Sparkline {{
        width: 1fr;
        height: 10;
    }}

    #table_wrap {{
        height: 1fr;
        margin-top: 1;
        background: {BG_DEEP};
        border: round {BG_ALT};
        padding: 1;
    }}

    #data {{
        height: 1fr;
        background: {BG_DEEP};
        border: none;
    }}

    DataTable {{
        background: {BG_DEEP};
        color: {FG};
        scrollbar-color: {BG_ALT};
        scrollbar-color-hover: {MUTED};
    }}

    DataTable .datatable--cursor {{
        background: {BG_ALT};
        color: {GREEN};
        text-style: bold;
    }}

    DataTable .datatable--header {{
        background: {BG_ALT};
        color: {CYAN};
        text-style: bold;
    }}

    DataTable .datatable--hover {{
        background: #2a3134;
    }}

    #detail {{
        height: 11;
        min-height: 11;
        background: {BG};
        border: round {BG_ALT};
        padding: 1;
        margin-top: 1;
        overflow-y: auto;
    }}

    .detail-title {{ color: {CYAN}; text-style: bold; }}

    .muted {{ color: {MUTED}; }}
    """

    # Textual exposes these key bindings through the footer.
    BINDINGS = [
        ("1", "go_dashboard", "Dashboard"),
        ("2", "go_wifi", "Wi-Fi"),
        ("3", "go_interfaces", "Interfaces"),
        ("4", "go_addresses", "Addresses"),
        ("5", "go_routes", "Routes"),
        ("6", "go_neighbours", "Neighbours"),
        ("7", "go_dns", "DNS"),
        ("8", "go_sockets", "Sockets"),
        ("9", "go_firewall", "Firewall"),
        ("0", "go_services", "Services"),
        ("-", "go_diagnostics", "Diagnostics"),
        ("=", "go_system", "System"),
        ("s", "scan", "Scan"),
        ("c", "connect", "Connect"),
        ("d", "disconnect", "Disconnect"),
        ("p", "wifi_power", "Wi-Fi power"),
        ("u", "interface_up", "Interface up"),
        ("x", "interface_down", "Interface down"),
        ("t", "trace", "Trace route"),
        ("a", "cycle_interface", "Next IF"),
        ("w", "cycle_wifi", "Next Wi-Fi"),
        ("r", "refresh_now", "Refresh"),
        ("l", "dns_flush", "DNS flush"),
        ("/", "command_palette", "Command"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.current_page = "dashboard"
        self.interface = default_interface()
        devices = wireless_devices()
        self.wifi = devices[0] if devices else None
        self.interfaces = [name for name in psutil.net_if_addrs() if name != "lo"]
        self.rx_history = deque([0.0] * HISTORY, maxlen=HISTORY)
        self.tx_history = deque([0.0] * HISTORY, maxlen=HISTORY)
        self.latency_history = deque([0.0] * HISTORY, maxlen=HISTORY)
        self.last_sample: dict[str, tuple[float, int, int]] = {}
        self.last_rx = 0.0
        self.last_tx = 0.0
        self.last_latency: float | None = None
        self.last_loss: float | None = None
        self.public_ip_cache = "—"
        self.public_ip_at = 0.0
        self.wifi_scan: list[tuple[str, str, str, str]] = []
        self.wifi_scan_raw = ""
        self.selected_row: dict[str, Any] | None = None
        self.status_line = "Starting…"
        self.filter_text = ""
        self._updating_selects = False
        self._last_page_render_at = 0.0
        self._snapshot: dict[str, Any] = {
            "wifi_detail": {
                "ssid": "—",
                "state": "unknown",
                "signal": "—",
                "bssid": "—",
                "frequency": "—",
                "tx_bitrate": "—",
            },
            "ipv4": [],
            "ipv6": [],
            "gateway": "—",
            "dns": "—",
            "sockets": (0, 0, 0, 0),
            "counters": None,
        }
        self._displayed_rows: list[tuple[Any, ...]] = []
        self._last_interface_options: tuple[str, ...] = ()
        self._last_wifi_options: tuple[str, ...] = ()

    # ----- compose -----

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="root"):
            with Vertical(id="sidebar"):
                yield Static("󰣇\nPENGNET\nEverblush", id="brand")
                yield Static("NAVIGATION", id="nav_label")
                yield OptionList(
                    *[Option(f"{icon}  {label}", id=name) for name, label, icon in PAGES],
                    id="nav",
                )
                yield Static(id="brand_meta")
            with Vertical(id="main"):
                with Horizontal(id="toolbar"):
                    yield Static(id="page_title")
                    yield Input(placeholder="⌕ filter…", id="filter")
                    yield Select([], id="interface_select", allow_blank=True, prompt="Interface")
                    yield Select([], id="wifi_select", allow_blank=True, prompt="Wi-Fi")
                    yield Button("󰍉", id="scan_btn", variant="primary")
                    yield Button("󰌘", id="connect_btn", variant="success")
                    yield Button("󰑐", id="refresh_btn", variant="default")
                with Vertical(id="content"):
                    with Horizontal(id="cards"):
                        yield Static(classes="card", id="card_link")
                        yield Static(classes="card", id="card_address")
                        yield Static(classes="card", id="card_gateway")
                        yield Static(classes="card", id="card_dns")
                        yield Static(classes="card", id="card_latency")
                    with Horizontal(id="graphs"):
                        with Vertical(classes="graph"):
                            yield Static("󰇚  RX • live Mbps")
                            yield Sparkline([0.0] * HISTORY, id="rx_graph")
                        with Vertical(classes="graph"):
                            yield Static("󰕒  TX • live Mbps")
                            yield Sparkline([0.0] * HISTORY, id="tx_graph")
                        with Vertical(classes="graph"):
                            yield Static("󰙏  Latency • live ms")
                            yield Sparkline([0.0] * HISTORY, id="lat_graph")
                    with Vertical(id="table_wrap"):
                        yield DataTable(id="data", cursor_type="row", zebra_stripes=True, show_row_labels=False)
                    yield Static(id="detail")
        yield Footer()

    def on_mount(self) -> None:
        self.register_theme(EVERBLUSH_THEME)
        self.theme = "everblush"
        self._configure_tables()
        self._refresh_selects()
        self._set_page("dashboard")
        self.set_interval(REFRESH_SECONDS, self.request_refresh)
        self.request_refresh()

    def _configure_tables(self) -> None:
        table = self.query_one("#data", DataTable)
        table.cursor_type = "row"
        table.show_cursor = True
        table.zebra_stripes = True

    # ----- worker / refresh -----

    def request_refresh(self) -> None:
        self.run_worker(
            self._refresh_worker,
            name="live-refresh",
            group="live-refresh",
            exclusive=True,
            thread=True,
            exit_on_error=False,
        )

    def _refresh_worker(self) -> None:
        interfaces = psutil.net_if_addrs()
        wireless = wireless_devices()
        interface = self.interface if self.interface in interfaces else default_interface()
        wifi = self.wifi if self.wifi in wireless else (wireless[:1] or [None])[0]

        rx, tx = self._sample_traffic(interface)
        gw = gateway()
        target = gw if gw != "—" else "1.1.1.1"
        latency, loss, _ = ping_host(target, count=1) if target else (None, None, "unreachable")

        ipv4, ipv6 = interface_addresses(interface)
        wifi_state = wifi_detail(wifi)
        dns_value = dns_link_status(interface)
        sockets_value = socket_counts()
        counters = interface_counters(interface)

        now = time.monotonic()
        pip = self.public_ip_cache
        pip_at = self.public_ip_at
        if now - pip_at > 120:
            pip = public_ip()
            pip_at = now

        self.call_from_thread(
            self._apply_refresh,
            interface,
            wifi,
            rx,
            tx,
            latency,
            loss,
            pip,
            pip_at,
            wifi_state,
            ipv4,
            ipv6,
            gw,
            dns_value,
            sockets_value,
            counters,
        )

    def _sample_traffic(self, interface: str | None) -> tuple[float, float]:
        counters = interface_counters(interface)
        if counters is None:
            return 0.0, 0.0
        now = time.monotonic()
        previous = self.last_sample.get(interface or "")
        self.last_sample[interface or ""] = (now, counters.bytes_recv, counters.bytes_sent)
        if previous is None:
            return 0.0, 0.0
        dt = max(0.001, now - previous[0])
        rx = max(0, counters.bytes_recv - previous[1]) * 8 / dt / 1_000_000
        tx = max(0, counters.bytes_sent - previous[2]) * 8 / dt / 1_000_000
        return rx, tx

    def _apply_refresh(
        self,
        interface: str | None,
        wifi: str | None,
        rx: float,
        tx: float,
        latency: float | None,
        loss: float | None,
        pip: str,
        pip_at: float,
        wifi_state: dict[str, str],
        ipv4: list[str],
        ipv6: list[str],
        gw: str,
        dns_value: str,
        sockets_value: tuple[int, int, int, int],
        counters: Any,
    ) -> None:
        self.interface = interface
        self.wifi = wifi
        self.last_rx = rx
        self.last_tx = tx
        self.last_latency = latency
        self.last_loss = loss
        self.public_ip_cache = pip
        self.public_ip_at = pip_at
        self._snapshot = {
            "wifi_detail": wifi_state,
            "ipv4": ipv4,
            "ipv6": ipv6,
            "gateway": gw,
            "dns": dns_value,
            "sockets": sockets_value,
            "counters": counters,
        }
        self.rx_history.append(rx)
        self.tx_history.append(tx)
        self.latency_history.append(latency or 0.0)

        self.query_one("#rx_graph", Sparkline).data = list(self.rx_history)
        self.query_one("#tx_graph", Sparkline).data = list(self.tx_history)
        self.query_one("#lat_graph", Sparkline).data = list(self.latency_history)

        self._refresh_selects()
        self._update_cards()
        self._update_sidebar_meta()
        if self.current_page == "dashboard":
            self._render_page()

    # ----- select controls -----

    def _refresh_selects(self) -> None:
        interfaces = tuple(sorted(name for name in psutil.net_if_addrs() if name != "lo"))
        wifis = tuple(wireless_devices())
        self.interfaces = list(interfaces)
        self._updating_selects = True
        try:
            interface_select = self.query_one("#interface_select", Select)
            if interfaces != self._last_interface_options:
                interface_select.set_options([(name, name) for name in interfaces])
                self._last_interface_options = interfaces
            if self.interface in interfaces and interface_select.value != self.interface:
                interface_select.value = self.interface

            wifi_select = self.query_one("#wifi_select", Select)
            if wifis != self._last_wifi_options:
                wifi_select.set_options([(name, name) for name in wifis])
                self._last_wifi_options = wifis
            if self.wifi in wifis and wifi_select.value != self.wifi:
                wifi_select.value = self.wifi
        except NoMatches:
            pass
        finally:
            self._updating_selects = False

    def on_select_changed(self, event: Select.Changed) -> None:
        if self._updating_selects:
            return
        if event.select.id == "interface_select" and event.value is not Select.NULL:
            self.interface = str(event.value)
            self.request_refresh()
        elif event.select.id == "wifi_select" and event.value is not Select.NULL:
            self.wifi = str(event.value)
            self._render_page()

    # ----- navigation -----

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        option_id = event.option.id
        if option_id is not None and option_id in PAGE_KEYS:
            self._set_page(str(option_id))

    def _set_page(self, page: str) -> None:
        if page not in PAGE_KEYS:
            return
        self.current_page = page
        nav = self.query_one("#nav", OptionList)
        try:
            for index, (name, _, _) in enumerate(PAGES):
                if name == page:
                    nav.highlighted = index
                    break
        except Exception:
            pass
        self._render_page()

    def _render_page(self) -> None:
        self._update_page_title()
        self._update_cards()
        table = self.query_one("#data", DataTable)
        table.clear(columns=True)
        self.selected_row = None
        self._displayed_rows = []

        method = getattr(self, f"render_{self.current_page}")
        columns, rows, detail = method()
        filter_text = self.filter_text.strip().lower()
        if filter_text:
            rows = [row for row in rows if filter_text in " ".join(str(cell) for cell in row).lower()]
        self._displayed_rows = list(rows)
        for column in columns:
            table.add_column(column)
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        if table.row_count:
            table.move_cursor(row=0, column=0)
        self.query_one("#detail", Static).update(detail)
        self._last_page_render_at = time.monotonic()

    def _update_page_title(self) -> None:
        label = next(label for name, label, _ in PAGES if name == self.current_page)
        icon = next(icon for name, _, icon in PAGES if name == self.current_page)
        self.query_one("#page_title", Static).update(f"{icon}  {label.upper()}")

    # ----- cards / sidebar -----

    def _link_state(self) -> str:
        if not self.interface:
            return "DOWN"
        stats = psutil.net_if_stats().get(self.interface)
        return "UP" if stats and stats.isup else "DOWN"

    def _update_cards(self) -> None:
        ipv4 = self._snapshot.get("ipv4", [])
        gw = str(self._snapshot.get("gateway", "—"))
        dns_value = str(self._snapshot.get("dns", "—"))
        card_values = [
            ("󰒄", "LINK", self._link_state(), GREEN if self._link_state() == "UP" else RED),
            ("󰩟", "IPv4", compact(ipv4[0] if ipv4 else "—", 24), BLUE),
            ("󰣺", "GATEWAY", gw, YELLOW),
            ("󰇖", "DNS", compact(dns_value, 24), MAGENTA),
            ("󰙏", "LATENCY", f"{self.last_latency:.1f} ms" if self.last_latency is not None else "—", CYAN),
        ]
        ids = ["card_link", "card_address", "card_gateway", "card_dns", "card_latency"]
        for widget_id, (icon, title, value, accent) in zip(ids, card_values):
            self.query_one(f"#{widget_id}", Static).update(metric_card(icon, title, value, accent))

    def _update_sidebar_meta(self) -> None:
        state = self._link_state()
        wifi = self._snapshot.get("wifi_detail") or {
            "ssid": "—",
            "state": "unknown",
        }
        self.query_one("#brand_meta", Static).update(
            Text.from_markup(
                f"[bold {CYAN}]HOST[/]  {escape(read_hostname())}\n"
                f"[bold {GREEN if state == 'UP' else RED}]LINK[/]  {state}  •  {escape(self.interface or 'none')}\n"
                f"[bold {PURPLE}]Wi-Fi[/]  {escape(compact(wifi['ssid'], 22))}\n"
                f"[bold {MUTED}]RX/TX[/]  {human_rate(self.last_rx)} / {human_rate(self.last_tx)}"
            )
        )

    # ------------------------------------------------------------------
    # Page renderers
    # ------------------------------------------------------------------

    def render_dashboard(self):
        counters = self._snapshot.get("counters")
        wifi = self._snapshot.get("wifi_detail") or {
            "ssid": "—",
            "state": "unknown",
            "signal": "—",
            "bssid": "—",
            "frequency": "—",
            "tx_bitrate": "—",
        }
        ipv4 = self._snapshot.get("ipv4", [])
        ipv6 = self._snapshot.get("ipv6", [])
        tcp, udp, listening, total = self._snapshot.get("sockets", (0, 0, 0, 0))
        gw = str(self._snapshot.get("gateway", "—"))
        dns_value = str(self._snapshot.get("dns", "—"))
        rows = [
            ("Interface", self.interface or "—", "Link", self._link_state()),
            ("Wi-Fi device", self.wifi or "—", "Wi-Fi state", wifi.get("state", "unknown")),
            ("SSID", wifi.get("ssid", "—"), "Signal", wifi.get("signal", "—")),
            ("IPv4", ", ".join(ipv4) or "—", "IPv6", ", ".join(ipv6[:2]) or "—"),
            ("Gateway", gw, "Public IP", self.public_ip_cache),
            ("DNS", dns_value, "Sockets", f"TCP {tcp} • UDP {udp} • Listen {listening}"),
            (
                "Traffic",
                f"↓ {human_bytes(counters.bytes_recv) if counters else '—'} / ↑ {human_bytes(counters.bytes_sent) if counters else '—'}",
                "Packets",
                f"↓ {counters.packets_recv:,} / ↑ {counters.packets_sent:,}" if counters else "—",
            ),
            ("Errors", f"RX {counters.errin if counters else 0} • TX {counters.errout if counters else 0}", "Drops", f"RX {counters.dropin if counters else 0} • TX {counters.dropout if counters else 0}"),
        ]
        detail = info_table("LIVE CONNECTION OVERVIEW", ["Metric", "Value", "Metric", "Value"], rows, GREEN)
        return ["Metric", "Value", "Metric", "Value"], rows, detail

    def render_wifi(self):
        wifi = self._snapshot.get("wifi_detail") or {
            "ssid": "—", "state": "unknown", "signal": "—",
            "bssid": "—", "frequency": "—", "tx_bitrate": "—",
        }
        rows = [
            ("Device", self.wifi or "—", "State", wifi["state"]),
            ("SSID", wifi["ssid"], "Signal", wifi["signal"]),
            ("BSSID", wifi["bssid"], "Frequency", wifi["frequency"]),
            ("TX bitrate", wifi["tx_bitrate"], "IPv4", ", ".join(interface_addresses(self.wifi)[0]) or "—"),
        ]
        self.status_line = "Press s to scan • c to connect selected/entered SSID • d disconnect • p power"
        detail = Group(
            info_table("WIRELESS LINK", ["Field", "Value", "Field", "Value"], rows, CYAN),
            Text.from_markup(f"[bold {YELLOW}]ACTIONS[/]  {escape(self.status_line)}"),
        )
        scan_rows = self.wifi_scan
        if scan_rows:
            return ["SSID", "Security", "Signal", "State"], scan_rows, detail
        return ["SSID", "Security", "Signal", "State"], [("No scan data", "—", "—", "Press s")], detail

    def render_interfaces(self):
        rows: list[tuple[str, ...]] = []
        stats = psutil.net_if_stats()
        counters = psutil.net_io_counters(pernic=True)
        for name in sorted(psutil.net_if_addrs()):
            if name == "lo":
                continue
            link = stats.get(name)
            count = counters.get(name)
            ips4, _ = interface_addresses(name)
            rows.append(
                (
                    name,
                    "UP" if link and link.isup else "DOWN",
                    str(link.mtu if link else "—"),
                    str(psutil.net_if_addrs()[name][0].address if psutil.net_if_addrs()[name] else "—"),
                    ", ".join(ips4[:1]) or "—",
                    human_bytes(count.bytes_recv) if count else "—",
                    human_bytes(count.bytes_sent) if count else "—",
                    f"{count.errin}/{count.errout}" if count else "—",
                    f"{count.dropin}/{count.dropout}" if count else "—",
                )
            )
        detail = Text.from_markup(f"[bold {CYAN}]SELECT AN INTERFACE[/]  cursor with mouse/keys • u up • x down • a next")
        return ["IF", "STATE", "MTU", "ADDR", "IPv4", "RX", "TX", "ERR", "DROP"], rows, detail

    def render_addresses(self):
        rows: list[tuple[str, str, str, str]] = []
        for name, entries in psutil.net_if_addrs().items():
            for entry in entries:
                family = getattr(entry.family, "name", str(entry.family))
                if entry.family == socket.AF_INET:
                    family = "IPv4"
                elif entry.family == socket.AF_INET6:
                    family = "IPv6"
                elif "AF_PACKET" in family or "AF_LINK" in family:
                    family = "MAC"
                rows.append((name, family, entry.address, entry.netmask or "—"))
        detail = info_table("ADDRESS INVENTORY", ["Interface", "Family", "Address", "Netmask"] , [], BLUE)
        return ["Interface", "Family", "Address", "Netmask"], rows, detail

    def render_routes(self):
        rows: list[tuple[str, str, str, str, str]] = []
        for route in current_routes():
            rows.append(
                (
                    str(route.get("dst", "default")),
                    str(route.get("gateway", "—")),
                    str(route.get("dev", "—")),
                    str(route.get("metric", "—")),
                    str(route.get("protocol", "—")),
                )
            )
        rules = current_rules()
        rule_hint = f"Main table routes: {len(rows)} • policy rules: {len(rules)} • gateway: {gateway()}"
        detail = Text.from_markup(f"[bold {YELLOW}]ROUTING[/]  {escape(rule_hint)}")
        return ["Destination", "Gateway", "Device", "Metric", "Protocol"], rows, detail

    def render_neighbours(self):
        rows: list[tuple[str, str, str, str, str]] = []
        for entry in neighbour_rows():
            rows.append(
                (
                    str(entry.get("dev", "—")),
                    str(entry.get("dst", "—")),
                    str(entry.get("lladdr", "—")),
                    str(entry.get("state", "—")),
                    str(entry.get("router", "")),
                )
            )
        detail = Text.from_markup(f"[bold {CYAN}]NEIGHBOUR TABLE[/]  ARP / IPv6 NDP • {len(rows)} visible entries")
        return ["Device", "IP", "MAC", "State", "Router"], rows, detail

    def render_dns(self):
        servers = dns_servers()
        rows = [("Configured", server, "resolvectl" if command_exists("resolvectl") else "/etc/resolv.conf") for server in servers]
        if not rows:
            rows = [("Configured", "—", "No DNS server detected")]
        if command_exists("resolvectl"):
            rc, out, err = run_cmd(["resolvectl", "status"], timeout=5)
            body = out or err or "No resolver status."
        else:
            try:
                body = Path("/etc/resolv.conf").read_text(errors="ignore")
            except OSError as exc:
                body = str(exc)
        detail = Group(
            info_table("DNS CONFIGURATION", ["Type", "Server", "Source"], rows, MAGENTA),
            Text.from_markup(f"[bold {MAGENTA}]ACTIVE LINK[/]  {escape(dns_link_status(self.interface))}"),
            Text(body[:10000]),
        )
        return ["Type", "Server", "Source"], rows, detail

    def render_sockets(self):
        rows: list[tuple[str, str, str, str, str]] = []
        if command_exists("ss"):
            rc, out, err = run_cmd(["ss", "-tunapH"], timeout=6)
            for line in (out or err).splitlines()[:150]:
                parts = re.split(r"\s+", line.strip())
                if len(parts) >= 5:
                    rows.append((parts[0], parts[1], parts[2], parts[3], " ".join(parts[4:])))
        tcp, udp, listening, total = socket_counts()
        detail = Text.from_markup(f"[bold {CYAN}]SOCKETS[/]  TCP={tcp} • UDP={udp} • LISTEN={listening} • TOTAL={total}")
        return ["Netid", "State", "Recv-Q", "Send-Q", "Local / Peer / Process"], rows, detail

    def render_firewall(self):
        rows = firewall_data()
        if command_exists("nft"):
            rc, out, err = run_cmd(["nft", "list", "ruleset"], timeout=6)
            if rc == 0:
                lines = [line.strip() for line in out.splitlines() if line.strip()]
                sample = [("nft", line[:100]) for line in lines[:80]]
                return ["Source", "Rule / State"], sample, info_table("FIREWALL SERVICES", ["Component", "State"], rows, RED)
        return ["Component", "State"], rows, info_table("FIREWALL SERVICES", ["Component", "State"], rows, RED)

    def render_services(self):
        rows = manager_snapshot()
        active = sum(1 for _, state in rows if state == "active")
        detail = Group(
            Text.from_markup(f"[bold {GREEN}]NETWORK SERVICES[/]  {active}/{len(rows)} active"),
            Text.from_markup("[bold {YELLOW}]MANAGERS[/]  iwd • NetworkManager • systemd-networkd • systemd-resolved • dhcpcd"),
        )
        return ["Service", "State"], rows, detail

    def render_diagnostics(self):
        gw = str(self._snapshot.get("gateway", "—"))
        latency = self.last_latency
        loss = self.last_loss
        dns_state, dns_values = dns_lookup("archlinux.org")
        checks = [
            ("Default route", gw, "PASS" if gw != "—" else "FAIL"),
            ("Gateway ping", f"{latency:.1f} ms" if latency is not None else "unreachable", "PASS" if latency is not None else "FAIL"),
            ("Packet loss", f"{loss:.1f}%" if loss is not None else "—", "PASS" if loss is not None and loss == 0 else "INFO"),
            ("DNS archlinux.org", ", ".join(dns_values[:3]), dns_state.upper()),
            ("iproute2", "available" if command_exists("ip") else "missing", "INFO"),
            ("iwd/iwctl", "available" if command_exists("iwctl") else "missing", "INFO"),
            ("Socket tool", "available" if command_exists("ss") else "missing", "INFO"),
            ("DNS tool", "available" if command_exists("resolvectl") else "fallback", "INFO"),
            ("Route trace", "available" if command_exists("tracepath") or command_exists("traceroute") else "missing", "INFO"),
        ]
        detail = Text.from_markup(f"[bold {CYAN}]DIAGNOSTIC TARGET[/]  {escape(gw if gw != '—' else '1.1.1.1')}  •  Use / for custom read-only commands")
        return ["Check", "Result", "Type"], checks, detail

    def render_hardware(self):
        rows: list[tuple[str, str]] = []
        if self.interface and command_exists("ethtool"):
            rc, out, err = run_cmd(["ethtool", self.interface], timeout=5)
            for line in (out or err).splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    rows.append((f"ethtool:{key.strip()}", value.strip()))
        if self.wifi and command_exists("iw"):
            rc, out, err = run_cmd(["iw", "dev", self.wifi, "info"], timeout=5)
            rows.extend(("iw", line.strip()) for line in (out or err).splitlines() if line.strip())
        rf = rfkill_output()
        rows.extend(("rfkill", line) for line in rf.splitlines() if line.strip())
        detail = Text.from_markup(f"[bold {BLUE}]HARDWARE[/]  interface={escape(self.interface or 'none')} • wireless={escape(self.wifi or 'none')}")
        return ["Source", "Value"], rows[:180], detail

    def render_logs(self):
        if not command_exists("journalctl"):
            return ["Service", "Log", "Age"], [("journalctl", "not installed", "—")], Text("journalctl is unavailable.")

        units = ["iwd", "NetworkManager", "systemd-networkd", "systemd-resolved"]
        args = ["journalctl"]
        for unit in units:
            args += ["-u", unit]
        args += ["--since", "-15 min", "-n", "120", "--no-pager", "-o", "short-iso"]
        rc, out, err = run_cmd(args, timeout=6)
        raw = out or err
        rows = [("network", line[:150], "recent") for line in raw.splitlines()[-120:] if line.strip()]
        if not rows:
            rows = [("network", "No recent network journal entries.", "—")]
        detail = Text.from_markup(
            f"[bold {MAGENTA}]NETWORK JOURNAL[/]  last 15 minutes • {len(rows)} visible entries"
        )
        return ["Service", "Log", "Age"], rows, detail

    def render_system(self):
        uname = os.uname()
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        load = os.getloadavg() if hasattr(os, "getloadavg") else (0, 0, 0)
        rows = [
            ("Hostname", read_hostname(), "Kernel", uname.release),
            ("OS", "Arch Linux", "Architecture", uname.machine),
            ("Uptime", human_duration(read_uptime()), "Python", f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"),
            ("CPU", f"{psutil.cpu_percent(interval=None):.0f}%", "Load", "/".join(f"{v:.2f}" for v in load)),
            ("Memory", f"{vm.percent:.0f}% • {human_bytes(vm.used)} / {human_bytes(vm.total)}", "Swap", f"{swap.percent:.0f}%"),
            ("Public IP", self.public_ip_cache, "Interface", self.interface or "—"),
        ]
        detail = info_table("HOST / RUNTIME", ["Field", "Value", "Field", "Value"], rows, GREEN)
        return ["Field", "Value", "Field", "Value"], rows, detail

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "filter":
            return
        self.filter_text = event.value
        self._render_page()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "scan_btn":
            self.action_scan()
        elif button_id == "connect_btn":
            self.action_connect()
        elif button_id == "refresh_btn":
            self.action_refresh_now()

    # ------------------------------------------------------------------
    # Data table interaction
    # ------------------------------------------------------------------

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        row_index = event.cursor_row
        self._inspect_row(row_index)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self._inspect_row(event.cursor_row)
        if self.current_page == "wifi":
            ssid = self._wifi_ssid_from_row(event.cursor_row)
            if ssid:
                self.notify(f"Selected Wi-Fi: {ssid}", severity="information")
        elif self.current_page == "interfaces":
            try:
                row = self.query_one("#data", DataTable).get_row_at(event.cursor_row)
                if row:
                    selected = str(row[0])
                    if selected in psutil.net_if_addrs():
                        self.interface = selected
                        self.request_refresh()
                        self.notify(f"Active interface: {selected}", severity="information")
            except Exception:
                pass

    def _inspect_row(self, row_index: int) -> None:
        table = self.query_one("#data", DataTable)
        try:
            cells = [str(cell) for cell in table.get_row_at(row_index)]
        except Exception:
            return
        if not cells:
            return
        preview = "  •  ".join(compact(cell, 28) for cell in cells[:6])
        self.query_one("#detail", Static).update(
            Text.from_markup(f"[bold {CYAN}]CURSOR[/]  row {row_index + 1}  •  {escape(preview)}")
        )

    def _wifi_ssid_from_row(self, row_index: int) -> str | None:
        rows = self._displayed_rows if self.current_page == "wifi" else self.wifi_scan
        if not 0 <= row_index < len(rows):
            return None
        return str(rows[row_index][0])

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_go_dashboard(self): self._set_page("dashboard")
    def action_go_wifi(self): self._set_page("wifi")
    def action_go_interfaces(self): self._set_page("interfaces")
    def action_go_addresses(self): self._set_page("addresses")
    def action_go_routes(self): self._set_page("routes")
    def action_go_neighbours(self): self._set_page("neighbours")
    def action_go_dns(self): self._set_page("dns")
    def action_go_sockets(self): self._set_page("sockets")
    def action_go_firewall(self): self._set_page("firewall")
    def action_go_services(self): self._set_page("services")
    def action_go_diagnostics(self): self._set_page("diagnostics")
    def action_go_system(self): self._set_page("system")

    def action_scan(self) -> None:
        if not self.wifi:
            self.push_screen(NoticeScreen("󰤨  WI-FI SCAN", "No wireless device was detected."))
            return
        self.run_worker(self._scan_worker, name="wifi-scan", group="actions", exclusive=True, thread=True, exit_on_error=False)

    def _scan_worker(self) -> None:
        raw, rows = get_network_scan(self.wifi)
        self.call_from_thread(self._apply_scan, raw, rows)

    def _apply_scan(self, raw: str, rows: list[tuple[str, str, str, str]]) -> None:
        self.wifi_scan_raw = raw
        self.wifi_scan = rows
        self._set_page("wifi")
        self.notify(f"Wi-Fi scan complete • {len(rows)} networks", severity="information")

    def action_connect(self) -> None:
        if not self.wifi:
            self.notify("No Wi-Fi device detected", severity="error")
            return
        ssid = None
        if self.current_page == "wifi":
            try:
                row = self.query_one("#data", DataTable).cursor_row
                ssid = self._wifi_ssid_from_row(row)
            except Exception:
                pass
        self.push_screen(ConnectScreen(self.wifi, ssid or ""))

    def wifi_connect(self, device: str, ssid: str, passphrase: str) -> None:
        args = ["iwctl"]
        if passphrase:
            args.append(f"--passphrase={passphrase}")
        args += ["station", device, "connect", ssid]
        self.run_worker(lambda: self._run_action("󰌘  CONNECT", args), name="wifi-connect", group="actions", exclusive=True, thread=True, exit_on_error=False)

    def action_disconnect(self) -> None:
        if not self.wifi or not command_exists("iwctl"):
            self.notify("iwctl/Wi-Fi unavailable", severity="error")
            return
        self.run_worker(lambda: self._run_action("󰤨  DISCONNECT", ["iwctl", "station", self.wifi, "disconnect"]), name="wifi-disconnect", group="actions", exclusive=True, thread=True, exit_on_error=False)

    def action_wifi_power(self) -> None:
        if not self.wifi or not command_exists("iwctl"):
            self.notify("iwctl/Wi-Fi unavailable", severity="error")
            return
        self.run_worker(self._wifi_power_worker, name="wifi-power", group="actions", exclusive=True, thread=True, exit_on_error=False)

    def _wifi_power_worker(self) -> None:
        rc, out, err = run_cmd(["iwctl", "device", self.wifi or "", "show"], timeout=4)
        data = parse_iwctl_kv(out) if rc == 0 else {}
        current = data.get("Powered", "on").lower()
        new_state = "off" if current == "on" else "on"
        result = run_cmd(["iwctl", "device", self.wifi or "", "set-property", "Powered", new_state], timeout=8)
        self.call_from_thread(self._action_result, "󰤨  WI-FI POWER", result)

    def _run_action(self, title: str, args: list[str]) -> None:
        result = run_cmd(args, timeout=30)
        self.call_from_thread(self._action_result, title, result)

    def _action_result(self, title: str, result: tuple[int, str, str]) -> None:
        rc, out, err = result
        body = out or err or ("OK" if rc == 0 else f"Command failed with exit={rc}")
        self.push_screen(NoticeScreen(title, body))
        self.request_refresh()

    def action_dns_flush(self) -> None:
        if not command_exists("resolvectl"):
            self.notify("resolvectl is unavailable", severity="error")
            return
        self.run_worker(
            lambda: self._run_action("󰇖  DNS CACHE FLUSH", ["resolvectl", "flush-caches"]),
            name="dns-flush", group="actions", exclusive=True, thread=True,
        )

    def action_cycle_interface(self) -> None:
        names = sorted([name for name in psutil.net_if_addrs() if name != "lo"])
        if not names:
            return
        current = names.index(self.interface) if self.interface in names else -1
        self.interface = names[(current + 1) % len(names)]
        self.request_refresh()

    def action_cycle_wifi(self) -> None:
        devices = wireless_devices()
        if not devices:
            self.notify("No Wi-Fi interface detected", severity="error")
            return
        current = devices.index(self.wifi) if self.wifi in devices else -1
        self.wifi = devices[(current + 1) % len(devices)]
        self._render_page()

    def action_interface_up(self) -> None:
        if not self.interface:
            return
        self.run_worker(lambda: self._run_action("󰒄  INTERFACE UP", ["ip", "link", "set", "dev", self.interface or "", "up"]), name="if-up", group="actions", exclusive=True, thread=True, exit_on_error=False)

    def action_interface_down(self) -> None:
        if not self.interface:
            return
        self.run_worker(lambda: self._run_action("󰒄  INTERFACE DOWN", ["ip", "link", "set", "dev", self.interface or "", "down"]), name="if-down", group="actions", exclusive=True, thread=True, exit_on_error=False)

    def action_trace(self) -> None:
        target = gateway()
        if target == "—":
            target = "1.1.1.1"
        if command_exists("tracepath"):
            args = ["tracepath", "-m", "8", target]
        elif command_exists("traceroute"):
            args = ["traceroute", "-m", "8", "-w", "1", target]
        else:
            self.notify("tracepath/traceroute is not installed", severity="error")
            return
        self.run_worker(
            lambda: self._run_action("󰣺  TRACE ROUTE", args),
            name="trace", group="actions", exclusive=True, thread=True,
        )

    def action_refresh_now(self):
        self.request_refresh()

    def action_command_palette(self):
        self.push_screen(CommandScreen())

    # Optional richer actions available from special pages.
    def on_key(self, event) -> None:
        if event.key == "f5":
            self.request_refresh()
        elif event.key == "escape":
            self.pop_screen() if len(self.screen_stack) > 1 else None

    def action_quit(self):
        self.exit()


def validate_environment() -> list[str]:
    required = ["ip", "ping"]
    return [name for name in required if not command_exists(name)]


def main() -> None:
    missing = validate_environment()
    if missing:
        print(f"PENGNET: missing required command(s): {', '.join(missing)}")
        print("Arch Linux: sudo pacman -S --needed iproute2 iputils")
        raise SystemExit(1)
    PengNet().run()


if __name__ == "__main__":
    main()
