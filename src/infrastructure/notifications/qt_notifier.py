#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional
from PyQt6.QtWidgets import QSystemTrayIcon
from src.infrastructure.notifications.notifier_base import NotifierBase
from src.ui.models.app_icon import AppIcon


class QtNotifier(NotifierBase):
    def __init__(self) -> None:
        self.tray: Optional[QSystemTrayIcon] = None

    def set_tray(self, tray: QSystemTrayIcon) -> None:
        self.tray = tray

    def notify(self, title: str, message: str, icon: AppIcon, timeout: int = 5000) -> None:
        if self.tray is None:
            raise Exception
            # TODO
        self.tray.showMessage(title, message, icon.icon, timeout)
