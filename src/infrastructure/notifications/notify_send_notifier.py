#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.infrastructure.command_executor import CommandExecutor
from src.infrastructure.notifications.notifier_base import NotifierBase
from src.ui.models.app_icon import AppIcon
from src.ui.ui_constants import UiConstants


class NotifySendNotifier(NotifierBase):
    def __init__(self) -> None:
        pass

    def notify(self, title: str, body: str, icon: AppIcon, timeout: int = 5000) -> None:
        CommandExecutor.execute(
        ["notify-send",
                "-a", UiConstants.APP_NAME,
                "-t", timeout,
                "-i", icon,
                title,
                body,
            ],
            check=False
        )
