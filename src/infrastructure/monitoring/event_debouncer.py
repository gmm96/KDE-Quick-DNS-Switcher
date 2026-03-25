#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable
from PyQt6.QtCore import QTimer


class Debouncer:
    def __init__(self, callback: Callable, delay: int = 500):
        self.callback: Callable = callback
        self.timer: QTimer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.callback)
        self.delay: int = delay

    def trigger(self):
        self.timer.start(self.delay)
