#!/usr/bin/env python3
"""
Telegram Sticker Maker - 主入口点

提供兼容的导入路径和启动方式，支持新的模块化结构。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 兼容性导入 - 保持旧的导入路径可用
from core.sticker_maker import TelegramStickerMaker, StickerConfig
from core.api_uploader import TelegramStickerUploader, load_env_file
from core.sticker_manager import TelegramStickerManager
from core.webm_converter import TelegramWebMConverter, TelegramWebMConfig

# Web应用导入 - 设为可选
try:
    from web.server import app
    from web.app import main as start_web_server
    WEB_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Web界面依赖缺失: {e}")
    print("💡 运行 'pip install -r requirements.txt' 安装依赖")
    WEB_AVAILABLE = False
    app = None
    start_web_server = None

def main():
    """主入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Telegram Sticker Maker')
    parser.add_argument('--web', action='store_true', help='启动Web界面')
    parser.add_argument('--port', type=int, default=5000, help='Web服务端口')
    parser.add_argument('input_file', nargs='?', help='输入文件路径')
    parser.add_argument('output_file', nargs='?', help='输出文件路径')
    
    args = parser.parse_args()
    
    if args.web:
        # 启动Web界面
        if not WEB_AVAILABLE:
            print("❌ Web界面不可用，请先安装依赖:")
            print("   pip install -r requirements.txt")
            sys.exit(1)
        print("🌐 启动Web界面...")
        os.environ['PORT'] = str(args.port)
        start_web_server()
    elif args.input_file:
        # 命令行模式 - 直接处理文件
        print("🛠️ 命令行模式")
        config = StickerConfig()
        config.input_path = args.input_file
        
        if args.output_file:
            config.output_dir = str(Path(args.output_file).parent)
        
        maker = TelegramStickerMaker(config)
        result = maker.process_file()
        
        if result['success']:
            print(f"✅ 处理完成: {result['output_file']}")
        else:
            print(f"❌ 处理失败: {result['error']}")
            sys.exit(1)
    else:
        # 默认启动Web界面
        if not WEB_AVAILABLE:
            print("❌ Web界面不可用，请先安装依赖:")
            print("   pip install -r requirements.txt")
            print("\n💡 或者使用命令行模式:")
            print("   python main.py input_file.gif")
            sys.exit(1)
        print("🌐 默认启动Web界面 (使用 --help 查看更多选项)")
        start_web_server()

if __name__ == '__main__':
    main()