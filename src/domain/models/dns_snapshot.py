#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Optional, Set, Tuple
from src.domain.models.dns_provider import DnsProvider
from src.domain.models.dns_status import DnsStatus
from src.domain.models.network_connection import NetworkConnection


class DnsSnapshot:
    def __init__(self, connections: List[NetworkConnection]) -> None:
        self.connections: List[NetworkConnection] = connections
        self.status: DnsStatus = DnsStatus.DISCONNECTED
        if self.connections:
            self.status = DnsStatus.AUTO if self.is_auto() else DnsStatus.MANUAL

    def matches_provider(self, provider: DnsProvider) -> bool:
        return all(
            conn.ipv4 == provider.ipv4 and \
            conn.ipv6 == provider.ipv6 and \
            conn.ipv4_ignore_auto_dns and \
            conn.ipv6_ignore_auto_dns \
            for conn in self.connections
        )

    def matches_state(self, other: Optional[DnsSnapshot]) -> bool:
        if not isinstance(other, DnsSnapshot): return False
        self_set: Set[Tuple[str, str, str, str, bool, bool]] = {conn.get_dns_identity() for conn in self.connections}
        other_set: Set[Tuple[str, str, str, str, bool, bool]] = {conn.get_dns_identity() for conn in other.connections}
        return self_set == other_set

    def is_auto(self) -> bool:
        return all(not conn.ipv4_ignore_auto_dns and not conn.ipv6_ignore_auto_dns for conn in self.connections)

    @property
    def all_ips(self) -> List[str]:
        all_ips: List[str] = []
        for conn in self.connections:
            all_ips.extend(conn.ipv4.get_ip_list())
        for conn in self.connections:
            all_ips.extend(conn.ipv6.get_ip_list())
        return list(dict.fromkeys(all_ips))
