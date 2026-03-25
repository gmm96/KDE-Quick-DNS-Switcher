#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from PyQt6.QtGui import QIcon


@dataclass
class AppIcon:
    name: str
    from_theme: bool
    icon: QIcon
    path: Optional[Path] = None
