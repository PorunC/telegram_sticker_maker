#!/usr/bin/env python3
"""
Telegram API 表情包自动上传器

通过 Telegram Bot API 直接创建和上传表情包，无需手动操作 @stickers 机器人
"""

import os
import sys
import json
import time
import logging
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

class TelegramStickerUploader:
    """Telegram 表情包自动上传器"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_base = f"https://api.telegram.org/bot{bot_token}/"
        self.logger = self._setup_logger()
        
        # 验证 Bot Token
        if not self._validate_token():
            raise ValueError("Invalid bot token or bot is not accessible")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _validate_token(self) -> bool:
        """验证 Bot Token"""
        try:
            response = self._api_request('getMe')
            if response and response.get('ok'):
                bot_info = response['result']
                self.logger.info(f"✓ Connected to bot: @{bot_info.get('username', 'unknown')}")
                return True
        except Exception as e:
            self.logger.error(f"Token validation failed: {e}")
        return False
    
    def _api_request(self, method: str, data: Dict = None, files: Dict = None) -> Optional[Dict]:
        """发送 API 请求"""
        url = urljoin(self.api_base, method)
        
        try:
            if files:
                response = requests.post(url, data=data, files=files, timeout=30)
            else:
                # 对于某些API方法（如createNewStickerSet），使用form-data而不是JSON
                if method in ['createNewStickerSet', 'addStickerToSet']:
                    response = requests.post(url, data=data, timeout=30)
                else:
                    response = requests.post(url, json=data, timeout=30)
            
            response.raise_for_status()
            result = response.json()
            
            # 记录API错误详情
            if not result.get('ok'):
                self.logger.error(f"Telegram API error for {method}: {result.get('description', 'Unknown error')}")
                if 'parameters' in result:
                    self.logger.error(f"Error parameters: {result['parameters']}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed for {method}: {e}")
            try:
                if e.response:
                    error_response = e.response.json()
                    self.logger.error(f"Telegram API error detail: {error_response}")
                    return error_response  # 返回错误响应而不是None
            except:
                pass
            return None
    
    def upload_sticker_file(self, user_id: int, sticker_file: str, sticker_format: str) -> Optional[str]:
        """上传贴纸文件到 Telegram"""
        if not os.path.exists(sticker_file):
            self.logger.error(f"Sticker file not found: {sticker_file}")
            return None
        
        # 根据文件扩展名确定格式
        file_ext = Path(sticker_file).suffix.lower()
        if file_ext in ['.png', '.webp']:
            format_type = 'static'
        elif file_ext == '.webm':
            format_type = 'video'
        elif file_ext == '.tgs':
            format_type = 'animated'
        else:
            self.logger.warning(f"Unknown file format: {file_ext}, assuming static")
            format_type = 'static'
        
        self.logger.info(f"Uploading {format_type} sticker: {os.path.basename(sticker_file)}")
        
        with open(sticker_file, 'rb') as f:
            files = {
                'sticker': (os.path.basename(sticker_file), f, self._get_mime_type(file_ext))
            }
            
            # 根据Telegram API文档，参数应该是sticker_type
            sticker_type_map = {
                'static': 'regular',
                'video': 'video',
                'animated': 'animated'
            }
            
            data = {
                'user_id': user_id,
                'sticker_type': sticker_type_map.get(format_type, 'regular')
            }
            
            response = self._api_request('uploadStickerFile', data=data, files=files)
            
        if response and response.get('ok'):
            file_id = response['result']['file_id']
            self.logger.info(f"✓ Uploaded successfully, file_id: {file_id}")
            return file_id
        else:
            error_msg = response.get('description', 'Unknown error') if response else 'No response'
            self.logger.error(f"Upload failed: {error_msg}")
            return None
    
    def _get_mime_type(self, file_ext: str) -> str:
        """获取 MIME 类型"""
        mime_types = {
            '.png': 'image/png',
            '.webp': 'image/webp', 
            '.webm': 'video/webm',
            '.tgs': 'application/x-tgsticker'
        }
        return mime_types.get(file_ext, 'application/octet-stream')
    
    def create_sticker_set(self, user_id: int, name: str, title: str, 
                          stickers: List[Dict], sticker_format: str = 'static') -> bool:
        """创建新的表情包"""
        self.logger.info(f"Creating sticker set: {title}")
        
        # 根据Telegram API文档，参数应该是sticker_type而不是sticker_format
        sticker_type_map = {
            'static': 'regular',
            'video': 'video', 
            'animated': 'animated'
        }
        
        data = {
            'user_id': user_id,
            'name': name,
            'title': title,
            'stickers': json.dumps(stickers),
            'sticker_type': sticker_type_map.get(sticker_format, 'regular')
        }
        
        response = self._api_request('createNewStickerSet', data=data)
        
        if response and response.get('ok'):
            self.logger.info(f"✓ Sticker set created successfully!")
            return True
        else:
            error_msg = response.get('description', 'Unknown error') if response else 'No response'
            self.logger.error(f"Failed to create sticker set: {error_msg}")
            return False
    
    def create_sticker_set_with_files(self, user_id: int, name: str, title: str, 
                                    stickers: List[Dict], sticker_format: str, files: Dict) -> bool:
        """创建新的表情包（直接上传文件）"""
        self.logger.info(f"Creating sticker set with files: {title}")
        
        # 根据最新的Telegram Bot API，不再需要sticker_type参数
        # API会根据InputSticker对象中的format字段自动识别类型
        data = {
            'user_id': user_id,
            'name': name,
            'title': title,
            'stickers': json.dumps(stickers)  # InputSticker对象数组
        }
        
        # 准备文件数据
        files_data = {}
        for key, file_handle in files.items():
            file_handle.seek(0)  # 重置文件指针
            files_data[key] = file_handle
        
        # 调试信息
        self.logger.info(f"Creating sticker set with data: {data}")
        self.logger.info(f"Files: {list(files_data.keys())}")
        
        response = self._api_request('createNewStickerSet', data=data, files=files_data)
        
        if response and response.get('ok'):
            self.logger.info(f"✓ Sticker set created successfully!")
            return True
        else:
            error_msg = response.get('description', 'Unknown error') if response else 'No response'
            self.logger.error(f"Failed to create sticker set: {error_msg}")
            if response:
                self.logger.error(f"Full response: {response}")
            return False
    
    def add_sticker_to_set(self, user_id: int, name: str, sticker: Dict) -> bool:
        """向现有表情包添加贴纸"""
        self.logger.info(f"Adding sticker to set: {name}")
        
        data = {
            'user_id': user_id,
            'name': name,
            'sticker': json.dumps(sticker)
        }
        
        response = self._api_request('addStickerToSet', data=data)
        
        if response and response.get('ok'):
            self.logger.info("✓ Sticker added successfully!")
            return True
        else:
            error_msg = response.get('description', 'Unknown error') if response else 'No response'
            self.logger.error(f"Failed to add sticker: {error_msg}")
            return False
    
    def get_sticker_set(self, name: str) -> Optional[Dict]:
        """获取表情包信息"""
        data = {'name': name}
        response = self._api_request('getStickerSet', data=data)
        
        if response and response.get('ok'):
            return response['result']
        return None
    
    def upload_sticker_pack(self, user_id: int, pack_name: str, pack_title: str,
                           sticker_files: List[str], emojis: List[str] = None) -> Dict[str, Any]:
        """上传完整的表情包"""
        result = {
            'success': False,
            'pack_name': pack_name,
            'pack_url': '',
            'uploaded_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        if not sticker_files:
            result['errors'].append("No sticker files provided")
            return result
        
        # 默认 emoji
        if not emojis:
            emojis = ["😀"] * len(sticker_files)
        elif len(emojis) < len(sticker_files):
            # 补充默认 emoji
            emojis.extend(["😀"] * (len(sticker_files) - len(emojis)))
        
        self.logger.info(f"Starting upload of {len(sticker_files)} stickers...")
        
        # 确定表情包格式
        first_file = sticker_files[0]
        file_ext = Path(first_file).suffix.lower()
        
        if file_ext in ['.png', '.webp']:
            sticker_format = 'static'
        elif file_ext == '.webm':
            sticker_format = 'video' 
        elif file_ext == '.tgs':
            sticker_format = 'animated'
        else:
            sticker_format = 'static'
        
        # 准备文件上传数据（新的API直接在createNewStickerSet中上传）
        sticker_data_list = []
        files_dict = {}
        
        for i, (sticker_file, emoji) in enumerate(zip(sticker_files, emojis)):
            self.logger.info(f"Processing {i+1}/{len(sticker_files)}: {os.path.basename(sticker_file)}")
            
            if not os.path.exists(sticker_file):
                result['failed_count'] += 1
                result['errors'].append(f"File not found: {os.path.basename(sticker_file)}")
                continue
            
            # 准备文件数据
            file_key = f"sticker_{i}"
            files_dict[file_key] = open(sticker_file, 'rb')
            
            # 根据文件格式设置format字段（保持video格式用于动态表情包）
            format_map = {
                'static': 'static',
                'video': 'video',    # WebM视频贴纸保持video格式
                'animated': 'animated'
            }
            
            sticker_data = {
                'sticker': f"attach://{file_key}",
                'emoji_list': [emoji],
                'format': format_map.get(sticker_format, 'static')
            }
            sticker_data_list.append(sticker_data)
            result['uploaded_count'] += 1
        
        if not sticker_data_list:
            result['errors'].append("No valid stickers to upload")
            return result
        
        # 创建表情包（直接上传文件）
        try:
            success = self.create_sticker_set_with_files(
                user_id, pack_name, pack_title, sticker_data_list, sticker_format, files_dict
            )
        finally:
            # 关闭文件句柄
            for f in files_dict.values():
                f.close()
        
        if success:
            result['success'] = True
            result['pack_url'] = f"https://t.me/addstickers/{pack_name}"
            self.logger.info(f"🎉 Sticker pack created successfully!")
            self.logger.info(f"📱 Share URL: {result['pack_url']}")
        else:
            result['errors'].append("Failed to create sticker set")
        
        return result
    
    def generate_pack_name(self, base_name: str, user_id: int) -> str:
        """生成唯一的表情包名称"""
        # Telegram 表情包名称规则: 只能包含字母、数字、下划线，以 _by_botname 结尾
        
        # 清理基础名称
        import re
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', base_name)
        clean_name = re.sub(r'_+', '_', clean_name)  # 合并多个下划线
        clean_name = clean_name.strip('_')  # 移除首尾下划线
        
        if not clean_name:
            clean_name = 'stickers'
        
        # 确保名称不超长（Telegram限制64字符）
        if len(clean_name) > 30:
            clean_name = clean_name[:30]
        
        # 获取 bot username
        bot_info = self._api_request('getMe')
        bot_username = bot_info['result']['username'] if bot_info and bot_info.get('ok') else 'bot'
        
        # 生成候选名称
        timestamp = int(time.time())
        candidates = [
            f"{clean_name}_by_{bot_username}",
            f"{clean_name}_{user_id}_by_{bot_username}",  
            f"{clean_name}_{timestamp}_by_{bot_username}"
        ]
        
        # 检查名称是否已存在
        for name in candidates:
            if len(name) <= 64:  # Telegram名称长度限制
                existing = self.get_sticker_set(name)
                if existing is None:  # None表示不存在
                    self.logger.info(f"Generated pack name: {name}")
                    return name
                else:
                    self.logger.info(f"Pack name {name} already exists, trying next...")
        
        # 如果都存在，使用时间戳生成唯一名称
        final_name = f"{clean_name}_{timestamp}_{user_id}_by_{bot_username}"
        if len(final_name) > 64:
            # 截断以适应长度限制
            max_clean_len = 64 - len(f"_{timestamp}_{user_id}_by_{bot_username}")
            clean_name = clean_name[:max_clean_len]
            final_name = f"{clean_name}_{timestamp}_{user_id}_by_{bot_username}"
        
        self.logger.info(f"Generated pack name: {final_name}")
        return final_name


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


def get_bot_token() -> Optional[str]:
    """获取 Bot Token"""
    # 优先从 .env 文件获取
    env_vars = load_env_file()
    token = env_vars.get('TELEGRAM_BOT_TOKEN')
    if token:
        return token
    
    # 从环境变量获取
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if token:
        return token
    
    # 从配置文件获取（向后兼容）
    config_file = 'telegram_bot.conf'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return f.read().strip()
        except Exception:
            pass
    
    # 提示用户输入
    print("🤖 需要 Telegram Bot Token 来自动上传表情包")
    print()
    print("📋 配置方式:")
    print("1. 创建 .env 文件并设置 TELEGRAM_BOT_TOKEN=your_token")
    print("2. 或设置环境变量 TELEGRAM_BOT_TOKEN")
    print("3. 或在此处手动输入")
    print()
    print("📋 获取 Bot Token 步骤:")
    print("1. 打开 Telegram，搜索 @BotFather")
    print("2. 发送 /newbot 创建新机器人")
    print("3. 按提示设置机器人名称")
    print("4. 复制获得的 Bot Token")
    print()
    
    token = input("请输入 Bot Token: ").strip()
    if token:
        # 优先保存到 .env 文件
        try:
            env_content = f"TELEGRAM_BOT_TOKEN={token}\n"
            if os.path.exists('.env'):
                # 如果 .env 文件存在，读取现有内容并更新
                with open('.env', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                updated = False
                for i, line in enumerate(lines):
                    if line.strip().startswith('TELEGRAM_BOT_TOKEN='):
                        lines[i] = f"TELEGRAM_BOT_TOKEN={token}\n"
                        updated = True
                        break
                
                if not updated:
                    lines.append(f"TELEGRAM_BOT_TOKEN={token}\n")
                
                with open('.env', 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            else:
                # 创建新的 .env 文件
                with open('.env', 'w', encoding='utf-8') as f:
                    f.write(env_content)
            
            print(f"✅ Token 已保存到 .env 文件")
        except Exception as e:
            # 备选方案：保存到配置文件（向后兼容）
            try:
                with open(config_file, 'w') as f:
                    f.write(token)
                print(f"✅ Token 已保存到 {config_file}")
            except Exception:
                print("⚠️ 保存配置失败，请手动创建 .env 文件")
    
    return token


def main():
    """测试函数"""
    if len(sys.argv) < 2:
        print("🤖 Telegram API 表情包上传器")
        print()
        print("用法:")
        print("  python telegram_api_uploader.py <sticker_directory> [user_id]")
        print()
        print("参数:")
        print("  sticker_directory  包含表情包文件的目录")
        print("  user_id           Telegram 用户 ID (可选，用于测试)")
        print()
        print("环境变量:")
        print("  TELEGRAM_BOT_TOKEN  Bot Token")
        return
    
    sticker_dir = sys.argv[1]
    user_id = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not os.path.isdir(sticker_dir):
        print(f"❌ 目录不存在: {sticker_dir}")
        return
    
    # 获取 Bot Token
    bot_token = get_bot_token()
    if not bot_token:
        print("❌ 未提供 Bot Token")
        return
    
    if not user_id:
        print("⚠️ 未提供用户 ID，这是测试模式")
        print("💡 在实际使用中，需要用户的 Telegram ID")
        return
    
    try:
        # 创建上传器
        uploader = TelegramStickerUploader(bot_token)
        
        # 查找表情包文件
        sticker_files = []
        for ext in ['.png', '.webp', '.webm', '.tgs']:
            sticker_files.extend(Path(sticker_dir).glob(f"*{ext}"))
        
        sticker_files = [str(f) for f in sticker_files]
        
        if not sticker_files:
            print(f"❌ 在 {sticker_dir} 中未找到表情包文件")
            return
        
        print(f"📁 找到 {len(sticker_files)} 个表情包文件")
        
        # 生成表情包信息
        pack_name = uploader.generate_pack_name(Path(sticker_dir).name, user_id)
        pack_title = f"{Path(sticker_dir).name} Stickers"
        
        # 上传表情包
        result = uploader.upload_sticker_pack(
            user_id=user_id,
            pack_name=pack_name,
            pack_title=pack_title,
            sticker_files=sticker_files
        )
        
        # 显示结果
        if result['success']:
            print(f"🎉 表情包上传成功!")
            print(f"📱 分享链接: {result['pack_url']}")
            print(f"📊 成功: {result['uploaded_count']}, 失败: {result['failed_count']}")
        else:
            print(f"❌ 表情包上传失败")
            for error in result['errors']:
                print(f"   {error}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()