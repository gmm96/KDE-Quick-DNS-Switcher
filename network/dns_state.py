#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
from network.ip_pair import IpPair
from network.dns_provider import DnsProvider
from network.network_connection import NetworkConnection


class DnsState:
    def __init__(self, ipv4: IpPair, ipv6: IpPair, ipv4_ignore_auto_dns: bool, ipv6_ignore_auto_dns: bool) -> None:
        self.ipv4: IpPair = ipv4
        self.ipv6: IpPair = ipv6
        self.ipv4_ignore_auto_dns: bool = ipv4_ignore_auto_dns
        self.ipv6_ignore_auto_dns: bool = ipv6_ignore_auto_dns

    @classmethod
    def from_network_connections(cls, connections: List[NetworkConnection]) -> DnsState:
        v4_total: List[str] = [ipv4 for conn in connections for ipv4 in conn.ipv4.get_ip_list()]
        v6_total: List[str] = [ipv6 for conn in connections for ipv6 in conn.ipv6.get_ip_list()]
        ignore_v4_all = all(conn.ipv4_ignore_auto_dns for conn in connections)
        ignore_v6_all = all(conn.ipv6_ignore_auto_dns for conn in connections)

        return cls(
            IpPair.from_list(4, list(dict.fromkeys(v4_total))),
            IpPair.from_list(6, list(dict.fromkeys(v6_total))),
            ignore_v4_all,
            ignore_v6_all
        )

    def matches_provider(self, provider: DnsProvider) -> bool:
        return self.ipv4 == provider.ipv4 and self.ipv6 == provider.ipv6

    @property
    def all_ips(self) -> List[str]:
        return self.ipv4.get_ip_list() + self.ipv6.get_ip_list()
