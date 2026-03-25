#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import platform
from src.app.quick_dns_switcher import QuickDnsSwitcher
from src.config.paths import Paths
from src.domain.services.dns_resolver import DnsResolver
from src.infrastructure.backend.network_backend_base import NetworkBackendBase
from src.infrastructure.dns_provider_catalog import DnsProviderCatalog
from src.infrastructure.monitoring.network_monitor_base import NetworkMonitorBase
from src.infrastructure.notifications.notifier_base import NotifierBase
from src.startup.linux_factory import LinuxFactory
from src.startup.platform_factory import PlatformFactory
from src.startup.windows_factory import WindowsFactory


class Bootstrap:
    @staticmethod
    def create_app() -> QuickDnsSwitcher:
        platform_factory: PlatformFactory = Bootstrap._get_platform_factory()
        backend: NetworkBackendBase = platform_factory.create_backend()
        catalog: DnsProviderCatalog = DnsProviderCatalog(Paths.DNS_PROVIDERS_FILE)
        resolver: DnsResolver = DnsResolver(catalog)
        notifier: NotifierBase = platform_factory.create_notifier()
        monitor: NetworkMonitorBase = platform_factory.create_monitor()
        return QuickDnsSwitcher(backend, catalog, resolver, notifier, monitor)

    @staticmethod
    def _get_platform_factory() -> PlatformFactory:
        if platform.system().lower() == "linux":
            return LinuxFactory()
        elif platform.system().lower() == "windows":
            return WindowsFactory()
        raise Exception(f"Unsupported system: {platform.system()}")
