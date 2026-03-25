#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Callable, List


class NetworkMonitorBase:
    def __init__(self) -> None:
        self._callbacks: List[Callable[[], None]] = []

    def on_event(self, callback: Callable[[], None]) -> None:
        self._callbacks.append(callback)

    def _emit(self) -> None:
        for callback in self._callbacks:
            callback()
