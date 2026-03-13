#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from network.backend.backend_factory import BackendFactory
from network.backend.network_backend_base import NetworkBackendBase
from utils.tools import display_error_dialog
from quick_dns_switcher import QuickDnsSwitcher

try:
    backend: NetworkBackendBase = BackendFactory.create()
    switcher: QuickDnsSwitcher = QuickDnsSwitcher(backend)
    switcher.run()
except Exception as e:
    logging.exception(e)
    display_error_dialog(str(e))
