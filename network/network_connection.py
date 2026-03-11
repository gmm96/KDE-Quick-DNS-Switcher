#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from network.ip_pair import IpPair


class NetworkConnection:
    def __init__(self, name: str, device: str, ipv4: IpPair, ipv6: IpPair) -> None:
        self.name: str = name
        self.device: str = device
        self.ipv4: IpPair = ipv4
        self.ipv6: IpPair = ipv6
        self.ipv4_ignore_auto_dns: bool = False
        self.ipv6_ignore_auto_dns: bool = False

    def set_ignore_auto_dns(self, ignore_ipv4: bool, ignore_ipv6: bool) -> None:
        self.ipv4_ignore_auto_dns = ignore_ipv4
        self.ipv6_ignore_auto_dns = ignore_ipv6

    def parse_ignore_auto_dns(self, value_ipv4: str, value_ipv6: str) -> None:
        ipv4_new_value, ipv6_new_value = False, False
        if "yes" == value_ipv4:
            ipv4_new_value = True
        if "yes" == value_ipv6:
            ipv6_new_value = True
        self.set_ignore_auto_dns(ipv4_new_value, ipv6_new_value)
