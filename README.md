# 🎯 Telegram Sticker Maker

专业的Telegram表情包制作和导入工具，支持将任何媒体文件转换为符合Telegram官方要求的表情包格式。

## 🚀 快速开始

### 方式一：Web界面 (推荐)
```bash
python main.py --web
# 或者
python start_web.py
```

### 方式二：命令行
```bash
python main.py input.gif output.tgs
```

### 方式三：一键安装
```bash
# 根据您的系统选择：
python deployment/scripts/install.py              # 通用Python安装
./deployment/scripts/install_linux.sh             # Linux
./deployment/scripts/install_macos.sh             # macOS  
./deployment/scripts/install_windows.bat          # Windows
```

## 📚 详细文档

- **[完整使用手册](docs/guides/APP_README.md)** - 详细功能说明和高级用法
- **[安装指南](docs/guides/INSTALL.md)** - 多平台安装说明和故障排除  
- **[部署说明](docs/guides/DEPLOY.md)** - 云平台部署配置
- **[开发指南](docs/guides/CLAUDE.md)** - 项目架构和开发信息

## 🏗️ 项目结构

```
telegram_sticker_maker/
├── 📦 core/                      # 核心功能模块
│   ├── sticker_maker.py          # 主制作器
│   ├── api_uploader.py           # API上传
│   ├── sticker_manager.py        # 表情包管理
│   └── webm_converter.py         # WebM转换
├── 📱 web/                       # Web界面  
│   ├── server.py                 # Flask服务器
│   ├── app.py                    # 启动器
│   ├── templates/                # HTML模板
│   └── static/                   # 静态资源
├── 🚀 deployment/                # 部署资源
│   ├── cloud/                    # 云平台配置
│   ├── docker/                   # Docker配置
│   └── scripts/                  # 安装脚本
├── 📚 docs/                      # 文档
├── 📁 data/                      # 数据目录
│   ├── uploads/                  # 上传文件
│   └── stickers/                 # 示例文件
├── main.py                       # 主入口点
├── start_web.py                  # Web启动入口(兼容)
└── requirements.txt              # Python依赖
```

## ✨ 主要特性

- **🖼️ 多格式支持**: GIF, PNG, WEBP, MP4, WebM → PNG/WebM表情包
- **🎨 智能转换**: 自动选择最佳输出格式 (静态PNG或动画WebM)
- **💻 Web界面**: 完整的图形界面，支持批量处理
- **🌍 跨平台**: Windows, macOS, Linux 全平台支持
- **🎯 官方兼容**: 完全符合Telegram 7.8+ 导入API要求

## 📄 许可证

本项目采用开源许可证，详见 [LICENSE](LICENSE) 文件。

---

**🎉 开始制作你的专属Telegram表情包吧！**