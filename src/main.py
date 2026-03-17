#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from src.app.quick_dns_switcher import QuickDnsSwitcher
from src.config.paths import Paths
from src.domain.services.dns_resolver import DnsResolver
from src.infrastructure.backend.backend_factory import BackendFactory
from src.infrastructure.backend.network_backend_base import NetworkBackendBase
from src.infrastructure.dns_provider_catalog import DnsProviderCatalog
from src.utils.tools import display_error_dialog


try:
    backend: NetworkBackendBase = BackendFactory.create()
    dns_provider_catalog: DnsProviderCatalog = DnsProviderCatalog(Paths.DNS_PROVIDERS_FILE)
    dns_resolver: DnsResolver = DnsResolver(dns_provider_catalog)
    switcher: QuickDnsSwitcher = QuickDnsSwitcher(backend, dns_provider_catalog, dns_resolver)
    switcher.run()
except Exception as e:
    logging.exception(e)
    display_error_dialog(str(e))
