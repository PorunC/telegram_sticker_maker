# 🎯 Telegram Sticker Maker

专业的Telegram表情包制作和导入工具，支持将任何媒体文件转换为符合Telegram官方要求的表情包格式。

## ✨ 主要特性

- **🖼️ 多格式支持**: GIF, PNG, WEBP, MP4, WebM → PNG/WebM表情包
- **🎨 智能转换**: 自动选择最佳输出格式 (静态PNG或动画WebM)
- **💻 命令行工具**: 高效批处理，支持脚本集成
- **🌍 跨平台**: Windows, macOS, Linux 全平台支持
- **🎯 官方兼容**: 完全符合Telegram 7.8+ 导入API要求

## 🚀 快速开始

### 一键安装

选择适合您系统的安装方式：

```bash
# Windows 用户
双击运行: install_windows.bat

# macOS 用户
./install_macos.sh

# Linux 用户  
./install_linux.sh

# 通用 Python 脚本
python3 install.py
```

### 配置 (可选)

创建 `.env` 文件来保存常用配置：

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置
# TELEGRAM_BOT_TOKEN=你的Bot Token
# TELEGRAM_USER_ID=你的用户ID
```

### 立即使用

```bash
# 命令行转换
python3 telegram_sticker_maker.py input.gif

# 自动上传到Telegram (需要配置)
python3 telegram_sticker_maker.py input.gif --upload
```

## 📋 格式支持

| 输入格式 | 输出格式 | 文件大小限制 | 适用场景 |
|----------|----------|--------------|----------|
| PNG, WEBP, JPG | PNG/WebP | ≤ 512KB | 静态表情、Logo |
| GIF, MP4, WebM | WebM (VP9) | ≤ 256KB | 动画表情、视频片段 |

**尺寸要求**: 512×512px (一边必须为512px，另一边≤512px)

## 🎨 使用示例
```bash
# 转换单个文件
python3 telegram_sticker_maker.py dance.gif

# 批量处理文件夹
python3 telegram_sticker_maker.py ./images/ --pack-name MyStickers

# 强制使用WebM格式
python3 telegram_sticker_maker.py video.mp4 --format webm --emoji 🎬

# 查看完整帮助
python3 telegram_sticker_maker.py --help
```

## 📱 导入到Telegram

### 🚀 自动上传 (推荐)

配置后一键上传到Telegram：

1. 与 [@BotFather](https://t.me/BotFather) 创建Bot获得Token
2. 与 [@userinfobot](https://t.me/userinfobot) 获得用户ID  
3. 配置 `.env` 文件或使用命令行参数
4. 使用 `--upload` 参数自动上传
5. 获得 `t.me/addstickers/xxx` 分享链接

### 📋 手动导入

通过 [@stickers](https://t.me/stickers) 机器人导入：

1. 打开Telegram，搜索 `@stickers`
2. 发送 `/newpack` 创建新表情包
3. 上传生成的文件并设置emoji
4. 完成后获得分享链接

## 🔧 技术要求

### 必需依赖
- **Python 3.7+**: 核心运行环境
- **Pillow**: 图像处理

### 可选依赖
- **FFmpeg**: WebM视频转换 (强烈推荐)
  - 不安装仅支持静态表情包
  - 安装后支持动画表情包

### 系统要求
- Windows 10+, macOS 10.14+, 或现代Linux发行版
- 512MB+ 可用内存
- 100MB+ 可用存储空间

## 📚 完整文档

- 📖 [完整使用手册](APP_README.md) - 详细功能说明和高级用法
- 🛠️ [安装指南](INSTALL.md) - 多平台安装说明和故障排除
- 🔧 [开发说明](CLAUDE.md) - 项目架构和开发信息

## 🎯 项目架构

```
🎯 Telegram Sticker Maker
├── 🛠️ 核心引擎
│   ├── telegram_sticker_maker.py   # 统一制作器
│   └── telegram_webm_converter.py  # WebM转换器  
├── ⚙️ 安装脚本
│   ├── install_windows.bat     # Windows安装
│   ├── install_macos.sh       # macOS安装
│   ├── install_linux.sh       # Linux安装
│   └── install.py             # 通用Python安装
└── 📖 文档和配置
    ├── APP_README.md          # 完整使用手册
    ├── INSTALL.md             # 安装指南
    └── requirements.txt       # Python依赖
```

## 🏆 优势对比

| 特性 | 本工具 | 在线转换器 | FFmpeg直接 |
|------|-------|------------|------------|
| **易用性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **转换质量** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **文件大小控制** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **批量处理** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ |
| **隐私安全** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **离线使用** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

- 🐛 [报告问题](../../issues)
- 💡 [功能建议](../../discussions) 
- 🔧 [提交代码](../../pulls)

## 📄 许可证

本项目采用开源许可证，详见 [LICENSE](LICENSE) 文件。

---

**🎉 开始制作你的专属Telegram表情包吧！**

> 💡 提示: 首次使用建议先阅读 [完整使用手册](APP_README.md) 了解所有功能。