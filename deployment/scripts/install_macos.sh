#!/bin/bash

# Telegram Sticker Maker - macOS 安装脚本
# 支持 macOS 10.14+ 和 Apple Silicon

set -e

echo "======================================"
echo "🎯 Telegram Sticker Maker - macOS 安装"
echo "======================================"
echo

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检测 macOS 版本和架构
detect_system() {
    MACOS_VERSION=$(sw_vers -productVersion)
    ARCH=$(uname -m)
    
    log_info "macOS 版本: $MACOS_VERSION"
    log_info "架构: $ARCH"
    
    # 检查 macOS 版本 (需要 10.14+)
    MAJOR_VERSION=$(echo $MACOS_VERSION | cut -d. -f1)
    MINOR_VERSION=$(echo $MACOS_VERSION | cut -d. -f2)
    
    if [ "$MAJOR_VERSION" -lt 10 ] || ([ "$MAJOR_VERSION" -eq 10 ] && [ "$MINOR_VERSION" -lt 14 ]); then
        log_error "需要 macOS 10.14 或更高版本，当前版本: $MACOS_VERSION"
        exit 1
    fi
}

# 检查并安装 Homebrew
install_homebrew() {
    if command_exists brew; then
        log_success "Homebrew 已安装"
        # 更新 Homebrew
        log_info "更新 Homebrew..."
        brew update
    else
        log_info "安装 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加 Homebrew 到 PATH (Apple Silicon)
        if [ "$ARCH" = "arm64" ]; then
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
    fi
}

# 安装 Python
install_python() {
    log_info "检查 Python 安装..."
    
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        log_info "当前 Python 版本: $PYTHON_VERSION"
        
        # 检查版本是否满足要求
        if python3 -c "import sys; exit(0 if sys.version_info >= (3,7) else 1)"; then
            log_success "Python 版本满足要求"
            return 0
        fi
    fi
    
    log_info "安装 Python..."
    brew install python@3.11
    
    # 确保 python3 指向正确版本
    if ! command_exists python3; then
        if [ "$ARCH" = "arm64" ]; then
            echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zprofile
            export PATH="/opt/homebrew/bin:$PATH"
        else
            echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zprofile
            export PATH="/usr/local/bin:$PATH"
        fi
    fi
}

# 安装 FFmpeg
install_ffmpeg() {
    log_info "安装 FFmpeg..."
    
    if command_exists ffmpeg; then
        log_success "FFmpeg 已安装"
    else
        brew install ffmpeg
    fi
    
    # 检查 VP9 支持
    if ffmpeg -encoders 2>/dev/null | grep -q libvpx-vp9; then
        log_success "VP9 编码器支持 ✓"
    else
        log_warning "VP9 编码器未找到，尝试重新安装 FFmpeg..."
        brew reinstall ffmpeg
    fi
}

# 检查开发者工具
check_xcode_tools() {
    log_info "检查 Xcode 开发者工具..."
    
    if ! xcode-select -p >/dev/null 2>&1; then
        log_info "安装 Xcode 开发者工具..."
        xcode-select --install
        
        echo "请按照提示安装 Xcode 开发者工具，然后重新运行此脚本"
        exit 1
    else
        log_success "Xcode 开发者工具已安装"
    fi
}

# 安装 Python 依赖
install_python_deps() {
    log_info "安装 Python 依赖..."
    
    # 升级 pip
    python3 -m pip install --upgrade pip
    
    # 安装项目依赖 (包含Web界面和代理支持)
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt
        log_success "Python 依赖安装完成 (包含Flask Web界面)"
    else
        log_warning "requirements.txt 未找到，手动安装核心依赖..."
        python3 -m pip install "Pillow>=10.0.0" "Flask==3.0.0" "requests>=2.31.0"
    fi
}

# 测试安装
test_installation() {
    log_info "测试安装..."
    
    # 测试 Python 版本
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    log_info "Python 版本: $PYTHON_VERSION"
    
    # 测试模块导入
    if python3 -c "from PIL import Image; print('✓ Pillow 导入成功')" 2>/dev/null; then
        log_success "Pillow 测试通过"
    else
        log_error "Pillow 测试失败"
        return 1
    fi
    
    # 测试 tkinter (macOS 自带)
    if python3 -c "import tkinter; print('✓ tkinter 导入成功')" 2>/dev/null; then
        log_success "tkinter 测试通过"
    else
        log_error "tkinter 测试失败"
        return 1
    fi
    
    # 测试 FFmpeg
    FFMPEG_VERSION=$(ffmpeg -version 2>/dev/null | head -n1 | grep -oE 'version [0-9]+\.[0-9]+' | grep -oE '[0-9]+\.[0-9]+')
    log_info "FFmpeg 版本: $FFMPEG_VERSION"
    
    # 测试核心模块
    if python3 -c "from telegram_sticker_maker import TelegramStickerMaker; print('✓ 核心模块导入成功')" 2>/dev/null; then
        log_success "核心模块测试通过"
    else
        log_error "核心模块测试失败"
        return 1
    fi
    
    log_success "所有测试通过！"
}

# 创建 macOS 应用包 (可选)
create_app_bundle() {
    log_info "是否创建 macOS 应用包？"
    read -p "创建 .app 应用包？[y/N] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        APP_NAME="Telegram Sticker Maker.app"
        APP_DIR="$APP_NAME/Contents"
        
        mkdir -p "$APP_DIR/MacOS"
        mkdir -p "$APP_DIR/Resources"
        
        # 创建 Info.plist
        cat > "$APP_DIR/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Telegram Sticker Maker</string>
    <key>CFBundleDisplayName</key>
    <string>Telegram Sticker Maker</string>
    <key>CFBundleIdentifier</key>
    <string>com.telegram.stickermaker</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleExecutable</key>
    <string>telegram_sticker_maker</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
        
        # 创建启动脚本
        cat > "$APP_DIR/MacOS/telegram_sticker_maker" << EOF
#!/bin/bash
BUNDLE_DIR="\$(dirname "\$0")/../.."
cd "\$BUNDLE_DIR"
python3 run_gui.py
EOF
        
        chmod +x "$APP_DIR/MacOS/telegram_sticker_maker"
        
        log_success "应用包创建完成: $APP_NAME"
        log_info "可以拖动到应用程序文件夹使用"
    fi
}

# 创建启动脚本
create_launcher() {
    log_info "创建启动脚本..."
    
    cat > telegram-sticker-maker << 'EOF'
#!/bin/bash
# Telegram Sticker Maker 启动脚本 (macOS)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 确保 Homebrew 在 PATH 中
if [ -f "/opt/homebrew/bin/brew" ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
elif [ -f "/usr/local/bin/brew" ]; then
    export PATH="/usr/local/bin:$PATH"
fi

if [ "$1" = "--gui" ] || [ $# -eq 0 ]; then
    python3 run_gui.py
else
    python3 telegram_sticker_maker.py "$@"
fi
EOF
    
    chmod +x telegram-sticker-maker
    log_success "启动脚本创建完成"
}

# 显示使用说明
show_usage() {
    echo
    echo "======================================"
    echo "🎉 安装完成！"
    echo "======================================"
    echo
    echo "使用方法:"
    echo
    echo "1. 🖥️  启动图形界面:"
    echo "   ./telegram-sticker-maker"
    echo "   或双击桌面应用 (如果已创建)"
    echo
    echo "2. 💻 命令行使用:"
    echo "   ./telegram-sticker-maker dance.gif"
    echo
    echo "3. 📝 Terminal 中直接使用:"
    echo "   python3 run_gui.py"
    echo "   python3 telegram_sticker_maker.py input.gif"
    echo
    echo "macOS 特殊说明:"
    echo "  - 首次运行可能需要允许应用访问文件"
    echo "  - 如果遇到权限问题，在 系统偏好设置 > 安全性与隐私 中允许"
    echo "  - 支持拖放文件到 Dock 图标"
    echo
    echo "故障排除:"
    echo "  - 如果 Python 命令找不到，重启终端或运行: source ~/.zprofile"
    echo "  - 如果 Homebrew 命令不工作，确保已正确安装"
    echo "  - Apple Silicon Mac 的 Homebrew 路径: /opt/homebrew/bin"
    echo "  - Intel Mac 的 Homebrew 路径: /usr/local/bin"
    echo
}

# 主函数
main() {
    # 检查是否在项目目录中
    if [ ! -f "telegram_sticker_maker.py" ]; then
        log_error "请在 Telegram Sticker Maker 项目目录中运行此脚本"
        exit 1
    fi
    
    # 系统检测
    detect_system
    
    echo "即将安装以下组件:"
    echo "  - Homebrew (包管理器)"
    echo "  - Python 3.11+"
    echo "  - FFmpeg (视频处理)"
    echo "  - Python 包: Pillow"
    echo
    read -p "是否继续安装？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "安装已取消"
        exit 0
    fi
    
    # 执行安装步骤
    check_xcode_tools
    install_homebrew
    install_python
    install_ffmpeg
    install_python_deps
    test_installation || exit 1
    create_launcher
    create_app_bundle
    show_usage
    
    log_success "macOS 安装完成！"
}

# 运行主函数
main "$@"