#!/usr/bin/env python3
"""
Telegram 表情包制作器 Web 服务启动器

便捷的启动脚本，包含依赖检查和环境设置
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def check_and_install_dependencies():
    """检查并安装依赖包"""
    print("🔍 检查Web服务依赖...")
    
    required_packages = [
        'flask',
        'flask_cors', 
        'PIL',
        'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                importlib.import_module('PIL')
            elif package == 'flask_cors':
                importlib.import_module('flask_cors')
            else:
                importlib.import_module(package)
            print(f"  ✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"\n📦 需要安装缺失的依赖包...")
        
        # 尝试安装缺失的包
        requirements_file = Path(__file__).parent / "requirements_web.txt"
        
        if requirements_file.exists():
            print(f"📝 使用 {requirements_file} 安装依赖...")
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', 
                    '-r', str(requirements_file)
                ])
                print("✅ 依赖包安装完成!")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ 依赖包安装失败: {e}")
                return False
        else:
            print("❌ 找不到 requirements_web.txt 文件")
            print("💡 请手动安装以下包:")
            for package in missing_packages:
                print(f"   pip install {package}")
            return False
    else:
        print("✅ 所有依赖包已安装!")
        return True

def check_external_dependencies():
    """检查外部依赖"""
    print("\n🔍 检查外部工具依赖...")
    
    # 检查FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("  ✓ FFmpeg")
        else:
            print("  ❌ FFmpeg (需要手动安装)")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("  ❌ FFmpeg (需要手动安装)")
        print("    💡 访问 https://ffmpeg.org/download.html 下载安装")
        return False
    
    return True

def check_project_files():
    """检查项目文件完整性"""
    print("\n🔍 检查项目文件...")
    
    required_files = [
        'web_server.py',
        'telegram_sticker_maker.py',
        'telegram_api_uploader.py',
        'telegram_sticker_manager.py',
        'templates/index.html',
        'static/css/style.css',
        'static/js/app.js'
    ]
    
    project_dir = Path(__file__).parent
    missing_files = []
    
    for file_path in required_files:
        full_path = project_dir / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"  ❌ {file_path}")
    
    if missing_files:
        print(f"\n❌ 缺少必需文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ 所有项目文件完整!")
    return True

def show_usage_info():
    """显示使用说明"""
    print("\n" + "="*60)
    print("🌐 Telegram 表情包制作器 Web 界面")
    print("="*60)
    print()
    print("📋 功能:")
    print("  • 配置 Telegram Bot Token 和用户 ID")
    print("  • 上传图片/视频文件制作表情包")
    print("  • 自动转换格式 (PNG/WebM)")
    print("  • 直接上传到 Telegram")
    print("  • 管理现有表情包 (CRUD)")
    print()
    print("🔗 访问地址:")
    print("  http://localhost:5000")
    print()
    print("📚 使用说明:")
    print("  1. 首先在'设置'页面配置 Bot Token")
    print("  2. 在'制作表情包'页面上传文件")
    print("  3. 在'管理表情包'页面管理现有包")
    print()
    print("⚠️  注意事项:")
    print("  • 需要创建 Telegram Bot (@BotFather)")
    print("  • 需要获取你的用户 ID (@userinfobot)")
    print("  • 支持文件格式: PNG, JPG, GIF, WebP, MP4, WebM")
    print("  • 最大文件大小: 50MB")
    print()

def start_web_server():
    """启动Web服务器"""
    print("🚀 启动Web服务器...")
    print("   按 Ctrl+C 停止服务")
    print()
    
    try:
        # 导入并运行Web服务器
        from web_server import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n👋 Web服务器已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🎉 Telegram 表情包制作器 Web 服务")
    print("=" * 50)
    
    # 检查项目文件
    if not check_project_files():
        print("\n❌ 项目文件不完整，请检查文件结构")
        sys.exit(1)
    
    # 检查Python依赖
    if not check_and_install_dependencies():
        print("\n❌ 依赖包安装失败，请手动安装")
        sys.exit(1)
    
    # 检查外部依赖（非强制）
    if not check_external_dependencies():
        print("\n⚠️  外部依赖缺失，部分功能可能无法使用")
        response = input("是否继续启动? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("👋 已取消启动")
            sys.exit(0)
    
    # 显示使用说明
    show_usage_info()
    
    # 等待用户确认
    input("按回车键启动Web服务器...")
    
    # 启动服务器
    start_web_server()

if __name__ == '__main__':
    main()