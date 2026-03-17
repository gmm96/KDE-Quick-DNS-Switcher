#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
from typing import Optional
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from src.config.paths import Paths
from src.domain.models.active_dns import ActiveDns
from src.domain.models.active_dns_view import ActiveDnsView
from src.domain.services.dns_resolver import DnsResolver
from src.infrastructure.backend.network_backend_base import NetworkBackendBase
from src.infrastructure.dns_provider_catalog import DnsProviderCatalog
from src.domain.models.dns_snapshot import DnsSnapshot
from src.domain.models.ip_pair import IpPair
from src.ui.tray_controller import TrayController
from src.ui.ui_constants import UiConstants
from src.utils.tools import execute_command


class QuickDnsSwitcher:
    def __init__(self, backend: NetworkBackendBase, catalog: DnsProviderCatalog, resolver: DnsResolver) -> None:
        self.app_id: str = "quick_dns_switcher"
        self.backend: NetworkBackendBase = backend
        self.catalog: DnsProviderCatalog = catalog
        self.resolver: DnsResolver = resolver
        self.dns_snapshot: Optional[DnsSnapshot] = None
        self.app: QApplication = QApplication(sys.argv)
        self._ensure_single_instance()
        self.tray: TrayController = TrayController(
            app=self.app,
            dns_provider_catalog=catalog,
            set_dns_callback=self._set_dns,
            open_config_callback=self._open_config,
            restart_callback=self._restart_app,
            quit_callback=self._quit_app
        )
        QTimer.singleShot(0, self._update_state)
        self.timer: QTimer = QTimer()
        self.timer.timeout.connect(self._update_state)
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
        QTimer.singleShot(500, self._update_state)

    def _update_state(self) -> None:
        dns_snapshot: DnsSnapshot = self.backend.get_dns_snapshot()
        if self.dns_snapshot and self.dns_snapshot.matches_state(dns_snapshot):
            return
        active_dns: ActiveDns = self.resolver.resolve(dns_snapshot)
        view: ActiveDnsView = ActiveDnsView.from_active_dns(active_dns)
        self.tray.update(view)
        self._send_notification(view)
        self.dns_snapshot: DnsSnapshot = dns_snapshot

    @staticmethod
    def _send_notification(view: ActiveDnsView) -> None:
        icon: str = str(Paths.ICONS_DIR / view.icon_key) if not view.from_theme else view.icon_key
        execute_command(
        ["notify-send",
                "-a", UiConstants.APP_NAME,
                "-t", "5000",
                "-i", icon,
                f"{view.display_name} DNS",
                "\n".join(view.body),
            ],
            output=False,
            raise_error=False
        )

    @staticmethod
    def _open_config() -> None:
        subprocess.Popen(["xdg-open", Paths.DNS_PROVIDERS_FILE])

    @staticmethod
    def _restart_app() -> None:
        python: str = sys.executable
        QApplication.quit()
        subprocess.Popen([python, "-m", "src.main"] + sys.argv[1:])

    def _quit_app(self) -> None:
        self.app.quit()
