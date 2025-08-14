#!/usr/bin/env python3
"""
Telegram WebM Sticker/Emoji Converter
专门为Telegram表情包和贴纸设计的GIF到WebM转换器

符合Telegram要求:
- WebM格式 + VP9编码
- Stickers: 512px一边，另一边≤512px  
- Emoji: 100x100px
- ≤3秒时长，≤30FPS，≤256KB文件大小
- 循环播放，无音频
"""

import os
import sys
import time
import logging
import subprocess
from typing import Tuple, Dict, Any
from dataclasses import dataclass
from PIL import Image, ImageSequence

@dataclass
class TelegramWebMConfig:
    """Telegram WebM配置"""
    # 输出类型
    output_type: str = "sticker"  # "sticker" 或 "emoji"
    
    # 尺寸约束
    max_width: int = 512
    max_height: int = 512
    emoji_size: Tuple[int, int] = (100, 100)
    
    # 性能约束
    max_duration: float = 3.0  # 秒
    max_fps: int = 30
    max_file_size_kb: int = 256
    
    # 编码参数
    video_codec: str = "libvpx-vp9"
    crf: int = 30  # 质量参数，越低质量越好
    speed: int = 4  # 编码速度，0-8，越高速度越快但质量略差
    
    def get_target_size(self) -> Tuple[int, int]:
        """获取目标尺寸"""
        if self.output_type == "emoji":
            return self.emoji_size
        return (self.max_width, self.max_height)


class TelegramWebMConverter:
    """Telegram WebM转换器"""
    
    def __init__(self, config: TelegramWebMConfig = None):
        self.config = config or TelegramWebMConfig()
        self.logger = self._setup_logger()
        self._validate_ffmpeg()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _validate_ffmpeg(self):
        """验证ffmpeg可用性"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("FFmpeg not found or not working")
            self.logger.info("✓ FFmpeg available")
        except FileNotFoundError:
            if os.name == 'nt':  # Windows
                raise RuntimeError("FFmpeg not installed. Run install_windows.bat or install from https://ffmpeg.org")
            else:  # Linux/macOS
                raise RuntimeError("FFmpeg not installed. Please install: sudo apt install ffmpeg")
    
    def analyze_gif(self, gif_path: str) -> Dict[str, Any]:
        """分析GIF属性"""
        with Image.open(gif_path) as img:
            info = {
                'path': gif_path,
                'size': img.size,
                'is_animated': getattr(img, 'is_animated', False),
                'n_frames': getattr(img, 'n_frames', 1),
                'duration': 0,
                'fps': 0
            }
            
            if info['is_animated']:
                # 计算总时长和平均FPS
                durations = []
                for frame in ImageSequence.Iterator(img):
                    duration = frame.info.get('duration', 100)  # 毫秒
                    durations.append(duration)
                
                total_duration_ms = sum(durations)
                info['duration'] = total_duration_ms / 1000.0  # 转换为秒
                info['fps'] = info['n_frames'] / info['duration'] if info['duration'] > 0 else 10
                info['avg_frame_duration'] = total_duration_ms / info['n_frames']
            
            return info
    
    def calculate_optimal_params(self, gif_info: Dict[str, Any]) -> Dict[str, Any]:
        """计算最优转换参数"""
        target_width, target_height = self.config.get_target_size()
        original_width, original_height = gif_info['size']
        
        # 计算缩放比例
        if self.config.output_type == "emoji":
            # Emoji必须是100x100
            scale_ratio = min(target_width / original_width, target_height / original_height)
            output_width, output_height = target_width, target_height
        else:
            # Sticker: 一边是512px，另一边≤512px
            if original_width >= original_height:
                scale_ratio = target_width / original_width
                output_width = target_width
                output_height = int(original_height * scale_ratio)
            else:
                scale_ratio = target_height / original_height
                output_height = target_height
                output_width = int(original_width * scale_ratio)
        
        # 时长和帧率限制
        duration = min(gif_info['duration'], self.config.max_duration)
        fps = min(gif_info['fps'], self.config.max_fps)
        
        # 如果原时长超过3秒，需要加速播放
        speed_factor = gif_info['duration'] / self.config.max_duration if gif_info['duration'] > self.config.max_duration else 1.0
        
        return {
            'output_width': output_width,
            'output_height': output_height,
            'scale_ratio': scale_ratio,
            'duration': duration,
            'fps': fps,
            'speed_factor': speed_factor,
            'needs_speed_adjustment': speed_factor > 1.0
        }
    
    def convert_with_ffmpeg(self, input_path: str, output_path: str, params: Dict[str, Any]) -> bool:
        """使用FFmpeg进行转换"""
        try:
            # 构建FFmpeg命令
            cmd = [
                'ffmpeg', '-y',  # 覆盖输出文件
                '-i', input_path,
                '-c:v', self.config.video_codec,
                '-crf', str(self.config.crf),
                '-speed', str(self.config.speed),
                '-vf', self._build_video_filter(params),
                '-r', str(params['fps']),
                '-t', str(params['duration']),
                '-an',  # 无音频
                '-f', 'webm',
                output_path
            ]
            
            self.logger.info(f"Running FFmpeg: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.logger.error(f"FFmpeg error: {result.stderr}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Conversion failed: {e}")
            return False
    
    def _build_video_filter(self, params: Dict[str, Any]) -> str:
        """构建视频滤镜字符串"""
        filters = []
        
        # 缩放滤镜
        if self.config.output_type == "emoji":
            # Emoji需要精确的100x100尺寸
            filters.append(f"scale=100:100:force_original_aspect_ratio=decrease")
            filters.append("pad=100:100:(ow-iw)/2:(oh-ih)/2:color=black@0")  # 透明填充
        else:
            # Sticker缩放
            filters.append(f"scale={params['output_width']}:{params['output_height']}")
        
        # 速度调整（如果需要）
        if params['needs_speed_adjustment']:
            filters.append(f"setpts={1/params['speed_factor']}*PTS")
        
        return ','.join(filters)
    
    def optimize_file_size(self, input_path: str, output_path: str, params: Dict[str, Any]) -> bool:
        """优化文件大小以满足256KB限制"""
        max_size_bytes = self.config.max_file_size_kb * 1024
        
        # 质量级别列表（CRF值）
        quality_levels = [30, 35, 40, 45, 50, 55, 60]
        
        for crf in quality_levels:
            temp_config = TelegramWebMConfig(
                output_type=self.config.output_type,
                crf=crf,
                speed=self.config.speed
            )
            temp_converter = TelegramWebMConverter(temp_config)
            
            temp_output = output_path + f".tmp_crf{crf}"
            
            if temp_converter.convert_with_ffmpeg(input_path, temp_output, params):
                file_size = os.path.getsize(temp_output)
                self.logger.info(f"CRF {crf}: {file_size} bytes ({file_size/1024:.1f} KB)")
                
                if file_size <= max_size_bytes:
                    # 找到合适的质量级别
                    os.rename(temp_output, output_path)
                    
                    # 清理其他临时文件
                    for other_crf in quality_levels:
                        temp_file = output_path + f".tmp_crf{other_crf}"
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                    
                    self.logger.info(f"✓ Optimized to {file_size} bytes with CRF {crf}")
                    return True
            
            # 如果转换失败，删除临时文件
            if os.path.exists(temp_output):
                os.remove(temp_output)
        
        self.logger.warning("Could not achieve target file size with acceptable quality")
        return False
    
    def convert_gif_to_webm(self, gif_path: str, output_path: str) -> Dict[str, Any]:
        """主转换函数"""
        result = {
            'success': False,
            'input_path': gif_path,
            'output_path': output_path,
            'message': '',
            'file_size_before': 0,
            'file_size_after': 0,
            'processing_time': 0
        }
        
        start_time = time.time()
        
        try:
            # 检查输入文件
            if not os.path.exists(gif_path):
                result['message'] = f"Input file not found: {gif_path}"
                return result
            
            result['file_size_before'] = os.path.getsize(gif_path)
            
            # 分析GIF
            gif_info = self.analyze_gif(gif_path)
            self.logger.info(f"GIF Info: {gif_info}")
            
            # 计算转换参数
            params = self.calculate_optimal_params(gif_info)
            self.logger.info(f"Conversion params: {params}")
            
            # 创建输出目录
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # 转换并优化文件大小
            if self.optimize_file_size(gif_path, output_path, params):
                result['file_size_after'] = os.path.getsize(output_path)
                result['success'] = True
                
                compression_ratio = (1 - result['file_size_after'] / result['file_size_before']) * 100
                result['message'] = (f"Success: {gif_info['size']} -> {params['output_width']}x{params['output_height']}, "
                                   f"{result['file_size_after']/1024:.1f}KB ({compression_ratio:.1f}% compression)")
            else:
                result['message'] = "Failed to optimize file size within limits"
            
        except Exception as e:
            result['message'] = f"Conversion failed: {str(e)}"
            self.logger.error(f"Error converting {gif_path}: {e}")
        
        finally:
            result['processing_time'] = time.time() - start_time
        
        return result


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("🎯 Telegram WebM Sticker/Emoji Converter")
        print("符合Telegram官方要求的WebM转换器")
        print()
        print("用法:")
        print("  python telegram_webm_converter.py input.gif output.webm [--emoji]")
        print()
        print("选项:")
        print("  --emoji    生成100x100像素的emoji（默认为512px贴纸）")
        print()
        print("要求:")
        print("  - WebM格式 + VP9编码")
        print("  - Stickers: 512px一边，另一边≤512px")  
        print("  - Emoji: 100x100px")
        print("  - ≤3秒时长，≤30FPS，≤256KB文件大小")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    is_emoji = '--emoji' in sys.argv
    
    # 配置转换器
    config = TelegramWebMConfig(
        output_type="emoji" if is_emoji else "sticker"
    )
    
    converter = TelegramWebMConverter(config)
    
    print(f"🎯 转换模式: {'Emoji (100x100)' if is_emoji else 'Sticker (512px)'}")
    print(f"📥 输入: {input_path}")
    print(f"📤 输出: {output_path}")
    print()
    
    # 执行转换
    result = converter.convert_gif_to_webm(input_path, output_path)
    
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"⏱️  处理时间: {result['processing_time']:.2f}秒")
        print(f"📊 文件大小: {result['file_size_before']:,} -> {result['file_size_after']:,} bytes")
    else:
        print(f"❌ 转换失败: {result['message']}")
        sys.exit(1)


if __name__ == '__main__':
    main()