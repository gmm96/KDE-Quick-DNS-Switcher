#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
from typing import List


class CommandExecutor:
    @staticmethod
    def execute(args: List[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.run(args, capture_output=True, text=True, **kwargs)

    @staticmethod
    def execute_async(args: List[str], **kwargs) -> None:
        subprocess.Popen(args, **kwargs)
