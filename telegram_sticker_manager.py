#!/usr/bin/env python3
"""
Telegram 表情包管理器 - 完整 CRUD 操作工具

支持对现有Telegram表情包进行全面管理：
- 查看表情包详细信息
- 添加/删除贴纸  
- 修改emoji和关键词
- 调整贴纸顺序
- 克隆表情包
- 备份表情包数据
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional
from telegram_api_uploader import TelegramStickerUploader, load_env_file

def get_proxy_config_from_env() -> Optional[Dict]:
    """从环境变量获取代理配置"""
    env_vars = load_env_file()
    
    if env_vars.get('PROXY_ENABLED') != 'true':
        return None
    
    proxy_type = env_vars.get('PROXY_TYPE', 'http')
    proxy_host = env_vars.get('PROXY_HOST', '')
    proxy_port = env_vars.get('PROXY_PORT', '')
    
    if not proxy_host or not proxy_port:
        return None
    
    # 构建代理URL
    if env_vars.get('PROXY_AUTH_ENABLED') == 'true':
        username = env_vars.get('PROXY_USERNAME', '')
        password = env_vars.get('PROXY_PASSWORD', '')
        if username and password:
            if proxy_type == 'http':
                proxy_url = f"http://{username}:{password}@{proxy_host}:{proxy_port}"
            else:
                proxy_url = f"{proxy_type}://{username}:{password}@{proxy_host}:{proxy_port}"
        else:
            proxy_url = f"{proxy_type}://{proxy_host}:{proxy_port}"
    else:
        proxy_url = f"{proxy_type}://{proxy_host}:{proxy_port}"
    
    return {
        'http': proxy_url,
        'https': proxy_url
    }

class TelegramStickerManager:
    """Telegram表情包管理器"""
    
    def __init__(self, bot_token: str):
        proxy_config = get_proxy_config_from_env()
        self.uploader = TelegramStickerUploader(bot_token, proxy_config)
        self.bot_info = self.uploader.bot_info
        self.bot_username = self.uploader.bot_username
    
    def list_stickers(self, pack_name: str) -> bool:
        """列出表情包中的所有贴纸"""
        print(f"📦 分析表情包: {pack_name}")
        print("=" * 60)
        
        analysis = self.uploader.analyze_sticker_set(pack_name)
        if 'error' in analysis:
            print(f"❌ {analysis['error']}")
            return False
        
        print(f"📝 标题: {analysis['title']}")
        print(f"🏷️ 名称: {analysis['name']}")
        print(f"🎨 类型: {analysis['sticker_type']}")
        print(f"📊 总数: {analysis['total_stickers']} 个贴纸")
        print(f"🎬 动画: {'是' if analysis['is_animated'] else '否'}")
        print(f"📹 视频: {'是' if analysis['is_video'] else '否'}")
        print()
        
        print("📋 贴纸列表:")
        print("-" * 60)
        for sticker in analysis['stickers']:
            print(f"  [{sticker['position']:2d}] {sticker['emoji']} - {sticker['file_id'][:20]}...")
            print(f"       尺寸: {sticker['width']}×{sticker['height']}px")
        
        print()
        print("📊 Emoji 统计:")
        for emoji, count in analysis['emoji_stats'].items():
            print(f"  {emoji}: {count} 次")
        
        return True
    
    def delete_sticker(self, file_id: str) -> bool:
        """删除指定贴纸"""
        print(f"🗑️ 删除贴纸: {file_id[:20]}...")
        return self.uploader.delete_sticker_from_set(file_id)
    
    def delete_pack(self, pack_name: str) -> bool:
        """删除整个表情包"""
        print(f"⚠️ 即将删除整个表情包: {pack_name}")
        confirm = input("确认删除？输入 'DELETE' 确认: ")
        
        if confirm != "DELETE":
            print("❌ 取消删除")
            return False
        
        print(f"🗑️ 删除表情包: {pack_name}")
        return self.uploader.delete_sticker_set(pack_name)
    
    def update_emoji(self, file_id: str, emoji_list: List[str]) -> bool:
        """更新贴纸emoji"""
        print(f"🎨 更新emoji: {file_id[:20]}... -> {emoji_list}")
        return self.uploader.set_sticker_emoji_list(file_id, emoji_list)
    
    def update_keywords(self, file_id: str, keywords: List[str]) -> bool:
        """更新贴纸关键词"""
        print(f"🔍 更新关键词: {file_id[:20]}... -> {keywords}")
        return self.uploader.set_sticker_keywords(file_id, keywords)
    
    def move_sticker(self, file_id: str, position: int) -> bool:
        """移动贴纸位置"""
        print(f"📍 移动贴纸: {file_id[:20]}... -> 位置 {position}")
        return self.uploader.set_sticker_position_in_set(file_id, position)
    
    def clone_pack(self, source_name: str, target_name: str, target_title: str, user_id: int) -> bool:
        """克隆表情包"""
        print(f"📋 克隆表情包: {source_name} -> {target_name}")
        result = self.uploader.clone_sticker_set(source_name, target_name, target_title, user_id)
        
        if result['success']:
            print(f"✅ 克隆成功！")
            print(f"📱 新表情包链接: {result['pack_url']}")
            print(f"📊 克隆贴纸数: {result['cloned_stickers']}")
            return True
        else:
            print(f"❌ 克隆失败: {result['error']}")
            return False
    
    def backup_pack(self, pack_name: str) -> bool:
        """备份表情包"""
        print(f"💾 备份表情包: {pack_name}")
        result = self.uploader.backup_sticker_set(pack_name)
        
        if result['success']:
            print(f"✅ 备份完成: {result['backup_file']}")
            return True
        else:
            print(f"❌ 备份失败: {result.get('error', 'Unknown error')}")
            return False
    
    def batch_update(self, updates_file: str) -> bool:
        """批量更新（从JSON文件）"""
        print(f"📄 批量更新: {updates_file}")
        
        try:
            with open(updates_file, 'r', encoding='utf-8') as f:
                updates = json.load(f)
            
            result = self.uploader.batch_update_emojis(updates)
            print(f"📊 批量更新结果: 成功 {result['successful']}, 失败 {result['failed']}")
            
            if result['errors']:
                print("❌ 错误详情:")
                for error in result['errors']:
                    print(f"  - {error}")
            
            return result['successful'] > 0
            
        except Exception as e:
            print(f"❌ 读取更新文件失败: {e}")
            return False


def show_help():
    """显示帮助信息"""
    print("🛠️ Telegram 表情包管理器")
    print("完整的表情包 CRUD 操作工具")
    print()
    print("用法:")
    print("  python telegram_sticker_manager.py <command> [options]")
    print()
    print("命令:")
    print("  list <pack_name>                     - 列出表情包详情")
    print("  delete-sticker <file_id>             - 删除指定贴纸")
    print("  delete-pack <pack_name>              - 删除整个表情包")
    print("  update-emoji <file_id> <emoji1,emoji2>  - 更新贴纸emoji")
    print("  update-keywords <file_id> <word1,word2> - 更新搜索关键词")
    print("  move <file_id> <position>            - 移动贴纸位置")
    print("  clone <source> <target> <title>      - 克隆表情包")
    print("  backup <pack_name>                   - 备份表情包")
    print("  batch-update <json_file>             - 批量更新")
    print()
    print("配置:")
    print("  通过 .env 文件设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_USER_ID")
    print("  或使用环境变量")
    print()
    print("示例:")
    print("  python telegram_sticker_manager.py list my_stickers_by_bot")
    print("  python telegram_sticker_manager.py update-emoji BAADBAADrwADBREAAT... 😀,😃,😄")
    print("  python telegram_sticker_manager.py clone source_pack target_pack \"新表情包\"")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1]
    
    if command in ['--help', '-h', 'help']:
        show_help()
        return
    
    # 加载配置
    env_vars = load_env_file()
    bot_token = env_vars.get('TELEGRAM_BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
    user_id = env_vars.get('TELEGRAM_USER_ID') or os.getenv('TELEGRAM_USER_ID')
    
    if not bot_token:
        print("❌ 需要配置 TELEGRAM_BOT_TOKEN")
        print("💡 在 .env 文件中设置或使用环境变量")
        return
    
    try:
        if user_id:
            user_id = int(user_id)
    except ValueError:
        print("❌ TELEGRAM_USER_ID 必须是数字")
        return
    
    # 创建管理器
    manager = TelegramStickerManager(bot_token)
    
    # 执行命令
    try:
        if command == 'list' and len(sys.argv) >= 3:
            manager.list_stickers(sys.argv[2])
        
        elif command == 'delete-sticker' and len(sys.argv) >= 3:
            manager.delete_sticker(sys.argv[2])
        
        elif command == 'delete-pack' and len(sys.argv) >= 3:
            manager.delete_pack(sys.argv[2])
        
        elif command == 'update-emoji' and len(sys.argv) >= 4:
            file_id = sys.argv[2]
            emoji_list = sys.argv[3].split(',')
            manager.update_emoji(file_id, emoji_list)
        
        elif command == 'update-keywords' and len(sys.argv) >= 4:
            file_id = sys.argv[2]
            keywords = sys.argv[3].split(',') if sys.argv[3] else []
            manager.update_keywords(file_id, keywords)
        
        elif command == 'move' and len(sys.argv) >= 4:
            file_id = sys.argv[2]
            position = int(sys.argv[3])
            manager.move_sticker(file_id, position)
        
        elif command == 'clone' and len(sys.argv) >= 5:
            if not user_id:
                print("❌ 克隆表情包需要配置 TELEGRAM_USER_ID")
                return
            source = sys.argv[2]
            target = sys.argv[3]
            title = sys.argv[4]
            manager.clone_pack(source, target, title, user_id)
        
        elif command == 'backup' and len(sys.argv) >= 3:
            manager.backup_pack(sys.argv[2])
        
        elif command == 'batch-update' and len(sys.argv) >= 3:
            manager.batch_update(sys.argv[2])
        
        else:
            print("❌ 无效的命令或参数不足")
            print("💡 使用 --help 查看帮助")
    
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()