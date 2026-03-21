#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.app.quick_dns_switcher import QuickDnsSwitcher
from src.config.paths import Paths
from src.domain.services.dns_resolver import DnsResolver
from src.infrastructure.backend.backend_factory import BackendFactory
from src.infrastructure.dns_provider_catalog import DnsProviderCatalog
from src.infrastructure.notifications.notifier_factory import NotifierFactory


class Bootstrap:
     @staticmethod
     def create_app() -> QuickDnsSwitcher:
         backend = BackendFactory.create()
         catalog = DnsProviderCatalog(Paths.DNS_PROVIDERS_FILE)
         resolver = DnsResolver(catalog)
         notifier = NotifierFactory.create()
         return QuickDnsSwitcher(backend, catalog, resolver, notifier)
