#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import Optional
from src.domain.models.active_dns_mode import ActiveDnsMode
from src.domain.models.dns_provider import DnsProvider
from src.domain.models.dns_snapshot import DnsSnapshot


@dataclass(frozen=True)
class ActiveDns:
    dns_snapshot: DnsSnapshot
    mode: ActiveDnsMode
    provider: Optional[DnsProvider] = None
