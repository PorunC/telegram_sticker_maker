# 🛠️ 安装指南

Telegram Sticker Maker 支持多种安装方式，选择适合您系统的方法：

## 🚀 一键安装 (推荐)

### Windows 用户
```cmd
双击运行: install_windows.bat
```

### macOS 用户  
```bash
./install_macos.sh
```

### Linux 用户
```bash
./install_linux.sh
```

### 通用 Python 脚本
```bash
python3 install.py
```

## 📋 手动安装

### 1. 安装 Python 3.7+
- **Windows**: [python.org](https://www.python.org/downloads/) (勾选"Add Python to PATH")
- **macOS**: `brew install python` 或从官网下载
- **Linux**: `sudo apt install python3 python3-pip` (Ubuntu/Debian)

### 2. 安装 Python 依赖
```bash
pip install Pillow>=8.0.0
```

### 3. 安装 FFmpeg
- **Windows**: [下载FFmpeg](https://www.gyan.dev/ffmpeg/builds/) 并添加到PATH
- **macOS**: `brew install ffmpeg`  
- **Linux**: `sudo apt install ffmpeg` (Ubuntu/Debian)

### 4. 验证安装
```bash
python3 -c "from PIL import Image; print('Pillow OK')"
ffmpeg -version
```

## 🎯 启动应用

安装完成后，有多种启动方式：

### 图形界面 (推荐)
```bash
# Windows
双击: start_gui.bat

# macOS/Linux  
./telegram-sticker-maker
# 或
python3 run_gui.py
```

### 命令行
```bash
# Windows
telegram_sticker_maker.bat input.gif

# macOS/Linux
./telegram-sticker-maker input.gif
# 或
python3 telegram_sticker_maker.py input.gif
```

## 🔍 故障排除

### 常见问题

**❌ "Python 未找到"**
- 确保Python已安装并添加到PATH
- Windows用户重新安装Python时勾选"Add Python to PATH"

**❌ "FFmpeg 未找到"**
- 确保FFmpeg已安装并添加到PATH  
- Windows用户可使用Chocolatey: `choco install ffmpeg`
- 重启终端/命令提示符

**❌ "tkinter 模块未找到"**
- Linux: `sudo apt install python3-tk`
- macOS: 重新安装Python (从python.org)
- Windows: 重新安装Python并选择tcl/tk组件

**❌ "权限被拒绝"**
- Linux/macOS: `chmod +x install_*.sh`
- Windows: 以管理员身份运行

**❌ "VP9 编码器未找到"**
- 重新安装FFmpeg确保包含libvpx-vp9
- 检查FFmpeg编译选项: `ffmpeg -encoders | grep vp9`

### 平台特定问题

**Windows:**
- 如果Chocolatey安装失败，使用管理员权限运行PowerShell
- 某些杀毒软件可能阻止下载，暂时禁用

**macOS:**
- 首次运行可能需要在"系统偏好设置 → 安全性与隐私"中允许
- Apple Silicon用户确保使用native Python

**Linux:**
- 某些发行版需要启用EPEL仓库获取FFmpeg
- 如果包管理器版本太旧，考虑使用Flatpak或Snap

## 📝 验证安装

运行以下命令验证所有组件：

```bash
# 通用测试脚本
python3 install.py --test-only

# 手动验证
python3 -c "
import sys
from PIL import Image
import tkinter
print(f'Python: {sys.version}')
print('Pillow: OK') 
print('tkinter: OK')
"

ffmpeg -version | head -1
```

## 🆘 获取帮助

如果遇到问题：

1. 📖 查看 [APP_README.md](APP_README.md) 获取详细使用指南
2. 🔍 检查上述故障排除部分
3. 🐛 在项目页面报告问题
4. 💬 搜索已知问题和解决方案

## 📚 依赖说明

### 必需依赖
- **Python 3.7+**: 核心运行环境
- **Pillow**: 图像处理库
- **tkinter**: GUI界面 (通常随Python安装)

### 可选依赖  
- **FFmpeg**: WebM视频转换 (推荐安装)
  - 不安装仅支持静态PNG表情包
  - 安装后支持动画WebM表情包

### 系统要求
- **Windows**: Windows 10+ (推荐)
- **macOS**: macOS 10.14+ (推荐)  
- **Linux**: 现代发行版 (Ubuntu 18.04+, CentOS 7+等)
- **内存**: 建议512MB+ 可用内存
- **存储**: 100MB+ 可用空间

---

🎉 **安装完成后即可开始制作专属的Telegram表情包！**