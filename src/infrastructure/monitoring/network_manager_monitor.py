#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Optional
from PyQt6.QtCore import QFileSystemWatcher
from src.infrastructure.errors.infrastructure_error import InfrastructureError
from src.infrastructure.monitoring.network_monitor_base import NetworkMonitorBase


class NetworkManagerMonitor(NetworkMonitorBase):
    PATH: str = "/etc/resolv.conf"

    def __init__(self, path: Optional[str] = PATH) -> None:
        super().__init__()
        self.file_path: str = self._resolve_file(path if path else NetworkManagerMonitor.PATH)
        self.dir_path: str = os.path.dirname(self.file_path)
        self.watcher: QFileSystemWatcher = QFileSystemWatcher()
        self._setup_watch()

    def _setup_watch(self) -> None:
        self.file_path = self._resolve_file(self.file_path)
        self.dir_path = os.path.dirname(self.file_path)
        self.watcher.removePaths(self.watcher.files())
        self.watcher.removePaths(self.watcher.directories())
        if not os.path.exists(self.file_path):
            raise InfrastructureError("DNS file resolv.conf could not be found in system.")
        self.watcher.addPath(self.file_path)
        self.watcher.fileChanged.connect(self.on_change)
        if not os.path.exists(self.dir_path):
            raise InfrastructureError("Directory of DNS file resolv.conf could not be found in system.")
        self.watcher.addPath(self.dir_path)
        self.watcher.directoryChanged.connect(self.on_change)

    def on_change(self, path: str) -> None:
        self._setup_watch()
        self._emit()

    @staticmethod
    def _resolve_file(path: str) -> str:
        try:
            if os.path.islink(path):
                real_path: str = os.path.realpath(path)
                if os.path.exists(real_path):
                    return real_path
        except (OSError, PermissionError):
            pass
        return path
