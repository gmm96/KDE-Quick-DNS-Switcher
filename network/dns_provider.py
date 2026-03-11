#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Dict
from network.ip_pair import IpPair


class DnsProvider:
    def __init__(self, name: str, ipv4: IpPair, ipv6: IpPair, icon: Optional[str] = None, icon_from_theme: bool = True) -> None:
        self.name: str = name
        self.ipv4: IpPair = ipv4
        self.ipv6: IpPair = ipv6
        self.icon: Optional[str] = icon
        self.icon_from_theme: bool = icon_from_theme

    @classmethod
    def from_dict(cls, name: str, data: Dict) -> DnsProvider:
        return cls(
            name=name,
            ipv4=IpPair(4, data.get("ipv4_1"), data.get("ipv4_2")),
            ipv6=IpPair(6, data.get("ipv6_1"), data.get("ipv6_2")),
            icon=data.get("icon"),
            icon_from_theme=data.get("icon_from_theme")
        )
