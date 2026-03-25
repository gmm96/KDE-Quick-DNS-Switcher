#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional
from src.infrastructure.monitoring.network_manager_monitor import NetworkManagerMonitor
from src.infrastructure.monitoring.network_monitor_base import NetworkMonitorBase
from src.infrastructure.monitoring.polling_network_monitor import PollingNetworkMonitor


class HybridNetworkMonitor(NetworkMonitorBase):
    def __init__(self, path: Optional[str] = None, interval: Optional[int] = None) -> None:
        super().__init__()
        self._watcher: NetworkManagerMonitor = NetworkManagerMonitor(path) if path else NetworkManagerMonitor()
        self._polling: PollingNetworkMonitor = PollingNetworkMonitor(interval) if interval else PollingNetworkMonitor()
        self._watcher.on_event(self._emit)
        self._polling.on_event(self._emit)
