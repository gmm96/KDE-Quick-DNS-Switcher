#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
from src.infrastructure.notifications.dbus_notifier import DbusNotifier
from src.infrastructure.notifications.notifier_base import NotifierBase
from src.infrastructure.notifications.qt_notifier import QtNotifier


class NotifierFactory:
    @staticmethod
    def create() -> NotifierBase:
        if platform.system() == "Linux":
            return DbusNotifier()
        elif platform.system() == "Windows":
            # TODO
            raise Exception("Windows is not currently supported.")
        return QtNotifier()
