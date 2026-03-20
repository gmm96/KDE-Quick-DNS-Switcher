#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import platform
from src.infrastructure.backend.network_backend_base import NetworkBackendBase
from src.infrastructure.backend.network_manager_backend import NetworkManagerBackend
from src.infrastructure.errors.backend_init_error import BackendInitError


class BackendFactory:
    @staticmethod
    def create() -> NetworkBackendBase:
        if platform.system() == "Linux":
            if shutil.which("nmcli"):
                return NetworkManagerBackend()
        elif platform.system() == "Windows":
            raise BackendInitError("Windows is not currently supported.")
        raise BackendInitError(f"Unsupported system: {platform.system()}")
