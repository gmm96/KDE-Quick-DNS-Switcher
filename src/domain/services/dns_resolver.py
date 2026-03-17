#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional
from src.domain.models.active_dns import ActiveDns
from src.domain.models.active_dns_mode import ActiveDnsMode
from src.domain.models.dns_provider import DnsProvider
from src.infrastructure.dns_provider_catalog import DnsProviderCatalog
from src.domain.models.dns_snapshot import DnsSnapshot
from src.domain.models.dns_status import DnsStatus


class DnsResolver:
    def __init__(self, dns_provider_catalog: DnsProviderCatalog) -> None:
        self.catalog: DnsProviderCatalog = dns_provider_catalog

    def resolve(self, dns_state: DnsSnapshot):
        if dns_state.status == DnsStatus.DISCONNECTED:
            return ActiveDns(dns_state, ActiveDnsMode.DISCONNECTED, None)
        if dns_state.status == DnsStatus.AUTO:
            return ActiveDns(dns_state, ActiveDnsMode.AUTO, None)
        provider: Optional[DnsProvider] = self._find_provider(dns_state)
        if provider:
            return ActiveDns(dns_state, ActiveDnsMode.PROVIDER, provider)
        return ActiveDns(dns_state, ActiveDnsMode.CUSTOM, None)

    def _find_provider(self, dns_state: DnsSnapshot) -> Optional[DnsProvider]:
        return next(
            (provider for provider in self.catalog.providers if dns_state.matches_provider(provider)),
            None
        )
