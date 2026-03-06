#!/usr/bin/env python3

import sys
import subprocess
import os
import json
import signal
import ipaddress
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtDBus import QDBusConnection
from PyQt6.QtCore import QObject, pyqtSlot


###############################################################################

# region Constants

PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(PROJECT_DIR, "dns-providers.json")
ICON_DIR = os.path.join(PROJECT_DIR, "icons")
APP_ID = "quick_dns_switcher"
APP_NAME = "Quick DNS switcher"
DIALOG_ERROR_TITLE = f"Error - {APP_NAME}"
AUTO_MODE_NAME = "Automatic"
AUTO_MODE_ICON = "network-workgroup"
DEFAULT_MODE_ICON = "network-server"

# endregion

###############################################################################


class NetworkMonitor(QObject):
    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(update_state)

    @pyqtSlot(int)
    def properties_changed(self, state):
        self.timer.start(500)


# region Functions

def display_error_dialog(content):
    QMessageBox.critical(None, DIALOG_ERROR_TITLE, content)


def load_dns_providers():
    if not os.path.exists(CONFIG_FILE):
        display_error_dialog(f"DNS configuration file not found:\n\n{CONFIG_FILE}")
        sys.exit(1)
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        display_error_dialog(f"Invalid JSON format in DNS configuration file:\n\n{CONFIG_FILE}\n\n{e}")
        sys.exit(1)
    except Exception as e:
        display_error_dialog(f"Unexpected error loading DNS configuration file:\n\n{e}")
        sys.exit(1)


def execute_command(args, output=True, raise_error=True):
    try:
        return subprocess.run(args, capture_output=output, text=True, check=raise_error)
    except subprocess.CalledProcessError as e:
        display_error_dialog(f"Error executing command:\n\n{' '.join(args)}\n\n{e}")
        sys.exit(1)


def get_provider_dns(provider):
    ipv4 = [ip for ip in [provider.get("ipv4_1"), provider.get("ipv4_2")] if ip]
    ipv6 = [ip for ip in [provider.get("ipv6_1"), provider.get("ipv6_2")] if ip]
    return ipv4, ipv6


def get_active_connections_with_dns():
    conns = []
    try:
        result = execute_command(["nmcli", "-t", "-f", "GENERAL.CONNECTION,GENERAL.DEVICE,IP4.DNS,IP6.DNS", "device", "show"])
        name = None
        device = None
        ipv4 = []
        ipv6 = []
        
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
                
            if line.startswith("GENERAL.CONNECTION:"):
                # Guarda el bloque anterior antes de empezar uno nuevo
                if name and device and device not in ("lo", "tun0", ""):
                    conns.append((name, device, ipv4.copy(), ipv6.copy()))
                
                name = line.split(":", 1)[1].strip()
                device = None
                ipv4 = []
                ipv6 = []
            elif line.startswith("GENERAL.DEVICE:"):
                device = line.split(":", 1)[1].strip()
            elif line.startswith("IP4.DNS"):
                ip = line.split(":", 1)[1].strip()
                if ip:
                    ipv4.append(ip)
            elif line.startswith("IP6.DNS"):
                ip = line.split(":", 1)[1].strip()
                if ip:
                    ipv6.append(ip)

        # Añade el último bloque al finalizar el bucle
        if name and device and device not in ("lo", "tun0", ""):
            conns.append((name, device, ipv4.copy(), ipv6.copy()))

    except Exception:
        pass

    return conns


def get_current_dns():
    ipv4_list = []
    ipv6_list = []
    for _, _, v4, v6 in get_active_connections_with_dns():
        ipv4_list.extend(v4)
        ipv6_list.extend(v6)
    ipv4_list = list(dict.fromkeys(ipv4_list))
    ipv6_list = list(dict.fromkeys(ipv6_list))
    return {"ipv4": ipv4_list, "ipv6": ipv6_list}


def set_dns(ipv4_list, ipv6_list):
    print("SET DNS:", ipv4_list, ipv6_list)
    v4 = ",".join(ipv4_list)
    v6 = ",".join(ipv6_list)
    connections = get_active_connections_with_dns()
    for name, device, current_v4, current_v6 in connections:
        if set(current_v4) == set(ipv4_list) and set(current_v6) == set(ipv6_list):
            continue

        if ipv4_list:
            execute_command(["nmcli", "connection", "modify", name, "ipv4.ignore-auto-dns", "yes", "ipv4.dns", v4], False)
        else:
            execute_command(["nmcli", "connection", "modify", name, "ipv4.ignore-auto-dns", "no", "ipv4.dns", ""], False)

        if ipv6_list:
            execute_command(["nmcli", "connection", "modify", name, "ipv6.ignore-auto-dns", "yes", "ipv6.dns", v6], False)
        else:
            execute_command(["nmcli", "connection", "modify", name, "ipv6.ignore-auto-dns", "no", "ipv6.dns", ""], False)

        _ = execute_command(["nmcli", "device", "reapply", device], False, False)

    QTimer.singleShot(500, update_state)


def detect_active_provider(current_dns):
    for name, data in DNS_PROVIDERS.items():
        v4_prov, v6_prov = get_provider_dns(data)
        match_v4 = set(v4_prov) == set(current_dns["ipv4"]) if v4_prov else not current_dns["ipv4"]
        match_v6 = set(v6_prov) == set(current_dns["ipv6"]) if v6_prov else not current_dns["ipv6"]  
        if match_v4 and match_v6:
            return name

    if current_dns["ipv4"] or current_dns["ipv6"]:
        return AUTO_MODE_NAME

    return "Disconnected"


def monitor_network_changes():
    global nm_monitor
    nm_monitor = NetworkMonitor()
    bus = QDBusConnection.systemBus()
    bus.connect(
        "org.freedesktop.NetworkManager",
        "/org/freedesktop/NetworkManager",
        "org.freedesktop.NetworkManager",
        "StateChanged",
        nm_monitor.properties_changed,
    )


def update_state():
    global last_dns
    current_dns = get_current_dns()
    active = detect_active_provider(current_dns)
    icon_name = None
    icon_file = None

    print(f"active: {active}\ncurrentDNS: {current_dns}\nlastDNS:{last_dns}")

    # Update menu and icon
    if active == AUTO_MODE_NAME:
        auto_action.setText(f"✔ {AUTO_MODE_NAME}")
        tray.setIcon(QIcon.fromTheme(AUTO_MODE_ICON))
    else:
        auto_action.setText(AUTO_MODE_NAME)
        if active and active in DNS_PROVIDERS:
            icon_name = DNS_PROVIDERS[active].get("icon")
            icon_file = os.path.join(ICON_DIR, icon_name)
            if icon_name and os.path.exists(icon_file):
                tray.setIcon(QIcon(icon_file))
            else:
                tray.setIcon(QIcon.fromTheme(DEFAULT_MODE_ICON))
    for name, action in actions.items():
        action.setText(f"✔ {name}" if name == active else name)

    # Notify if changed
    all_ips = current_dns["ipv4"] + current_dns["ipv6"]
    if last_dns is not None and current_dns != last_dns:
        msg = [f"DNS changed to {active}.\n \n"]
        #msg = []
        if all_ips:
            all_ips_formatted = [f" • <i>{ip}</i>" for ip in all_ips]
            msg.append("\n".join(all_ips_formatted))
        icon_file = icon_file if icon_file else AUTO_MODE_ICON
        #execute_command(["notify-send", "-a", APP_NAME, "-i", icon_file, APP_NAME, "\n".join(msg)])
        #execute_command(["notify-send", "-a", APP_NAME, "-i", icon_file, "-t", "5000", active, "\n".join(msg)])
        execute_command(["notify-send", "-a", APP_NAME, "-i", icon_file, "-t", "5000", f"{active} DNS", "\n".join(msg)])
    last_dns = current_dns

    # Update tooltip
    tooltip = (
        f"{APP_NAME}\n"
        f"——————————\n"
        f"{active}\n\n"
        f"{'\n'.join(current_dns["ipv4"])}\n"
        f"{'\n'.join(current_dns["ipv6"])}"
    )
    tray.setToolTip(tooltip)


def make_set_dns_action(ipv4_list, ipv6_list):
    def handler(checked=False):
        set_dns(ipv4_list, ipv6_list)
    return handler


def ensure_single_instance():
    socket = QLocalSocket()
    socket.connectToServer(APP_ID)
    if socket.waitForConnected(500):
        socket.close()
        pid_file = "/tmp/kde_quick_dns_switcher.pid"
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r") as f:
                    old_pid = int(f.read().strip())
                os.kill(old_pid, signal.SIGTERM)
            except Exception:
                pass
    server = QLocalServer()
    try:
        server.removeServer(APP_ID)
    except Exception:
        pass
    server.listen(APP_ID)
    with open("/tmp/kde_quick_dns_switcher.pid", "w") as f:
        f.write(str(os.getpid()))
    return server


def open_config():
    editor = os.environ.get("EDITOR", "xdg-open")
    subprocess.Popen([editor, CONFIG_FILE])


def restart_app():
    python = sys.executable
    QApplication.quit()
    subprocess.Popen([python] + sys.argv)

# endregion


###############################################################################


# region App

last_dns = None
DNS_PROVIDERS = load_dns_providers()
app = QApplication(sys.argv)
app.server = ensure_single_instance()
tray = QSystemTrayIcon()
menu = QMenu()
actions = {}
monitor_network_changes()


# Menu structure
title_action = QAction(APP_NAME)
title_action.setEnabled(False)
menu.addAction(title_action)

menu.addSeparator()

auto_action = QAction(QIcon.fromTheme(AUTO_MODE_ICON), AUTO_MODE_NAME)
auto_action.triggered.connect(make_set_dns_action([], []))
menu.addAction(auto_action)

menu.addSeparator()

for name in sorted(DNS_PROVIDERS.keys()):
    data = DNS_PROVIDERS[name]
    ipv4, ipv6 = get_provider_dns(data)
    icon_name = data.get("icon")
    icon_file = os.path.join(ICON_DIR, icon_name)
    if icon_name and os.path.exists(icon_file):
        action = QAction(QIcon(icon_file), name)
    else:
        action = QAction(QIcon.fromTheme(DEFAULT_MODE_ICON), name)
    action.triggered.connect(make_set_dns_action(ipv4, ipv6))
    menu.addAction(action)
    actions[name] = action

menu.addSeparator()

options_title_action = QAction("Options")
options_title_action.setEnabled(False)
menu.addAction(options_title_action)

edit_action = QAction(QIcon.fromTheme("edit"), "Edit DNS providers")
edit_action.triggered.connect(open_config)
menu.addAction(edit_action)

restart_action = QAction(QIcon.fromTheme("vm-restart"), "Restart")
restart_action.triggered.connect(restart_app)
menu.addAction(restart_action)

exit_action = QAction(QIcon.fromTheme("exit"), "Exit")
exit_action.triggered.connect(app.quit)
menu.addAction(exit_action)


# Initial icon
tray.setContextMenu(menu)
tray.setIcon(QIcon.fromTheme(DEFAULT_MODE_ICON))
tray.show()


# Update state timer
#timer = QTimer()
#timer.timeout.connect(update_state)
#timer.start(5000)
update_state()


# Exit
sys.exit(app.exec())

# endregion
