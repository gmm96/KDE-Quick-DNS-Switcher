#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import os
import json
import signal
import ipaddress
import socket
import struct
import sys
from typing import Optional, List, Dict
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusReply
from PyQt6.QtCore import QObject, QTimer, pyqtSlot
from utils.tools import ensure_single_instance, display_error_dialog, execute_command
from utils.constants import Constants
from network.ip_pair import IpPair
from network.dns_configuration import DnsConfiguration
from network.dns_provider import DnsProvider
from network.dns_state import DnsState
from network.network_connection import NetworkConnection


PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(PROJECT_DIR, "dns-providers.json")
ICON_DIR = os.path.join(PROJECT_DIR, "icons")


class QtNetworkMonitor(QObject):
    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(update_state)

    @pyqtSlot(str, "QVariantMap", "QStringList")
    def handle_dbus_change(self, interface, changed, invalidated):
        if "ActiveConnections" in changed or "State" in changed:
            self.timer.start(800)


# region Functions

def get_provider_dns(provider):
    ipv4 = [ip for ip in [provider.get("ipv4_1"), provider.get("ipv4_2")] if ip]
    ipv6 = [ip for ip in [provider.get("ipv6_1"), provider.get("ipv6_2")] if ip]
    return ipv4, ipv6


def get_active_connections_with_dns() -> List[NetworkConnection]:
    conns = []

    try:
        result = execute_command(["nmcli",
            "-t",
            "-f",
            "GENERAL.CONNECTION,GENERAL.DEVICE,IP4.DNS,IP6.DNS",
            "device",
            "show"
        ])

        name, device = None, None
        ipv4_list, ipv6_list = [], []

        IGNORED_DEVICES = {"lo", "tun0", ""}

        def flush():
            if device and device not in IGNORED_DEVICES:
                display_name = name if name else f"Interface {device}"

                conns.append(
                    NetworkConnection(
                        display_name,
                        device,
                        IpPair.from_list(4, ipv4_list),
                        IpPair.from_list(6, ipv6_list)
                    )
                )

        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            key, value = line.split(":", 1)
            value = value.strip()

            if key == "GENERAL.CONNECTION":
                # nuevo bloque → guardar anterior
                if device is not None:
                    flush()

                name = value
                device = None
                ipv4_list = []
                ipv6_list = []

            elif key == "GENERAL.DEVICE":
                device = value

            elif key.startswith("IP4.DNS"):
                if value:
                    ipv4_list.append(value)

            elif key.startswith("IP6.DNS"):
                if value:
                    ipv6_list.append(value)

        # último bloque
        flush()

    except Exception as e:
        print(f"DEBUG ERROR: {e}")

    return conns


def get_current_dns() -> DnsState:
    v4_total, v6_total = [], []
    for conn in get_active_connections_with_dns():
        v4_total.extend(conn.ipv4.get_ip_list())
        v6_total.extend(conn.ipv6.get_ip_list())
    
    return DnsState(
        IpPair.from_list(4, list(dict.fromkeys(v4_total))),
        IpPair.from_list(6, list(dict.fromkeys(v6_total)))
    )


def set_dns(target_v4: IpPair, target_v6: IpPair):
    v4_ips = target_v4.get_ip_list()
    v4_str = ",".join(v4_ips)
    
    # DEBUG REAL en consola
    print(f"\n--- CAMBIANDO DNS ---")
    print(f"Objetivo: {v4_str if v4_str else 'AUTOMÁTICO'}")

    for conn in get_active_connections_with_dns():
        print(f"Aplicando a: {conn.name} ({conn.device})")
        
        # MODO: 'yes' para ignorar el DNS del router (usar manual), 'no' para automático
        ignore_auto = "yes" if v4_ips else "no"
        
        # Comando básico y robusto
        # 1. Modificar la conexión (el perfil)
        subprocess.run(["nmcli", "connection", "modify", conn.name, 
                        "ipv4.ignore-auto-dns", ignore_auto, 
                        "ipv4.dns", v4_str], check=False)
        
        # 2. Forzar la aplicación (REAPPLY)
        # Si reapply falla, el 'up' es el plan B
        res = subprocess.run(["nmcli", "device", "reapply", conn.device], capture_output=True)
        if res.returncode != 0:
            print("Reapply falló, forzando refresco de conexión...")
            subprocess.run(["nmcli", "connection", "up", conn.name], check=False)

    # Forzamos actualización de la UI
    QTimer.singleShot(1200, update_state)


def monitor_network_changes():
    global nm_monitor
    nm_monitor = QtNetworkMonitor()
    QDBusConnection.systemBus().connect(
        "org.freedesktop.NetworkManager",
        "/org/freedesktop/NetworkManager",
        "org.freedesktop.DBus.Properties",
        "PropertiesChanged",
        nm_monitor.handle_dbus_change
    )


def update_state():
    print("UPDATE_STATE CALLED")

    global last_dns_ips
    state = get_current_dns()
    active_name = Constants.AUTO_MODE_NAME

    print(f"DEBUG UI: IPs detectadas en el sistema: v4={state.ipv4.get_ip_list()} v6={state.ipv6.get_ip_list()}")
    
    for provider in dns_config.get_all():
        if state.matches_provider(provider):
            active_name = provider.name
            break

    print(f"DEBUG UI: Proveedor detectado -> {active_name}")

    # Icono
    provider_obj = dns_config.get_by_name(active_name)
    if active_name == Constants.AUTO_MODE_NAME:
        tray.setIcon(QIcon.fromTheme(Constants.AUTO_MODE_ICON))
    elif provider_obj and provider_obj.icon:
        icon_p = os.path.join(ICON_DIR, provider_obj.icon)
        tray.setIcon(QIcon(icon_p) if os.path.exists(icon_p) else QIcon.fromTheme(Constants.DEFAULT_MODE_ICON))
    else:
        tray.setIcon(QIcon.fromTheme(Constants.DEFAULT_MODE_ICON))

    # Menú (Checkmarks)
    auto_action.setText(f"✔ {Constants.AUTO_MODE_NAME}" if active_name == Constants.AUTO_MODE_NAME else Constants.AUTO_MODE_NAME)
    for name, action in provider_actions.items():
        action.setText(f"✔ {name}" if name == active_name else name)

    # Notificación si hay cambio real
    current_ips = state.all_ips
    if last_dns_ips is not None and set(current_ips) != set(last_dns_ips):
        icon = "network-server"
        if provider_obj and provider_obj.icon:
            icon = os.path.join(ICON_DIR, provider_obj.icon)
        body = "DNS: " + (", ".join(current_ips) if current_ips else "System Default")
        execute_command(["notify-send", "-a", Constants.APP_NAME, "-t", "5000", "-i", icon, f"Network: {active_name}", body], False, False)
    last_dns_ips = current_ips

    # Tooltip
    tray.setToolTip(f"{Constants.APP_NAME}\n{active_name}\n\n" + "\n".join(current_ips))


def make_set_dns_action(ipv4: IpPair, ipv6: IpPair):
    def handler(*args):
        set_dns(ipv4, ipv6)
    return handler


def open_config():
    subprocess.Popen(["xdg-open", CONFIG_FILE])


def restart_app():
    python = sys.executable
    QApplication.quit()
    subprocess.Popen([python] + sys.argv)

# endregion


###############################################################################


# region App

app = QApplication(sys.argv)
app.server = ensure_single_instance()

dns_config = DnsConfiguration(CONFIG_FILE)
last_dns_ips = None
provider_actions = {}

tray = QSystemTrayIcon()
menu = QMenu()

monitor_network_changes()


# Menu structure
title_action = QAction(Constants.APP_NAME)
title_action.setEnabled(False)
menu.addAction(title_action)

menu.addSeparator()

auto_action = QAction(QIcon.fromTheme(Constants.AUTO_MODE_ICON), Constants.AUTO_MODE_NAME)
auto_action.triggered.connect(make_set_dns_action(IpPair(4), IpPair(6)))
menu.addAction(auto_action)

menu.addSeparator()

for provider in sorted(dns_config.get_all(), key=lambda x: x.name):
    action = QAction(provider.name)
    action.triggered.connect(make_set_dns_action(provider.ipv4, provider.ipv6))
    icon_path = os.path.join(ICON_DIR, provider.icon)
    if provider.icon and os.path.exists(icon_path):
        q_icon = QIcon(icon_path)
    else:
        q_icon = QIcon.fromTheme(Constants.DEFAULT_MODE_ICON)
    action.setIcon(q_icon)
    menu.addAction(action)
    provider_actions[provider.name] = action

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

tray.setIcon(QIcon.fromTheme(Constants.DEFAULT_MODE_ICON))
tray.setContextMenu(menu)
tray.show()
update_state()

timer = QTimer()
timer.timeout.connect(update_state)
timer.start(1500)

sys.exit(app.exec())

# endregion
