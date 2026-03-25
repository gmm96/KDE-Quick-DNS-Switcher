#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from src.infrastructure.backend.network_manager_backend import NetworkManagerBackend
from src.infrastructure.monitoring.network_monitor_base import NetworkMonitorBase
from src.infrastructure.notifications.notifier_base import NotifierBase


class PlatformFactory(ABC):
    @abstractmethod
    def create_backend(self) -> NetworkManagerBackend:
        pass

    @abstractmethod
    def create_notifier(self) -> NotifierBase:
        pass

    @abstractmethod
    def create_monitor(self) -> NetworkMonitorBase:
        pass
