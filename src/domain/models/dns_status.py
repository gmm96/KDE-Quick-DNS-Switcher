#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum


class DnsStatus(Enum):
    DISCONNECTED = 0
    AUTO = 1
    MANUAL = 2
