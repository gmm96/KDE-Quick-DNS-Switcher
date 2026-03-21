#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from src.ui.models.app_icon import AppIcon


class NotifierBase(ABC):
    @abstractmethod
    def notify(self, title: str, message: str, icon: AppIcon, timeout: int = 5000) -> None:
        pass
