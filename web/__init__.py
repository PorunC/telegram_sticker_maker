"""
Telegram Sticker Maker - Web界面模块

提供完整的Web界面用于表情包制作和管理。
"""

from .server import app
from .app import main as start_web

__all__ = [
    'app',
    'start_web'
]

__version__ = '1.0.0'