#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt6.QtCore import QTimer, QObject
from src.infrastructure.monitoring.network_monitor_base import NetworkMonitorBase


class PollingNetworkMonitor(QObject, NetworkMonitorBase):
    def __init__(self, interval_ms: int = 1500):
        QObject.__init__(self)
        NetworkMonitorBase.__init__(self)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._emit)
        self._timer.start(interval_ms)
