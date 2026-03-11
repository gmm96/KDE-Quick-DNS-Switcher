#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Constants:
    APP_ID = "quick_dns_switcher"
    APP_NAME = "Quick DNS switcher"
    CONFIG_FILENAME = "dns-providers.json"
    ICON_DIRNAME = "icons"
    AUTO_MODE_NAME = "Automatic"
    AUTO_MODE_ICON = "network-workgroup"
    CUSTOM_MODE_ICON = "network-server"
    IGNORED_DEVICES = {"", "lo", "tun0", "docker0", "virbr0", "tailscale0", "wg0"}
