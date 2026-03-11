#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import os
import logging
from typing import Optional, List, Dict
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer
from utils.tools import ensure_single_instance, display_error_dialog, execute_command
from utils.constants import Constants
from network.ip_pair import IpPair
from network.dns_configuration import DnsConfiguration
from network.dns_provider import DnsProvider
from network.dns_state import DnsState
from network.network_connection import NetworkConnection


PROJECT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(PROJECT_DIR, Constants.CONFIG_FILENAME)
ICON_DIR = os.path.join(PROJECT_DIR, Constants.ICON_DIRNAME)


# region Functions

def get_active_connections_with_dns() -> List[NetworkConnection]:
    conns: List[NetworkConnection] = []
    name: Optional[str] = None
    device: Optional[str] = None
    connected: bool = False
    ipv4_list: List[str] = []
    ipv6_list: List[str] = []

    def flush():
        if device and name and connected and device not in Constants.IGNORED_DEVICES:
            conns.append(
                NetworkConnection(
                    name,
                    device,
                    IpPair.from_list(4, ipv4_list),
                    IpPair.from_list(6, ipv6_list)
                )
            )

    result = execute_command([
        "nmcli", "-t", "-f", "GENERAL.CONNECTION,GENERAL.DEVICE,GENERAL.STATE,IP4.DNS,IP6.DNS", "device", "show"
    ])
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line: continue
        if ":" not in line: continue

        key, value = line.split(":", 1)
        value = value.strip()
        if key == "GENERAL.CONNECTION":
            flush()
            name = value
            device = None
            ipv4_list = []
            ipv6_list = []
        elif key == "GENERAL.DEVICE":
            device = value
        elif key == "GENERAL.STATE":
            connected = value.startswith("100")
        elif key.startswith("IP4.DNS"):
            if value:
                ipv4_list.append(value)
        elif key.startswith("IP6.DNS"):
            if value:
                ipv6_list.append(value)

    flush()
    for conn in conns:
        result = execute_command(["nmcli", "-g", "ipv4.ignore-auto-dns,ipv6.ignore-auto-dns", "connection", "show", conn.name])
        ipv4_ignore_auto_dns, ipv6_ignore_auto_dns = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        conn.parse_ignore_auto_dns(ipv4_ignore_auto_dns, ipv6_ignore_auto_dns)

    return conns


def get_current_dns() -> DnsState:
    v4_total: List[str] = []
    v6_total: List[str] = []
    for conn in get_active_connections_with_dns():
        v4_total.extend(conn.ipv4.get_ip_list())
        v6_total.extend(conn.ipv6.get_ip_list())
    return DnsState(
        IpPair.from_list(4, list(dict.fromkeys(v4_total))),
        IpPair.from_list(6, list(dict.fromkeys(v6_total)))
    )


def set_dns(target_v4: IpPair, target_v6: IpPair):
    v4_ips = target_v4.get_ip_list()
    v6_ips = target_v6.get_ip_list()
    v4_ignore_auto = "yes" if v4_ips else "no"
    v6_ignore_auto = "yes" if v6_ips else "no"
    for conn in get_active_connections_with_dns():
        execute_command([
            "nmcli",
            "connection",
            "modify", conn.name, 
            "ipv4.ignore-auto-dns", v4_ignore_auto, 
            "ipv6.ignore-auto-dns", v6_ignore_auto, 
            "ipv4.dns", ",".join(v4_ips),
            "ipv6.dns", ",".join(v6_ips)
        ])
        result_reapply = execute_command(["nmcli", "device", "reapply", conn.device], True, False)
        if result_reapply.returncode != 0:
            logging.warning("Error resetting network, trying aggressive method...", stack_info=True)
            result_up = execute_command(["nmcli", "connection", "up", conn.name], True, True)

    QTimer.singleShot(500, update_state)


def make_set_dns_action(ipv4: IpPair, ipv6: IpPair):
    def handler(*args):
        set_dns(ipv4, ipv6)
    return handler


def update_state():
    global last_dns_ips
    connections: List[NetworkConnection] = get_active_connections_with_dns()
    dns_state: DnsState = DnsState.from_network_connections(connections)

    active_name: str = "Custom DNS"
    if not dns_state.ipv4_ignore_auto_dns and not dns_state.ipv6_ignore_auto_dns:
        active_name = Constants.AUTO_MODE_NAME
    else:
        for dns_provider in dns_config.get_all():
            if dns_state.matches_provider(dns_provider):
                active_name = dns_provider.name
                break

    # Tray icon
    active_provider = dns_config.get_by_name(active_name)
    if active_name == Constants.AUTO_MODE_NAME:
        tray.setIcon(QIcon.fromTheme(Constants.AUTO_MODE_ICON))
    elif active_provider and active_provider.icon:
        if active_provider.icon_from_theme:
            tray.setIcon(QIcon.fromTheme(active_provider.icon))
        else:
            icon_path = os.path.join(ICON_DIR, active_provider.icon)
            if os.path.exists(icon_path):
                tray.setIcon(QIcon(icon_path))
            else:
                tray.setIcon(QIcon.fromTheme(Constants.CUSTOM_MODE_ICON))
    else:
        tray.setIcon(QIcon.fromTheme(Constants.CUSTOM_MODE_ICON))

    # Menu items
    auto_action.setText(f"✔ {Constants.AUTO_MODE_NAME}" if active_name == Constants.AUTO_MODE_NAME else Constants.AUTO_MODE_NAME)
    for name, action in provider_actions.items():
        action.setText(f"✔ {name}" if name == active_name else name)

    # Notification
    current_ips = dns_state.all_ips
    if last_dns_ips is not None and set(current_ips) != set(last_dns_ips):
        icon = "network-server"
        if active_provider and active_provider.icon:
            icon = os.path.join(ICON_DIR, active_provider.icon)
        body = "\n".join(current_ips) if current_ips else "System Default"
        execute_command(["notify-send", "-a", Constants.APP_NAME, "-t", "5000", "-i", icon, active_name, body], False, False)
    last_dns_ips = current_ips

    # Tooltip
    tray.setToolTip(f"{Constants.APP_NAME}\n{active_name}\n----------------------------\n" + "\n".join(current_ips))


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
tray = QSystemTrayIcon()
menu = QMenu()

dns_config = DnsConfiguration(CONFIG_FILE)
last_dns_ips = None
provider_actions = {}

# Menu structure
title_action = QAction(Constants.APP_NAME.upper())
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
        q_icon = QIcon.fromTheme(Constants.CUSTOM_MODE_ICON)
    action.setIcon(q_icon)
    menu.addAction(action)
    provider_actions[provider.name] = action

menu.addSeparator()

options_title_action = QAction("OPTIONS")
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

tray.setIcon(QIcon.fromTheme(Constants.CUSTOM_MODE_ICON))
tray.setContextMenu(menu)
tray.show()
update_state()

# Update timer
timer = QTimer()
timer.timeout.connect(update_state)
timer.start(1500)

sys.exit(app.exec())

# endregion
