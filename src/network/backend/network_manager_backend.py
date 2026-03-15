#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import List, Optional, Tuple, Set
from src.network.backend.network_backend_base import NetworkBackendBase
from src.network.dns_state import DnsState
from src.network.ip_pair import IpPair
from src.network.network_connection import NetworkConnection
from src.utils.tools import execute_command


class NetworkManagerBackend(NetworkBackendBase):
    IGNORED_DEVICES: Set[str] = {"", "lo", "tun0", "docker0", "virbr0", "tailscale0", "wg0"}

    def __init__(self) -> None:
        self.connections: List[NetworkConnection] = []

    def get_dns_state(self) -> DnsState:
        self.connections = []
        self._retrieve_active_connections_info()
        self._fill_auto_ignore_dns_field()
        return DnsState(self.connections)

    def _retrieve_active_connections_info(self) -> None:
        name: Optional[str] = None
        device: Optional[str] = None
        ipv4_list: List[str] = []
        ipv6_list: List[str] = []
        connected: bool = False

        def flush() -> None:
            if device and name and connected and device not in NetworkManagerBackend.IGNORED_DEVICES:
                self.connections.append(
                    NetworkConnection(
                        name,
                        device,
                        IpPair.from_list(4, ipv4_list),
                        IpPair.from_list(6, ipv6_list)
                    )
                )

        result = execute_command([
            "nmcli", "-t", "-f", "GENERAL.CONNECTION,GENERAL.DEVICE,GENERAL.STATE,IP4.DNS,IP6.DNS", "device", "show"
        ])
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line: continue
            if ":" not in line: continue

            key, value = line.split(":", 1)
            value = value.strip()
            if key == "GENERAL.CONNECTION":
                flush()
                name = value
                device = None
                connected = False
                ipv4_list = []
                ipv6_list = []
            elif key == "GENERAL.DEVICE":
                device = value
            elif key == "GENERAL.STATE":
                connected = value.startswith("100")
            elif key.startswith("IP4.DNS"):
                if value:
                    ipv4_list.append(value)
            elif key.startswith("IP6.DNS"):
                if value:
                    ipv6_list.append(value)

        flush()


    def _fill_auto_ignore_dns_field(self) -> None:
        for conn in self.connections:
            result = execute_command(
                ["nmcli", "-g", "ipv4.ignore-auto-dns,ipv6.ignore-auto-dns", "connection", "show", conn.name]
            )
            ipv4_ignore_auto_dns, ipv6_ignore_auto_dns = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            conn.parse_ignore_auto_dns(ipv4_ignore_auto_dns, ipv6_ignore_auto_dns)


    def set_dns(self, ipv4: IpPair, ipv6: IpPair) -> None:
        v4_ips: List[str] = ipv4.get_ip_list()
        v6_ips: List[str] = ipv6.get_ip_list()
        v4_ignore_auto: str = "yes" if v4_ips else "no"
        v6_ignore_auto: str = "yes" if v6_ips else "no"
        for conn in self.get_dns_state().connections:
            execute_command([
                "nmcli",
                "connection",
                "modify", conn.name,
                "ipv4.ignore-auto-dns", v4_ignore_auto,
                "ipv6.ignore-auto-dns", v6_ignore_auto,
                "ipv4.dns", ",".join(v4_ips),
                "ipv6.dns", ",".join(v6_ips)
            ])
            result_reapply = execute_command(["nmcli", "device", "reapply", conn.device], True, False)
            if result_reapply.returncode != 0:
                logging.warning("Error resetting network, trying aggressive method...", stack_info=True)
                execute_command(["nmcli", "connection", "up", conn.name], True, True)
