# !/usr/bin/python3
# -*- coding: utf-8 -*-


from ip_pair import IpPair
from dns_provider import DnsProvider
from typing import List


class DnsState:
    def __init__(self, ipv4: IpPair, ipv6: IpPair) -> None:
        self.ipv4 = ipv4
        self.ipv6 = ipv6

    def matches_provider(self, provider: DnsProvider) -> bool:
        return self.ipv4 == provider.ipv4 and self.ipv6 == provider.ipv6

    @property
    def all_ips(self) -> List[str]:
        return self.ipv4.get_ip_list() + self.ipv6.get_ip_list()
