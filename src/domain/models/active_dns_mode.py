#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum


class ActiveDnsMode(Enum):
    DISCONNECTED = 0
    AUTO = 1
    PROVIDER = 2
    CUSTOM = 3
