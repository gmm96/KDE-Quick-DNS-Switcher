#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import abstractmethod, ABC
from src.domain.models.dns_snapshot import DnsSnapshot
from src.domain.models.ip_pair import IpPair


class NetworkBackendBase(ABC):
    @abstractmethod
    def get_dns_snapshot(self) -> DnsSnapshot:
        pass

    @abstractmethod
    def set_dns(self, ipv4: IpPair, ipv6: IpPair) -> None:
        pass
