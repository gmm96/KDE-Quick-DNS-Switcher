#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List
from network.ip_pair import IpPair
from network.dns_provider import DnsProvider


class DnsState:
    def __init__(self, ipv4: IpPair, ipv6: IpPair) -> None:
        self.ipv4: IpPair = ipv4
        self.ipv6: IpPair = ipv6

    def matches_provider(self, provider: DnsProvider) -> bool:
        return self.ipv4 == provider.ipv4

    @property
    def all_ips(self) -> List[str]:
        return self.ipv4.get_ip_list() + self.ipv6.get_ip_list()
