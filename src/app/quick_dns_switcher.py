#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from typing import Optional
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.config.paths import Paths
from src.domain.models.active_dns import ActiveDns
from src.domain.models.active_dns_mode import ActiveDnsMode
from src.domain.models.active_dns_view import ActiveDnsView
from src.domain.services.dns_resolver import DnsResolver
from src.infrastructure.backend.network_backend_base import NetworkBackendBase
from src.infrastructure.command_executor import CommandExecutor
from src.infrastructure.dns_provider_catalog import DnsProviderCatalog
from src.domain.models.dns_snapshot import DnsSnapshot
from src.domain.models.ip_pair import IpPair
from src.infrastructure.notifications.notifier_base import NotifierBase
from src.infrastructure.notifications.qt_notifier import QtNotifier
from src.ui.models.app_icon import AppIcon
from src.ui.tray_controller import TrayController
from src.ui.ui_constants import UiConstants
from src.ui.ui_context import UiContext


class QuickDnsSwitcher:
    def __init__(self, backend: NetworkBackendBase, catalog: DnsProviderCatalog, resolver: DnsResolver, notifier: NotifierBase) -> None:
        self.app_id: str = "quick_dns_switcher"
        self.backend: NetworkBackendBase = backend
        self.catalog: DnsProviderCatalog = catalog
        self.resolver: DnsResolver = resolver
        self.notifier: NotifierBase = notifier
        self.dns_snapshot: Optional[DnsSnapshot] = None
        self.app: QApplication = QApplication(sys.argv)
        self.app.setDesktopFileName(UiConstants.APP_NAME)
        self.app.setQuitOnLastWindowClosed(False)
        self.app.setApplicationName(UiConstants.APP_NAME)
        self._ensure_single_instance()
        self.tray: TrayController = TrayController(
            app=self.app,
            dns_provider_catalog=catalog,
            set_dns_callback=self._set_dns,
            open_config_callback=self._open_config,
            restart_callback=self._restart_app,
            quit_callback=self._quit_app
        )
        if isinstance(self.notifier, QtNotifier):
            self.notifier.set_tray(self.tray.tray)
        QTimer.singleShot(0, UiContext.safe_callback(self._update_state))
        self.timer: QTimer = QTimer()
        self.timer.timeout.connect(UiContext.safe_callback(self._update_state))
        self.timer.start(1500)

    def run(self) -> None:
        sys.exit(self.app.exec())

    def _ensure_single_instance(self) -> None:
        socket: QLocalSocket = QLocalSocket()
        socket.connectToServer(self.app_id)
        if socket.waitForConnected(500):
            sys.exit(0)
        self.server: QLocalServer = QLocalServer()
        self.server.removeServer(self.app_id)
        self.server.listen(self.app_id)

    def _set_dns(self, ipv4: IpPair, ipv6: IpPair) -> None:
        self.backend.set_dns(ipv4, ipv6)
        QTimer.singleShot(500, UiContext.safe_callback(self._update_state))

    def _update_state(self) -> None:
        dns_snapshot: DnsSnapshot = self.backend.get_dns_snapshot()
        if self.dns_snapshot and self.dns_snapshot.matches_state(dns_snapshot):
            return
        active_dns: ActiveDns = self.resolver.resolve(dns_snapshot)
        view: ActiveDnsView = ActiveDnsView.from_active_dns(active_dns)
        self.tray.update(view)
        self._send_notification(view)
        self.dns_snapshot: DnsSnapshot = dns_snapshot

    def _send_notification(self, view: ActiveDnsView) -> None:
        icon: AppIcon = self.tray.get_icon(view.icon_key, view.from_theme)
        title: str = f"{view.display_name} DNS" if view.mode != ActiveDnsMode.DISCONNECTED else view.display_name
        self.notifier.notify(title, "\n".join(view.body), icon)

    @staticmethod
    def _open_config() -> None:
        CommandExecutor.execute_async(["xdg-open", Paths.DNS_PROVIDERS_FILE])

    @staticmethod
    def _restart_app() -> None:
        QApplication.quit()
        CommandExecutor.execute_async([sys.executable, "-m", "src.main"] + sys.argv[1:])

    def _quit_app(self) -> None:
        self.app.quit()
