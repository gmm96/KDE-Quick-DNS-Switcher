#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from typing import List
from src.domain.models.active_dns_mode import ActiveDnsMode
from src.domain.models.dns_snapshot import DnsSnapshot
from src.domain.models.active_dns import ActiveDns
from src.ui.ui_constants import UiConstants


@dataclass(frozen=True)
class ActiveDnsView:
    display_name: str
    icon_key: str
    from_theme: bool
    body: List[str]
    dns_snapshot: DnsSnapshot
    mode: ActiveDnsMode

    @staticmethod
    def from_active_dns(active_dns: ActiveDns) -> ActiveDnsView:
        if active_dns.mode == ActiveDnsMode.DISCONNECTED:
            display_name: str = UiConstants.DISCONNECTED_NAME
            icon_key: str = UiConstants.DISCONNECTED_ICON
            from_theme: bool = False
        elif active_dns.mode == ActiveDnsMode.AUTO:
            display_name: str = UiConstants.AUTO_NAME
            icon_key: str = UiConstants.AUTO_ICON
            from_theme: bool = False
        elif active_dns.provider:
            display_name: str = active_dns.provider.name
            icon_key: str = active_dns.provider.icon
            from_theme: bool = active_dns.provider.icon_from_theme
        else:
            display_name: str = UiConstants.CUSTOM_NAME
            icon_key: str = UiConstants.DEFAULT_ICON
            from_theme: bool = False
        body: List[str] = active_dns.dns_snapshot.all_ips if active_dns.dns_snapshot.all_ips else [UiConstants.DEFAULT_BODY]
        return ActiveDnsView(
            display_name=display_name,
            icon_key=icon_key,
            from_theme=from_theme,
            body=body,
            dns_snapshot=active_dns.dns_snapshot,
            mode=active_dns.mode
        )
