#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import os
from typing import Dict, Callable, Any, List, Optional
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer
from network.backend.network_backend_base import NetworkBackendBase
from network.dns_provider import DnsProvider
from network.dns_state import DnsState
from network.ip_pair import IpPair
from network.dns_configuration import DnsConfiguration
from network.network_connection import NetworkConnection
from utils.tools import execute_command


class QuickDnsSwitcher:
    APP_ID: str = "quick_dns_switcher"
    APP_NAME: str = "Quick DNS Switcher"
    CONFIG_FILENAME: str = "dns_providers.json"
    ICONS_DIRNAME: str = "icons"
    AUTO_MODE_NAME: str = "Automatic"
    AUTO_ICON_KEY: str = "network-workgroup"
    DEFAULT_MODE_NAME: str = "Custom DNS"
    DEFAULT_ICON_KEY: str = "network-server"

    PROJECT_DIR: str = os.path.dirname(os.path.realpath(__file__))
    CONFIG_FILE: str = os.path.join(PROJECT_DIR, CONFIG_FILENAME)
    ICONS_DIR: str = os.path.join(PROJECT_DIR, ICONS_DIRNAME)

    def __init__(self, backend: NetworkBackendBase) -> None:
        self.dns_config: DnsConfiguration = DnsConfiguration(QuickDnsSwitcher.CONFIG_FILE)
        self.backend: NetworkBackendBase = backend
        self.last_dns_ips: Optional[List[str]] = None

        self.app: QApplication = QApplication(sys.argv)
        self._ensure_single_instance()
        self.tray: QSystemTrayIcon = QSystemTrayIcon()
        self.menu: QMenu = QMenu()
        self.menu_provider_actions: Dict[str, QAction] = {}
        self.theme_icons: Dict[str, QIcon] = {}
        self.storage_icons: Dict[str, QIcon] = {}
        self._create_icons()
        self._build_menu()

        self.tray.setIcon(self._get_icon(QuickDnsSwitcher.DEFAULT_ICON_KEY))
        self.tray.show()
        self.tray.setContextMenu(self.menu)
        QTimer.singleShot(0, self._update_state)

        self.timer: QTimer = QTimer()
        self.timer.timeout.connect(self._update_state)
        self.timer.start(1500)


    def run(self) -> None:
        sys.exit(self.app.exec())


    def _ensure_single_instance(self) -> None:
        socket: QLocalSocket = QLocalSocket()
        socket.connectToServer(QuickDnsSwitcher.APP_ID)
        if socket.waitForConnected(500):
            sys.exit(0)
        self.server: QLocalServer = QLocalServer()
        self.server.removeServer(QuickDnsSwitcher.APP_ID)
        self.server.listen(QuickDnsSwitcher.APP_ID)


    def _create_icons(self) -> None:
        self.theme_icons[QuickDnsSwitcher.DEFAULT_ICON_KEY] = QIcon.fromTheme(QuickDnsSwitcher.DEFAULT_ICON_KEY)
        self.theme_icons[QuickDnsSwitcher.AUTO_ICON_KEY] = QIcon.fromTheme(QuickDnsSwitcher.AUTO_ICON_KEY)
        for provider in self.dns_config.get_all():
            if provider.icon:
                if provider.icon_from_theme:
                    qicon: QIcon = QIcon.fromTheme(provider.icon)
                    if not qicon.isNull():
                        self.theme_icons[provider.icon] = qicon
                else:
                    icon_path = os.path.join(QuickDnsSwitcher.ICONS_DIR, provider.icon)
                    if os.path.exists(icon_path):
                        qicon: QIcon = QIcon(icon_path)
                        if not qicon.isNull():
                            self.storage_icons[provider.icon] = qicon


    def _get_icon(self, key: str, from_theme: bool = True) -> QIcon:
        if from_theme:
            return self.theme_icons.get(key, self.theme_icons[QuickDnsSwitcher.DEFAULT_ICON_KEY])
        else:
            return self.storage_icons.get(key, self.theme_icons[QuickDnsSwitcher.DEFAULT_ICON_KEY])


    def _build_menu(self):
        # Title
        title_action: QAction = QAction(QuickDnsSwitcher.APP_NAME.upper(), self.menu)
        title_action.setEnabled(False)
        self.menu.addAction(title_action)
        self.menu.addSeparator()
        # Automatic DNS
        self.auto_action: QAction = QAction(self._get_icon(QuickDnsSwitcher.AUTO_ICON_KEY), QuickDnsSwitcher.AUTO_MODE_NAME, self.menu)
        self.auto_action.triggered.connect(self._make_set_dns_action(IpPair(4), IpPair(6)))
        self.menu.addAction(self.auto_action)
        self.menu.addSeparator()
        # Provider DNS
        for provider in sorted(self.dns_config.get_all(), key=lambda x: x.name):
            provider_action: QAction = QAction(provider.name, self.menu)
            provider_action.triggered.connect(self._make_set_dns_action(provider.ipv4, provider.ipv6))
            provider_action.setIcon(self._get_icon(provider.icon, from_theme=provider.icon_from_theme))
            self.menu.addAction(provider_action)
            self.menu_provider_actions[provider.name] = provider_action
        self.menu.addSeparator()
        # Options
        options_title_action: QAction = QAction("OPTIONS", self.menu)
        options_title_action.setEnabled(False)
        self.menu.addAction(options_title_action)
        edit_action: QAction = QAction(QIcon.fromTheme("edit"), "Edit DNS providers", self.menu)
        edit_action.triggered.connect(self._open_config)
        self.menu.addAction(edit_action)
        restart_action: QAction = QAction(QIcon.fromTheme("vm-restart"), "Restart", self.menu)
        restart_action.triggered.connect(self._restart_app)
        self.menu.addAction(restart_action)
        exit_action: QAction = QAction(QIcon.fromTheme("exit"), "Exit", self.menu)
        exit_action.triggered.connect(self._quit_app)
        self.menu.addAction(exit_action)


    @staticmethod
    def _open_config() -> None:
        subprocess.Popen(["xdg-open", QuickDnsSwitcher.CONFIG_FILE])


    @staticmethod
    def _restart_app() -> None:
        python: str = sys.executable
        QApplication.quit()
        subprocess.Popen([python] + sys.argv)


    def _quit_app(self) -> None:
        self.app.quit()


    def _update_state(self):
        connections: List[NetworkConnection] = self.backend.get_active_connections()
        dns_state: DnsState = DnsState.from_network_connections(connections)
        if not dns_state.ipv4_ignore_auto_dns and not dns_state.ipv6_ignore_auto_dns:
            active_name: str = QuickDnsSwitcher.AUTO_MODE_NAME
        else:
            active_name: str = next(
                (provider.name for provider in self.dns_config.get_all() if dns_state.matches_provider(provider)),
                QuickDnsSwitcher.DEFAULT_MODE_NAME
            )
        active_provider: Optional[DnsProvider] = self.dns_config.get_by_name(active_name)
        self._update_tray_icon(active_name, active_provider)
        self._update_menu_items(active_name)
        current_ips: List[str] = dns_state.all_ips
        self._send_notification(active_name, active_provider, current_ips)
        self._update_tooltip(active_name, current_ips)


    def _update_tray_icon(self, active_name: str, active_provider: Optional[DnsProvider]):
        if active_name == QuickDnsSwitcher.AUTO_MODE_NAME:
            self.tray.setIcon(self._get_icon(QuickDnsSwitcher.AUTO_ICON_KEY))
        elif active_provider and active_provider.icon:
            self.tray.setIcon(self._get_icon(active_provider.icon, from_theme=active_provider.icon_from_theme))
        else:
            self.tray.setIcon(self._get_icon(QuickDnsSwitcher.DEFAULT_ICON_KEY))


    def _update_menu_items(self, active_name: str):
        self.auto_action.setText(
            f"✔ {QuickDnsSwitcher.AUTO_MODE_NAME}"
            if active_name == QuickDnsSwitcher.AUTO_MODE_NAME
            else QuickDnsSwitcher.AUTO_MODE_NAME
        )
        for name, action in self.menu_provider_actions.items():
            action.setText(f"✔ {name}" if name == active_name else name)


    def _send_notification(self, active_name: str, active_provider: Optional[DnsProvider], current_ips: List[str]) -> None:
        if self.last_dns_ips is not None and set(current_ips) != set(self.last_dns_ips):
            icon = "network-server"
            if active_provider and active_provider.icon:
                icon = os.path.join(QuickDnsSwitcher.ICONS_DIR, active_provider.icon)
            body = "\n".join(current_ips) if current_ips else "System Default"
            execute_command(
                ["notify-send", "-a", QuickDnsSwitcher.APP_NAME, "-t", "5000", "-i", icon, active_name, body], False,
                False)
        self.last_dns_ips = current_ips


    def _update_tooltip(self, active_name: str, current_ips: List[str]) -> None:
        tooltip_text = (
            f"{QuickDnsSwitcher.APP_NAME}\n"
            f"{'-' * 28}\n"
            f"{active_name}\n"
            f"{'-' * 28}\n"
            f"{'\n'.join(current_ips)}"
        )
        self.tray.setToolTip(tooltip_text)


    def _make_set_dns_action(self, ipv4: IpPair, ipv6: IpPair) -> Callable[..., Any]:
        def handler(*args: Any) -> None:
            self.backend.set_dns(ipv4, ipv6)
        return handler
