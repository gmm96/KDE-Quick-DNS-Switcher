#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Callable, Any
from src.app.error_handler import ErrorHandler


class UiContext:
    error_handler: Optional[ErrorHandler] = None

    @staticmethod
    def safe_callback(function: Callable[[], Any]) -> Callable[..., None]:
        def wrapper(*args: Any, **kwargs: Any) -> None:
            try:
                function()
            except Exception as e:
                UiContext.error_handler.handle(e)
        return wrapper
