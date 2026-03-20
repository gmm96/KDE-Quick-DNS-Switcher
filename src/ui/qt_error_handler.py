#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from src.app.error_handler import ErrorHandler
from src.ui.dialog_controller import DialogController


class QtErrorHandler(ErrorHandler):
    def _show(self, title: str, message: str):
        logging.error(f"{title}: {message}")
        DialogController.show_error(f"{title}\n\n{message}")
