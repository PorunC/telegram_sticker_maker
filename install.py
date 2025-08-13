#!/usr/bin/env python3
"""
Telegram Sticker Maker - 通用 Python 安装脚本
跨平台自动检测并安装依赖
"""

import os
import sys
import subprocess
import platform
import urllib.request
import tempfile
import shutil
from pathlib import Path

def get_platform_info():
    """获取平台信息"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    return {
        'system': system,
        'machine': machine, 
        'python_version': python_version,
        'is_windows': system == 'windows',
        'is_macos': system == 'darwin',
        'is_linux': system == 'linux',
        'is_arm': 'arm' in machine or 'aarch64' in machine
    }

def log(level, message):
    """日志输出"""
    icons = {'INFO': '💡', 'SUCCESS': '✅', 'WARNING': '⚠️', 'ERROR': '❌'}
    icon = icons.get(level, '📝')
    print(f"{icon} {message}")

def run_command(cmd, shell=False, check=True, capture_output=False):
    """执行命令"""
    try:
        if isinstance(cmd, str):
            cmd = cmd.split() if not shell else cmd
        
        result = subprocess.run(
            cmd, 
            shell=shell, 
            check=check, 
            capture_output=capture_output,
            text=True
        )
        
        if capture_output:
            return result.stdout.strip()
        return True
        
    except subprocess.CalledProcessError as e:
        if capture_output:
            return None
        return False
    except FileNotFoundError:
        return False

def check_command_exists(command):
    """检查命令是否存在"""
    return shutil.which(command) is not None

def check_python_requirements():
    """检查Python版本要求"""
    log('INFO', f"检查Python版本... 当前: {sys.version}")
    
    if sys.version_info < (3, 7):
        log('ERROR', f"需要Python 3.7+，当前版本: {sys.version_info.major}.{sys.version_info.minor}")
        return False
    
    log('SUCCESS', "Python版本满足要求")
    return True

def install_python_packages():
    """安装Python依赖包"""
    log('INFO', "安装Python依赖包...")
    
    # 升级pip
    log('INFO', "升级pip...")
    if not run_command([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip']):
        log('WARNING', "pip升级失败，继续安装...")
    
    # 安装核心依赖
    packages = ['Pillow>=8.0.0']
    
    for package in packages:
        log('INFO', f"安装 {package}...")
        if run_command([sys.executable, '-m', 'pip', 'install', package]):
            log('SUCCESS', f"{package} 安装成功")
        else:
            log('ERROR', f"{package} 安装失败")
            return False
    
    return True


def install_ffmpeg_windows():
    """在Windows上安装FFmpeg"""
    log('INFO', "检查FFmpeg...")
    
    if check_command_exists('ffmpeg'):
        log('SUCCESS', "FFmpeg 已安装")
        return True
    
    log('WARNING', "FFmpeg 未安装")
    
    # 检查包管理器
    if check_command_exists('choco'):
        log('INFO', "使用Chocolatey安装FFmpeg...")
        if run_command('choco install ffmpeg -y', shell=True):
            log('SUCCESS', "FFmpeg 通过Chocolatey安装成功")
            return True
    
    if check_command_exists('winget'):
        log('INFO', "使用Winget安装FFmpeg...")
        if run_command('winget install --id Gyan.FFmpeg --silent --accept-package-agreements', shell=True):
            log('SUCCESS', "FFmpeg 通过Winget安装成功")
            return True
    
    log('WARNING', "自动安装失败，请手动安装FFmpeg")
    log('INFO', "下载地址: https://www.gyan.dev/ffmpeg/builds/")
    return False

def install_ffmpeg_macos():
    """在macOS上安装FFmpeg"""
    log('INFO', "检查FFmpeg...")
    
    if check_command_exists('ffmpeg'):
        log('SUCCESS', "FFmpeg 已安装")
        return True
    
    if not check_command_exists('brew'):
        log('WARNING', "Homebrew 未安装，请先安装: https://brew.sh")
        return False
    
    log('INFO', "使用Homebrew安装FFmpeg...")
    if run_command('brew install ffmpeg', shell=True):
        log('SUCCESS', "FFmpeg 安装成功")
        return True
    else:
        log('ERROR', "FFmpeg 安装失败")
        return False

def install_ffmpeg_linux():
    """在Linux上安装FFmpeg"""
    log('INFO', "检查FFmpeg...")
    
    if check_command_exists('ffmpeg'):
        log('SUCCESS', "FFmpeg 已安装")
        return True
    
    # 尝试不同的包管理器
    package_managers = [
        ('apt', 'sudo apt update && sudo apt install -y ffmpeg'),
        ('yum', 'sudo yum install -y ffmpeg'),
        ('dnf', 'sudo dnf install -y ffmpeg'),
        ('pacman', 'sudo pacman -S --noconfirm ffmpeg'),
        ('zypper', 'sudo zypper install -y ffmpeg')
    ]
    
    for pm, cmd in package_managers:
        if check_command_exists(pm):
            log('INFO', f"使用 {pm} 安装FFmpeg...")
            if run_command(cmd, shell=True):
                log('SUCCESS', "FFmpeg 安装成功")
                return True
            break
    
    log('WARNING', "自动安装失败，请手动安装FFmpeg")
    return False

def install_ffmpeg():
    """根据平台安装FFmpeg"""
    platform_info = get_platform_info()
    
    if platform_info['is_windows']:
        return install_ffmpeg_windows()
    elif platform_info['is_macos']:
        return install_ffmpeg_macos()
    elif platform_info['is_linux']:
        return install_ffmpeg_linux()
    else:
        log('WARNING', f"未支持的平台: {platform_info['system']}")
        return False

def test_installation():
    """测试安装结果"""
    log('INFO', "测试安装...")
    
    tests_passed = 0
    total_tests = 0
    
    # 测试Python模块
    total_tests += 1
    try:
        from PIL import Image
        log('SUCCESS', "Pillow 模块测试通过")
        tests_passed += 1
    except ImportError:
        log('ERROR', "Pillow 模块测试失败")
    
    
    # 测试FFmpeg
    total_tests += 1
    if check_command_exists('ffmpeg'):
        # 检查VP9支持
        vp9_output = run_command('ffmpeg -encoders', shell=True, check=False, capture_output=True)
        if vp9_output and 'libvpx-vp9' in vp9_output:
            log('SUCCESS', "FFmpeg (含VP9) 测试通过")
        else:
            log('WARNING', "FFmpeg 可用但VP9支持未确认")
        tests_passed += 1
    else:
        log('WARNING', "FFmpeg 测试失败")
    
    # 测试核心模块
    total_tests += 1
    if os.path.exists('telegram_sticker_maker.py'):
        try:
            # 简单的导入测试
            import importlib.util
            spec = importlib.util.spec_from_file_location("telegram_sticker_maker", "telegram_sticker_maker.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            log('SUCCESS', "核心模块测试通过")
            tests_passed += 1
        except Exception as e:
            log('WARNING', f"核心模块测试失败: {e}")
    else:
        log('WARNING', "核心模块文件未找到")
    
    log('INFO', f"测试完成: {tests_passed}/{total_tests} 通过")
    return tests_passed >= 3  # 至少3个测试通过才认为安装成功

def create_launchers():
    """创建启动脚本"""
    log('INFO', "创建启动脚本...")
    
    platform_info = get_platform_info()
    
    if platform_info['is_windows']:
        # Windows批处理文件
        with open('telegram_sticker_maker.bat', 'w', encoding='utf-8') as f:
            f.write('@echo off\n')
            f.write('cd /d "%~dp0"\n')
            f.write('python telegram_sticker_maker.py %*\n')
        
        log('SUCCESS', "Windows启动脚本创建完成")
        
    else:
        # Unix shell脚本
        script_content = '''#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
python3 telegram_sticker_maker.py "$@"
'''
        
        with open('telegram-sticker-maker', 'w') as f:
            f.write(script_content)
        
        os.chmod('telegram-sticker-maker', 0o755)
        log('SUCCESS', "Unix启动脚本创建完成")

def show_usage():
    """显示使用说明"""
    platform_info = get_platform_info()
    
    print("\n" + "="*50)
    print("🎉 安装完成！")
    print("="*50)
    
    print("\n💡 使用方法:")
    
    if platform_info['is_windows']:
        print("\n💻 命令行:")
        print("   telegram_sticker_maker.bat input.gif")
        
    else:
        print("\n💻 命令行:")
        print("   ./telegram-sticker-maker input.gif")
    
    print("\n🐍 直接Python:")
    print("   python3 telegram_sticker_maker.py input.gif")
    
    print("\n📖 示例:")
    print("   转换单个文件: telegram_sticker_maker.py dance.gif")
    print("   批量转换: telegram_sticker_maker.py ./images/ --pack-name MyPack")
    
    print("\n🔍 故障排除:")
    print("   - 如果WebM转换失败，检查FFmpeg安装")
    print("   - 重启终端/命令提示符刷新环境变量")
    print("   - 确保输入文件格式受支持 (GIF, PNG, WEBP, MP4, WebM)")

def main():
    """主函数"""
    print("🎯 Telegram Sticker Maker - 通用安装脚本")
    print("=" * 50)
    
    platform_info = get_platform_info()
    log('INFO', f"检测到系统: {platform_info['system']} ({platform_info['machine']})")
    log('INFO', f"Python 版本: {platform_info['python_version']}")
    
    # 检查是否在项目目录中
    if not os.path.exists('telegram_sticker_maker.py'):
        log('ERROR', "请在Telegram Sticker Maker项目目录中运行此脚本")
        return False
    
    # 用户确认
    try:
        response = input("\n是否继续安装依赖？[y/N]: ").lower().strip()
        if response not in ['y', 'yes']:
            print("安装已取消")
            return False
    except KeyboardInterrupt:
        print("\n安装已取消")
        return False
    
    print("\n开始安装...")
    
    # 安装步骤
    steps = [
        ("检查Python要求", check_python_requirements),
        ("安装Python包", install_python_packages), 
        ("安装FFmpeg", install_ffmpeg),
        ("测试安装", test_installation),
        ("创建启动脚本", create_launchers)
    ]
    
    for step_name, step_func in steps:
        log('INFO', f"执行: {step_name}")
        if not step_func():
            log('WARNING', f"{step_name} 未完全成功，但继续安装...")
        print()
    
    show_usage()
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n安装被用户中断")
        sys.exit(1)
    except Exception as e:
        log('ERROR', f"安装过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)