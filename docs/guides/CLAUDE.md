# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram Sticker Maker is a comprehensive Python tool for creating, converting, and managing Telegram stickers. It supports multiple input formats (GIF, PNG, WEBP, MP4, WebM) and automatically chooses the optimal output format (PNG for static, WebM for animated) while adhering to Telegram's size and format requirements.

## Core Commands

### Development Setup
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Cross-platform installation script
python3 install.py

# Platform-specific install scripts
./install_windows.bat    # Windows
./install_macos.sh       # macOS
./install_linux.sh      # Linux
```

### Basic Usage
```bash
# Convert single file (auto-format selection)
python3 telegram_sticker_maker.py input.gif

# Batch convert folder
python3 telegram_sticker_maker.py ./images/ --pack-name MyStickers

# Force WebM format for animations
python3 telegram_sticker_maker.py video.mp4 --format webm --emoji 🎬

# Auto-upload to Telegram (requires bot config)
python3 telegram_sticker_maker.py input.gif --upload

# Start web interface
python3 web_server.py
```

### WebM Conversion Only
```bash
# Direct WebM conversion with specific parameters
python3 telegram_webm_converter.py input.gif output.webm --type sticker
```

## Architecture

The project uses a modular architecture with specialized components:

### Core Modules

1. **telegram_sticker_maker.py**: Main unified sticker creation tool
   - Auto-detects input format and selects optimal output
   - Handles both static (PNG/WebP) and animated (WebM) conversion
   - Integrates with Telegram API for automatic upload
   - Uses `StickerConfig` dataclass for configuration management

2. **telegram_webm_converter.py**: Specialized WebM converter  
   - Converts animations to Telegram-compatible WebM format
   - Handles VP9 encoding with size optimization
   - Supports both sticker (512px) and emoji (100px) modes
   - Uses `TelegramWebMConfig` for encoding parameters

3. **telegram_api_uploader.py**: Telegram Bot API integration
   - Creates sticker sets via Telegram Bot API
   - Handles file uploads and metadata management
   - Supports proxy configuration and error handling
   - Returns shareable sticker pack links

4. **telegram_sticker_manager.py**: Sticker pack management
   - CRUD operations for existing sticker packs
   - Bulk operations and pack organization
   - Integration with uploader for seamless workflow

5. **web_server.py**: Flask-based web interface
   - File upload and conversion through browser
   - Real-time progress tracking with WebSocket-like updates
   - Configuration management (.env editing)
   - Batch processing and pack management UI

### Installation and Setup

- **install.py**: Cross-platform Python installer with dependency detection
- **install_*.sh/.bat**: Platform-specific shell scripts for automated setup
- **start_web.py**: Web server entry point for cloud deployments

## Technical Requirements

### Python Dependencies (requirements.txt)
- **Pillow>=10.0.0**: Core image processing
- **Flask==3.0.0**: Web interface
- **requests>=2.31.0**: API communication  
- **python-dotenv>=1.0.0**: Configuration management

### External Dependencies
- **FFmpeg**: Required for WebM video conversion (strongly recommended)
- **gifsicle**: Optional GIF optimization tool

### Format Specifications
- **Static stickers**: PNG/WebP, ≤512KB, 512px on one side
- **Animated stickers**: WebM VP9, ≤256KB, ≤3 seconds, ≤30 FPS
- **Size constraints**: Max 512x512px, one dimension must be 512px

## Configuration

### Environment Variables (.env)
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_USER_ID=your_user_id
PROXY_HOST=optional_proxy_host
PROXY_PORT=optional_proxy_port
```

### Key Configuration Classes
- `StickerConfig`: Main sticker creation parameters
- `TelegramWebMConfig`: WebM encoding settings
- Platform detection in `install.py` for dependency management

## Cloud Deployment

The project includes configurations for multiple cloud platforms:
- **Vercel**: `vercel.json` for serverless deployment
- **Railway**: `railway.json` with Nixpacks support  
- **Render**: `render.yaml` for container deployment
- **Docker**: `Dockerfile` for containerized deployment