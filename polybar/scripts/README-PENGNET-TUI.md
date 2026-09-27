# PENGNET 🐧📡

Everblush network control centre for Arch Linux. A mouse-friendly Textual TUI with live monitoring, selectable tables, Wi-Fi control, Linux networking inspection, diagnostics, and system visibility.

## UI

- Everblush dark palette
- Cursor / mouse navigation in the sidebar
- Cursor-enabled `DataTable` views
- Interface and Wi-Fi dropdown selectors
- Live RX / TX / latency sparklines
- Filter box for the active table
- Action buttons for scan, connect, refresh
- Modal connection form with hidden passphrase input
- Command palette restricted to read-only networking commands

## Pages

| Page | What it shows |
|---|---|
| `Dashboard` | Link, IPv4, gateway, DNS, latency, Wi-Fi, sockets, traffic, packets, errors, drops |
| `Wi-Fi` | Wireless link state, SSID, BSSID, signal, frequency, bitrate, scan table |
| `Interfaces` | Interface state, MTU, address, IPv4, RX/TX, errors, drops |
| `Addresses` | IPv4, IPv6, MAC and netmask inventory |
| `Routes` | Main routing table, metrics, gateway, protocol, policy-rule count |
| `Neighbours` | ARP / IPv6 NDP neighbour table |
| `DNS` | Resolver servers, active-link DNS and resolver status |
| `Sockets` | TCP/UDP sockets, state, queues and process endpoint data |
| `Firewall` | nftables / firewalld state plus visible nftables rules |
| `Services` | iwd, NetworkManager, systemd-networkd, resolved, dhcpcd and firewall services |
| `Diagnostics` | Default route, gateway ping, packet loss, DNS resolution and tool availability |
| `Hardware` | ethtool, iw and rfkill information |
| `Logs` | Recent journal entries for common network services |
| `System` | Hostname, kernel, uptime, CPU, load, memory, swap and public IP |

## Arch packages

```bash
sudo pacman -S --needed \
  iwd \
  iproute2 \
  iputils \
  iw \
  ethtool \
  nftables \
  python-textual \
  python-rich \
  python-psutil \
  curl
```

The Python dependencies can also be installed with:

```bash
pip install -r requirements.txt --break-system-packages
```

## Run

```bash
chmod +x pengnet.py
./pengnet.py
```

## Controls

```text
Mouse / ↑ ↓ / Enter   navigate menus and tables
1                    Dashboard
2                    Wi-Fi
3                    Interfaces
4                    Addresses
5                    Routes
6                    Neighbours
7                    DNS
8                    Sockets
9                    Firewall
0                    Services
-                    Diagnostics
=                    System
s                    Wi-Fi scan
c                    Connect to selected Wi-Fi
d                    Disconnect Wi-Fi
p                    Wi-Fi power toggle
u                    Bring selected interface up
x                    Bring selected interface down
a                    Next interface
w                    Next Wi-Fi device
l                    Flush DNS cache via resolvectl
r / F5               Refresh
/                    Read-only network command palette
q                    Quit
```

## Notes

PENGNET does not persist Wi-Fi passwords. The command palette deliberately blocks privilege escalation and common mutating network subcommands. Interface up/down, Wi-Fi operations and DNS cache flush still depend on the local Linux permissions, daemon and network-manager setup.

The live dashboard reads real local counters and system/network state; graphs are not simulated.
