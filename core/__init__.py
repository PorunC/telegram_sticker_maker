"""
Telegram Sticker Maker - 核心功能模块

包含所有核心的表情包制作、管理和上传功能。
"""

from .sticker_maker import TelegramStickerMaker, StickerConfig
from .api_uploader import TelegramStickerUploader, load_env_file
from .sticker_manager import TelegramStickerManager
from .webm_converter import TelegramWebMConverter, TelegramWebMConfig

__all__ = [
    'TelegramStickerMaker',
    'StickerConfig', 
    'TelegramStickerUploader',
    'load_env_file',
    'TelegramStickerManager',
    'TelegramWebMConverter',
    'TelegramWebMConfig'
]

__version__ = '1.0.0'