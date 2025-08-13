#!/usr/bin/env python3
"""
Telegram Sticker Maker - 统一表情包制作和导入工具

自动选择最佳格式并导入到Telegram:
- 静态图片 → PNG/WebP (≤512KB)
- 动画/视频 → WebM (≤256KB)

支持Telegram 7.8+导入API
"""

import os
import sys
import json
import time
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from PIL import Image, ImageSequence
import urllib.parse
import webbrowser

@dataclass
class StickerConfig:
    """表情包配置"""
    # 输入信息
    input_path: str = ""
    output_dir: str = "output"
    
    # 表情包元数据
    pack_name: str = "MyCustomStickers"
    emojis: List[str] = None
    
    # 格式限制
    static_max_size_kb: int = 512
    webm_max_size_kb: int = 256
    
    # 尺寸要求
    max_dimension: int = 512
    
    # 自动选择策略
    auto_format: bool = True
    preferred_format: str = "auto"  # "auto", "static", "webm"
    
    # Telegram API 自动上传
    auto_upload: bool = False
    bot_token: str = ""
    user_id: int = 0
    
    def __post_init__(self):
        if self.emojis is None:
            self.emojis = ["😀"]  # 默认emoji


def load_env_file(env_path: str = ".env") -> Dict[str, str]:
    """加载 .env 文件"""
    env_vars = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"⚠️ 读取 .env 文件失败: {e}")
    return env_vars


class TelegramStickerMaker:
    """Telegram表情包制作器"""
    
    def __init__(self, config: StickerConfig = None):
        self.config = config or StickerConfig()
        self.logger = self._setup_logger()
        self.temp_dir = tempfile.mkdtemp()
        
        # 导入WebM转换器
        self._load_webm_converter()
        
        # 导入Telegram API上传器
        self._load_telegram_uploader()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _load_webm_converter(self):
        """加载WebM转换器"""
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            from telegram_webm_converter import TelegramWebMConverter, TelegramWebMConfig
            self.webm_converter = TelegramWebMConverter
            self.webm_config = TelegramWebMConfig
            self.logger.info("✓ WebM converter loaded")
        except Exception as e:
            self.logger.error(f"Failed to load WebM converter: {e}")
            raise
    
    def _load_telegram_uploader(self):
        """加载Telegram API上传器"""
        try:
            from telegram_api_uploader import TelegramStickerUploader
            self.telegram_uploader_class = TelegramStickerUploader
            self.logger.info("✓ Telegram API uploader loaded")
        except Exception as e:
            self.logger.warning(f"Telegram API uploader not available: {e}")
            self.telegram_uploader_class = None
    
    def analyze_input(self, input_path: str) -> Dict[str, Any]:
        """分析输入文件特征"""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        file_size = os.path.getsize(input_path)
        file_ext = Path(input_path).suffix.lower()
        
        analysis = {
            'path': input_path,
            'size_bytes': file_size,
            'size_kb': file_size / 1024,
            'extension': file_ext,
            'is_animated': False,
            'is_video': False,
            'dimensions': (0, 0),
            'frame_count': 1,
            'duration': 0.0,
            'complexity_score': 0,
            'recommended_format': 'static'
        }
        
        try:
            if file_ext in ['.gif', '.webp', '.png', '.jpg', '.jpeg']:
                # 图片文件分析
                with Image.open(input_path) as img:
                    analysis['dimensions'] = img.size
                    analysis['is_animated'] = getattr(img, 'is_animated', False)
                    
                    if analysis['is_animated']:
                        analysis['frame_count'] = getattr(img, 'n_frames', 1)
                        
                        # 计算总时长
                        durations = []
                        for frame in ImageSequence.Iterator(img):
                            duration = frame.info.get('duration', 100)
                            durations.append(duration)
                        
                        analysis['duration'] = sum(durations) / 1000.0  # 转换为秒
                        
                        # 复杂度评分（基于帧数、尺寸、时长）
                        complexity = (
                            analysis['frame_count'] * 0.1 +
                            (analysis['dimensions'][0] * analysis['dimensions'][1]) / 10000 +
                            analysis['duration'] * 2
                        )
                        analysis['complexity_score'] = complexity
            
            elif file_ext in ['.mp4', '.avi', '.mov', '.webm']:
                # 视频文件分析
                analysis['is_video'] = True
                analysis['is_animated'] = True
                
                # 使用ffprobe分析视频
                try:
                    cmd = [
                        'ffprobe', '-v', 'quiet', '-print_format', 'json',
                        '-show_format', '-show_streams', input_path
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        data = json.loads(result.stdout)
                        
                        video_stream = next(
                            (s for s in data['streams'] if s['codec_type'] == 'video'),
                            None
                        )
                        
                        if video_stream:
                            analysis['dimensions'] = (
                                video_stream.get('width', 0),
                                video_stream.get('height', 0)
                            )
                        
                        if 'format' in data:
                            analysis['duration'] = float(data['format'].get('duration', 0))
                        
                        # 视频复杂度更高
                        analysis['complexity_score'] = 50 + analysis['duration'] * 10
                
                except Exception as e:
                    self.logger.warning(f"Video analysis failed: {e}")
        
        except Exception as e:
            self.logger.warning(f"File analysis failed: {e}")
        
        # 推荐格式
        analysis['recommended_format'] = self._recommend_format(analysis)
        
        return analysis
    
    def _recommend_format(self, analysis: Dict[str, Any]) -> str:
        """根据分析结果推荐最佳格式"""
        if not analysis['is_animated']:
            return 'static'
        else:
            # 所有动画都使用WebM
            return 'webm'
    
    def create_static_sticker(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """创建静态PNG表情包"""
        result = {
            'success': False,
            'format': 'static',
            'output_path': output_path,
            'file_size': 0,
            'message': ''
        }
        
        try:
            with Image.open(input_path) as img:
                # 转换为RGBA（支持透明）
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 计算缩放尺寸
                width, height = img.size
                if width > self.config.max_dimension or height > self.config.max_dimension:
                    # 需要缩放
                    if width >= height:
                        new_width = self.config.max_dimension
                        new_height = int(height * (self.config.max_dimension / width))
                    else:
                        new_height = self.config.max_dimension
                        new_width = int(width * (self.config.max_dimension / height))
                    
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 确保输出目录存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 保存为PNG
                img.save(output_path, 'PNG', optimize=True)
                
                file_size = os.path.getsize(output_path)
                
                # 检查大小限制
                max_size = self.config.static_max_size_kb * 1024
                if file_size > max_size:
                    # 尝试压缩
                    quality = 95
                    while file_size > max_size and quality > 10:
                        # 转换为WebP格式压缩
                        webp_path = output_path.replace('.png', '.webp')
                        img.save(webp_path, 'WEBP', quality=quality, method=6)
                        
                        file_size = os.path.getsize(webp_path)
                        if file_size <= max_size:
                            os.remove(output_path)
                            os.rename(webp_path, output_path.replace('.png', '.webp'))
                            result['output_path'] = output_path.replace('.png', '.webp')
                            break
                        
                        quality -= 10
                        if os.path.exists(webp_path):
                            os.remove(webp_path)
                
                result['file_size'] = os.path.getsize(result['output_path'])
                result['success'] = result['file_size'] <= max_size
                result['message'] = f"Static sticker created: {result['file_size']/1024:.1f}KB"
                
        except Exception as e:
            result['message'] = f"Failed to create static sticker: {e}"
            self.logger.error(result['message'])
        
        return result
    
    
    def create_webm_sticker(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """创建WebM视频表情包"""
        result = {
            'success': False,
            'format': 'webm',
            'output_path': output_path,
            'file_size': 0,
            'message': ''
        }
        
        try:
            # 使用WebM转换器
            webm_config = self.webm_config(
                output_type="sticker",
                max_file_size_kb=self.config.webm_max_size_kb
            )
            converter = self.webm_converter(webm_config)
            
            conversion_result = converter.convert_gif_to_webm(input_path, output_path)
            
            result['success'] = conversion_result['success']
            result['file_size'] = conversion_result.get('file_size_after', 0)
            result['message'] = conversion_result['message']
            
        except Exception as e:
            result['message'] = f"Failed to create WebM sticker: {e}"
            self.logger.error(result['message'])
        
        return result
    
    def create_sticker_pack(self, input_files: List[str], pack_name: str = None) -> Dict[str, Any]:
        """创建完整的表情包"""
        pack_name = pack_name or self.config.pack_name
        output_dir = os.path.join(self.config.output_dir, pack_name)
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            'pack_name': pack_name,
            'output_dir': output_dir,
            'stickers': [],
            'total_files': len(input_files),
            'successful': 0,
            'failed': 0
        }
        
        for i, input_file in enumerate(input_files):
            self.logger.info(f"Processing {i+1}/{len(input_files)}: {input_file}")
            
            # 分析输入文件
            try:
                analysis = self.analyze_input(input_file)
                self.logger.info(f"Recommended format: {analysis['recommended_format']}")
                
                # 选择格式
                format_choice = analysis['recommended_format']
                if not self.config.auto_format:
                    format_choice = self.config.preferred_format
                
                # 生成输出文件名
                base_name = Path(input_file).stem
                
                sticker_result = None
                
                if format_choice == 'static':
                    output_path = os.path.join(output_dir, f"{base_name}.png")
                    sticker_result = self.create_static_sticker(input_file, output_path)
                elif format_choice == 'webm':
                    output_path = os.path.join(output_dir, f"{base_name}.webm")
                    sticker_result = self.create_webm_sticker(input_file, output_path)
                
                if sticker_result and sticker_result['success']:
                    results['successful'] += 1
                    sticker_result['input_file'] = input_file
                    sticker_result['analysis'] = analysis
                    results['stickers'].append(sticker_result)
                else:
                    results['failed'] += 1
                    self.logger.error(f"Failed to process {input_file}")
                    
            except Exception as e:
                results['failed'] += 1
                self.logger.error(f"Error processing {input_file}: {e}")
        
        # 生成表情包元数据
        self._generate_pack_metadata(results)
        
        return results
    
    def _generate_pack_metadata(self, results: Dict[str, Any]):
        """生成表情包元数据"""
        metadata = {
            'pack_name': results['pack_name'],
            'created_at': time.time(),
            'total_stickers': results['successful'],
            'formats_used': {},
            'stickers': []
        }
        
        for sticker in results['stickers']:
            fmt = sticker['format']
            if fmt not in metadata['formats_used']:
                metadata['formats_used'][fmt] = 0
            metadata['formats_used'][fmt] += 1
            
            metadata['stickers'].append({
                'file': os.path.basename(sticker['output_path']),
                'format': fmt,
                'size_kb': sticker['file_size'] / 1024,
                'emoji': self.config.emojis[0] if self.config.emojis else "😀"
            })
        
        # 保存元数据
        metadata_path = os.path.join(results['output_dir'], 'pack_info.json')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Pack metadata saved to {metadata_path}")
    
    def upload_to_telegram(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """自动上传表情包到Telegram"""
        upload_result = {
            'success': False,
            'pack_url': '',
            'message': '',
            'uploaded_count': 0,
            'failed_count': 0
        }
        
        if not self.config.auto_upload:
            upload_result['message'] = 'Auto upload disabled'
            return upload_result
        
        if not self.telegram_uploader_class:
            upload_result['message'] = 'Telegram API uploader not available'
            return upload_result
        
        if not self.config.bot_token:
            upload_result['message'] = 'Bot token not provided'
            return upload_result
        
        if not self.config.user_id:
            upload_result['message'] = 'User ID not provided'
            return upload_result
        
        if not results['stickers']:
            upload_result['message'] = 'No stickers to upload'
            return upload_result
        
        try:
            # 创建上传器实例
            uploader = self.telegram_uploader_class(self.config.bot_token)
            
            # 收集表情包文件
            sticker_files = [sticker['output_path'] for sticker in results['stickers']]
            emojis = [self.config.emojis[0] if self.config.emojis else "😀"] * len(sticker_files)
            
            # 生成表情包名称
            pack_name = uploader.generate_pack_name(results['pack_name'], self.config.user_id)
            pack_title = f"{results['pack_name']} Stickers"
            
            self.logger.info(f"🚀 Uploading sticker pack to Telegram...")
            
            # 上传表情包
            api_result = uploader.upload_sticker_pack(
                user_id=self.config.user_id,
                pack_name=pack_name,
                pack_title=pack_title,
                sticker_files=sticker_files,
                emojis=emojis
            )
            
            upload_result['success'] = api_result['success']
            upload_result['pack_url'] = api_result['pack_url']
            upload_result['uploaded_count'] = api_result['uploaded_count']
            upload_result['failed_count'] = api_result['failed_count']
            
            if api_result['success']:
                upload_result['message'] = f"Successfully uploaded {api_result['uploaded_count']} stickers"
            else:
                upload_result['message'] = f"Upload failed: {'; '.join(api_result['errors'])}"
            
        except Exception as e:
            upload_result['message'] = f"Upload error: {e}"
            self.logger.error(f"Upload error: {e}")
        
        return upload_result
    
    def generate_telegram_import_url(self, pack_dir: str) -> str:
        """生成Telegram导入URL"""
        # 这里应该实现真正的Telegram导入API集成
        # 目前生成一个指向@stickers机器人的URL
        
        pack_name = os.path.basename(pack_dir)
        encoded_name = urllib.parse.quote(pack_name)
        
        # Telegram导入URL格式（这是一个简化的实现）
        base_url = "https://t.me/stickers"
        import_url = f"{base_url}?start=import_{encoded_name}"
        
        return import_url
    
    def open_telegram_import(self, pack_dir: str):
        """打开Telegram导入页面"""
        import_url = self.generate_telegram_import_url(pack_dir)
        
        print(f"\n🎯 Telegram导入链接:")
        print(f"📱 {import_url}")
        print(f"\n📋 使用说明:")
        print(f"1. 点击上方链接打开Telegram")
        print(f"2. 与 @stickers 机器人对话")
        print(f"3. 使用 /newpack 命令创建新表情包")
        print(f"4. 上传 {pack_dir} 目录中的文件")
        
        # 尝试自动打开浏览器
        try:
            webbrowser.open(import_url)
        except:
            pass


def show_help():
    """显示帮助信息"""
    print("🎯 Telegram Sticker Maker")
    print("统一表情包制作和导入工具")
    print()
    print("用法:")
    print("  python telegram_sticker_maker.py <input_file_or_directory> [options]")
    print()
    print("选项:")
    print("  --pack-name NAME     表情包名称 (默认: MyCustomStickers)")
    print("  --format FORMAT      强制格式: static/webm/auto (默认: auto)")
    print("  --emoji EMOJI        默认emoji (默认: 😀)")
    print("  --output-dir DIR     输出目录 (默认: output)")
    print("  --open-telegram      完成后打开Telegram导入")
    print("  --upload             自动上传到Telegram (需要Bot Token)")
    print("  --bot-token TOKEN    Telegram Bot Token")
    print("  --user-id ID         Telegram 用户ID")
    print("  --help, -h           显示此帮助信息")
    print()
    print("支持格式:")
    print("  📥 输入: GIF, PNG, WEBP, MP4, WebM")
    print("  📤 输出: PNG/WebP (静态), WebM (动画/视频)")
    print()
    print("示例:")
    print("  python telegram_sticker_maker.py my_image.gif")
    print("  python telegram_sticker_maker.py ./images/ --pack-name MyPack")
    print("  python telegram_sticker_maker.py dance.gif --format webm --emoji 🎬")
    print("  python telegram_sticker_maker.py ./stickers/ --upload --bot-token TOKEN --user-id 123456")
    print()
    print("Telegram自动上传:")
    print("  1. 与@BotFather创建Bot获得Token")
    print("  2. 获取你的Telegram用户ID")
    print("  3. 创建.env文件配置或使用命令行参数")
    print("  4. 使用--upload选项自动上传表情包")
    print("  5. 获得t.me/addstickers/xxx分享链接")
    print()
    print(".env文件配置:")
    print("  复制 .env.example 为 .env 并填写配置")
    print("  TELEGRAM_BOT_TOKEN=你的Bot Token")
    print("  TELEGRAM_USER_ID=你的用户ID")

def main():
    """主函数"""
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h']:
        show_help()
        sys.exit(0)
    
    # 解析参数
    input_path = sys.argv[1]
    
    config = StickerConfig()
    open_telegram = False
    
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--pack-name' and i + 1 < len(args):
            config.pack_name = args[i + 1]
            i += 2
        elif args[i] == '--format' and i + 1 < len(args):
            fmt = args[i + 1]
            if fmt in ['static', 'webm', 'auto']:
                config.preferred_format = fmt
                config.auto_format = (fmt == 'auto')
            else:
                print(f"❌ 无效格式: {fmt}，支持: static, webm, auto")
                sys.exit(1)
            i += 2
        elif args[i] == '--emoji' and i + 1 < len(args):
            config.emojis = [args[i + 1]]
            i += 2
        elif args[i] == '--output-dir' and i + 1 < len(args):
            config.output_dir = args[i + 1]
            i += 2
        elif args[i] == '--open-telegram':
            open_telegram = True
            i += 1
        elif args[i] == '--upload':
            config.auto_upload = True
            i += 1
        elif args[i] == '--bot-token' and i + 1 < len(args):
            config.bot_token = args[i + 1]
            config.auto_upload = True  # 自动启用上传
            i += 2
        elif args[i] == '--user-id' and i + 1 < len(args):
            try:
                config.user_id = int(args[i + 1])
            except ValueError:
                print(f"❌ 无效的用户ID: {args[i + 1]}")
                sys.exit(1)
            i += 2
        else:
            i += 1
    
    # 加载 .env 文件配置
    env_vars = load_env_file()
    
    # 处理Telegram上传配置
    if config.auto_upload:
        # 从 .env 文件或环境变量获取 Bot Token
        if not config.bot_token:
            config.bot_token = (
                env_vars.get('TELEGRAM_BOT_TOKEN', '') or 
                os.getenv('TELEGRAM_BOT_TOKEN', '')
            )
        
        # 从 .env 文件或环境变量获取用户ID
        if not config.user_id:
            user_id_str = (
                env_vars.get('TELEGRAM_USER_ID', '') or 
                os.getenv('TELEGRAM_USER_ID', '')
            )
            if user_id_str:
                try:
                    config.user_id = int(user_id_str)
                except ValueError:
                    print(f"❌ .env 文件中的用户ID格式错误: {user_id_str}")
                    sys.exit(1)
        
        # 应用 .env 文件中的其他配置
        if not config.pack_name or config.pack_name == "MyCustomStickers":
            pack_prefix = env_vars.get('PACK_NAME_PREFIX', '')
            if pack_prefix:
                config.pack_name = pack_prefix
        
        if not config.emojis or config.emojis == ["😀"]:
            default_emoji = env_vars.get('DEFAULT_EMOJI', '')
            if default_emoji:
                config.emojis = [default_emoji]
        
        # 验证上传参数
        if not config.bot_token:
            print("❌ 自动上传需要Bot Token")
            print("💡 方式1: 使用 --bot-token TOKEN 参数")
            print("💡 方式2: 在 .env 文件中设置 TELEGRAM_BOT_TOKEN=your_token")
            print("💡 方式3: 设置环境变量 TELEGRAM_BOT_TOKEN")
            print("📝 获取Token: 与@BotFather对话创建Bot")
            sys.exit(1)
        
        if not config.user_id:
            print("❌ 自动上传需要用户ID")
            print("💡 方式1: 使用 --user-id ID 参数")
            print("💡 方式2: 在 .env 文件中设置 TELEGRAM_USER_ID=your_id")
            print("💡 方式3: 设置环境变量 TELEGRAM_USER_ID")
            print("📝 获取用户ID: 与@userinfobot对话获取你的Telegram ID")
            sys.exit(1)
    
    # 创建制作器
    maker = TelegramStickerMaker(config)
    
    # 收集输入文件
    input_files = []
    if os.path.isfile(input_path):
        input_files = [input_path]
    elif os.path.isdir(input_path):
        for ext in ['*.gif', '*.png', '*.webp', '*.jpg', '*.jpeg', '*.mp4', '*.webm']:
            import glob
            input_files.extend(glob.glob(os.path.join(input_path, ext)))
            input_files.extend(glob.glob(os.path.join(input_path, ext.upper())))
    
    if not input_files:
        print(f"❌ 未找到支持的文件: {input_path}")
        sys.exit(1)
    
    print(f"🎯 Telegram表情包制作器")
    print(f"📥 输入文件: {len(input_files)} 个")
    print(f"📦 表情包名称: {config.pack_name}")
    print(f"🎨 格式策略: {config.preferred_format if not config.auto_format else 'auto'}")
    if config.auto_upload:
        print(f"🚀 自动上传: 启用 (用户ID: {config.user_id})")
    print()
    
    # 创建表情包
    results = maker.create_sticker_pack(input_files, config.pack_name)
    
    # 自动上传到Telegram
    upload_result = None
    if config.auto_upload and results['successful'] > 0:
        upload_result = maker.upload_to_telegram(results)
    
    # 显示结果
    print("\n" + "="*50)
    print("📊 制作结果")
    print("="*50)
    print(f"✅ 成功: {results['successful']} 个")
    print(f"❌ 失败: {results['failed']} 个")
    print(f"📁 输出目录: {results['output_dir']}")
    
    if results['successful'] > 0:
        print(f"\n📋 生成的表情包:")
        format_counts = {}
        for sticker in results['stickers']:
            fmt = sticker['format']
            if fmt not in format_counts:
                format_counts[fmt] = 0
            format_counts[fmt] += 1
            
            file_name = os.path.basename(sticker['output_path'])
            file_size = sticker['file_size'] / 1024
            print(f"  {fmt.upper()}: {file_name} ({file_size:.1f}KB)")
        
        print(f"\n📈 格式统计:")
        for fmt, count in format_counts.items():
            print(f"  {fmt.upper()}: {count} 个")
        
        # 显示上传结果
        if upload_result:
            print(f"\n🚀 Telegram上传结果:")
            if upload_result['success']:
                print(f"✅ 上传成功！")
                print(f"📱 分享链接: {upload_result['pack_url']}")
                print(f"📊 上传: {upload_result['uploaded_count']} 个，失败: {upload_result['failed_count']} 个")
            else:
                print(f"❌ 上传失败: {upload_result['message']}")
        
        # 打开Telegram导入
        if open_telegram and not upload_result:
            maker.open_telegram_import(results['output_dir'])
    
    print(f"\n🎉 表情包制作完成！")
    if upload_result and upload_result['success']:
        print(f"🎉 已自动上传到Telegram！")
        print(f"📱 立即分享: {upload_result['pack_url']}")
    else:
        print(f"📱 手动导入: 打开Telegram → @stickers → /newpack")


if __name__ == '__main__':
    main()