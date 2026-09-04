"""Caminhos de recursos do aplicativo e dados locais do usuario."""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "Integracao_EA-Khan"


def app_data_dir() -> Path:
    """Retorna o diretorio gravavel usado por cada professor no Windows."""
    base_dir = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA")
    if base_dir:
        return Path(base_dir) / APP_NAME
    return Path.home() / ".integracao-ea-khan"


def user_data_path(*parts: str) -> Path:
    return app_data_dir().joinpath(*parts)


def resource_path(*parts: str) -> Path:
    """Localiza arquivos incluidos pelo PyInstaller ou pelo projeto fonte."""
    if getattr(sys, "frozen", False):
        base_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base_dir = Path(__file__).resolve().parents[1]
    return base_dir.joinpath(*parts)
