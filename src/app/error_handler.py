#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.infrastructure.errors.backend_command_error import BackendCommandError
from src.infrastructure.errors.backend_init_error import BackendInitError
from src.infrastructure.errors.dns_catalog_load_error import DnsCatalogLoadError


class ErrorHandler:
    def handle(self, error: Exception):
        if isinstance(error, BackendInitError):
            self._handle_backend_init_error(error)
        elif isinstance(error, DnsCatalogLoadError):
            self._handle_catalog_error(error)
        elif isinstance(error, BackendCommandError):
            self._handle_backend_command_error(error)
        else:
            self._handle_unknown(error)

    def _handle_backend_init_error(self, error: BackendInitError) -> None:
        self._show("Backend initialization error", str(error))

    def _handle_catalog_error(self, error: DnsCatalogLoadError) -> None:
        self._show("Configuration error", str(error))

    def _handle_backend_command_error(self, error: BackendCommandError) -> None:
        self._show("Backend command error", str(error))

    def _handle_unknown(self, error) -> None:
        self._show("Unexpected error", str(error))

    def _show(self, title: str, message: str) -> None:
        raise NotImplementedError
