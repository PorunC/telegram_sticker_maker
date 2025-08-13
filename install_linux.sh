#!/bin/bash

# Telegram Sticker Maker - Linux 安装脚本
# 支持 Ubuntu/Debian/CentOS/Fedora 等主要发行版

set -e  # 遇到错误立即退出

echo "======================================"
echo "🎯 Telegram Sticker Maker - Linux 安装"
echo "======================================"
echo

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检测发行版
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO=$ID
        VERSION=$VERSION_ID
    elif [ -f /etc/redhat-release ]; then
        DISTRO="rhel"
    elif [ -f /etc/debian_version ]; then
        DISTRO="debian"
    else
        DISTRO="unknown"
    fi
    
    log_info "检测到系统: $DISTRO $VERSION"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 安装系统包管理器包
install_system_packages() {
    log_info "安装系统依赖..."
    
    case $DISTRO in
        ubuntu|debian)
            log_info "使用 apt 安装依赖..."
            sudo apt update
            sudo apt install -y python3 python3-pip python3-venv python3-tk ffmpeg
            ;;
        fedora)
            log_info "使用 dnf 安装依赖..."
            sudo dnf install -y python3 python3-pip python3-venv python3-tkinter ffmpeg
            ;;
        centos|rhel)
            log_info "使用 yum 安装依赖..."
            # 需要启用 EPEL 仓库获取 ffmpeg
            sudo yum install -y epel-release
            sudo yum install -y python3 python3-pip python3-venv tkinter ffmpeg
            ;;
        arch|manjaro)
            log_info "使用 pacman 安装依赖..."
            sudo pacman -Sy --noconfirm python python-pip python-virtualenv tk ffmpeg
            ;;
        opensuse*)
            log_info "使用 zypper 安装依赖..."
            sudo zypper install -y python3 python3-pip python3-venv python3-tk ffmpeg
            ;;
        *)
            log_warning "未识别的发行版: $DISTRO"
            log_warning "请手动安装: python3, python3-pip, python3-venv, python3-tk, ffmpeg"
            ;;
    esac
}

# 检查 Python 版本
check_python() {
    log_info "检查 Python 版本..."
    
    if ! command_exists python3; then
        log_error "Python3 未安装"
        return 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    log_info "Python 版本: $PYTHON_VERSION"
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
        log_error "需要 Python 3.7 或更高版本，当前版本: $PYTHON_VERSION"
        return 1
    fi
    
    log_success "Python 版本检查通过"
}

# 检查 FFmpeg
check_ffmpeg() {
    log_info "检查 FFmpeg..."
    
    if ! command_exists ffmpeg; then
        log_error "FFmpeg 未安装"
        return 1
    fi
    
    FFMPEG_VERSION=$(ffmpeg -version 2>/dev/null | head -n1 | grep -oE 'version [0-9]+\.[0-9]+' | grep -oE '[0-9]+\.[0-9]+')
    log_info "FFmpeg 版本: $FFMPEG_VERSION"
    
    # 检查 VP9 编码器支持
    if ffmpeg -encoders 2>/dev/null | grep -q libvpx-vp9; then
        log_success "VP9 编码器支持 ✓"
    else
        log_warning "VP9 编码器未找到，WebM 转换可能不工作"
    fi
    
    log_success "FFmpeg 检查完成"
}

# 安装 Python 依赖
install_python_deps() {
    log_info "安装 Python 依赖..."
    
    # 升级 pip
    python3 -m pip install --user --upgrade pip
    
    # 安装项目依赖 (包含Web界面和代理支持)
    if [ -f "requirements.txt" ]; then
        python3 -m pip install --user -r requirements.txt
        log_success "Python 依赖安装完成 (包含Flask Web界面)"
    else
        log_warning "requirements.txt 未找到，手动安装核心依赖..."
        python3 -m pip install --user "Pillow>=8.0.0"
    fi
}

# 测试安装
test_installation() {
    log_info "测试安装..."
    
    # 测试 Python 导入
    if python3 -c "from PIL import Image; print('✓ Pillow 导入成功')" 2>/dev/null; then
        log_success "Pillow 测试通过"
    else
        log_error "Pillow 测试失败"
        return 1
    fi
    
    # 测试Web框架导入
    if python3 -c "import flask; print('✓ Flask 导入成功')" 2>/dev/null; then
        log_success "Flask Web框架测试通过"
    else
        log_error "Flask 测试失败"
        return 1
    fi
    
    # 测试核心模块导入
    if python3 -c "from telegram_sticker_maker import TelegramStickerMaker; print('✓ 核心模块导入成功')" 2>/dev/null; then
        log_success "核心模块测试通过"
    else
        log_error "核心模块测试失败"
        return 1
    fi
    
    log_success "所有测试通过！"
}

# 创建启动脚本
create_launcher() {
    log_info "创建启动脚本..."
    
    cat > telegram-sticker-maker << 'EOF'
#!/bin/bash
# Telegram Sticker Maker 启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ "$1" = "--web" ] || [ $# -eq 0 ]; then
    echo "🌐 启动Web界面..."
    python3 start_web.py
elif [ "$1" = "--cli" ]; then
    shift
    python3 telegram_sticker_maker.py "$@"
else
    python3 telegram_sticker_maker.py "$@"
fi
EOF
    
    chmod +x telegram-sticker-maker
    log_success "启动脚本创建完成: ./telegram-sticker-maker"
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
    echo "🌐 Web界面 (推荐):"
    echo "   ./telegram-sticker-maker                  # 启动Web界面"
    echo "   ./telegram-sticker-maker --web            # 同上"
    echo "   或: python3 start_web.py"
    echo
    echo "💻 命令行使用:"
    echo "   ./telegram-sticker-maker --cli input.gif"
    echo "   或: python3 telegram_sticker_maker.py input.gif"
    echo
    echo "📖 查看帮助:"
    echo "   python3 telegram_sticker_maker.py --help"
    echo
    echo "示例:"
    echo "  ./telegram-sticker-maker                   # Web界面"
    echo "  ./telegram-sticker-maker --cli dance.gif  # 命令行转换"
    echo
    echo "故障排除:"
    echo "  - 如果遇到权限问题，尝试: chmod +x ./telegram-sticker-maker"
    echo "  - 如果 WebM 转换失败，检查 FFmpeg 的 VP9 编码器支持"
    echo
}

# 主函数
main() {
    # 检查是否在项目目录中
    if [ ! -f "telegram_sticker_maker.py" ]; then
        log_error "请在 Telegram Sticker Maker 项目目录中运行此脚本"
        exit 1
    fi
    
    # 检测系统
    detect_distro
    
    # 询问用户是否继续
    echo "即将安装以下依赖:"
    echo "  - Python 3.7+"
    echo "  - Python 包: Pillow, Flask, requests (含代理支持)"
    echo "  - 系统包: python3-tk, ffmpeg"
    echo
    read -p "是否继续安装？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "安装已取消"
        exit 0
    fi
    
    # 执行安装步骤
    install_system_packages
    check_python || exit 1
    check_ffmpeg || exit 1
    install_python_deps
    test_installation || exit 1
    create_launcher
    show_usage
}

# 运行主函数
main "$@"