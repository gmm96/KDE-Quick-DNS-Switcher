#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from typing import Union
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication, QMessageBox
from src.ui.ui_constants import UiConstants


class DialogController:
    @staticmethod
    def show_error(content: str) -> None:
        app = DialogController._get_qapplication_instance()
        QMessageBox.critical(None, f"Error - {UiConstants.APP_NAME}", content)

    @staticmethod
    def show_info(content: str) -> None:
        app = DialogController._get_qapplication_instance()
        QMessageBox.information(None, UiConstants.APP_NAME, content)

    @staticmethod
    def _get_qapplication_instance() -> Union[QCoreApplication, QApplication]:
        app = QApplication.instance()
        return app if app is not None else QApplication(sys.argv)
