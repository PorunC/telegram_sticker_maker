@echo off
chcp 65001 >nul 2>&1

title Telegram Sticker Maker - Windows 安装

echo.
echo ========================================
echo 🎯 Telegram Sticker Maker - Windows 安装
echo ========================================
echo.

REM 设置变量
set PYTHON_MIN_VERSION=3.7
set INSTALL_SUCCESS=0

echo 📋 即将安装以下组件:
echo   - Python 3.7+ (如果未安装)
echo   - Python 包: Pillow
echo   - FFmpeg (视频处理)
echo   - 桌面快捷方式
echo.

set /p CONTINUE="是否继续安装？[y/N]: "
if /i not "%CONTINUE%"=="y" (
    echo 安装已取消
    pause
    exit /b 0
)

echo.
echo =====================================
echo [1/5] 检查 Python 安装
echo =====================================

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Python
    echo.
    echo 🔗 正在打开 Python 下载页面...
    start https://www.python.org/downloads/
    echo.
    echo 📥 请下载并安装 Python 3.7 或更高版本
    echo 💡 安装时请勾选 "Add Python to PATH" 选项
    echo.
    echo 安装完成后请重新运行此脚本
    pause
    exit /b 1
)

REM 获取Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python 已安装: %PYTHON_VERSION%

REM 检查Python版本
python -c "import sys; exit(0 if sys.version_info >= (3,7) else 1)" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python 版本太低，需要 3.7 或更高版本
    echo 当前版本: %PYTHON_VERSION%
    echo 请更新 Python 后重试
    pause
    exit /b 1
)

echo.
echo =====================================
echo [2/5] 升级 pip 和安装 Python 依赖
echo =====================================

echo 📦 升级 pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ⚠️ pip 升级失败，继续安装...
)

REM 检查是否有requirements.txt
if exist "requirements.txt" (
    echo 📦 安装所有Python依赖 (包含Web界面)...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ 依赖安装失败
        echo 尝试单独安装核心依赖...
        python -m pip install "Pillow>=10.0.0" "Flask==3.0.0" "requests>=2.31.0"
    )
) else (
    echo 📦 安装核心Python依赖...
    python -m pip install "Pillow>=10.0.0" "Flask==3.0.0" "requests>=2.31.0"
)
if %errorlevel% neq 0 (
    echo ❌ Python依赖安装失败
    echo 可能原因: 网络问题或权限不足
    echo 尝试手动安装: pip install -r requirements.txt
    pause
    exit /b 1
)
echo ✅ Python依赖安装成功 (包含Flask Web界面)

echo.
echo =====================================
echo [3/5] 检查和安装 FFmpeg
echo =====================================

ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ FFmpeg 已安装
    goto :test_vp9
)

echo ⚠️ 未找到 FFmpeg
echo.
echo 🔧 FFmpeg 安装选项:
echo   1. 使用 Chocolatey 自动安装 (推荐)
echo   2. 使用 Winget 自动安装
echo   3. 手动下载安装
echo   4. 跳过 FFmpeg 安装 (仅支持静态贴纸)
echo.

choice /c 1234 /n /m "请选择安装方式 [1-4]: "
set CHOICE_RESULT=%errorlevel%

if %CHOICE_RESULT% equ 4 (
    echo ⏭️ 跳过 FFmpeg 安装
    echo ⚠️ 只能制作静态贴纸，无法转换动画
    goto :test_installation
)

if %CHOICE_RESULT% equ 3 (
    echo 🔗 正在打开 FFmpeg 下载页面...
    start https://www.gyan.dev/ffmpeg/builds/
    echo.
    echo 📥 请下载 FFmpeg 并解压到任意目录
    echo 🔧 然后将 ffmpeg\bin 目录添加到系统 PATH 环境变量
    echo.
    echo 📝 添加到 PATH 的步骤:
    echo   1. 右键 "此电脑" → 属性
    echo   2. 高级系统设置 → 环境变量
    echo   3. 在系统变量中找到 Path，点击编辑
    echo   4. 新建，输入 FFmpeg 的 bin 目录路径
    echo   5. 确定保存，重启命令提示符
    echo.
    pause
    goto :test_installation
)

if %CHOICE_RESULT% equ 2 (
    echo 🔧 使用 Winget 安装 FFmpeg...
    winget --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Winget 未找到，请使用其他方式安装
        goto :manual_ffmpeg
    )
    winget install --id Gyan.FFmpeg --silent --accept-package-agreements
    goto :test_ffmpeg
)

if %CHOICE_RESULT% equ 1 (
    echo 🔧 使用 Chocolatey 安装 FFmpeg...
    
    REM 检查 Chocolatey
    choco --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo 📦 Chocolatey 未安装，正在安装...
        echo 🔐 需要管理员权限安装 Chocolatey
        
        powershell -Command "& {if (([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) { Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1')) } else { Write-Host '需要管理员权限安装 Chocolatey' }}"
        
        REM 刷新环境变量
        call refreshenv >nul 2>&1
        
        REM 再次检查
        choco --version >nul 2>&1
        if %errorlevel% neq 0 (
            echo ❌ Chocolatey 安装失败
            echo 💡 请以管理员身份运行命令提示符，或手动安装 FFmpeg
            pause
            exit /b 1
        )
    )
    
    echo ✅ Chocolatey 可用，安装 FFmpeg...
    choco install ffmpeg -y
    
    REM 刷新环境变量
    call refreshenv >nul 2>&1
)

:test_ffmpeg
echo 🧪 测试 FFmpeg 安装...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ FFmpeg 安装失败或未添加到 PATH
    echo 💡 请确保 ffmpeg.exe 在系统 PATH 中
    echo 🔄 你可能需要重启命令提示符或重新登录
    pause
) else (
    echo ✅ FFmpeg 安装成功
)

:test_vp9
echo 🧪 检查 VP9 编码器支持...
ffmpeg -encoders 2>nul | findstr "libvpx-vp9" >nul
if %errorlevel% equ 0 (
    echo ✅ VP9 编码器支持
) else (
    echo ⚠️ VP9 编码器未找到，WebM 转换可能受限
)

:test_installation
echo.
echo =====================================
echo [4/5] 测试安装
echo =====================================

echo 🧪 测试 Python 模块...
python -c "from PIL import Image; print('✅ Pillow 导入成功')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Pillow 测试失败
    set INSTALL_SUCCESS=1
) else (
    echo ✅ Pillow 测试通过
)


REM 测试核心模块
if exist "telegram_sticker_maker.py" (
    python -c "from telegram_sticker_maker import TelegramStickerMaker; print('✅ 核心模块导入成功')" 2>nul
    if %errorlevel% neq 0 (
        echo ❌ 核心模块测试失败
        set INSTALL_SUCCESS=1
    ) else (
        echo ✅ 核心模块测试通过
    )
)

echo.
echo =====================================
echo [5/5] 创建快捷方式和启动脚本
echo =====================================

echo 📝 创建启动脚本...

REM 创建命令行启动脚本
echo @echo off > telegram_sticker_maker.bat
echo cd /d "%%~dp0" >> telegram_sticker_maker.bat
echo python telegram_sticker_maker.py %%* >> telegram_sticker_maker.bat

echo ✅ 启动脚本创建完成

REM 创建桌面快捷方式 (可选)
set /p CREATE_SHORTCUT="是否在桌面创建快捷方式？[y/N]: "
if /i "%CREATE_SHORTCUT%"=="y" (
    echo 📱 创建桌面快捷方式...
    
    REM 使用 PowerShell 创建快捷方式
    powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%USERPROFILE%\Desktop\Telegram Sticker Maker.lnk'); $SC.TargetPath = '%CD%\start_gui.bat'; $SC.WorkingDirectory = '%CD%'; $SC.Description = 'Telegram Sticker Maker GUI'; $SC.Save()"
    
    if exist "%USERPROFILE%\Desktop\Telegram Sticker Maker.lnk" (
        echo ✅ 桌面快捷方式创建成功
    ) else (
        echo ⚠️ 桌面快捷方式创建失败
    )
)

echo.
echo ========================================
echo 🎉 安装完成！
echo ========================================

if %INSTALL_SUCCESS% neq 0 (
    echo ⚠️ 安装过程中遇到一些问题，但核心功能应该可以使用
    echo 如果遇到问题，请查看错误信息或寻求帮助
    echo.
)

echo 💡 使用方法:
echo.
echo 1. 💻 命令行:
echo    telegram_sticker_maker.bat input.gif
echo.
echo 2. 🔧 直接 Python:
echo    python telegram_sticker_maker.py input.gif
echo.
echo 📖 示例:
echo   telegram_sticker_maker.bat dance.gif
echo   telegram_sticker_maker.bat ./images/ --pack-name MyPack
echo.
echo 🔍 故障排除:
echo   - 如果 WebM 转换失败，检查 FFmpeg 安装
echo   - 如果遇到权限问题，尝试以管理员身份运行
echo   - 重启命令提示符以刷新 PATH 环境变量
echo.


pause