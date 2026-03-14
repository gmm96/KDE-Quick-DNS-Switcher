#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
from PyQt6.QtWidgets import QMessageBox
from typing import List


def display_error_dialog(content: str) -> None:
    QMessageBox.critical(None, f"Error - Quick DNS Switcher", content)


def execute_command(args: List[str], output: bool = True, raise_error: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(args, capture_output=output, text=True, check=raise_error)
    except subprocess.CalledProcessError as e:
        display_error_dialog(f"Error executing command:\n\n{' '.join(args)}\n\n{e}")
        sys.exit(1)
