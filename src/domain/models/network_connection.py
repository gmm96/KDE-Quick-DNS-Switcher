#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Tuple
from src.domain.models.ip_pair import IpPair


class NetworkConnection:
    def __init__(self, name: str, device: str, ipv4: IpPair, ipv6: IpPair, ipv4_ignore_auto_dns: bool = False, ipv6_ignore_auto_dns: bool = False) -> None:
        self.name: str = name
        self.device: str = device
        self.ipv4: IpPair = ipv4
        self.ipv6: IpPair = ipv6
        self.ipv4_ignore_auto_dns: bool = ipv4_ignore_auto_dns
        self.ipv6_ignore_auto_dns: bool = ipv6_ignore_auto_dns

    def parse_ignore_auto_dns(self, value_ipv4: str, value_ipv6: str) -> None:
        possible_values: Tuple[str, str] = ("yes", "no")
        if value_ipv4 in possible_values:
            self.ipv4_ignore_auto_dns = value_ipv4 == "yes"
        if value_ipv6 in possible_values:
            self.ipv6_ignore_auto_dns = value_ipv6 == "yes"

    def get_dns_identity(self) -> Tuple[str, str, str, str, bool, bool]:
        return (
            self.ipv4.main,
            self.ipv4.alternative,
            self.ipv6.main,
            self.ipv6.alternative,
            self.ipv4_ignore_auto_dns,
            self.ipv6_ignore_auto_dns
        )

    def __eq__(self, other: Optional[object]) -> bool:
        if not isinstance(other, NetworkConnection): return False
        return self.ipv4 == other.ipv4 and \
            self.ipv6 == other.ipv6 and \
            self.ipv4_ignore_auto_dns == other.ipv4_ignore_auto_dns and \
            self.ipv6_ignore_auto_dns == other.ipv6_ignore_auto_dns
