#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Dict, Callable, Any
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from src.config.paths import Paths
from src.domain.models.active_dns_mode import ActiveDnsMode
from src.domain.models.active_dns_view import ActiveDnsView
from src.infrastructure.dns_provider_catalog import DnsProviderCatalog
from src.domain.models.ip_pair import IpPair
from src.ui.ui_constants import UiConstants


class TrayController:
    def __init__(self,
        app: QApplication,
        dns_provider_catalog: DnsProviderCatalog,
        set_dns_callback: Callable[[IpPair, IpPair], None],
        open_config_callback: Callable[[], None],
        restart_callback: Callable[[], None],
        quit_callback: Callable[[], None]
    ) -> None:
        self.app = app
        self.catalog = dns_provider_catalog
        self.set_dns_callback = set_dns_callback
        self.tray = QSystemTrayIcon()
        self.menu = QMenu()
        self.menu_provider_actions: Dict[str, QAction] = {}
        self.theme_icons: Dict[str, QIcon] = {}
        self.storage_icons: Dict[str, QIcon] = {}
        self._create_icons()
        self._build_menu(open_config_callback, restart_callback, quit_callback)
        self.tray.setIcon(self._get_icon(UiConstants.DEFAULT_ICON_KEY))
        self.tray.setContextMenu(self.menu)
        self.tray.show()

    def _create_icons(self) -> None:
        self.theme_icons[UiConstants.DISCONNECTED_ICON_KEY] = QIcon.fromTheme(UiConstants.DISCONNECTED_ICON_KEY)
        self.theme_icons[UiConstants.AUTO_ICON_KEY] = QIcon.fromTheme(UiConstants.AUTO_ICON_KEY)
        self.theme_icons[UiConstants.DEFAULT_ICON_KEY] = QIcon.fromTheme(UiConstants.DEFAULT_ICON_KEY)
        for provider in self.catalog.providers:
            if provider.icon:
                if provider.icon_from_theme:
                    qicon: QIcon = QIcon.fromTheme(provider.icon)
                    if not qicon.isNull():
                        self.theme_icons[provider.icon] = qicon
                else:
                    icon_path: Path = Paths.ICONS_DIR / provider.icon
                    if icon_path.exists():
                        qicon: QIcon = QIcon(str(icon_path))
                        if not qicon.isNull():
                            self.storage_icons[provider.icon] = qicon

    def _get_icon(self, key: str, from_theme: bool = True) -> QIcon:
        if from_theme:
            return self.theme_icons.get(key, self.theme_icons[UiConstants.DEFAULT_ICON_KEY])
        return self.storage_icons.get(key, self.theme_icons[UiConstants.DEFAULT_ICON_KEY])

    def _build_menu(self, open_config_callback: Callable, restart_callback: Callable, quit_callback: Callable) -> None:
        # Title
        title_action: QAction = QAction(UiConstants.APP_NAME.upper(), self.menu)
        title_action.setEnabled(False)
        self.menu.addAction(title_action)
        self.menu.addSeparator()
        # Automatic DNS
        self.auto_action = QAction(self._get_icon(UiConstants.AUTO_ICON_KEY), UiConstants.AUTO_NAME, self.menu)
        self.auto_action.triggered.connect(self._make_set_dns_action(IpPair(4), IpPair(6)))
        self.menu.addAction(self.auto_action)
        self.menu.addSeparator()
        # Provider DNS
        for provider in sorted(self.catalog.providers, key=lambda x: x.name):
            action: QAction = QAction(provider.name, self.menu)
            action.triggered.connect(self._make_set_dns_action(provider.ipv4, provider.ipv6))
            action.setIcon(self._get_icon(provider.icon, provider.icon_from_theme))
            self.menu.addAction(action)
            self.menu_provider_actions[provider.name] = action
        self.menu.addSeparator()
        # Options
        options_title: QAction = QAction("OPTIONS", self.menu)
        options_title.setEnabled(False)
        self.menu.addAction(options_title)
        edit_action: QAction = QAction(QIcon.fromTheme("edit"), "Edit DNS providers", self.menu)
        edit_action.triggered.connect(open_config_callback)
        self.menu.addAction(edit_action)
        restart_action: QAction = QAction(QIcon.fromTheme("vm-restart"), "Restart", self.menu)
        restart_action.triggered.connect(restart_callback)
        self.menu.addAction(restart_action)
        exit_action: QAction = QAction(QIcon.fromTheme("exit"), "Exit", self.menu)
        exit_action.triggered.connect(quit_callback)
        self.menu.addAction(exit_action)

    def update(self, view: ActiveDnsView) -> None:
        self._update_icon(view)
        self._update_menu(view)
        self._update_tooltip(view)

    def _update_icon(self, view: ActiveDnsView) -> None:
        self.tray.setIcon(self._get_icon(view.icon_key, view.from_theme))

    def _update_menu(self, view: ActiveDnsView) -> None:
        self.auto_action.setText(f"✔ {UiConstants.AUTO_NAME}" if view.mode == ActiveDnsMode.AUTO else UiConstants.AUTO_NAME)
        for name, action in self.menu_provider_actions.items():
            action.setText(f"✔ {name}" if name == view.display_name else name)

    def _update_tooltip(self, view: ActiveDnsView) -> None:
        title: str = view.display_name
        if view.mode != ActiveDnsMode.DISCONNECTED:
            title = f"{title.capitalize()} DNS"
        dash_count: int = 10
        tooltip: str = (
            f"{UiConstants.APP_NAME}\n"
            f"{'—' * dash_count}\n"
            f"{title}\n"
            f"{'—' * dash_count}\n"
            f"{'\n'.join(view.body)}"
        )
        self.tray.setToolTip(tooltip)

    def _make_set_dns_action(self, ipv4: IpPair, ipv6: IpPair) -> Callable[..., None]:
        def handler(*args: Any) -> None:
            self.set_dns_callback(ipv4, ipv6)
        return handler
