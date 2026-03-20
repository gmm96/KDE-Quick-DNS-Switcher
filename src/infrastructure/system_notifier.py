#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.infrastructure.command_executor import CommandExecutor
from src.ui.ui_constants import UiConstants


class SystemNotifier:
    @staticmethod
    def notify(title: str, body: str, icon: str) -> None:
        CommandExecutor.execute(
        ["notify-send",
                "-a", UiConstants.APP_NAME,
                "-t", "5000",
                "-i", icon,
                title,
                body,
            ],
            check=False
        )
