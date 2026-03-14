#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import abstractmethod, ABC
from typing import List
from network.ip_pair import IpPair
from network.network_connection import NetworkConnection


class NetworkBackendBase(ABC):

    @abstractmethod
    def get_active_connections(self) -> List[NetworkConnection]:
        pass

    @abstractmethod
    def set_dns(self, ipv4: IpPair, ipv6: IpPair):
        pass
