#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
from typing import List, Optional, Dict
from src.domain.models.dns_provider import DnsProvider
from src.infrastructure.errors.dns_catalog_load_error import DnsCatalogLoadError


class DnsProviderCatalog:
    def __init__(self, file_path: Path) -> None:
        self.file_path: Path = file_path
        self.providers: List[DnsProvider]= []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.file_path):
            raise DnsCatalogLoadError(f"DNS configuration file not found:\n\n{self.file_path}")
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data: Dict[str, Dict[str, str]] = json.load(f)
        except json.JSONDecodeError as e:
            raise DnsCatalogLoadError(f"Invalid JSON format in DNS configuration file:\n\n{self.file_path}\n\n{e}") from e
        except Exception as e:
            raise DnsCatalogLoadError(f"Unexpected error loading DNS configuration file:\n\n{self.file_path}\n\n{e}") from e
        self.providers = [DnsProvider.from_dict(name, details) for name, details in data.items()]

    def get_provider_by_name(self, name: str) -> Optional[DnsProvider]:
        return next((dns for dns in self.providers if dns.name == name), None)
