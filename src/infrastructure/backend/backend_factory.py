#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
from src.infrastructure.backend.network_manager_backend import NetworkManagerBackend
from src.infrastructure.backend.network_backend_base import NetworkBackendBase


class BackendFactory:
    @staticmethod
    def create() -> NetworkBackendBase:
        if shutil.which(str("nmcli")):
            return NetworkManagerBackend()
        raise RuntimeError("Unsupported system")