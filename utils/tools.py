#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from typing import List
from utils.constants import Constants


def display_error_dialog(content: str) -> None:
    QMessageBox.critical(None, f"Error - {Constants.APP_NAME}", content)


def execute_command(args: List[str], output: bool = True, raise_error: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=output, text=True, check=raise_error)
    except subprocess.CalledProcessError as e:
        display_error_dialog(f"Error executing command:\n\n{' '.join(args)}\n\n{e}")
        sys.exit(1)


def ensure_single_instance() -> QLocalServer:
    socket = QLocalSocket()
    socket.connectToServer(Constants.APP_ID)
    if socket.waitForConnected(500):
        sys.exit(0)
    server = QLocalServer()
    server.removeServer(Constants.APP_ID)
    server.listen(Constants.APP_ID)
    return server
