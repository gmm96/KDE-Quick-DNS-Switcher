# !/usr/bin/python3
# -*- coding: utf-8 -*-

from ip_pair import IpPair


class NetworkConnection:
    def __init__(self, name: str, device: str, ipv4: IpPair, ipv6: IpPair) -> None:
        self.name = name
        self.device = device
        self.ipv4 = ipv4
        self.ipv6 = ipv6
